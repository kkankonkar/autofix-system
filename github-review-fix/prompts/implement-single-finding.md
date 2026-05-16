# Implement Single Code Review Finding

You are tasked with implementing a fix for a specific code review finding that has been marked as `bob_fixable: true`.

## Review Finding Details

**File:** {{FILE_PATH}}  
**Line:** {{LINE_NUMBER}}  
**Severity:** {{SEVERITY}}  
**Type:** {{TYPE}}

### Issue Description
{{ISSUE_DESCRIPTION}}

### Suggested Fix
{{SUGGESTION}}

### Additional Context
{{DETAILS}}

### User Guidance
{{USER_INSTRUCTION}}

---

## Your Task

Implement the suggested fix for this specific finding. Follow these steps:

### 1. Understand the Context
- Read the target file to understand the surrounding code
- Identify the exact location and scope of the issue
- Understand how this code is used in the broader system

### 2. Implement the Fix
- Apply the suggested fix with minimal changes
- Follow existing code patterns and conventions in the file
- Ensure the fix addresses the root cause, not just symptoms
- Preserve existing functionality and behavior
- Maintain backward compatibility

### 3. Verify the Fix
- Ensure the code compiles/runs without errors
- Check that the fix doesn't introduce new issues
- Verify the fix addresses the original issue completely
- Consider edge cases and potential side effects

## Implementation Guidelines

### Code Quality Standards
- **Minimal Changes:** Only modify what's necessary to fix the issue
- **Consistency:** Match existing code style, naming, and patterns
- **Clarity:** Add comments if the fix requires explanation
- **Safety:** Don't introduce breaking changes or new bugs
- **Testing:** If tests exist, ensure they still pass

### Severity-Based Approach

**CRITICAL/HIGH Severity:**
- Must be fixed completely and correctly
- Prioritize correctness over elegance
- Add defensive checks if needed
- Document any assumptions

**MEDIUM Severity:**
- Implement the suggested improvement
- Balance between ideal solution and pragmatism
- Consider maintainability impact

**LOW Severity:**
- Implement if straightforward
- Don't over-engineer the solution
- Keep changes minimal

### When to Deviate from Suggestion

You may deviate from the suggested fix if:
1. The suggestion would break existing functionality
2. A better approach is clearly evident from the code context
3. The suggestion conflicts with established patterns in the codebase

**If you deviate, you MUST explain why in your summary.**

## Output Requirements

After implementing the fix, provide a brief summary:

### Summary Format
```
✅ Fix Implemented

**Changes Made:**
- [List specific changes made to the code]

**Approach:**
- [Explain why this approach was chosen]
- [Note any deviations from the suggestion and why]

**Files Modified:**
- [List all files that were changed]

**Verification:**
- [Describe how you verified the fix works]
- [Note any tests run or checks performed]

**Considerations:**
- [Any trade-offs or limitations]
- [Any follow-up work needed]
```

## Important Constraints

### DO:
✅ Read the entire target file for context  
✅ Make focused, minimal changes  
✅ Follow existing code patterns  
✅ Preserve existing functionality  
✅ Add comments for complex fixes  
✅ Verify the fix addresses the issue  
✅ Check for potential side effects  

### DON'T:
❌ Make unrelated changes or "improvements"  
❌ Introduce breaking changes  
❌ Change public APIs without careful consideration  
❌ Add unnecessary complexity  
❌ Ignore existing code conventions  
❌ Skip verification steps  
❌ Assume the suggestion is always perfect  

## Example Scenarios

### Example 1: Extract Magic Numbers to Constants

**Issue:** Timeout values hardcoded throughout file  
**Suggestion:** Define constants at module level

**Good Implementation:**
```python
# At top of file, after imports
QUOTE_CREATE_TIMEOUT = 45.0
QUOTE_GET_TIMEOUT = 60.0
HOLD_CREATE_TIMEOUT = 90.0

# Then replace all occurrences
response = requests.post(url, timeout=QUOTE_CREATE_TIMEOUT)
```

**Summary:**
```
✅ Fix Implemented

**Changes Made:**
- Added 6 timeout constants at module level (lines 15-20)
- Replaced 12 hardcoded timeout values with named constants

**Approach:**
- Grouped related timeouts together
- Used descriptive names matching the operation
- Maintained exact same timeout values for backward compatibility

**Files Modified:**
- proxy/endpoints.py

**Verification:**
- All timeout values preserved (no behavior change)
- Code compiles without errors
- Improved readability and maintainability
```

### Example 2: Fix Race Condition

**Issue:** Shared state accessed without synchronization  
**Suggestion:** Add mutex lock

**Good Implementation:**
```python
import threading

class Scheduler:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
    
    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            # ... rest of start logic
```

**Summary:**
```
✅ Fix Implemented

**Changes Made:**
- Added threading.Lock to Scheduler.__init__
- Wrapped all _running access with lock context manager
- Added import threading at top of file

**Approach:**
- Used threading.Lock (standard library) for simplicity
- Context manager ensures lock is always released
- Minimal changes to existing logic

**Files Modified:**
- scheduler/scheduler.py

**Verification:**
- No deadlocks in basic testing
- Existing tests still pass
- Race condition eliminated

**Considerations:**
- Lock is coarse-grained (entire method)
- Could be optimized later if performance issue
- All _running access points now protected
```

## Special Cases

### If the Fix Cannot Be Implemented

If you determine the fix cannot or should not be implemented:

1. **Explain clearly why** (technical constraints, breaking changes, etc.)
2. **Suggest an alternative** if possible
3. **Document the blocker** for future reference

**Format:**
```
⚠️ Fix Not Implemented

**Reason:**
[Clear explanation of why the fix cannot be applied]

**Alternative Approach:**
[Suggest alternative if available, or "None identified"]

**Recommendation:**
[What should be done instead - mark as blocked, needs discussion, etc.]
```

### If the Suggestion is Unclear

If the suggestion is ambiguous or unclear:

1. **Make your best interpretation** based on the issue description
2. **Document your interpretation** in the summary
3. **Explain your reasoning** for the approach chosen

## Final Checklist

Before completing, verify:

- [ ] Target file has been read and understood
- [ ] Fix addresses the root issue, not just symptoms
- [ ] Changes are minimal and focused
- [ ] Existing code patterns are followed
- [ ] No breaking changes introduced
- [ ] Code compiles/runs without errors
- [ ] Fix has been verified to work
- [ ] Summary is complete and accurate

---

**Remember:** The goal is a focused, correct fix that addresses the specific issue while maintaining code quality and existing functionality. When in doubt, prefer minimal, safe changes over ambitious refactoring.