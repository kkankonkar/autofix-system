# Multi-File Fixes and Path Normalization

## Overview

The autofix system now supports:
1. **Path Normalization** - Converts absolute paths like `/app/consumer/billing.py` to relative repo paths
2. **Multi-File Fixes** - Applies fixes across multiple files in a single PR

## Problem 1: Path Normalization

### The Issue

Stack traces often contain absolute paths from the runtime environment:
```
Traceback (most recent call last):
  File "/app/consumer/billing_consumer.py", line 45, in process
    result = calculate_total(items)
TypeError: 'NoneType' object is not subscriptable
```

But the actual repository structure might be:
```
repo/
├── consumer/
│   └── billing_consumer.py
├── src/
│   └── consumer/
│       └── billing_consumer.py
```

### The Solution

The system now includes intelligent path normalization that:

1. **Strips absolute prefixes** (`/app/`, `/usr/local/`, etc.)
2. **Searches by filename** in the repository
3. **Matches path suffixes** (e.g., `consumer/billing_consumer.py`)
4. **Scores multiple matches** to find the best fit

### Implementation

**Location:** [`src/repo_manager/service.py:23-78`](../src/repo_manager/service.py:23-78)

```python
def find_file_in_repo(self, checkout_dir: Path, partial_path: str) -> Optional[str]:
    """
    Find a file in the repository by searching for partial path matches.
    
    Strategies:
    1. Try path as-is (relative)
    2. Search for filename in entire repo
    3. Match path suffix (e.g., consumer/file.py)
    4. Score multiple matches by path similarity
    """
```

### Example Flow

```python
# Input from stack trace
path = "/app/consumer/billing_consumer.py"

# Normalization process
repo_manager.find_file_in_repo(checkout_dir, path)

# Strategy 1: Try as-is
# ❌ "app/consumer/billing_consumer.py" not found

# Strategy 2: Search by filename
# ✓ Found: ["consumer/billing_consumer.py", "src/consumer/billing_consumer.py"]

# Strategy 3: Match suffix "consumer/billing_consumer.py"
# ✓ Found: "consumer/billing_consumer.py"

# Result: "consumer/billing_consumer.py"
```

## Problem 2: Multi-File Fixes

### The Issue

Some fixes require changes across multiple files:

**Example:** Adding null checks
- **File 1:** `src/services/user_service.py` - Add null check
- **File 2:** `src/utils/validator.py` - Add validation function
- **File 3:** `tests/test_user_service.py` - Add test cases

Previously, the system could only handle one file per PR.

### The Solution

The system now supports multiple file changes in a single PR through:

1. **New `FileChange` model** - Represents a single file change
2. **`file_changes` array** - List of all file changes in a fix
3. **Batch processing** - Applies all changes before committing
4. **Backward compatibility** - Still supports single-file fixes

### Data Models

**Location:** [`src/models/fix_proposal.py`](../src/models/fix_proposal.py)

```python
class FileChange(BaseModel):
    """Represents a change to a single file."""
    file_path: str
    original_code: str = ""
    fixed_code: str

class FixProposal(BaseModel):
    """Represents a proposed fix for an error."""
    analysis_id: str
    file_path: str  # Primary file (backward compatibility)
    file_changes: List[FileChange] = []  # NEW: Multiple files
    original_code: str = ""  # Deprecated
    fixed_code: str = ""  # Deprecated
    explanation: str
    commit_message: str
    pr_description: str
    test_suggestions: List[str] = []
```

## Complete Workflow

### Single File Fix (Backward Compatible)

```json
{
  "analysis_id": "log-abc123",
  "file_path": "consumer/billing_consumer.py",
  "original_code": "result = calculate_total(items)",
  "fixed_code": "result = calculate_total(items) if items else 0",
  "explanation": "Added null check for items",
  "commit_message": "Fix: Add null check in billing consumer"
}
```

### Multi-File Fix (New)

```json
{
  "analysis_id": "log-abc123",
  "file_path": "consumer/billing_consumer.py",
  "file_changes": [
    {
      "file_path": "consumer/billing_consumer.py",
      "original_code": "result = calculate_total(items)",
      "fixed_code": "result = calculate_total(items) if items else 0"
    },
    {
      "file_path": "utils/validator.py",
      "original_code": "",
      "fixed_code": "def validate_items(items):\n    return items is not None and len(items) > 0"
    },
    {
      "file_path": "tests/test_billing.py",
      "original_code": "",
      "fixed_code": "def test_empty_items():\n    assert calculate_total(None) == 0"
    }
  ],
  "explanation": "Added null checks and validation",
  "commit_message": "Fix: Add comprehensive null handling for billing"
}
```

## PR Creation with Multi-File Support

**Location:** [`src/main.py:298-375`](../src/main.py:298-375)

### Process Flow

```
1. Clone repository
   ↓
2. Check for file_changes array
   ↓
3. For each file change:
   a. Normalize file path (handle /app/consumer/file.py → consumer/file.py)
   b. Validate file exists
   c. Apply change (replace or write)
   d. Track modified files
   ↓
4. Commit all changes together
   ↓
5. Push and create PR
```

### Code Example

