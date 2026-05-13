# Auto-Detect Target File Path Feature

## Overview

The autofix system now automatically detects the target file path for PR creation, eliminating the need for manual input. This makes the system truly automated and reduces human intervention.

## How It Works

### Detection Priority

The system attempts to detect the target file path in the following order:

1. **From Error Analysis** - Uses the `file_path` field detected by the AI agent during error analysis
2. **From Fix Record** - Uses the `file_path` field from the generated fix
3. **From Stack Trace** - Parses the stack trace to extract file paths using regex patterns

### Supported Stack Trace Formats

The system can parse file paths from various stack trace formats:

#### Python
```
File "/path/to/file.py", line 123, in function_name
```

#### JavaScript/TypeScript
```
at /path/to/file.js:45:12
at Object.<anonymous> (/path/to/file.ts:89:5)
```

#### Java
```
at com.example.MyClass.method(MyClass.java:123)
```

#### Generic
```
in /path/to/file.go:45
Error in path/to/file.rb:123
```

## API Usage

### Endpoint: `POST /api/v1/pr/create/{log_id}`

#### With Auto-Detection (Recommended)
```bash
curl -X POST "http://localhost:8000/api/v1/pr/create/log-abc123" \
  -F "base_branch=main"
```

#### With Manual Override
```bash
curl -X POST "http://localhost:8000/api/v1/pr/create/log-abc123" \
  -F "target_file_path=src/services/user_service.py" \
  -F "base_branch=main"
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `log_id` | string | Yes | - | The log entry ID to create PR for |
| `target_file_path` | string | No | Auto-detected | Relative path from repo root |
| `base_branch` | string | No | "main" | Base branch for the PR |

## Error Handling

If auto-detection fails, the API returns:

```json
{
  "detail": "Could not auto-detect target file path. Please provide target_file_path explicitly."
}
```

In this case, you can retry with an explicit `target_file_path` parameter.

## Implementation Details

### Auto-Detection Function

```python
def auto_detect_target_file_path(
    analysis: dict, 
    fix_record: dict, 
    checkout_dir: Path
) -> Optional[str]:
    """
    Auto-detect the target file path from analysis or fix record.
    
    Returns:
        str: Relative file path from repository root
        None: If detection fails
    """
```

### Validation

The system validates that detected file paths:
- Exist in the cloned repository
- Are actual files (not directories)
- Are relative to the repository root

### Regex Patterns Used

```python
patterns = [
    r'File ["\']([^"\']+)["\']',  # Python style
    r'at ([^\s:]+):\d+',  # JavaScript/TypeScript style
    r'in ([^\s]+):\d+',  # Generic style
    r'([a-zA-Z0-9_/.-]+\.(py|js|ts|java|go|rb|php|cpp|c|h)):\d+',  # file.ext:line
]
```

## Benefits

1. **Fully Automated** - No manual file path input required
2. **Intelligent** - Uses multiple detection strategies
3. **Flexible** - Falls back to manual input if needed
4. **Validated** - Ensures file exists before attempting fix
5. **Multi-Language** - Supports various programming languages

## Example Workflow

### Complete Automated Flow

```bash
# 1. Ingest log file
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
  -F "repository_url=https://github.com/org/my-app" \
  -F "log_file=@error.log"

# Response: {"log_id": "log-abc123", ...}

# 2. Generate fix (automatic)
curl -X POST "http://localhost:8000/api/v1/fix/log-abc123"

# 3. Create PR with auto-detected file path
curl -X POST "http://localhost:8000/api/v1/pr/create/log-abc123" \
  -F "base_branch=main"

# Response includes detected file path:
{
  "status": "success",
  "log_id": "log-abc123",
  "branch_name": "autofix/log-abc123",
  "target_file_path": "src/services/user_service.py",  # Auto-detected!
  "pull_request": {
    "pr_number": 42,
    "pr_url": "https://github.com/org/my-app/pull/42"
  }
}
```

## Testing

### Test Auto-Detection

```python
# Test with Python error
log_content = """
Traceback (most recent call last):
  File "src/services/auth.py", line 45, in authenticate
    user = get_user(user_id)
TypeError: 'NoneType' object is not subscriptable
"""

# The system will automatically detect: src/services/auth.py
```

### Test with JavaScript error

```javascript
// Error log
Error: Cannot read property 'name' of undefined
    at getUserName (/app/src/utils/user.js:23:15)
    at processUser (/app/src/controllers/user.js:89:5)

// The system will automatically detect: src/utils/user.js
```

## Configuration

No additional configuration is required. The feature works out-of-the-box with the existing error analysis system.

## Limitations

1. **Complex Stack Traces** - May fail with heavily obfuscated or minified code
2. **Multiple Files** - If error spans multiple files, detects the first one
3. **Non-Standard Formats** - Custom log formats may not be parsed correctly

## Fallback Strategy

If auto-detection fails:
1. System returns clear error message
2. User can provide explicit `target_file_path`
3. System continues with manual path

## Future Enhancements

- [ ] Support for multiple file fixes in single PR
- [ ] Machine learning-based path prediction
- [ ] Integration with code analysis tools
- [ ] Support for monorepo structures
- [ ] Custom regex pattern configuration

## Related Documentation

- [Main System Design](../AUTOMATED_FIX_SYSTEM_DESIGN.md)
- [Implementation Guide](../IMPLEMENTATION_GUIDE.md)
- [API Documentation](API.md)