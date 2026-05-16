#!/bin/bash

# Submit PR Comments Script
# Submits code review findings from JSON to GitHub PR as inline comments

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source libraries
source "$SCRIPT_DIR/lib/comment_formatter.sh"
source "$SCRIPT_DIR/lib/github_api.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo "======================================================================"
    echo "$1"
    echo "======================================================================"
    echo ""
}

# Parse command line arguments
parse_args() {
    REVIEW_FILE=""
    PR_NUMBER=""
    DRY_RUN=false
    SEVERITY_FILTER=""
    TYPE_FILTER=""
    EXCLUDE_SEVERITY=""
    BATCH_SIZE="${MAX_COMMENTS_PER_BATCH:-30}"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --severity)
                SEVERITY_FILTER="$2"
                shift 2
                ;;
            --type)
                TYPE_FILTER="$2"
                shift 2
                ;;
            --exclude-severity)
                EXCLUDE_SEVERITY="$2"
                shift 2
                ;;
            --batch-size)
                BATCH_SIZE="$2"
                shift 2
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$REVIEW_FILE" ]; then
                    REVIEW_FILE="$1"
                elif [ -z "$PR_NUMBER" ]; then
                    PR_NUMBER="$1"
                else
                    print_error "Unknown argument: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [ -z "$REVIEW_FILE" ] || [ -z "$PR_NUMBER" ]; then
        print_error "Missing required arguments"
        show_usage
        exit 1
    fi
    
    local review_root="${GITHUB_WORKSPACE:-$PWD}"
    if [ -f "$REVIEW_FILE" ]; then
        REVIEW_FILE="$(cd "$(dirname "$REVIEW_FILE")" && pwd)/$(basename "$REVIEW_FILE")"
    elif [ -f "$review_root/$REVIEW_FILE" ]; then
        REVIEW_FILE="$review_root/$REVIEW_FILE"
    else
        print_error "Review file not found: $REVIEW_FILE"
        exit 1
    fi
}

# Show usage
show_usage() {
    cat <<EOF
Submit PR Comments - Post code review findings to GitHub PR

Usage:
  $0 <review_file> <pr_number> [options]

Arguments:
  review_file       Path to review JSON file (e.g., review1.json)
  pr_number         GitHub PR number

Options:
  --dry-run                Preview comments without submitting
  --severity <level>       Only submit findings of this severity (high|medium|low)
  --type <type>            Only submit findings of this type (bug|security|maintainability)
  --exclude-severity <lvl> Exclude findings of this severity
  --batch-size <n>         Number of comments per batch (default: 30)
  -h, --help               Show this help message

Environment Variables:
  GITHUB_TOKEN             GitHub personal access token (required)
  GITHUB_OWNER             Repository owner/organization
  GITHUB_REPO              Repository name

Examples:
  # Submit all findings to PR #123
  $0 review1.json 123

  # Preview without submitting
  $0 review1.json 123 --dry-run

  # Only submit high severity findings
  $0 review1.json 123 --severity high

  # Submit bugs and security issues only
  $0 review1.json 123 --type bug,security

  # Exclude low severity findings
  $0 review1.json 123 --exclude-severity low

Configuration:
  Set up config/github.env with:
    GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
    GITHUB_OWNER="your-org"
    GITHUB_REPO="pay-go-metrics-monitor"
EOF
}

# Filter findings based on criteria
filter_findings() {
    local review_file="$1"
    local jq_filter=".findings[]"
    
    # Apply severity filter
    if [ -n "$SEVERITY_FILTER" ]; then
        IFS=',' read -ra SEVERITIES <<< "$SEVERITY_FILTER"
        local severity_conditions=""
        for sev in "${SEVERITIES[@]}"; do
            if [ -n "$severity_conditions" ]; then
                severity_conditions="$severity_conditions or "
            fi
            severity_conditions="${severity_conditions}.severity == \"$sev\""
        done
        jq_filter="$jq_filter | select($severity_conditions)"
    fi
    
    # Apply type filter
    if [ -n "$TYPE_FILTER" ]; then
        IFS=',' read -ra TYPES <<< "$TYPE_FILTER"
        local type_conditions=""
        for type in "${TYPES[@]}"; do
            if [ -n "$type_conditions" ]; then
                type_conditions="$type_conditions or "
            fi
            type_conditions="${type_conditions}.type == \"$type\""
        done
        jq_filter="$jq_filter | select($type_conditions)"
    fi
    
    # Apply exclude severity filter
    if [ -n "$EXCLUDE_SEVERITY" ]; then
        IFS=',' read -ra EXCLUDE_SEVS <<< "$EXCLUDE_SEVERITY"
        for sev in "${EXCLUDE_SEVS[@]}"; do
            jq_filter="$jq_filter | select(.severity != \"$sev\")"
        done
    fi
    
    jq -c "$jq_filter" "$review_file"
}

