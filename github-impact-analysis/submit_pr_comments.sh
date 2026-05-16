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
    
    if [ ! -f "$REVIEW_FILE" ]; then
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
    
    # Check JSON structure - support both old (.findings[]) and new (.files[].issues[]) formats
    local has_findings=$(jq -r 'has("findings")' "$review_file" 2>/dev/null)
    local has_files=$(jq -r 'has("files")' "$review_file" 2>/dev/null)
    
    if [ "$has_files" = "true" ]; then
        # New format: .files[].issues[]
        local jq_filter='.files[] | .file_path as $file | .issues[] | . + {file: $file, line: .line}'
    elif [ "$has_findings" = "true" ]; then
        # Old format: .findings[]
        local jq_filter=".findings[]"
    else
        echo "Error: Unknown JSON format in $review_file" >&2
        return 1
    fi
    
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
    local skipped_findings_list=""  # Track skipped findings for summary
    
    # Get unique files from filtered findings
    local files=$(echo "$filtered_findings" | jq -r '.file' | sort -u)
    
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        
        # File paths are now relative (Bob runs from GITHUB_WORKSPACE)
        local relative_file="$file"
        
        # Check if file is in PR
        if ! echo "$pr_files" | grep -q "^${relative_file}$"; then
            print_warning "File not in PR (skipping): $relative_file"
            local skip_count=$(echo "$filtered_findings" | jq -c "select(.file == \"$file\")" | wc -l | xargs)
            comments_skipped=$((comments_skipped + skip_count))
            continue
        fi
        
        files_processed=$((files_processed + 1))
        
        # Get findings for this file
        local file_findings=$(echo "$filtered_findings" | jq -c "select(.file == \"$file\")")
        local file_finding_count=$(echo "$file_findings" | wc -l | xargs)
        
        print_info "Processing $relative_file ($file_finding_count finding(s))..."
        
        # Submit comments individually to handle line validation
        local comment_count=0
        local skipped_lines=0
        
        while IFS= read -r finding; do
            [ -z "$finding" ] && continue
            
            local line=$(echo "$finding" | jq -r '.line')
            local comment_body=$(format_finding_with_code "$finding")
            
            # Create single comment for this finding
            local single_comment=$(jq -n \
                --arg path "$relative_file" \
                --argjson line "$line" \
                --arg body "$comment_body" \
                '[{path: $path, line: $line, body: $body}]')
            
            comment_count=$((comment_count + 1))
            
            # Submit individually to handle 422 errors gracefully
            if [ "$DRY_RUN" = false ]; then
                if create_review_batch "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number" "$commit_sha" "$single_comment" "Code review findings from Fixium" 2>/dev/null; then
                    comments_submitted=$((comments_submitted + 1))
                    print_success "✓ Line $line"
                else
                    print_warning "⊘ Line $line (not in PR diff, skipping)"
                    skipped_lines=$((skipped_lines + 1))
                    comments_skipped=$((comments_skipped + 1))
                    # Add to skipped findings list
                    skipped_findings_list="${skipped_findings_list}${finding}"$'\n'
                fi
            else
                print_info "[DRY RUN] Would submit comment for line $line"
                comments_submitted=$((comments_submitted + 1))
            fi
            
            # Small delay to avoid rate limiting
            sleep 0.5
        done <<< "$file_findings"
        
        # Report skipped lines for this file
        if [ $skipped_lines -gt 0 ]; then
            print_warning "Skipped $skipped_lines comment(s) on lines not in PR diff"
        fi
        
        print_success "Completed $relative_file"
        echo ""
    done <<< "$files"
    
    # Print summary
    print_header "📊 Summary"
    echo "   Files processed: $files_processed"
    echo "   Comments submitted: $comments_submitted"
    echo "   Comments skipped: $comments_skipped"
    echo ""
    
    # Post summary comment with skipped findings if any
    if [ $comments_skipped -gt 0 ] && [ "$DRY_RUN" = false ] && [ -n "$skipped_findings_list" ]; then
        echo ""
        print_info "Posting summary comment with skipped findings..."
        
        # Build summary comment
        local summary_body="## 📋 Fixium Code Review Summary\n\n"
        summary_body+="✅ **${comments_submitted}** findings posted as inline comments\n"
        summary_body+="⚠️ **${comments_skipped}** findings skipped (lines not in PR diff)\n\n"
        summary_body+="### Skipped Findings\n\n"
        summary_body+="The following findings could not be posted as inline comments because they reference lines that were not changed in this PR:\n\n"
        
        # Format skipped findings
        while IFS= read -r finding; do
            [ -z "$finding" ] && continue
            
            local file=$(echo "$finding" | jq -r '.file')
            local line=$(echo "$finding" | jq -r '.line')
            local severity=$(echo "$finding" | jq -r '.severity')
            local type=$(echo "$finding" | jq -r '.type')
            local title=$(echo "$finding" | jq -r '.title // .issue')
            local description=$(echo "$finding" | jq -r '.description // .details')
            
            summary_body+="#### $(get_severity_badge "$severity") **${severity^^}** | $(get_type_icon "$type") **${type^^}**\n"
            summary_body+="**File:** \`${file}\` (Line ${line})\n"
            summary_body+="**Issue:** ${title}\n\n"
            if [ -n "$description" ] && [ "$description" != "null" ]; then
                summary_body+="${description}\n\n"
            fi
            summary_body+="---\n\n"
        done <<< "$skipped_findings_list"
        
        summary_body+="\n*💡 Tip: These findings are on unchanged lines. Consider reviewing the entire file context.*"
        
        # Post as PR comment
        if github_client=$(command -v gh 2>/dev/null); then
            echo -e "$summary_body" | gh pr comment "$pr_number" --body-file - 2>/dev/null || \
                curl -s -X POST \
                    -H "Authorization: token $GITHUB_TOKEN" \
                    -H "Accept: application/vnd.github.v3+json" \
                    "$GITHUB_API_URL/repos/$GITHUB_OWNER/$GITHUB_REPO/issues/$pr_number/comments" \
                    -d "{\"body\": $(echo -e "$summary_body" | jq -Rs .)}" > /dev/null
        else
            curl -s -X POST \
                -H "Authorization: token $GITHUB_TOKEN" \
                -H "Accept: application/vnd.github.v3+json" \
                "$GITHUB_API_URL/repos/$GITHUB_OWNER/$GITHUB_REPO/issues/$pr_number/comments" \
                -d "{\"body\": $(echo -e "$summary_body" | jq -Rs .)}" > /dev/null
        fi
        
        print_success "Summary comment posted"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        print_info "🔍 DRY RUN MODE - No comments were actually submitted"
    else
        print_success "🎉 Review comments submitted successfully!"
        echo ""
        print_info "🔗 View PR: https://github.com/$GITHUB_OWNER/$GITHUB_REPO/pull/$pr_number"
    fi
}

# Main function
main() {
    parse_args "$@"
    submit_comments "$REVIEW_FILE" "$PR_NUMBER"
}

main "$@"

# Made with Bob
