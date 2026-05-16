# Code Review with JSON Output

## Description
Comprehensive code review following established workflow with structured JSON output for findings.

## Prompt Template

Review the code changes in {{FILE_PATH_OR_BRANCH}} following the workflow defined in prompts/review-workflow.md.

**Review Scope:**
- Bugs and edge cases
- Security vulnerabilities  
- Performance issues
- Maintainability and code duplication
- Missing tests
- Race conditions
- Breaking changes

**Output Requirements:**
Generate a JSON file named `{{OUTPUT_FILE}}` with findings structured by severity levels (critical, high, medium, low).

Include local uncommitted changes in the review.

## Variables

- `{{FILE_PATH_OR_BRANCH}}`: Can be:
  - Single file path: `./path/to/file.go`
  - Directory: `./path/to/directory/`
  - Branch name: `main`, `feature-branch`
  - Multiple files: Space-separated list of file paths
  - File list reference: `@files.txt` (shell script expands this into individual file paths)
- `{{OUTPUT_FILE}}`: Name of the JSON output file (e.g., review_2026-04-28.json)

## File List Format

When using `@files.txt` syntax in the shell script, the script will:
1. Read the file list
2. Validate each file exists
3. Expand the list into individual file paths
4. Pass all files to Fixium in a single command

The file should contain:
- One file path per line
- Comments starting with `#` are ignored
- Empty lines are ignored
- Relative or absolute paths

Example `files.txt`:
```
# Files to review
./handlers/v2/consumption.go
./handlers/v2/offerings.go
./internal/common/kube.go

# Add more files as needed
./path/to/another/file.go
```

**Note:** Fixium receives the expanded file paths, not the `@files.txt` reference. The shell script handles the file list expansion.

## JSON Output Format

**IMPORTANT:** Output MUST conform to the canonical schema defined in `schema/review_output.schema.json`.

### Required Structure

```json
{
  "pr_number": 123,
  "files_reviewed": ["path/to/file1.go", "path/to/file2.go"],
  "review_summary": {
    "total_findings": 8,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 2
  },
  "findings": [
    {
      "file": "path/to/file.go",
      "line": 123,
      "column": 5,
      "severity": "critical|high|medium|low",
      "type": "security|bug|maintainability|performance|style",
      "title": "Short title of the issue",
      "description": "Detailed description of the issue",
      "details": "Additional context (optional)",
      "suggestion": "Suggested fix (optional)",
      "code_snippet": "Problematic code (optional)"
    }
  ],
  "recommendations": [
    {
      "priority": "critical|high|medium|low",
      "action": "High-level recommendation"
    }
  ],
  "positive_aspects": [
    "Good practice noted during review"
  ],
  "overall_assessment": "Summary of the review",
  "reviewed_by": "Bob Shell Code Review",
  "review_date": "2026-05-14T10:58:39.158Z"
}
```

### Schema Validation

- All output MUST validate against `schema/review_output.schema.json`
- Use snake_case for all field names (e.g., `total_findings`, not `totalFindings`)
- Use `review_summary` key (not `summary`)
- Severity values: `critical`, `high`, `medium`, `low`
- Type values: `security`, `bug`, `maintainability`, `performance`, `style`

### Field Requirements

**Required fields:**
- `pr_number`: Pull request number
- `files_reviewed`: Array of reviewed file paths
- `review_summary`: Object with `total_findings`, `critical`, `high`, `medium`, `low`
- `findings`: Array of finding objects

**Optional fields:**
- `recommendations`: High-level action items
- `positive_aspects`: Good practices noted
- `overall_assessment`: Summary text
- `reviewed_by`: Reviewer identifier
- `review_date`: ISO 8601 timestamp
```

## Usage Examples

### Review Specific File
```
Review ./scheduler/scheduler.go following prompts/review-workflow.md and generate review_scheduler.json
```

### Review Directory
```
Review all Go files in ./scheduler/ directory following prompts/review-workflow.md and generate review_scheduler_package.json
```

### Review Multiple Files from List
When using the shell script:
```bash
./review_workflow.sh review @changed_files.txt
```

The script expands the file list and Fixium receives:
```
Review ./handlers/v2/consumption.go ./handlers/v2/offerings.go ./internal/common/kube.go following prompts/review-workflow.md and generate review_changes.json
```

Where `changed_files.txt` contains:
```
./handlers/v2/consumption.go
./handlers/v2/offerings.go
./internal/common/kube.go
```

### Review Branch Changes
```
Compare my local branch with main, review all changes following prompts/review-workflow.md, and generate review_feature.json
```

### Review Uncommitted Changes
```
Review all uncommitted changes following prompts/review-workflow.md and generate review_uncommitted.json
```

## Severity Levels

- **Critical**: Bugs, race conditions, security vulnerabilities that could cause system failure or data loss
- **High**: Functionality issues, missing validation, missing tests for critical code
- **Medium**: Maintainability issues, code duplication, magic numbers, hardcoded values
- **Low**: Performance optimizations, minor improvements, style suggestions

## Notes

- The review follows the comprehensive workflow defined in `.bob/review-workflow.md`
- All findings include file path, line number, and actionable suggestions
- The JSON output can be easily parsed by CI/CD tools or review dashboards
- Review includes both committed and uncommitted changes unless specified otherwise