# Submit comments to PR
submit_comments() {
    local review_file="$1"
    local pr_number="$2"
    
    print_header "📤 Submitting Review Comments to PR #$pr_number"
    
    # Validate environment
    if [ -z "$GITHUB_TOKEN" ]; then
        print_error "GITHUB_TOKEN not set"
        echo "Set it via: export GITHUB_TOKEN='ghp_xxxxxxxxxxxx'"
        exit 1
    fi
    
    if [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ]; then
        print_error "GITHUB_OWNER and GITHUB_REPO must be set"
        echo "Set them in config/github.env or as environment variables"
        exit 1
    fi
    
    print_info "Repository: $GITHUB_OWNER/$GITHUB_REPO"
    print_info "PR Number: $pr_number"
    print_info "Review file: $review_file"
    
    # Validate token
    echo ""
    print_info "Validating GitHub token..."
    if ! validate_token; then
        exit 1
    fi
    
    # Check rate limit
    echo ""
    print_info "Checking API rate limit..."
    check_rate_limit
    
    # Get PR information
    echo ""
    print_info "Fetching PR information..."
    local commit_sha=$(get_pr_commit_sha "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number")
    if [ $? -ne 0 ]; then
        print_error "Failed to get PR commit SHA"
        exit 1
    fi
    print_success "Commit SHA: $commit_sha"
    
    # Get PR files
    print_info "Fetching PR files..."
    local pr_files=$(get_pr_files "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number")
    if [ $? -ne 0 ]; then
        print_error "Failed to get PR files"
        exit 1
    fi
    local pr_file_count=$(echo "$pr_files" | wc -l | xargs)
    print_success "PR contains $pr_file_count file(s)"
    
    # Filter findings
    echo ""
    print_info "Filtering findings..."
    local filtered_findings=$(filter_findings "$review_file")
    local total_findings=$(echo "$filtered_findings" | wc -l | xargs)
    
    if [ -z "$filtered_findings" ] || [ "$total_findings" -eq 0 ]; then
        print_warning "No findings match the filter criteria"
        exit 0
    fi
    
    print_success "Found $total_findings finding(s) to process"
    
    # Group findings by file
    echo ""
    print_info "Processing findings by file..."
    
    local comments_submitted=0
    local comments_skipped=0
    local files_processed=0
    local failed_comments=0
    local failed_summary=""
    
    # Get unique files from filtered findings
    local files=$(echo "$filtered_findings" | jq -r '.file' | sort -u)
    
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        
        # Check if file is in PR
        if ! echo "$pr_files" | grep -q "^${file}$"; then
            print_warning "File not in PR (skipping): $file"
            local skip_count=$(echo "$filtered_findings" | jq -c "select(.file == \"$file\")" | wc -l | xargs)
            comments_skipped=$((comments_skipped + skip_count))
            continue
        fi
        
        files_processed=$((files_processed + 1))
        
        # Get findings for this file
        local file_findings=$(echo "$filtered_findings" | jq -c "select(.file == \"$file\")")
        local file_finding_count=$(echo "$file_findings" | wc -l | xargs)
        
        print_info "Processing $file ($file_finding_count finding(s))..."
        
        while IFS= read -r finding; do
            [ -z "$finding" ] && continue
            
            local line=$(echo "$finding" | jq -r '.line')
            local title=$(echo "$finding" | jq -r '.title // .description // "Unknown finding"')
            local severity=$(echo "$finding" | jq -r '.severity // "unknown"')
            local comment_body=$(format_finding_with_code "$finding")
            
            if [ "$DRY_RUN" = true ]; then
                print_info "[DRY RUN] Would submit comment for $file:$line"
                comments_submitted=$((comments_submitted + 1))
            else
                print_info "Submitting comment for $file:$line..."
                if create_review_comment "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number" "$commit_sha" "$file" "$line" "$comment_body"; then
                    print_success "Comment submitted for $file:$line"
                    comments_submitted=$((comments_submitted + 1))
                else
                    print_error "Failed to submit comment for $file:$line"
                    comments_skipped=$((comments_skipped + 1))
                    failed_comments=$((failed_comments + 1))
                    failed_summary="${failed_summary}- [${severity}] ${file}:${line} - ${title}"$'\n'
                fi
                sleep 1
            fi
        done <<< "$file_findings"
        
        print_success "Completed $file"
        echo ""
    done <<< "$files"
    
    # Print summary
    print_header "📊 Summary"
    echo "   Files processed: $files_processed"
    echo "   Comments submitted: $comments_submitted"
    echo "   Comments skipped: $comments_skipped"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        print_info "🔍 DRY RUN MODE - No comments were actually submitted"
        return 0
    fi
    
    if [ "$failed_comments" -gt 0 ]; then
        print_warning "Failed inline comments summary:"
        echo "$failed_summary"
        return 1
    fi
    
    if [ "$comments_submitted" -eq 0 ]; then
        print_error "No review comments were submitted"
        return 1
    fi
    
    print_success "🎉 Review comments submitted successfully!"
    echo ""
    print_info "🔗 View PR: https://github.com/$GITHUB_OWNER/$GITHUB_REPO/pull/$pr_number"
}

# Main function
main() {
    parse_args "$@"
    submit_comments "$REVIEW_FILE" "$PR_NUMBER"
}

main "$@"

# Made with Bob
