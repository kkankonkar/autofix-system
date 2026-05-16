# Verify Implementation Fixes

## Description
Quick prompt for verifying that code review findings have been properly implemented.

## Prompt Template

Review the implementations documented in {{IMPLEMENTATION_FILE}} against the current code state. Verify each fix and check for new issues introduced by the changes. Generate {{OUTPUT_FILE}} with verification results. Reference {{ORIGINAL_REVIEW_FILE}} for context.

Follow the verification workflow in prompts/code-review-post-fixes-check.md.

## Variables

- `{{IMPLEMENTATION_FILE}}`: Path to implementation JSON (e.g., implementation1.json)
- `{{OUTPUT_FILE}}`: Name of verification review JSON (e.g., review2.json)
- `{{ORIGINAL_REVIEW_FILE}}`: Path to original review JSON (e.g., review1.json)

## Usage Examples

### Standard Verification
```
Review the implementations documented in implementation1.json against the current code state. Verify each fix and check for new issues. Generate review2.json with verification results. Reference review1.json for context.
```

### Quick Critical-Only Check
```
Verify only critical and high severity implementations from implementation1.json. Generate review2_critical.json.
```

### Specific File Verification
```
Verify implementations for scheduler/scheduler.go from implementation1.json and generate review2_scheduler.json.
```

## What Gets Verified

✅ Each implemented fix is correct and complete
✅ No new bugs introduced by the fixes
✅ Blocked items have reasonable justifications
✅ Skipped items have reasonable justifications
✅ Code quality maintained or improved

## Output Format

JSON file with:
- New findings (if any issues found)
- Implementation verification status for each fix
- Assessment of blocked/skipped decisions
- Overall quality summary

See prompts/code-review-post-fixes-check.md for detailed workflow and JSON format.
