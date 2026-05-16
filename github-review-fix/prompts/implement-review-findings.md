# Implement Code Review Findings

## Description
Implement fixes for code review findings with tracking of completed and blocked items in JSON output.

## Prompt Template

Implement the code review findings from {{REVIEW_FILE}}.

**Implementation Requirements:**
- Fix all critical and high severity issues first
- Address medium and low severity issues where feasible
- For each finding, either:
  - Implement the suggested fix
  - Document why it cannot be implemented (technical constraints, breaking changes, etc.)
- Maintain code quality and existing patterns
- Ensure all changes are tested and don't break existing functionality

**Output Requirements:**
Generate a JSON file named `{{OUTPUT_FILE}}` tracking implementation status for each finding.

## Variables

- `{{REVIEW_FILE}}`: Path to the review JSON file (e.g., review1.json)
- `{{OUTPUT_FILE}}`: Name of the implementation tracking file (e.g., implementation_2026-04-28.json)

## JSON Output Format

```json
{
  "reviewFile": "review1.json",
  "implementationDate": "2026-04-28T08:00:00Z",
  "implementations": [
    {
      "file": "path/to/file.go",
      "lineNumber": 123,
      "severity": "critical|high|medium|low",
      "originalComment": "Original review comment",
      "status": "implemented|blocked|skipped",
      "implementation": {
        "description": "What was changed",
        "filesModified": ["file1.go", "file2.go"],
        "approach": "Brief description of the fix approach"
      },
      "blockReason": "Why it couldn't be implemented (only if status is blocked)",
      "skipReason": "Why it was skipped (only if status is skipped)"
    }
  ],
  "summary": {
    "totalFindings": 14,
    "implemented": 10,
    "blocked": 2,
    "skipped": 2,
    "byFile": {
      "scheduler/scheduler.go": {
        "implemented": 10,
        "blocked": 2,
        "skipped": 2
      }
    }
  }
}
```

## Implementation Guidelines

### Priority Order
1. **Critical** - Must be fixed immediately (bugs, security, race conditions)
2. **High** - Should be fixed (functionality, missing validation)
3. **Medium** - Fix if time permits (maintainability, duplication)
4. **Low** - Nice to have (performance optimizations, minor improvements)

### When to Mark as "Blocked"
- Would introduce breaking changes to public APIs
- Requires architectural changes beyond scope
- Depends on external dependencies or infrastructure
- Would conflict with existing design patterns
- Requires team discussion or approval

### When to Mark as "Skipped"
- Low priority items with minimal impact
- Subjective style preferences
- Would require extensive refactoring for minimal benefit
- Already addressed by other fixes

### Implementation Best Practices
- Make minimal changes to fix the issue
- Follow existing code patterns and conventions
- Add comments explaining complex fixes
- Ensure backward compatibility
- Run tests after each fix
- Group related fixes together

## Usage Examples

### Implement All Findings
```
Implement the code review findings from review1.json and generate implementation_2026-04-28.json
```

### Implement Critical and High Only
```
Implement only critical and high severity findings from review1.json and generate implementation_critical_high.json
```

### Implement Specific File Findings
```
Implement findings for scheduler/scheduler.go from review1.json and generate implementation_scheduler.json
```

## Example Implementation Scenarios

### Scenario 1: Successfully Implemented
```json
{
  "file": "scheduler/scheduler.go",
  "lineNumber": 170,
  "severity": "critical",
  "originalComment": "Bug: Incorrect next run calculation",
  "status": "implemented",
  "implementation": {
    "description": "Fixed daily job next run calculation using time.Date()",
    "filesModified": ["scheduler/scheduler.go"],
    "approach": "Replaced Truncate/Add logic with time.Date() for accurate 13:00 UTC calculation"
  }
}
```

### Scenario 2: Blocked Implementation
```json
{
  "file": "scheduler/scheduler.go",
  "lineNumber": 18,
  "severity": "high",
  "originalComment": "Unexported field 'running' should be private",
  "status": "blocked",
  "blockReason": "Making 'running' private would break existing external packages that directly access this field. Requires coordination with dependent services."
}
```

### Scenario 3: Skipped Implementation
```json
{
  "file": "scheduler/scheduler.go",
  "lineNumber": 250,
  "severity": "medium",
  "originalComment": "Remove 'Made with Bob' comment",
  "status": "skipped",
  "skipReason": "Low priority cosmetic change. Can be addressed in future cleanup."
}
```

## Validation Checklist

Before marking as complete:
- [ ] All critical findings addressed (implemented or documented as blocked)
- [ ] All high severity findings addressed
- [ ] Implementation JSON file generated with complete tracking
- [ ] All modified files compile without errors
- [ ] Existing tests still pass
- [ ] New tests added for bug fixes (if applicable)
- [ ] Code follows project conventions
- [ ] No new warnings or errors introduced

## Notes

- Always explain why something cannot be implemented
- Document any assumptions made during implementation
- If a fix requires breaking changes, clearly state the impact
- Group related fixes to minimize file changes
- Test thoroughly after each implementation
- Update documentation if public APIs change
