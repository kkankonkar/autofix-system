# Quick Start: GitHub PR Comments

Get started with automated PR comment submission in 5 minutes.

## Prerequisites

- `jq` installed (`brew install jq` on macOS)
- GitHub Personal Access Token
- Access to a GitHub repository

## Step 1: Install jq (if needed)

```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq  # Debian/Ubuntu
sudo yum install jq      # RHEL/CentOS
```

## Step 2: Create GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (full control)
   - ✅ `write:discussion`
4. Generate and copy the token

## Step 3: Configure

```bash
cd ~/pay-go-metrics-monitor

# Option A: Edit config file
cp config/github.env config/github.env.local
nano config/github.env.local

# Add your values:
GITHUB_TOKEN="ghp_your_token_here"
GITHUB_OWNER="your-org"
GITHUB_REPO="pay-go-metrics-monitor"

# Load config
source config/github.env.local
```

```bash
# Option B: Export environment variables
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_OWNER="your-org"
export GITHUB_REPO="pay-go-metrics-monitor"
```

## Step 4: Test the Setup

```bash
# Validate your token
./lib/github_api.sh --validate-token

# Check rate limit
./lib/github_api.sh --rate-limit

# Test comment formatting
./lib/comment_formatter.sh --test review1.json 0
```

## Step 5: Review a Pull Request

```bash
# Review PR #123 (fetches files automatically)
./review_workflow.sh review-pr 123

# This will:
# - Fetch changed files from PR
# - Run Fixium review
# - Generate review_pr123.json
# - Show instructions for submitting
```

## Step 6: Preview Comments (Dry Run)

```bash
# Preview what would be submitted to PR #123
./submit_pr_comments.sh review_pr123.json 123 --dry-run
```

## Step 7: Submit Comments

```bash
# Submit all findings to PR #123
./submit_pr_comments.sh review1.json 123

# Or use the workflow script
./review_workflow.sh submit review1.json 123
```

## Common Use Cases

### Only High Severity Issues

```bash
./submit_pr_comments.sh review1.json 123 --severity high
```

### Bugs and Security Only

```bash
./submit_pr_comments.sh review1.json 123 --type bug,security
```

### Exclude Low Priority

```bash
./submit_pr_comments.sh review1.json 123 --exclude-severity low

## Example Workflows

### Workflow 1: Review PR and Auto-Submit

```bash
# One command to review and submit
./review_workflow.sh review-pr 123 review_pr123.json --auto-submit
```

### Workflow 2: Review PR with Manual Submission

```bash
# 1. Review the PR
./review_workflow.sh review-pr 123

# 2. Preview comments
./submit_pr_comments.sh review_pr123.json 123 --dry-run

# 3. Submit high/medium severity only
./submit_pr_comments.sh review_pr123.json 123 --exclude-severity low

# 4. Check PR
open "https://github.com/$GITHUB_OWNER/$GITHUB_REPO/pull/123"
```

### Workflow 3: Review Local Files

```bash
# 1. Review local code
./review_workflow.sh review @changed_files.txt review1.json

# 2. Preview comments
./submit_pr_comments.sh review1.json 123 --dry-run

# 3. Submit to PR
./submit_pr_comments.sh review1.json 123
```
```

## Troubleshooting

### "GITHUB_TOKEN not set"

```bash
# Check if token is set
echo $GITHUB_TOKEN

# If empty, export it
export GITHUB_TOKEN="ghp_your_token_here"
```

### "Token validation failed"

- Check token hasn't expired
- Verify token has correct scopes
- Regenerate token if needed

### "PR not found"

```bash
# Verify PR exists
./lib/github_api.sh --pr-info your-org your-repo 123

# Check owner/repo are correct
echo $GITHUB_OWNER
echo $GITHUB_REPO
```

### "File not in PR"

This is normal - comments are only posted for files changed in the PR. Files not in the PR diff are automatically skipped.

## Next Steps

- Read [README-pr-comments.md](README-pr-comments.md) for full documentation
- Integrate with CI/CD pipeline
- Customize filtering options
- Set up automated workflows

## Example Workflow

```bash
# 1. Review code
./review_workflow.sh review @changed_files.txt review1.json

# 2. Preview comments
./submit_pr_comments.sh review1.json 123 --dry-run

# 3. Submit high/medium severity only
./submit_pr_comments.sh review1.json 123 --exclude-severity low

# 4. Check PR
open "https://github.com/$GITHUB_OWNER/$GITHUB_REPO/pull/123"
```

## Help

```bash
# Show help for submit script
./submit_pr_comments.sh --help

# Show help for workflow
./review_workflow.sh

# Test individual components
./lib/comment_formatter.sh --help
./lib/github_api.sh --help
```

## Security Notes

- Never commit `GITHUB_TOKEN` to version control
- Use `.gitignore` for `config/github.env.local`
- Rotate tokens regularly
- Use tokens with minimal required scopes
- Consider using GitHub Apps for production

## Support

For issues or questions, see [README-pr-comments.md](README-pr-comments.md) for detailed documentation.