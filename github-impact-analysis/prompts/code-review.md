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
          "comment": "Detailed comment with explanation and suggestion"
        }
      ]
    }
  ],
  "summary": {
    "totalFindings": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }
}
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
