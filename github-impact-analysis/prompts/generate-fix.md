# Code Generation for GitHub Issue Implementation

## Objective
Generate code changes to implement a GitHub issue based on the issue analysis and current codebase context.

## Code Generation Process

### Step 1: Understand the Issue

Review the issue analysis:
- Issue type (bug, feature, enhancement)
- Requirements and acceptance criteria
- Affected components
- Related issues

### Step 2: Analyze Current Codebase

Before making changes, understand the existing code:

**Read Relevant Files**:
- Files mentioned in the issue
- Related files in the same directory
- Configuration files
- Test files

**Understand Patterns**:
- Coding style and conventions
- Architecture patterns used
- Error handling approach
- Testing patterns
- Documentation style

**Check Dependencies**:
- Imported modules
- External libraries
- Internal dependencies
- Database schemas

### Step 3: Plan the Implementation

Create an implementation plan:

**For Bug Fixes**:
1. Identify the root cause
2. Determine the minimal fix
3. Consider edge cases
4. Plan for testing
5. Check for similar bugs elsewhere

**For Features**:
1. Design the API/interface
2. Plan data structures
3. Identify integration points
4. Plan error handling
5. Design tests

**For Enhancements**:
1. Understand current implementation
2. Plan backward compatibility
3. Identify performance impact
4. Plan migration if needed
5. Update documentation

### Step 4: Generate Code Changes

For each file that needs changes:

**File Actions**:
- `create`: New file
- `modify`: Update existing file
- `delete`: Remove file

**For New Files**:
- Provide complete file content
- Follow project structure
- Include appropriate imports
- Add file-level documentation
- Follow naming conventions

**For Modified Files**:
- Provide complete new content
- Generate unified diff
- Preserve existing functionality
- Maintain code style
- Update related comments

**For Deleted Files**:
- Ensure no dependencies remain
- Update imports in other files
- Remove from build configs

### Step 5: Add Tests

Generate appropriate tests:

**Unit Tests**:
- Test new functions/methods
- Test edge cases
- Test error conditions
- Follow existing test patterns

**Integration Tests** (if applicable):
- Test component interactions
- Test API endpoints
- Test database operations

**Test File Naming**:
- Python: `test_<module>.py`
- JavaScript: `<module>.test.js` or `<module>.spec.js`
- Follow project conventions

### Step 6: Validate Changes

Check generated code for:
- Syntax errors
- Import errors
- Type errors
- Logic errors
- Security issues
- Performance issues

## Output Format

Generate a JSON file with the following structure:

```json
{
  "issueNumber": 123,
  "changes": [
    {
      "file": "src/auth/oauth.py",
      "action": "modify",
      "content": "Complete new file content...",
      "diff": "--- a/src/auth/oauth.py\n+++ b/src/auth/oauth.py\n@@ -45,6 +45,12 @@\n...",
      "description": "Add automatic token refresh logic",
      "linesAdded": 25,
      "linesRemoved": 5
    },
    {
      "file": "tests/test_oauth.py",
      "action": "create",
      "content": "import unittest\n\nclass TestOAuthRefresh(unittest.TestCase):\n    ...",
      "description": "Add tests for token refresh",
      "linesAdded": 45,
      "linesRemoved": 0
    }
  ],
  "testsAdded": [
    "tests/test_oauth.py"
  ],
  "validationStatus": "passed",
  "validationErrors": [],
  "implementationNotes": "Implemented automatic token refresh using a background task that checks token expiry every 5 minutes. Added error handling for refresh failures with exponential backoff retry logic."
}
```

## Code Quality Guidelines

### General Principles

1. **Follow Existing Patterns**: Match the style and patterns in the codebase
2. **Keep It Simple**: Implement the minimal solution that meets requirements
3. **Handle Errors**: Add appropriate error handling and logging
4. **Add Comments**: Explain complex logic and non-obvious decisions
5. **Write Tests**: Cover new functionality with tests

### Language-Specific Guidelines

#### Python
```python
# Follow PEP 8
# Use type hints
# Add docstrings
# Handle exceptions properly

def refresh_token(token: str) -> Optional[str]:
    """
    Refresh an expired OAuth token.
    
    Args:
        token: The expired token
        
    Returns:
        New token if successful, None otherwise
        
    Raises:
        TokenRefreshError: If refresh fails after retries
    """
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise TokenRefreshError(f"Failed to refresh token: {e}")
```

