# How Fixium Comment Triggers Work

## Overview

Fixium is triggered by **PR comments** on GitHub. When someone comments on a Pull Request with a special command, the GitHub Actions workflow runs automatically.

## The Flow

```
User comments on PR → GitHub Actions triggered → Fixium runs review → Posts results
```

## Environment Variables Explained

### `COMMENT_BODY`
**What it is:** The full text of the PR comment that triggered the workflow

**Example values:**
```
"Fixium:review"
"Fixium:review --severity high"
"Fixium:review --severity high,medium --type bug,security"
"Please review this code. Fixium:review --exclude-severity low"
```

**Used for:**
1. **Command parsing** - Extract the Fixium command and options
2. **Filter extraction** - Parse `--severity`, `--type`, `--exclude-*` flags
3. **Validation** - Ensure the command is valid

**Code location:** `fixium/comment_parser.py`

### `COMMENT_USER`
**What it is:** The GitHub username of the person who posted the comment

**Example values:**
```
"maheshsa"
"john-doe"
"alice-smith"
```

**Used for:**
1. **Authorization** - Check if user is allowed to trigger reviews
2. **Audit trail** - Track who requested the review
3. **Notifications** - Mention user in error messages

**Code location:** `fixium/access_control.py`

## How It Works in GitHub Actions

### 1. Trigger Event

```yaml
on:
  issue_comment:
    types: [created]
```

When someone posts a comment on a PR, GitHub fires the `issue_comment` event.

### 2. Filter Check

```yaml
if: |
  github.event.issue.pull_request &&
  contains(github.event.comment.body, 'Fixium:review')
```

Only runs if:
- ✅ Comment is on a Pull Request (not a regular issue)
- ✅ Comment contains "Fixium:review"

### 3. Extract Variables

```yaml
env:
  COMMENT_BODY: ${{ github.event.comment.body }}
  COMMENT_USER: ${{ github.event.comment.user.login }}
```

GitHub provides these from the event payload:
- `github.event.comment.body` - Full comment text
- `github.event.comment.user.login` - Username

### 4. Pass to Python

```python
# In fixium/config.py
self.comment_body = os.getenv('COMMENT_BODY', '')
self.comment_user = os.getenv('COMMENT_USER', '')
```

## Usage Examples

### Example 1: Basic Review

**User comments:**
```
Fixium:review
```

**What happens:**
- `COMMENT_BODY` = `"Fixium:review"`
- `COMMENT_USER` = `"maheshsa"`
- Parser extracts: `command="review"`, no filters
- Access control checks if "maheshsa" is authorized
- Runs full review on all PR files
- Posts all findings (all severities, all types)

### Example 2: Filtered Review

**User comments:**
```
Fixium:review --severity high,critical --type bug,security
```

**What happens:**
- `COMMENT_BODY` = `"Fixium:review --severity high,critical --type bug,security"`
- `COMMENT_USER` = `"alice-smith"`
- Parser extracts:
  - `command="review"`
  - `filters.severity=["high", "critical"]`
  - `filters.type=["bug", "security"]`
- Access control checks if "alice-smith" is authorized
- Runs review on all PR files
- Posts only HIGH/CRITICAL severity BUG/SECURITY findings

### Example 3: Exclude Low Priority

**User comments:**
```
Please review this carefully.
Fixium:review --exclude-severity low --exclude-type maintainability
```

**What happens:**
- `COMMENT_BODY` = Full comment text (including "Please review...")
- `COMMENT_USER` = `"john-doe"`
- Parser finds "Fixium:review" in the text
- Parser extracts:
  - `command="review"`
  - `filters.exclude_severity=["low"]`
  - `filters.exclude_type=["maintainability"]`
- Access control checks if "john-doe" is authorized
- Runs review on all PR files
- Posts all findings EXCEPT low severity and maintainability issues

## Authorization

### Setting Authorized Users

In GitHub repository secrets, set:
```
FIXIUM_AUTHORIZED_USERS=user1,user2,user3
```

### Authorization Check

```python
# In fixium/main.py
if not access_control.is_authorized(config.comment_user):
    message = access_control.get_unauthorized_message(config.comment_user)
    github_client.post_comment(config.pr_number, message)
    sys.exit(1)
```

### Unauthorized Response

