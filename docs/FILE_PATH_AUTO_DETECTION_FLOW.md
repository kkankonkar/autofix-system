# File Path Auto-Detection Flow

## Overview

The autofix system now automatically detects and passes the target file path through the entire workflow, from error analysis to PR creation. This eliminates the need for manual file path input.

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOG INGESTION                                                 │
│    POST /api/v1/logs/ingest                                      │
│    - Upload log file + repository URL                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ERROR ANALYSIS (Automatic)                                    │
│    AI Agent analyzes the error                                   │
│    ┌──────────────────────────────────────────────────────┐    │
│    │ Analysis Output:                                      │    │
│    │ {                                                     │    │
│    │   "error_type": "TypeError",                          │    │
│    │   "file_path": "src/services/user.py",  ◄─── DETECTED│    │
│    │   "line_number": 45,                                  │    │
│    │   "analysis": "...",                                  │    │
│    │   "fixable": true                                     │    │
│    │ }                                                     │    │
│    └──────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. FIX GENERATION                                                │
│    POST /api/v1/fix/{log_id}                                     │
│    ┌──────────────────────────────────────────────────────┐    │
│    │ Fix Generator:                                        │    │
│    │ 1. Receives analysis with file_path                   │    │
│    │ 2. Generates fix code                                 │    │
│    │ 3. Stores file_path in FixProposal  ◄─── STORED      │    │
│    └──────────────────────────────────────────────────────┘    │
│    ┌──────────────────────────────────────────────────────┐    │
│    │ Response:                                             │    │
│    │ {                                                     │    │
│    │   "log_id": "log-abc123",                             │    │
│    │   "fix_generated": true,                              │    │
│    │   "detected_file_path": "src/services/user.py",       │    │
│    │   "fix": {                                            │    │
│    │     "file_path": "src/services/user.py", ◄─── PASSED │    │
│    │     "original_code": "...",                           │    │
│    │     "fixed_code": "...",                              │    │
│    │     ...                                               │    │
│    │   }                                                   │    │
│    │ }                                                     │    │
│    └──────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PR CREATION (Fully Automatic)                                │
│    POST /api/v1/pr/create/{log_id}                               │
│    - No target_file_path parameter needed!                       │
│    ┌──────────────────────────────────────────────────────┐    │
│    │ Auto-Detection Logic:                                 │    │
│    │ 1. Check fix_record["file_path"]     ◄─── PRIMARY    │    │
│    │ 2. Check analysis["file_path"]       ◄─── FALLBACK   │    │
│    │ 3. Parse stack trace                 ◄─── LAST RESORT│    │
│    │ 4. Validate file exists in repo                       │    │
│    └──────────────────────────────────────────────────────┘    │
│    ┌──────────────────────────────────────────────────────┐    │
│    │ Response:                                             │    │
│    │ {                                                     │    │
│    │   "status": "success",                                │    │
│    │   "target_file_path": "src/services/user.py",         │    │
│    │   "pull_request": {                                   │    │
│    │     "pr_number": 42,                                  │    │
│    │     "pr_url": "https://github.com/..."               │    │
│    │   }                                                   │    │
│    │ }                                                     │    │
│    └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Error Analysis Phase

**Location:** [`src/main.py:165-221`](../src/main.py:165-221)

The AI agent analyzes the error and extracts:
- Error type
- **File path** (from stack trace or code analysis)
- Line number
- Root cause

```python
analysis = {
    "error_type": "TypeError",
    "file_path": "src/services/user.py",  # ← Detected here
    "line_number": 45,
    "analysis": "Null pointer access",
    "fixable": True
}
```

### 2. Fix Generation Phase

**Location:** [`src/fix_generator/service.py:17-37`](../src/fix_generator/service.py:17-37)

The fix generator:
1. Receives the analysis (including file_path)
2. Generates the fix code
3. **Stores file_path in FixProposal model**

```python
# In FixGenerator.generate_fix()
file_path = (
    error_analysis.get("file_path") or 
    fix_data.get("file_path") or 
    ""
)

return FixProposal(
    analysis_id=analysis_id,
    file_path=file_path,  # ← Stored in fix record
    original_code=...,
    fixed_code=...,
    ...
)
```

### 3. PR Creation Phase