```python
# Handle multiple file changes
file_changes = fix_record.get("file_changes", [])

if file_changes:
    files_modified = []
    for change in file_changes:
        change_file_path = change.get("file_path", "")
        
        # Normalize the file path
        normalized_path = repo_manager.find_file_in_repo(
            checkout_dir, 
            change_file_path
        )
        
        # Apply the change
        if change.get("original_code"):
            repo_manager.replace_code_snippet(
                checkout_dir=checkout_dir,
                file_path=normalized_path,
                original_code=change["original_code"],
                fixed_code=change["fixed_code"]
            )
        else:
            repo_manager.write_file(
                checkout_dir, 
                normalized_path, 
                change["fixed_code"]
            )
        
        files_modified.append(normalized_path)
    
    # All files modified, now commit
    repo_manager.commit_and_push(repo, branch_name, commit_message)
```

## API Examples

### Example 1: Path Normalization

**Input Log:**
```
Error in /app/consumer/billing_consumer.py at line 45
TypeError: 'NoneType' object is not subscriptable
```

**System Processing:**
```bash
# 1. Ingest log
POST /api/v1/logs/ingest
# Analysis detects: file_path = "/app/consumer/billing_consumer.py"

# 2. Generate fix
POST /api/v1/fix/log-abc123
# Response includes normalized path:
{
  "file_path": "consumer/billing_consumer.py",  # ← Normalized!
  "detected_file_path": "consumer/billing_consumer.py"
}

# 3. Create PR
POST /api/v1/pr/create/log-abc123
# System automatically uses normalized path
{
  "target_file_path": "consumer/billing_consumer.py",
  "pull_request": { ... }
}
```

### Example 2: Multi-File Fix

**AI Agent Response:**
```json
{
  "file_changes": [
    {
      "file_path": "/app/services/user_service.py",
      "original_code": "user = data['user']",
      "fixed_code": "user = data.get('user')"
    },
    {
      "file_path": "/app/utils/validator.py",
      "original_code": "",
      "fixed_code": "def validate_user(data):\n    return 'user' in data"
    }
  ]
}
```

**System Processing:**
```bash
# Normalize paths
/app/services/user_service.py → services/user_service.py
/app/utils/validator.py → utils/validator.py

# Apply all changes
✓ Modified: services/user_service.py
✓ Created: utils/validator.py

# Create single PR with both changes
PR #42: "Fix: Add user validation and null checks"
Files changed: 2
```

## Path Normalization Strategies

### Strategy 1: Direct Match
```python
# Input: "consumer/billing.py"
# Check: checkout_dir / "consumer/billing.py"
# Result: ✓ Found
```

### Strategy 2: Filename Search
```python
# Input: "/app/consumer/billing.py"
# Search: Find all "billing.py" in repo
# Found: ["consumer/billing.py", "tests/billing.py"]
# Result: Multiple matches → proceed to Strategy 3
```

### Strategy 3: Suffix Match
```python
# Input: "/app/consumer/billing.py"
# Extract suffix: "consumer/billing.py"
# Check: checkout_dir / "consumer/billing.py"
# Result: ✓ Found
```

### Strategy 4: Best Match Scoring
```python
# Input: "/app/services/consumer/billing.py"
# Found multiple: 
#   - "consumer/billing.py" (score: 2)
#   - "services/consumer/billing.py" (score: 3) ← Best match
# Result: "services/consumer/billing.py"
```

## Benefits

### Path Normalization
- ✅ Handles absolute paths from Docker containers
- ✅ Works with different deployment environments
- ✅ Finds files even with partial paths
- ✅ Intelligent matching for ambiguous cases

### Multi-File Fixes
- ✅ Comprehensive fixes in single PR
- ✅ Related changes grouped together
- ✅ Better code review experience
- ✅ Atomic commits (all or nothing)

## Error Handling

### Path Not Found
```json
{
  "detail": "Could not find file: /app/consumer/billing.py in repository"
}
```

**Solution:** Check if file exists in repo or provide correct path manually.

### Multiple Ambiguous Matches
```
Found multiple matches for "billing.py":
- consumer/billing.py
- admin/billing.py
- tests/billing.py
```

**Solution:** System uses best match scoring, but you can override with explicit path.

### No File Changes
```json
{
  "detail": "No valid file changes found in fix"
}
```

**Solution:** Ensure fix contains at least one file change with valid code.

## Testing

### Test Path Normalization

```python
# Test absolute path
assert find_file_in_repo(repo, "/app/consumer/billing.py") == "consumer/billing.py"

# Test partial path
assert find_file_in_repo(repo, "consumer/billing.py") == "consumer/billing.py"

# Test filename only
assert find_file_in_repo(repo, "billing.py") == "consumer/billing.py"
```

### Test Multi-File Fix

```python
fix_proposal = FixProposal(
    analysis_id="test-123",
    file_changes=[
        FileChange(
            file_path="services/user.py",
            fixed_code="def get_user(): ..."
        ),
        FileChange(
            file_path="tests/test_user.py",
            fixed_code="def test_get_user(): ..."
        )
    ]
)

# Should create PR with 2 file changes
pr = create_pull_request(fix_proposal)
assert len(pr.files_changed) == 2
```

## Future Enhancements

- [ ] Support for file deletions
- [ ] Support for file renames/moves
- [ ] Dependency analysis for related files
- [ ] Automatic test file generation
- [ ] Configuration file updates
- [ ] Documentation updates in same PR

## Related Documentation

- [File Path Auto-Detection Flow](FILE_PATH_AUTO_DETECTION_FLOW.md)
- [Auto-Detect File Path Feature](AUTO_DETECT_FILE_PATH.md)
- [Main System Design](../AUTOMATED_FIX_SYSTEM_DESIGN.md)