If user is not authorized, Fixium posts:
```
@unauthorized-user - You are not authorized to trigger Fixium reviews.

**Authorized users:** user1, user2, user3

Please contact a repository administrator if you need access.
```

## Command Parsing

### Valid Commands

```python
# All case-insensitive
"Fixium:review"
"fixium:review"
"FIXIUM:REVIEW"
```

### Valid Filters

**Severity:**
- `--severity high` - Only high severity
- `--severity high,medium` - High and medium
- `--exclude-severity low` - Everything except low

**Type:**
- `--type bug` - Only bugs
- `--type bug,security` - Bugs and security issues
- `--exclude-type maintainability` - Everything except maintainability

**Valid severity values:** `critical`, `high`, `medium`, `low`

**Valid type values:** `bug`, `security`, `maintainability`, `performance`

### Invalid Commands

These will be rejected:
```
"Review this code"  # Missing "Fixium:review"
"Fixium:review --severity invalid"  # Invalid severity
"Fixium:review --type unknown"  # Invalid type
```

## Error Handling

### Invalid Command
```python
error_handler.handle_invalid_command(config.comment_body)
```
Posts a comment explaining valid command format.

### Invalid Filters
```python
error_handler.handle_invalid_filters(errors)
```
Posts a comment listing filter validation errors.

### Unauthorized User
```python
message = access_control.get_unauthorized_message(config.comment_user)
github_client.post_comment(config.pr_number, message)
```
Posts a comment explaining authorization requirements.

## Testing Locally

### Simulate Comment Trigger

```bash
# Set environment variables
export COMMENT_BODY="Fixium:review --severity high"
export COMMENT_USER="your-username"
export PR_NUMBER="123"
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="owner/repo"

# Run Fixium
python3 -m fixium.main
```

### Test Different Commands

```bash
# Basic review
export COMMENT_BODY="Fixium:review"
python3 -m fixium.main

# Filtered review
export COMMENT_BODY="Fixium:review --severity high,medium --type bug"
python3 -m fixium.main

# With exclusions
export COMMENT_BODY="Fixium:review --exclude-severity low"
python3 -m fixium.main
```

### Test Authorization

```bash
# Authorized user
export COMMENT_USER="authorized-user"
export FIXIUM_AUTHORIZED_USERS="authorized-user,another-user"
python3 -m fixium.main

# Unauthorized user
export COMMENT_USER="random-user"
export FIXIUM_AUTHORIZED_USERS="authorized-user,another-user"
python3 -m fixium.main  # Should fail with authorization error
```

## Real-World Example

### Scenario
Alice wants to review a PR for critical security issues only.

### Steps

1. **Alice comments on PR #456:**
   ```
   @bob Can you also check this?
   Fixium:review --severity critical --type security
   ```

2. **GitHub Actions triggers:**
   - Event: `issue_comment.created`
   - PR: #456
   - Comment body: Full text above
   - Comment user: "alice"

3. **Fixium runs:**
   ```python
   config.comment_body = "@bob Can you also check this?\nFixium:review --severity critical --type security"
   config.comment_user = "alice"
   config.pr_number = 456
   ```

4. **Parser extracts:**
   ```python
   command = "review"
   filters.severity = ["critical"]
   filters.type = ["security"]
   ```

5. **Authorization check:**
   ```python
   if "alice" in authorized_users:  # ✅ Pass
       # Continue
   ```

6. **Review runs:**
   - Analyzes all files in PR #456
   - Filters for CRITICAL + SECURITY only
   - Posts inline comments on PR

7. **Alice sees results:**
   - Inline comments on specific lines
   - Only critical security issues shown
   - Other issues filtered out

## Summary

| Variable | Source | Purpose | Example |
|----------|--------|---------|---------|
| `COMMENT_BODY` | PR comment text | Parse command & filters | `"Fixium:review --severity high"` |
| `COMMENT_USER` | Comment author | Authorization check | `"alice-smith"` |
| `PR_NUMBER` | PR being commented on | Target for review | `456` |
| `GITHUB_TOKEN` | GitHub Actions secret | API authentication | `ghp_xxx...` |
| `GITHUB_REPOSITORY` | Repository context | Target repository | `owner/repo` |

---

**Related Documentation:**
- [README.md](README.md) - Main documentation
- [TESTING.md](TESTING.md) - Testing guide
- [AGENTS.md](AGENTS.md) - Agent rules