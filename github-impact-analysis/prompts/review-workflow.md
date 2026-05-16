# Code Review Workflow for Fixium

## Overview
This document defines a comprehensive code review workflow that can be reused across projects. It covers review aspects, methodology, and reporting standards.

## Review Workflow Steps

### 1. Get Context
- **For specific branch reviews**: Use `git diff` to compare local branch with specified branch (e.g., main) and include local uncommitted changes. Exclude untracked files.
- **For general reviews**: Use `git diff` to get all changes in the working directory, including local uncommitted changes and changes to the remote tracking branch.
- **For each changed file**: Run `read_file` with `display_line_numbers` to see full context.

### 2. Find Related Code
- Check where modified functions are used
- Look for similar code patterns
- Find imports of modified files
- Search for test files with patterns: `_test.`, `test_*`, `.spec.`
- Check for both direct usage and indirect dependencies

### 3. Review Changes
Check each file for:
- **Bugs**: Logic errors, null checks, edge cases
- **Security**: Input validation, SQL injection, auth checks
- **Performance**: Nested loops, unnecessary queries, memory leaks
- **Style**: Naming, formatting, code organization
- **Tests**: New code has tests, tests updated for changes

### 4. Verify Impact
- Search for breaking changes in public APIs
- Check if all related files were updated
- Look for missing config or documentation updates

### 5. Report Findings
Report findings as specified in the "Findings Format" section below.

## Review Aspects

### Functionality Aspects
- **Edge Cases**: Review code for edge cases that cause unexpected or invalid behavior (unintended/invalid input, null or empty values)
- **Hardcoding**: Don't allow forbidden hardcoding unless in test cases
- **Error Handling**: Ensure appropriate abstraction, logging, or graceful handling. HTTP status codes should fit actual errors (400 for bad request, 500 for server error)
- **Resource Management**: Clean up resources and ensure closing open resources when done
- **Global State**: Check if changes introduce unnecessary global state
- **Breaking Changes**: Check if new additions introduce breaking changes to public interfaces/functions
- **Race Conditions**: Identify potential race conditions in concurrent code
- **State Management**: Warn against unnecessary global state usage
- **Backward Compatibility**: Ensure no breaking changes to public APIs, function signatures, or data structures

### Security Aspects
- **Sensitive Data Logging**: Identify instances where sensitive information might be logged or printed
- **Input Sanitization**: Check for proper sanitization and validation of user inputs
- **Gitignore Recommendations**: Suggest changes to avoid committing secrets or sensitive files
- **Secure Dependencies**: Flag usage of outdated, vulnerable, or untrusted third-party libraries
- **Security Fixes**: Recommend specific fixes to mitigate security risks

### Maintainability Aspects
- **Magic Numbers**: Identify numeric literals used directly without explanation
- **String Literals**: Find string literals that should be constants or configuration values
- **Duplicate Values**: Detect same literal values used in multiple places
- **Environment-dependent Values**: Identify values that might need to change based on environment
- **Variable Naming**: Check if variable/constant names clearly explain their purpose

### Performance Aspects
- **Batching**: Identify repeated network or database calls that can be batched
- **Caching**: Review usage of caching for frequently accessed data
- **Asset Optimization**: Highlight need to compress or minify static assets
- **Debouncing/Throttling**: Examine event-driven code for optimization opportunities

## Findings Format

```
<relative-path-to-file>:<line>:<column> - <type>: <short description>
<explanation>
<suggestion>
```

### Example Findings
```
src/scheduler/scheduler.go:92:2 - maintainability: Magic number should be constant
  The magic number 30 should be extracted to a named constant
  Define const IMMEDIATE_EXECUTION_THRESHOLD = 30 * time.Second

src/scheduler/scheduler.go:170:1 - performance: Complex time calculation could be simplified
  The next run calculation is overly complex and hard to understand
  Use time.Date() with cleaner arithmetic for better readability
```

## Tool Usage Tips
- Cache file contents to avoid re-reading
- Discover project structure efficiently
- Use combined commands to minimize operations
- Search for patterns using efficient tools like `find`, `grep`, and `git` commands

## Efficiency Guidelines
- Combine multiple actions into single commands where possible
- Use efficient tools with appropriate filters
- Minimize unnecessary operations when exploring codebase

## Code Quality Standards
- Write clean, efficient code with minimal comments
- Avoid redundancy in comments
- Focus on minimal changes needed to solve problems
- Consider splitting large functions or files when appropriate

## Usage Instructions
1. Load this workflow at the start of any code review session
2. Follow the steps sequentially
3. Use the review aspects as a checklist
4. Format findings according to the specified format
5. Complete all steps before submitting findings
