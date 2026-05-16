#!/usr/bin/env bash
#
# implement_finding.sh - Implement a single code review finding using Bob Shell
#
# Usage: implement_finding.sh <file_path> <line_number> <comment_body> [instruction]
#
# Arguments:
#   file_path     - Path to file containing the issue
#   line_number   - Line number of the issue
#   comment_body  - Full review comment body (markdown)
#   instruction   - Optional user guidance for implementation
#
# Returns:
#   0 on success, 1 on failure
#   Outputs JSON result to stdout

set -euo pipefail

# Source library functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/lib"

if [[ -f "${LIB_DIR}/github_api.sh" ]]; then
    source "${LIB_DIR}/github_api.sh"
fi

# Configuration
PROMPT_FILE="${SCRIPT_DIR}/prompts/implement-single-finding.md"
RUNTIME_DIR="${SCRIPT_DIR}/.runtime"
BOB_TIMEOUT="${BOB_TIMEOUT:-600}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Parse review comment to extract structured data
parse_review_comment() {
    local comment_body="$1"
    local severity="unknown"
    local type="unknown"
    local issue=""
    local suggestion=""
    local details=""
    
    # Extract severity and type from header
    if [[ "$comment_body" =~ (CRITICAL|HIGH|MEDIUM|LOW)[[:space:]]*SEVERITY[[:space:]]*\|[[:space:]]*[🔧🐛🔒⚡🎨][[:space:]]*([A-Z]+) ]]; then
        severity="${BASH_REMATCH[1]}"
        type="${BASH_REMATCH[2]}"
    fi
    
    # Extract issue (between "Issue:" and next section or double newline)
    if [[ "$comment_body" =~ Issue:[[:space:]]*([^$'\n']+($'\n'[^$'\n']+)*) ]]; then
        issue="${BASH_REMATCH[1]}"
        # Trim at Details:, Suggestion:, or bob_fixable:
        issue=$(echo "$issue" | sed -n '/Details:\|Suggestion:\|bob_fixable:/q;p' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    fi
    
    # Extract suggestion
    if [[ "$comment_body" =~ Suggestion:[[:space:]]*([^$'\n']+($'\n'[^$'\n']+)*) ]]; then
        suggestion="${BASH_REMATCH[1]}"
        suggestion=$(echo "$suggestion" | sed -n '/Details:\|bob_fixable:/q;p' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    fi
    
    # Extract details
    if [[ "$comment_body" =~ Details:[[:space:]]*([^$'\n']+($'\n'[^$'\n']+)*) ]]; then
        details="${BASH_REMATCH[1]}"
        details=$(echo "$details" | sed -n '/Suggestion:\|bob_fixable:/q;p' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    fi
    
    # Export for use in prompt substitution
    export PARSED_SEVERITY="$severity"
    export PARSED_TYPE="$type"
    export PARSED_ISSUE="$issue"
    export PARSED_SUGGESTION="$suggestion"
    export PARSED_DETAILS="$details"
}

# Stage the implement prompt with variable substitution
stage_implement_prompt() {
    local file_path="$1"
    local line_number="$2"
    local instruction="$3"
    
    if [[ ! -f "$PROMPT_FILE" ]]; then
        log_error "Prompt file not found: $PROMPT_FILE"
        return 1
    fi
    
    # Create runtime directory
    mkdir -p "$RUNTIME_DIR"
    
    local staged_prompt="${RUNTIME_DIR}/implement-prompt-$$.md"
    
    # Substitute variables in prompt template
    sed -e "s|{{FILE_PATH}}|${file_path}|g" \
        -e "s|{{LINE_NUMBER}}|${line_number}|g" \
        -e "s|{{SEVERITY}}|${PARSED_SEVERITY}|g" \
        -e "s|{{TYPE}}|${PARSED_TYPE}|g" \
        -e "s|{{ISSUE_DESCRIPTION}}|${PARSED_ISSUE}|g" \
        -e "s|{{SUGGESTION}}|${PARSED_SUGGESTION}|g" \
        -e "s|{{DETAILS}}|${PARSED_DETAILS}|g" \
        -e "s|{{USER_INSTRUCTION}}|${instruction:-None provided}|g" \
        "$PROMPT_FILE" > "$staged_prompt"
    
    echo "$staged_prompt"
}

# Extract Bob cost from output
extract_bob_cost() {
    local output="$1"
    local cost="unknown"
    
    # Look for cost patterns in Bob output
    if [[ "$output" =~ \$([0-9]+\.[0-9]+) ]]; then
        cost="\$${BASH_REMATCH[1]}"
    elif [[ "$output" =~ ([0-9]+\.[0-9]+)[[:space:]]*tokens ]]; then
        cost="${BASH_REMATCH[1]} tokens"
    fi
    
    echo "$cost"
}

# Execute Bob Shell to implement the fix
execute_bob_implement() {
    local staged_prompt="$1"
    local bob_output_file="${RUNTIME_DIR}/bob-output-$$.txt"
    local bob_error_file="${RUNTIME_DIR}/bob-error-$$.txt"
    
    log_info "Executing Bob Shell with implement prompt..."
    
    # Check if bob command exists
    if ! command -v bob &> /dev/null; then
        log_error "Bob Shell CLI not found in PATH"
        echo '{"success": false, "error": "Bob Shell CLI not found in PATH", "output": "", "bob_cost_used": "unknown"}'
        return 1
    fi
    
    # Execute Bob with --yolo flag for automatic execution
    local exit_code=0
    if timeout "${BOB_TIMEOUT}s" bob --yolo < "$staged_prompt" > "$bob_output_file" 2> "$bob_error_file"; then
        exit_code=0
    else
        exit_code=$?
    fi
    
    local bob_output=$(cat "$bob_output_file" 2>/dev/null || echo "")
    local bob_error=$(cat "$bob_error_file" 2>/dev/null || echo "")
    local bob_cost=$(extract_bob_cost "$bob_output")
    
    # Clean up temporary files
    rm -f "$staged_prompt" "$bob_output_file" "$bob_error_file"
    
    if [[ $exit_code -eq 124 ]]; then
        log_error "Bob Shell execution timed out after ${BOB_TIMEOUT}s"
        echo "{\"success\": false, \"error\": \"Execution timed out after ${BOB_TIMEOUT}s\", \"output\": \"$bob_output\", \"bob_cost_used\": \"$bob_cost\"}"
        return 1
    elif [[ $exit_code -ne 0 ]]; then
        log_error "Bob Shell execution failed with exit code $exit_code"
        echo "{\"success\": false, \"error\": \"Bob execution failed: $bob_error\", \"output\": \"$bob_output\", \"bob_cost_used\": \"$bob_cost\"}"
        return 1
    fi
    
    log_info "Bob Shell execution completed successfully"
    echo "{\"success\": true, \"output\": \"$bob_output\", \"bob_cost_used\": \"$bob_cost\"}"
    return 0
}

# Verify implementation by checking for file modifications
verify_implementation() {
    local file_path="$1"
    
    # Check if file was modified (has uncommitted changes)
    if git diff --quiet "$file_path" 2>/dev/null; then
        log_warn "No changes detected in $file_path"
        return 1
    fi
    
    log_info "Changes detected in $file_path"
    return 0
}

# Commit and push changes
commit_and_push_changes() {
    local file_path="$1"
    local line_number="$2"
    local comment_body="$3"
    
    log_info "Committing and pushing changes..."
    
    # Add safe.directory exception for Docker/mounted volumes
    git config --global --add safe.directory /workspace 2>/dev/null || true
    
    # Configure git user (required for commits in Docker)
    # TODO: take this from env, hardcoded for now
    git config --global user.name "MaheshZ"
    git config --global user.email "mahesh.sawaiker@gmail.com"
    
    # If in detached HEAD, get the branch name and check it out
    if git symbolic-ref -q HEAD >/dev/null 2>&1; then
        log_info "Already on a branch"
    else
        log_warn "In detached HEAD state, attempting to find and checkout branch..."
        # Get the branch name from git reflog or remote branches
        local branch_name=$(git branch -r --contains HEAD | grep -v HEAD | head -1 | sed 's/.*origin\///')
        if [[ -n "$branch_name" ]]; then
            log_info "Found branch: $branch_name, checking out..."
            git checkout "$branch_name" 2>&1 || log_warn "Could not checkout branch, will push to HEAD"
        else
            log_warn "Could not determine branch name, will attempt to push detached HEAD"
        fi
    fi
    
    # Stage the modified file
    if ! git add "$file_path" 2>&1; then
        log_error "Failed to stage file: $file_path"
        return 1
    fi
    
    # Extract issue summary for commit message
    local issue_summary=""
    if [[ "$comment_body" =~ Issue:[[:space:]]*([^$'\n']+) ]]; then
        issue_summary="${BASH_REMATCH[1]}"
        # Truncate if too long
        if [[ ${#issue_summary} -gt 72 ]]; then
            issue_summary="${issue_summary:0:69}..."
        fi
    fi
    
    # Create commit message
    local commit_msg="Fix: ${issue_summary:-Code review finding at ${file_path}:${line_number}}

Implemented fix for code review finding.

File: ${file_path}
Line: ${line_number}
Severity: ${PARSED_SEVERITY}
Type: ${PARSED_TYPE}"
    
    # Commit changes
    if ! git commit -m "$commit_msg" 2>&1; then
        log_error "Failed to commit changes"
        return 1
    fi
    
    log_info "Changes committed successfully"
    
    # Push changes
    if ! git push 2>&1; then
        log_error "Failed to push changes"
        log_warn "You may need to manually push the changes"
        return 1
    fi
    
    log_info "Changes pushed successfully"
    return 0
}

# Main execution
main() {
    if [[ $# -lt 3 ]]; then
        log_error "Usage: $0 <file_path> <line_number> <comment_body> [instruction]"
        echo '{"success": false, "error": "Invalid arguments", "output": "", "bob_cost_used": "unknown"}'
        exit 1
    fi
    
    local file_path="$1"
    local line_number="$2"
    local comment_body="$3"
    local instruction="${4:-}"
    
    log_info "Starting implementation for ${file_path}:${line_number}"
    log_info "Current directory: $(pwd)"
    log_info "Checking file: $file_path"
    
    # Validate file exists (relative to current directory)
    if [[ ! -f "$file_path" ]]; then
        log_error "File not found: $file_path"
        log_error "Current directory contents:"
        ls -la "$(dirname "$file_path" 2>/dev/null || echo ".")" >&2 || true
        echo "{\"success\": false, \"error\": \"File not found: $file_path (cwd: $(pwd))\", \"output\": \"\", \"bob_cost_used\": \"unknown\"}"
        exit 1
    fi
    
    log_info "File found: $file_path"
    
    # Parse review comment
    parse_review_comment "$comment_body"
    
    # Stage prompt with substitutions
    local staged_prompt
    if ! staged_prompt=$(stage_implement_prompt "$file_path" "$line_number" "$instruction"); then
        echo '{"success": false, "error": "Failed to stage prompt", "output": "", "bob_cost_used": "unknown"}'
        exit 1
    fi
    
    # Execute Bob Shell
    local result
    result=$(execute_bob_implement "$staged_prompt")
    local exit_code=$?
    
    # Output result
    echo "$result"
    
    # Verify implementation if successful
    if [[ $exit_code -eq 0 ]]; then
        if verify_implementation "$file_path"; then
            log_info "Implementation verified successfully"
            
            # Commit and push changes
            if commit_and_push_changes "$file_path" "$line_number" "$comment_body"; then
                log_info "Changes committed and pushed to PR"
            else
                log_warn "Implementation successful but failed to push changes"
                # Don't fail the entire operation if push fails
            fi
        else
            log_warn "Implementation completed but no changes detected"
        fi
    fi
    
    exit $exit_code
}

# Run main function
main "$@"

# Made with Bob
