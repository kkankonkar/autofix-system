#!/bin/bash

# Code Review Workflow Automation Script
# This script helps automate the Fixium code review workflow

set -e  # Exit on error

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

# Get script directory for finding prompts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Bob CLI is available (internal tool)
check_bob() {
    if ! command -v bob &> /dev/null; then
        print_error "Bob CLI not found. Please ensure 'bob' is in your PATH"
        exit 1
    fi
    print_success "Bob CLI found: $(which bob)"
}



# Phase 1: Review
phase1_review() {
    local target="$1"
    local output_file="${2:-review_$(date +%Y-%m-%d).json}"
    
    print_header "📋 Phase 1: Code Review"
    
    # Check if target is a file list and expand it
    if [[ "$target" == @* ]]; then
        # Target starts with @, treat as file list
        local file_list="${target:1}"  # Remove @ prefix
        
        if [ ! -f "$file_list" ]; then
            print_error "File list not found: $file_list"
            return 1
        fi
        
        print_info "File list: $file_list"
        
        # Read and expand file list into space-separated paths
        local expanded_files=""
        local file_count=0
        while IFS= read -r file_path || [ -n "$file_path" ]; do
            # Skip empty lines and comments
            [[ -z "$file_path" || "$file_path" =~ ^[[:space:]]*# ]] && continue
            
            # Trim whitespace
            file_path=$(echo "$file_path" | xargs)
            
            if [ ! -f "$file_path" ]; then
                print_warning "File not found (skipping): $file_path"
                continue
            fi
            
            expanded_files="$expanded_files $file_path"
            file_count=$((file_count + 1))
        done < "$file_list"
        
        if [ $file_count -eq 0 ]; then
            print_error "No valid files found in: $file_list"
            return 1
        fi
        
        print_success "Found $file_count valid file(s) in list"
        print_info "Expanded files: $expanded_files"
        
        # Replace target with expanded file list
        target="$expanded_files"
    else
        print_info "Target: $target"
    fi
    
    print_info "Output: $output_file"
    
    # Copy prompts to current directory so Bob can access them
    # Bob's workspace is restricted to current working directory
    if [ ! -d "prompts" ]; then
        print_info "Copying prompts to workspace..."
        cp -r "$SCRIPT_DIR/prompts" . 2>/dev/null || true
    fi
    
    # Use relative path now that prompts are in workspace
    local prompts_path="prompts/review-workflow.md"
    if [ ! -f "$prompts_path" ]; then
        print_warning "Prompts file not found, Bob will use default review criteria"
        local command="Review $target and generate $output_file with comprehensive code review"
    else
        local command="Review $target following $prompts_path and generate $output_file"
    fi
    
    print_info "Executing Fixium review..."
    print_info "Command: bob -p \"$command\" --yolo"
    echo ""
    echo "⏳ Bob is processing... (this may take several minutes)"
    echo "   If stuck for >5 minutes, press Ctrl+C and check:"
    echo "   - BOBSHELL_API_KEY is set correctly"
    echo "   - Bob CLI is working: bob --version"
    echo "   - Network connectivity to Bob API"
    echo ""
    
    # Execute Bob Shell in non-interactive mode with -p flag and --yolo for auto-approval
    # Add timestamp before and after to show it's running
    local start_time=$(date +%s)
    if ! bob -p "$command" --yolo; then
        print_error "Fixium review command failed"
        return 1
    fi
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo ""
    print_success "Bob completed in ${duration}s"
    
    echo ""
    
    if [ -f "$output_file" ]; then
        print_success "Review file created: $output_file"
        
        # Parse and display summary
        if command -v jq &> /dev/null; then
            local total=$(jq '.summary.totalFindings // 0' "$output_file")
            local critical=$(jq '.summary.critical // 0' "$output_file")
            local high=$(jq '.summary.high // 0' "$output_file")
            local medium=$(jq '.summary.medium // 0' "$output_file")
            local low=$(jq '.summary.low // 0' "$output_file")
            
            echo ""
            print_info "Review Summary:"
            echo "   Total findings: $total"
            echo "   Critical: $critical"
            echo "   High: $high"
            echo "   Medium: $medium"
            echo "   Low: $low"
        fi
        
        return 0
    else
        print_error "Review file not found: $output_file"
        return 1
    fi
}

# Phase 2: Implement
phase2_implement() {
    local review_file="$1"
    local output_file="${2:-implementation$(echo $review_file | grep -o '[0-9]*' | head -1).json}"
    
    print_header "🔧 Phase 2: Implement Fixes"
    print_info "Review file: $review_file"
    print_info "Output: $output_file"
    
    if [ ! -f "$review_file" ]; then
        print_error "Review file not found: $review_file"
        return 1
    fi
    
    local command="Implement the code review findings from $review_file and generate $output_file"
    
    print_info "Executing Fixium implementation..."
    echo ""
    
    # Execute Bob Shell in non-interactive mode with -p flag and --yolo for auto-approval
    if ! bob -p "$command" --yolo; then
        print_error "Fixium implementation command failed"
        return 1
    fi
    
    echo ""
    
    if [ -f "$output_file" ]; then
        print_success "Implementation file created: $output_file"
        
        if command -v jq &> /dev/null; then
            local total=$(jq '.summary.totalFindings // 0' "$output_file")
            local implemented=$(jq '.summary.implemented // 0' "$output_file")
            local blocked=$(jq '.summary.blocked // 0' "$output_file")
            local skipped=$(jq '.summary.skipped // 0' "$output_file")
            
            echo ""
            print_info "Implementation Summary:"
            echo "   Total findings: $total"
            echo "   Implemented: $implemented"
            echo "   Blocked: $blocked"
            echo "   Skipped: $skipped"
        fi
        
        return 0
    else
        print_error "Implementation file not found: $output_file"
        return 1
    fi
}

# Phase 3: Verify
phase3_verify() {
    local impl_file="$1"
    local review_file="$2"
    local output_file="${3:-review$(($(echo $impl_file | grep -o '[0-9]*' | head -1) + 1)).json}"
    
    print_header "✓ Phase 3: Verify Implementations"
    print_info "Implementation file: $impl_file"
    print_info "Original review: $review_file"
    print_info "Output: $output_file"
    
    if [ ! -f "$impl_file" ]; then
        print_error "Implementation file not found: $impl_file"
        return 1
    fi
    
    if [ ! -f "$review_file" ]; then
        print_error "Review file not found: $review_file"
        return 1
    fi
    
    local command="Review the implementations documented in $impl_file against the current code state. Verify each fix and check for new issues. Generate $output_file with verification results. Reference $review_file for context."
    
    print_info "Executing Fixium verification..."
    echo ""
    
    # Execute Bob Shell in non-interactive mode with -p flag and --yolo for auto-approval
    if ! bob -p "$command" --yolo; then
        print_error "Fixium verification command failed"
        return 1
    fi
    
    echo ""
    
    if [ -f "$output_file" ]; then
        print_success "Verification file created: $output_file"
        
        if command -v jq &> /dev/null; then
            local new_findings=$(jq '.summary.totalNewFindings // 0' "$output_file")
            local verified=$(jq '.implementationVerification.verified // 0' "$output_file")
            local issues=$(jq '.implementationVerification.issuesFound // 0' "$output_file")
            
            echo ""
            print_info "Verification Summary:"
            echo "   New findings: $new_findings"
            echo "   Implementations verified: $verified"
            echo "   Implementations with issues: $issues"
            
            if [ "$new_findings" -eq 0 ]; then
                print_success "🎉 No new issues - code is clean!"
                return 0
            else
                print_warning "New issues found - iteration needed"
                return 2  # Special code for "needs iteration"
            fi
        fi
        
        return 0
    else
        print_error "Verification file not found: $output_file"
        return 1
    fi
}

# Review PR workflow
review_pr() {
    local pr_number="$1"
    local output_file="${2:-review_pr${pr_number}.json}"
    local auto_submit="${3:-false}"
    
    print_header "🔍 Review Pull Request #$pr_number"
    
    # Validate environment
    if [ -z "$GITHUB_TOKEN" ]; then
        print_error "GITHUB_TOKEN not set"
        echo "Set it via: export GITHUB_TOKEN='ghp_xxxxxxxxxxxx'"
        return 1
    fi
    
    if [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ]; then
        print_error "GITHUB_OWNER and GITHUB_REPO must be set"
        echo "Set them in config/github.env or as environment variables"
        return 1
    fi
    
    print_info "Repository: $GITHUB_OWNER/$GITHUB_REPO"
    print_info "PR Number: $pr_number"
    print_info "Output: $output_file"
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Source GitHub API library
    source "$SCRIPT_DIR/lib/github_api.sh"
    
    # Validate token
    echo ""
    print_info "Validating GitHub token..."
    if ! validate_token; then
        return 1
    fi
    
    # Get PR information
    echo ""
    print_info "Fetching PR information..."
    local pr_info=$(get_pr_info "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number")
    if [ $? -ne 0 ]; then
        print_error "Failed to get PR information"
        return 1
    fi
    
    local pr_title=$(echo "$pr_info" | jq -r '.title')
    local pr_state=$(echo "$pr_info" | jq -r '.state')
    local pr_base=$(echo "$pr_info" | jq -r '.base.ref')
    
    print_success "PR Title: $pr_title"
    print_info "State: $pr_state"
    print_info "Base branch: $pr_base"
    
    if [ "$pr_state" != "open" ]; then
        print_warning "PR is not open (state: $pr_state)"
    fi
    
    # Get PR files
    echo ""
    print_info "Fetching changed files from PR..."
    local file_list="pr_${pr_number}_files.txt"
    
    local pr_files=$(get_pr_files "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number")
    if [ $? -ne 0 ]; then
        print_error "Failed to get PR files"
        return 1
    fi
    
    local file_count=$(echo "$pr_files" | wc -l | xargs)
    print_success "Found $file_count file(s) in PR"
    
    # Check if running in CI/container (files may not be checked out)
    local in_container=false
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ ! -d ".git" ]; then
        in_container=true
        print_info "Running in CI/container mode - will review PR files directly"
    fi
    
    # Filter files that exist locally (or use all files if in container)
    echo ""
    local existing_files=""
    local missing_count=0
    local existing_count=0
    
    if [ "$in_container" = true ]; then
        # In container: use all PR files (Bob will run from GITHUB_WORKSPACE)
        print_info "Using all PR files (container mode)..."
        existing_files="$pr_files"
        existing_count=$file_count
        print_success "Will review $existing_count file(s) from PR"
    else
        # Local: check which files exist
        print_info "Checking which files exist locally..."
        while IFS= read -r file; do
            [ -z "$file" ] && continue
            
            if [ -f "$file" ]; then
                existing_files="${existing_files}${file}"$'\n'
                existing_count=$((existing_count + 1))
            else
                print_warning "File not found locally (skipping): $file"
                missing_count=$((missing_count + 1))
            fi
        done <<< "$pr_files"
        
        if [ $existing_count -eq 0 ]; then
            print_error "No PR files found in current directory"
            echo ""
            print_info "This usually means:"
            echo "   1. You're not in the repository root directory"
            echo "   2. The PR is for a different repository"
            echo "   3. The files haven't been checked out locally"
            echo ""
            print_info "Solutions:"
            echo "   - cd to the repository root: cd /path/to/$GITHUB_REPO"
            echo "   - Checkout the PR branch: gh pr checkout $pr_number"
            echo "   - Or review from the PR branch directory"
            return 1
        fi
        
        print_success "Found $existing_count file(s) locally"
        if [ $missing_count -gt 0 ]; then
            print_warning "Skipped $missing_count file(s) not found locally"
        fi
    fi
    
    # Write existing files to list
    echo -n "$existing_files" > "$file_list"
    
    echo ""
    print_info "Files to review:"
    echo "$existing_files" | sed 's/^/   - /'
    
    echo ""
    print_info "Contents of file list ($file_list):"
    cat "$file_list"
    echo ""
    
    # Review the files
    echo ""
    print_header "📋 Running Code Review"
    
    if ! phase1_review "@$file_list" "$output_file"; then
        print_error "Review failed"
        rm -f "$file_list"
        return 1
    fi
    
    # Auto-submit if requested
    if [ "$auto_submit" = "true" ]; then
        echo ""
        print_header "📤 Auto-submitting Comments to PR"
        
        "$SCRIPT_DIR/submit_pr_comments.sh" "$output_file" "$pr_number"
        local submit_result=$?
        
        if [ $submit_result -eq 0 ]; then
            print_success "Comments submitted successfully!"
        else
            print_error "Failed to submit comments"
            return 1
        fi
    else
        echo ""
        print_info "Review complete. To submit comments to PR, run:"
        echo "   $0 submit $output_file $pr_number"
        echo ""
        print_info "Or submit with filtering:"
        echo "   $0 submit $output_file $pr_number --severity high"
    fi
    
    # Cleanup
    rm -f "$file_list"
    
    return 0
}
# Documentation Analysis
analyze_docs() {
    local pr_number="$1"
    local output_file="${2:-docs_analysis_pr${pr_number}.json}"
    
    print_header "📚 Analyzing Documentation Gaps for PR #$pr_number"
    
    # Validate environment
    if [ -z "$GITHUB_TOKEN" ]; then
        print_error "GITHUB_TOKEN not set"
        echo "Set it via: export GITHUB_TOKEN='ghp_xxxxxxxxxxxx'"
        return 1
    fi
    
    if [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ]; then
        print_error "GITHUB_OWNER and GITHUB_REPO must be set"
        echo "Set them in config/github.env or as environment variables"
        return 1
    fi
    
    print_info "Repository: $GITHUB_OWNER/$GITHUB_REPO"
    print_info "PR Number: $pr_number"
    print_info "Output: $output_file"
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Source GitHub API library
    source "$SCRIPT_DIR/lib/github_api.sh"
    
    # Validate token
    echo ""
    print_info "Validating GitHub token..."
    if ! validate_token; then
        return 1
    fi
    
    # Discover all documentation files
    echo ""
    print_info "Discovering documentation files..."
    local doc_files=$(find . -name "*.md" \
        -not -path "*/node_modules/*" \
        -not -path "*/.git/*" \
        -not -path "*/vendor/*" \
        -not -path "*/build/*" \
        -not -path "*/dist/*" \
        -not -path "*/__pycache__/*" \
        -not -path "*/.venv/*" \
        -not -path "*/venv/*")
    
    local doc_count=$(echo "$doc_files" | wc -l | xargs)
    print_success "Found $doc_count documentation file(s)"
    
    # Show discovered files
    echo ""
    print_info "Documentation files discovered:"
    echo "$doc_files" | head -20 | sed 's/^/   - /'
    if [ $doc_count -gt 20 ]; then
        echo "   ... and $((doc_count - 20)) more"
    fi
    
    # Get PR files
    echo ""
    print_info "Fetching changed files from PR..."
    local pr_files=$(get_pr_files "$GITHUB_OWNER" "$GITHUB_REPO" "$pr_number")
    if [ $? -ne 0 ]; then
        print_error "Failed to get PR files"
        return 1
    fi
    
    local pr_file_count=$(echo "$pr_files" | wc -l | xargs)
    print_success "Found $pr_file_count file(s) changed in PR"
    
    # Create file lists
    local pr_file_list="pr_${pr_number}_files.txt"
    local doc_file_list="pr_${pr_number}_docs.txt"
    echo "$pr_files" > "$pr_file_list"
    echo "$doc_files" > "$doc_file_list"
    
    # Load the documentation analysis prompt template
    local prompt_file="$SCRIPT_DIR/prompts/analyze-documentation.md"
    if [ ! -f "$prompt_file" ]; then
        print_error "Prompt template not found: $prompt_file"
        rm -f "$pr_file_list" "$doc_file_list"
        return 1
    fi
    
    print_info "Loading prompt template..."
    local prompt_template=$(cat "$prompt_file")
    
    # Build Bob command with full prompt and context
    local command="$prompt_template

## PR Context for Analysis

**PR Number:** #${pr_number}
**Repository:** $GITHUB_OWNER/$GITHUB_REPO

**Changed Files in PR:**
@${pr_file_list}

**All Documentation Files in Repository:**
@${doc_file_list}

## Instructions

1. Read and analyze ALL files in @${pr_file_list} to understand the PR changes
2. Classify the changes as MAJOR or MINOR following the guidelines above
3. If MAJOR, read ALL documentation files in @${doc_file_list}
4. For each documentation file, identify gaps based on the PR changes
5. Generate ${output_file} with the exact JSON structure specified above

**IMPORTANT:**
- You MUST read the actual content of files in @${pr_file_list} to understand what changed
- You MUST read the actual content of files in @${doc_file_list} to check for gaps
- Provide specific, actionable suggestions with example markdown content
- Include the 'exampleContent' field with actual markdown to add
- Link each suggestion to the specific PR files that triggered it"
    
    print_info "Executing documentation analysis with Bob AI..."
    echo ""
    
    # Execute Bob Shell in non-interactive mode with -p flag and --yolo for auto-approval
    if ! bob -p "$command" --yolo; then
        print_error "Documentation analysis failed"
        rm -f "$pr_file_list" "$doc_file_list"
        return 1
    fi
    
    # Cleanup temp files
    rm -f "$pr_file_list" "$doc_file_list"
    
    echo ""
    
    if [ -f "$output_file" ]; then
        print_success "Analysis complete: $output_file"
        
        # Display summary
        if command -v jq &> /dev/null; then
            local should_update=$(jq -r '.shouldUpdateDocs' "$output_file" 2>/dev/null || echo "true")
            local total_gaps=$(jq '.summary.totalGaps // 0' "$output_file" 2>/dev/null || echo "0")
            local total_docs=$(jq '.summary.totalDocsDiscovered // 0' "$output_file" 2>/dev/null || echo "0")
            
            echo ""
            print_info "Analyzed $total_docs documentation file(s)"
            
            if [ "$should_update" = "true" ]; then
                print_warning "📝 Documentation updates recommended: $total_gaps gap(s) found"
                
                # Show breakdown by file type
                echo ""
                print_info "Gaps by file type:"
                jq -r '.summary.byFileType // {} | to_entries[] | "   - \(.key): \(.value)"' "$output_file" 2>/dev/null || echo "   (details not available)"
            else
                print_success "✓ No documentation updates needed (minor changes only)"
            fi
        fi
        
        return 0
    else
        print_error "Analysis output not found: $output_file"
        return 1
    fi
}


# Auto workflow
auto_workflow() {
    local target="$1"
    local max_iterations="${2:-3}"
    
    print_header "🚀 Automated Code Review Workflow"
    print_info "Target: $target"
    print_info "Max iterations: $max_iterations"
    
    # Phase 1: Initial Review
    phase1_review "$target" "review1.json" || {
        print_error "Workflow failed at Phase 1: Review"
        return 1
    }
    
    local current_review="review1.json"
    local iteration=1
    
    while [ $iteration -le $max_iterations ]; do
        print_header "🔄 Iteration $iteration/$max_iterations"
        
        # Phase 2: Implement
        local impl_file="implementation${iteration}.json"
        phase2_implement "$current_review" "$impl_file" || {
            print_error "Workflow failed at Phase 2: Implementation (iteration $iteration)"
            return 1
        }
        
        # Phase 3: Verify
        local next_review="review$((iteration + 1)).json"
        phase3_verify "$impl_file" "$current_review" "$next_review"
        local verify_result=$?
        
        if [ $verify_result -eq 1 ]; then
            print_error "Workflow failed at Phase 3: Verification (iteration $iteration)"
            return 1
        elif [ $verify_result -eq 0 ]; then
            print_header "🎉 Workflow Complete - No New Issues Found!"
            echo ""
            print_info "Summary:"
            echo "   Total iterations: $iteration"
            echo "   Final review: $next_review"
            echo "   Code status: Production Ready ✅"
            return 0
        fi
        
        # Prepare for next iteration
        current_review="$next_review"
        iteration=$((iteration + 1))
    done
    
    print_header "⚠️  Maximum iterations ($max_iterations) reached"
    echo ""
    print_info "Summary:"
    echo "   Completed iterations: $max_iterations"
    echo "   Latest review: $current_review"
    echo "   Status: Issues remain - manual review recommended"
    return 1
}

# Main script
main() {
    check_bob
    
    case "${1:-}" in
        review)
            if [ -z "${2:-}" ]; then
                print_error "Usage: $0 review <target> [output_file]"
                exit 1
            fi
            phase1_review "$2" "${3:-}"
            ;;
        implement)
            if [ -z "${2:-}" ]; then
                print_error "Usage: $0 implement <review_file> [output_file]"
                exit 1
            fi
            phase2_implement "$2" "${3:-}"
            ;;
        verify)
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                print_error "Usage: $0 verify <implementation_file> <original_review_file> [output_file]"
                exit 1
            fi
            phase3_verify "$2" "$3" "${4:-}"
            ;;
        auto)
            if [ -z "${2:-}" ]; then
                print_error "Usage: $0 auto <target> [max_iterations]"
                exit 1
            fi
            auto_workflow "$2" "${3:-3}"
            ;;
        submit)
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                print_error "Usage: $0 submit <review_file> <pr_number> [options]"
                exit 1
            fi
            # Get script directory
            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            # Pass all arguments to submit_pr_comments.sh
            shift  # Remove 'submit' command
            "$SCRIPT_DIR/submit_pr_comments.sh" "$@"
            ;;
        review-pr)
            if [ -z "${2:-}" ]; then
                print_error "Usage: $0 review-pr <pr_number> [output_file] [--auto-submit]"
                exit 1
            fi
            local auto_submit="false"
            if [ "${4:-}" = "--auto-submit" ] || [ "${3:-}" = "--auto-submit" ]; then
                auto_submit="true"
            fi
            review_pr "$2" "${3:-}" "$auto_submit"
            ;;
        analyze-docs)
            if [ -z "${2:-}" ]; then
                print_error "Usage: $0 analyze-docs <pr_number> [output_file]"
                exit 1
            fi
            analyze_docs "$2" "${3:-}"
            ;;
        *)
            echo "Code Review Workflow Automation"
            echo ""
            echo "Usage:"
            echo "  $0 review <target> [output_file]"
            echo "  $0 review-pr <pr_number> [output_file] [--auto-submit]"
            echo "  $0 implement <review_file> [output_file]"
            echo "  $0 verify <implementation_file> <original_review_file> [output_file]"
            echo "  $0 auto <target> [max_iterations]"
            echo "  $0 submit <review_file> <pr_number> [options]"
            echo "  $0 analyze-docs <pr_number> [output_file]"
            echo ""
            echo "Target can be:"
            echo "  - Single file:     ./path/to/file.go"
            echo "  - Directory:       ./path/to/directory/"
            echo "  - File list:       @files.txt (one file path per line)"
            echo "  - PR number:       Use review-pr command"
            echo ""
            echo "Examples:"
            echo "  # Review local files"
            echo "  $0 review ./scheduler/scheduler.go"
            echo "  $0 review ./handlers/v2/"
            echo "  $0 review @changed_files.txt"
            echo ""
            echo "  # Review a Pull Request"
            echo "  $0 review-pr 123"
            echo "  $0 review-pr 123 review_pr123.json"
            echo "  $0 review-pr 123 review_pr123.json --auto-submit"
            echo ""
            echo "  # Analyze documentation gaps"
            echo "  $0 analyze-docs 123"
            echo "  $0 analyze-docs 123 docs_analysis.json"
            echo ""
            echo "  # Implement and verify"
            echo "  $0 implement review1.json"
            echo "  $0 verify implementation1.json review1.json"
            echo "  $0 auto @files_to_review.txt 5"
            echo ""
            echo "  # Submit comments to PR"
            echo "  $0 submit review1.json 123"
            echo "  $0 submit review1.json 123 --dry-run"
            echo "  $0 submit review1.json 123 --severity high"
            echo ""
            echo "File list format (files.txt):"
            echo "  ./path/to/file1.go"
            echo "  ./path/to/file2.go"
            echo "  # Comments are ignored"
            echo "  ./path/to/file3.go"
            exit 1
            ;;
    esac
}

main "$@"
