# Code Review Post-Fixes Verification

## Description
Verify that code review findings have been properly implemented and identify any new issues introduced by the fixes.

## Prompt Template

Review the implementations documented in {{IMPLEMENTATION_FILE}} against the current code state. Verify each fix and check for new issues introduced by the changes.

**Verification Scope:**
- Verify each implemented fix is correct and complete
- Check for new bugs or issues introduced by the fixes
- Validate that blocked items have reasonable justifications
- Validate that skipped items have reasonable justifications
- Identify any redundant or suboptimal implementations

**Output Requirements:**
Generate a JSON file named `{{OUTPUT_FILE}}` with verification results and any new findings.

Reference the original review file {{ORIGINAL_REVIEW_FILE}} for context.

## Variables

- `{{IMPLEMENTATION_FILE}}`: Path to the implementation tracking JSON (e.g., implementation1.json)
- `{{OUTPUT_FILE}}`: Name of the verification review JSON (e.g., review2.json)
- `{{ORIGINAL_REVIEW_FILE}}`: Path to the original review JSON (e.g., review1.json)

## JSON Output Format

```json
{
  "reviewFile": "implementation1.json",
  "reviewDate": "2026-04-28T14:37:41Z",
  "previousReview": "review1.json",
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "count": 0,
      "comments": [
        {
          "file": "path/to/file.go",
          "lineNumber": 123,
          "comment": "Description of new issue found"
        }
      ]
    }
  ],
  "implementationVerification": {
    "totalImplementations": 9,
    "verified": 8,
    "issuesFound": 1,
    "details": [
      {
        "originalLineNumber": 170,
        "severity": "critical",
        "status": "verified|issue_found",
        "comment": "Assessment of the implementation"
      }
    ]
  },
  "blockedItemsReview": {
    "totalBlocked": 1,
    "reasonable": 1,
    "details": [
      {
        "originalLineNumber": 1,
        "severity": "high",
        "originalComment": "Original review comment",
        "blockReason": "Reason given for blocking",
        "reviewerAssessment": "Assessment of whether block reason is valid"
      }
    ]
  },
  "skippedItemsReview": {
    "totalSkipped": 4,
    "reasonable": 4,
    "details": [
      {
        "originalLineNumber": 18,
        "severity": "high",
        "originalComment": "Original review comment",
        "skipReason": "Reason given for skipping",
        "reviewerAssessment": "Assessment of whether skip reason is valid"
      }
    ]
  },
  "summary": {
    "totalNewFindings": 3,
    "implementationsVerified": 8,
    "implementationsWithIssues": 1,
    "blockedItemsReasonable": 1,
    "skippedItemsReasonable": 4,
    "overallAssessment": "Summary of implementation quality"
  }
}
```

## Verification Workflow

### 1. Read Implementation File
- Load the implementation tracking JSON
- Understand what was implemented, blocked, or skipped
- Note the files that were modified

### 2. Read Current Code State
- Read all modified files with line numbers
- Compare current state with implementation descriptions
- Verify changes match what was documented

### 3. Verify Each Implementation
For each implemented fix:
- **Locate the change** in the current code
- **Verify correctness** - Does it properly address the original issue?
- **Check for side effects** - Did it introduce new problems?
- **Assess quality** - Is it implemented following best practices?

Status options:
- `verified` - Implementation is correct and complete
- `issue_found` - Implementation has problems or introduced new issues

### 4. Review Blocked Items
For each blocked item:
- **Read the block reason**
- **Assess validity** - Is the reason legitimate?
- **Check alternatives** - Could it have been implemented differently?

Assessment criteria:
- ✅ Reasonable: Breaking changes, architectural constraints, requires team discussion
- ❌ Unreasonable: Lack of effort, misunderstanding, easily solvable

### 5. Review Skipped Items
For each skipped item:
- **Read the skip reason**
- **Assess validity** - Is the reason legitimate?
- **Check impact** - What's the cost of not fixing it?

Assessment criteria:
- ✅ Reasonable: Low priority, minimal impact, subjective preference, already addressed
- ❌ Unreasonable: Important issue dismissed, incorrect assessment

### 6. Identify New Issues
Check for problems introduced by fixes:
- **Type errors** or incorrect conversions
- **Redundant code** or unnecessary complexity
- **Performance regressions**
- **Breaking changes** not documented
- **Incomplete fixes** that only partially address the issue

### 7. Generate Verification Report
Create comprehensive JSON with:
- New findings from verification
- Status of each implementation
- Assessment of blocked/skipped decisions
- Overall quality assessment

## Verification Checklist

- [ ] All implemented fixes verified against current code
- [ ] Each implementation assessed for correctness
- [ ] New issues introduced by fixes identified
- [ ] All blocked items reviewed for reasonableness
- [ ] All skipped items reviewed for reasonableness
- [ ] Verification JSON generated with complete tracking
- [ ] Overall assessment provided

## Assessment Guidelines

### Implementation Status
- **Verified**: Fix is correct, complete, and doesn't introduce issues
- **Issue Found**: Fix has problems, is incomplete, or introduces new issues

### Block/Skip Reasonableness
- **Reasonable**: Valid technical, architectural, or process constraints
- **Unreasonable**: Could have been fixed with reasonable effort

### New Issue Severity
- **Critical**: Bugs, security issues, data corruption risks
- **High**: Functionality problems, incorrect behavior
- **Medium**: Maintainability issues, code quality problems
- **Low**: Minor improvements, style issues

## Usage Examples

### Verify Implementation
```
Review the implementations documented in implementation1.json against the current code state. Verify each fix and check for new issues. Generate review2.json with verification results. Reference review1.json for context.
```

### Verify Specific Severity
```
Review only critical and high severity implementations from implementation1.json. Verify correctness and generate review2_critical_high.json.
```

### Quick Verification
```
Quick verification of implementations in implementation1.json. Focus on critical fixes only. Generate review2_quick.json.
```

## Example Verification Scenarios

### Scenario 1: Correctly Implemented
```json
{
  "originalLineNumber": 170,
  "severity": "critical",
  "status": "verified",
  "comment": "Next run calculation correctly fixed using time.Date() at line 190. Implementation is correct."
}
```

### Scenario 2: Implementation Has Issues
```json
{
  "originalLineNumber": 92,
  "severity": "medium",
  "status": "issue_found",
  "comment": "Constant IMMEDIATE_EXECUTION_THRESHOLD correctly defined at line 13, but usage at line 109 has type conversion issue. See new finding."
}
```

### Scenario 3: Reasonable Block
```json
{
  "originalLineNumber": 1,
  "severity": "high",
  "blockReason": "Creating comprehensive unit tests requires creating a new test file...",
  "reviewerAssessment": "Reasonable. Unit test creation is indeed a separate task that requires significant effort."
}
```

### Scenario 4: Reasonable Skip
```json
{
  "originalLineNumber": 18,
  "severity": "high",
  "skipReason": "The 'running' field is already lowercase (unexported) in Go...",
  "reviewerAssessment": "Correct. The field is already properly encapsulated. The original review comment was incorrect."
}
```

## Notes

- This workflow creates accountability for implementation quality
- Verifies that fixes don't introduce new problems
- Validates decision-making for blocked/skipped items
- Provides feedback loop for continuous improvement
- Documents the complete review → implement → verify cycle
- Can be repeated iteratively until all issues are resolved