#### JavaScript/TypeScript
```javascript
// Use modern ES6+ syntax
// Add JSDoc comments
// Handle promises properly
// Use async/await

/**
 * Refresh an expired OAuth token
 * @param {string} token - The expired token
 * @returns {Promise<string|null>} New token or null
 * @throws {TokenRefreshError} If refresh fails
 */
async function refreshToken(token) {
  try {
    // Implementation
  } catch (error) {
    console.error('Token refresh failed:', error);
    throw new TokenRefreshError(`Failed to refresh token: ${error.message}`);
  }
}
```

#### Go
```go
// Follow Go conventions
// Add godoc comments
// Handle errors explicitly
// Use defer for cleanup

// RefreshToken refreshes an expired OAuth token.
// Returns the new token or an error if refresh fails.
func RefreshToken(token string) (string, error) {
    // Implementation
    if err != nil {
        return "", fmt.Errorf("failed to refresh token: %w", err)
    }
    return newToken, nil
}
```

### Security Considerations

1. **Input Validation**: Validate all user inputs
2. **SQL Injection**: Use parameterized queries
3. **XSS Prevention**: Sanitize output
4. **Authentication**: Verify user permissions
5. **Secrets**: Never hardcode secrets
6. **Logging**: Don't log sensitive data

### Performance Considerations

1. **Database Queries**: Optimize queries, use indexes
2. **Caching**: Cache expensive operations
3. **Async Operations**: Use async for I/O operations
4. **Memory**: Avoid memory leaks
5. **Algorithms**: Use efficient algorithms

## Example Implementations

### Example 1: Bug Fix (Token Refresh)

**Issue**: OAuth token refresh fails

**Generated Changes**:

```json
{
  "changes": [
    {
      "file": "src/auth/oauth.py",
      "action": "modify",
      "content": "import time\nimport logging\nfrom typing import Optional\n\nlogger = logging.getLogger(__name__)\n\nclass OAuthManager:\n    def __init__(self, client_id: str, client_secret: str):\n        self.client_id = client_id\n        self.client_secret = client_secret\n        self.token_cache = {}\n    \n    def refresh_token(self, refresh_token: str) -> Optional[str]:\n        \"\"\"Refresh an expired OAuth token with retry logic.\"\"\"\n        max_retries = 3\n        retry_delay = 1\n        \n        for attempt in range(max_retries):\n            try:\n                response = requests.post(\n                    'https://oauth.example.com/token',\n                    data={\n                        'grant_type': 'refresh_token',\n                        'refresh_token': refresh_token,\n                        'client_id': self.client_id,\n                        'client_secret': self.client_secret\n                    }\n                )\n                response.raise_for_status()\n                \n                data = response.json()\n                new_token = data['access_token']\n                \n                # Cache the new token\n                self.token_cache[refresh_token] = {\n                    'access_token': new_token,\n                    'expires_at': time.time() + data['expires_in']\n                }\n                \n                logger.info('Token refreshed successfully')\n                return new_token\n                \n            except requests.RequestException as e:\n                logger.warning(f'Token refresh attempt {attempt + 1} failed: {e}')\n                if attempt < max_retries - 1:\n                    time.sleep(retry_delay)\n                    retry_delay *= 2  # Exponential backoff\n                else:\n                    logger.error('Token refresh failed after all retries')\n                    return None\n        \n        return None\n",
      "diff": "--- a/src/auth/oauth.py\n+++ b/src/auth/oauth.py\n@@ -1,5 +1,6 @@\n import time\n import logging\n+from typing import Optional\n \n logger = logging.getLogger(__name__)\n \n@@ -10,15 +11,35 @@ class OAuthManager:\n         self.token_cache = {}\n     \n-    def refresh_token(self, refresh_token: str) -> str:\n-        \"\"\"Refresh an expired OAuth token.\"\"\"\n-        response = requests.post(\n-            'https://oauth.example.com/token',\n-            data={\n-                'grant_type': 'refresh_token',\n-                'refresh_token': refresh_token,\n-                'client_id': self.client_id,\n-                'client_secret': self.client_secret\n-            }\n-        )\n-        return response.json()['access_token']\n+    def refresh_token(self, refresh_token: str) -> Optional[str]:\n+        \"\"\"Refresh an expired OAuth token with retry logic.\"\"\"\n+        max_retries = 3\n+        retry_delay = 1\n+        \n+        for attempt in range(max_retries):\n+            try:\n+                response = requests.post(\n+                    'https://oauth.example.com/token',\n+                    data={\n+                        'grant_type': 'refresh_token',\n+                        'refresh_token': refresh_token,\n+                        'client_id': self.client_id,\n+                        'client_secret': self.client_secret\n+                    }\n+                )\n+                response.raise_for_status()\n+                \n+                data = response.json()\n+                new_token = data['access_token']\n+                \n+                # Cache the new token\n+                self.token_cache[refresh_token] = {\n+                    'access_token': new_token,\n+                    'expires_at': time.time() + data['expires_in']\n+                }\n+                \n+                logger.info('Token refreshed successfully')\n+                return new_token\n+                \n+            except requests.RequestException as e:\n+                logger.warning(f'Token refresh attempt {attempt + 1} failed: {e}')\n+                if attempt < max_retries - 1:\n+                    time.sleep(retry_delay)\n+                    retry_delay *= 2  # Exponential backoff\n+                else:\n+                    logger.error('Token refresh failed after all retries')\n+                    return None\n+        \n+        return None\n",
      "description": "Add retry logic with exponential backoff for token refresh",
      "linesAdded": 35,
      "linesRemoved": 10
    }
  ],
  "implementationNotes": "Added retry logic with exponential backoff (1s, 2s, 4s) for token refresh failures. Added token caching to avoid unnecessary refresh calls. Improved error handling and logging."
}
```

