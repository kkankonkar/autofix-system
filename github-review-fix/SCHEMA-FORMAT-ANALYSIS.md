# Schema Format Analysis - Multiple Bob Shell Outputs

## Problem: Inconsistent JSON Formats

Bob Shell is producing **different JSON formats** across different runs:

### Format 1 (review_pr3.json - Earlier)
```json
{
  "pr_number": 3,
  "files_reviewed": ["README.md"],
  "review_summary": {
    "total_findings": 8,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 2
  },
  "findings": [
    {
      "severity": "critical",
      "type": "security",
      ...
    }
  ]
}
```

### Format 2 (review_pr3 2.json - Latest)
```json
{
  "pr_number": 3,
  "files_reviewed": ["README.md"],
  "statistics": {
    "total_findings": 8,
    "critical": 1,
    "high": 3,
    "medium": 2,
    "low": 2,
    "info": 1
  },
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "SECURITY",
      ...
    }
  ]
}
```

## Key Differences

| Field | Format 1 | Format 2 |
|-------|----------|----------|
| Summary key | `review_summary` | `statistics` |
| Severity values | `critical`, `high`, `medium`, `low` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` |
| Type/Category key | `type` | `category` |
| Type values | `security`, `bug`, etc. | `SECURITY`, `DOCUMENTATION`, etc. |
| Additional fields | `reviewed_by`, `review_date` | `reviewer`, `review_date`, `overall_assessment`, `summary` |

## Root Cause

Bob Shell is **not following the schema** defined in `schema/review_output.schema.json`. The prompt in `prompts/code-review.md` references the schema, but Bob is generating different formats.

## Solutions

### Option 1: Enforce Schema in Prompt (Recommended)
Update the Bob Shell prompt to be more explicit about the exact format required.

### Option 2: Support Multiple Formats
Make the Python code flexible enough to handle both formats (not recommended - defeats the purpose of having a schema).

### Option 3: Validate Output
Add a validation step after Bob generates the JSON to ensure it conforms to the schema before the Python runner processes it.

## Recommendation

**Option 1 + Option 3**: 
1. Make the prompt more explicit with examples
2. Add validation in the shell script before passing to Python
3. Reject non-conforming output with clear error messages

This ensures consistency and makes debugging easier.

## Next Steps

1. Update `prompts/code-review.md` with explicit format requirements
2. Add JSON schema validation to `review_workflow.sh`
3. Update Python code to provide clear error messages for non-conforming JSON
4. Add schema validation tests

---

**Analysis Date**: 2026-05-14  
**Issue**: Bob Shell producing inconsistent JSON formats  
**Impact**: Python runner cannot reliably parse review results