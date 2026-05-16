# Code Review Prompts for Fixium

This directory contains reusable prompt templates for automated code reviews, implementation tracking, and verification.

## Files

### 1. review-workflow.md
Comprehensive code review workflow defining:
- Review methodology and steps
- Review aspects (functionality, security, maintainability, performance)
- Findings format and severity levels
- Tool usage tips and efficiency guidelines

### 2. code-review.md
Prompt template for conducting code reviews with JSON output:
- Reviews code changes following the workflow
- Generates structured JSON findings by severity
- Includes usage examples for different scenarios

**Usage:**
```
Review ./path/to/file.go following prompts/review-workflow.md and generate review_YYYY-MM-DD.json
```

### 3. implement-review-findings.md
Prompt template for implementing review findings:
- Implements fixes with priority ordering (Critical → High → Medium → Low)
- Tracks implementation status (implemented/blocked/skipped)
- Generates JSON output documenting what was fixed and why items were blocked

**Usage:**
```
Implement the code review findings from review1.json and generate implementation_YYYY-MM-DD.json
```

### 4. code-review-post-fixes-check.md
Detailed workflow for verifying implementations after fixes:
- Comprehensive verification methodology
- Step-by-step verification process
- Detailed JSON output format specification
- Assessment guidelines and criteria

### 5. verify-implementations.md (Quick Prompt)
Concise prompt for post-implementation verification:
- Quick verification of implemented fixes
- References detailed workflow in code-review-post-fixes-check.md
- Simple usage examples

**Usage:**
```
Review the implementations documented in implementation1.json against the current code state. Verify each fix and check for new issues. Generate review2.json with verification results. Reference review1.json for context.
```

## Complete Workflow

### Phase 1: Initial Review
1. **Review Code** → Use `code-review.md` prompt
2. **Output**: `review_YYYY-MM-DD.json` with findings by severity

### Phase 2: Implementation
1. **Implement Fixes** → Use `implement-review-findings.md` prompt
2. **Output**: `implementation_YYYY-MM-DD.json` tracking what was fixed/blocked/skipped

### Phase 3: Verification
1. **Verify Fixes** → Use `verify-implementations.md` prompt (references `code-review-post-fixes-check.md`)
2. **Output**: `review2.json` verifying implementations and identifying new issues

### Phase 4: Iteration (if needed)
1. If new issues found in Phase 3, repeat Phase 2 and 3 until clean
2. Track each iteration with numbered files (implementation2.json, review3.json, etc.)

## JSON Output Formats

### Review Output (Phase 1 & 3)
```json
{
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "count": 0,
      "comments": [
        {
          "file": "path/to/file.go",
          "lineNumber": 123,
          "comment": "Issue description with suggestion"
        }
      ]
    }
  ],
  "summary": {
    "totalFindings": 14,
    "critical": 2,
    "high": 4,
    "medium": 6,
    "low": 2
  }
}
```

### Implementation Output (Phase 2)
```json
{
  "implementations": [
    {
      "file": "path/to/file.go",
      "lineNumber": 123,
      "severity": "critical",
      "status": "implemented|blocked|skipped",
      "implementation": {
        "description": "What was changed",
        "filesModified": ["file1.go"],
        "approach": "How it was fixed"
      },
      "blockReason": "Why blocked (if applicable)",
      "skipReason": "Why skipped (if applicable)"
    }
  ],
  "summary": {
    "totalFindings": 14,
    "implemented": 9,
    "blocked": 1,
    "skipped": 4
  }
}
```

### Verification Output (Phase 3)
```json
{
  "implementationVerification": {
    "totalImplementations": 9,
    "verified": 8,
    "issuesFound": 1,
    "details": [
      {
        "originalLineNumber": 170,
        "severity": "critical",
        "status": "verified|issue_found",
        "comment": "Assessment of implementation"
      }
    ]
  },
  "blockedItemsReview": {
    "totalBlocked": 1,
    "reasonable": 1,
    "details": [...]
  },
  "skippedItemsReview": {
    "totalSkipped": 4,
    "reasonable": 4,
    "details": [...]
  }
}
```

## Example Complete Cycle

```bash
# Phase 1: Initial Review
Review ./scheduler/scheduler.go following prompts/review-workflow.md and generate review1.json

# Phase 2: Implement Fixes
Implement the code review findings from review1.json and generate implementation1.json

# Phase 3: Verify Implementations
Review the implementations documented in implementation1.json against the current code state. 
Verify each fix and check for new issues. Generate review2.json with verification results. 
Reference review1.json for context.

# Phase 4: If issues found, iterate
Implement the code review findings from review2.json and generate implementation2.json
# Then verify again...
```

## Quick Reference

| Phase | Prompt File | Input | Output |
|-------|-------------|-------|--------|
| 1. Review | code-review.md | Source files | review1.json |
| 2. Implement | implement-review-findings.md | review1.json | implementation1.json |
| 3. Verify | verify-implementations.md | implementation1.json | review2.json |
| 4. Iterate | (repeat 2-3) | review2.json | implementation2.json, review3.json... |

## Benefits

- **Accountability**: Complete audit trail from review → implementation → verification
- **Quality Assurance**: Catches issues introduced by fixes
- **Decision Validation**: Reviews blocked/skipped decisions for reasonableness
- **Continuous Improvement**: Iterative process until all issues resolved
- **Automation Ready**: JSON outputs can be parsed by CI/CD tools
- **Version Control**: All prompts and outputs are version-controlled

## Notes

- All prompt files reference `prompts/review-workflow.md` for consistency
- JSON outputs can be parsed by CI/CD tools or review dashboards
- Prompts are version-controlled and can be customized per project
- The workflow supports iterative refinement until code quality goals are met
- Use `verify-implementations.md` for quick verification (it references the detailed workflow)