**Location:** [`src/main.py:268-353`](../src/main.py:268-353)

The PR creator:
1. Retrieves the fix record (which contains file_path)
2. Auto-detects file path if not provided by user
3. Validates the file exists in the repository
4. Applies the fix and creates PR

```python
# Auto-detect if not provided
if not target_file_path:
    target_file_path = auto_detect_target_file_path(
        analysis, 
        fix_record, 
        checkout_dir
    )
```

## Detection Priority

The system uses a **3-tier priority** for file path detection:

### Priority 1: Fix Record (Most Reliable)
```python
file_path = fix_record.get("file_path")
```
- Stored during fix generation
- Already validated by AI agent
- **Recommended source**

### Priority 2: Analysis Record (Fallback)
```python
file_path = analysis.get("file_path")
```
- Detected during error analysis
- May not be validated yet

### Priority 3: Stack Trace Parsing (Last Resort)
```python
# Parse patterns like:
# - File "path/to/file.py", line 123
# - at /path/to/file.js:45
# - in path/to/file.go:89
```
- Regex-based extraction
- Works for standard stack trace formats

## API Examples

### Complete Automated Flow

```bash
# Step 1: Ingest log
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
  -F "repository_url=https://github.com/org/my-app" \
  -F "log_file=@error.log"

# Response:
# {
#   "log_id": "log-abc123",
#   "message": "Log file ingested and analyzed"
# }

# Step 2: Generate fix
curl -X POST "http://localhost:8000/api/v1/fix/log-abc123"

# Response:
# {
#   "log_id": "log-abc123",
#   "fix_generated": true,
#   "detected_file_path": "src/services/user.py",  ← File path detected!
#   "fix": {
#     "file_path": "src/services/user.py",
#     "original_code": "...",
#     "fixed_code": "..."
#   }
# }

# Step 3: Create PR (no file path needed!)
curl -X POST "http://localhost:8000/api/v1/pr/create/log-abc123" \
  -F "base_branch=main"

# Response:
# {
#   "status": "success",
#   "target_file_path": "src/services/user.py",  ← Auto-detected!
#   "pull_request": {
#     "pr_number": 42,
#     "pr_url": "https://github.com/org/my-app/pull/42"
#   }
# }
```

### Manual Override (Optional)

If auto-detection fails or you want to override:

```bash
curl -X POST "http://localhost:8000/api/v1/pr/create/log-abc123" \
  -F "target_file_path=src/custom/path.py" \
  -F "base_branch=main"
```

## Benefits

### 1. **Zero Manual Input**
- File path automatically flows through the system
- No need to manually specify target file

### 2. **Reliable Detection**
- Uses AI-detected path from analysis
- Stored and validated during fix generation
- Multiple fallback strategies

### 3. **Transparent**
- File path shown in fix generation response
- Included in PR creation response
- Easy to verify and override if needed

### 4. **Robust**
- Validates file exists before applying fix
- Clear error messages if detection fails
- Manual override always available

## Error Handling

### Scenario 1: File Path Not Detected

```json
{
  "detail": "Could not auto-detect target file path. Please provide target_file_path explicitly."
}
```

**Solution:** Provide explicit file path:
```bash
curl -X POST ".../pr/create/log-abc123" \
  -F "target_file_path=src/services/user.py"
```

### Scenario 2: File Not Found in Repository

```json
{
  "detail": "Target file not found: src/services/user.py"
}
```

**Solution:** Verify the file path is correct and exists in the repository.

## Code References

| Component | File | Lines |
|-----------|------|-------|
| FixProposal Model | [`src/models/fix_proposal.py`](../src/models/fix_proposal.py) | 7-31 |
| Fix Generator | [`src/fix_generator/service.py`](../src/fix_generator/service.py) | 17-37 |
| PR Creation Endpoint | [`src/main.py`](../src/main.py) | 268-353 |
| Auto-Detection Logic | [`src/main.py`](../src/main.py) | 462-507 |
| File Validation | [`src/main.py`](../src/main.py) | 508-515 |

## Summary

The file path now **automatically flows** through the entire system:

1. **Detected** during error analysis
2. **Stored** in fix generation
3. **Retrieved** during PR creation
4. **Validated** before applying fix

This makes the system truly automated with minimal human intervention required!