### Example 2: Feature Implementation (Dark Mode)

**Issue**: Add dark mode support

**Generated Changes**:

```json
{
  "changes": [
    {
      "file": "src/hooks/useTheme.ts",
      "action": "create",
      "content": "import { useState, useEffect } from 'react';\n\nexport type Theme = 'light' | 'dark' | 'system';\n\nexport function useTheme() {\n  const [theme, setTheme] = useState<Theme>(() => {\n    // Load from localStorage or default to system\n    const saved = localStorage.getItem('theme');\n    return (saved as Theme) || 'system';\n  });\n\n  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');\n\n  useEffect(() => {\n    // Resolve 'system' to actual theme\n    if (theme === 'system') {\n      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');\n      setResolvedTheme(mediaQuery.matches ? 'dark' : 'light');\n\n      const handler = (e: MediaQueryListEvent) => {\n        setResolvedTheme(e.matches ? 'dark' : 'light');\n      };\n\n      mediaQuery.addEventListener('change', handler);\n      return () => mediaQuery.removeEventListener('change', handler);\n    } else {\n      setResolvedTheme(theme);\n    }\n  }, [theme]);\n\n  useEffect(() => {\n    // Apply theme to document\n    document.documentElement.setAttribute('data-theme', resolvedTheme);\n    localStorage.setItem('theme', theme);\n  }, [theme, resolvedTheme]);\n\n  return { theme, setTheme, resolvedTheme };\n}\n",
      "description": "Create theme hook with system preference support",
      "linesAdded": 40,
      "linesRemoved": 0
    }
  ],
  "testsAdded": ["src/hooks/useTheme.test.ts"],
  "implementationNotes": "Implemented dark mode with three options: light, dark, and system (follows OS preference). Theme preference is persisted in localStorage. System preference is detected using matchMedia API and updates automatically when OS theme changes."
}
```

## Best Practices Summary

1. ✅ Read and understand existing code before making changes
2. ✅ Follow project conventions and patterns
3. ✅ Add comprehensive error handling
4. ✅ Include logging for debugging
5. ✅ Write tests for new functionality
6. ✅ Add comments for complex logic
7. ✅ Validate inputs and sanitize outputs
8. ✅ Consider performance implications
9. ✅ Handle edge cases
10. ✅ Provide complete file content for all changes

---

**Generated by Fixium Code Generator**