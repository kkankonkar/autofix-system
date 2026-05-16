# GitHub Issue Analysis for Code Implementation

## Objective
Analyze a GitHub issue to determine if it has sufficient context for automated code implementation, and extract structured requirements.

## Analysis Steps

### Step 1: Classify Issue Type

Determine the issue type based on labels, title, and description:

**Bug Fix**:
- Labels: bug, defect, error, broken
- Keywords: fix, error, broken, fails, doesn't work
- Requires: reproduction steps, expected vs actual behavior

**Feature Request**:
- Labels: feature, enhancement, new
- Keywords: add, implement, create, new feature
- Requires: clear requirements, acceptance criteria

**Enhancement**:
- Labels: enhancement, improvement, optimization
- Keywords: improve, enhance, optimize, better
- Requires: current behavior description, proposed improvement

**Documentation**:
- Labels: documentation, docs
- Keywords: document, readme, guide
- Requires: what needs to be documented

### Step 2: Check Context Sufficiency

Evaluate if the issue provides enough information for implementation:

#### Required for ALL Issues:
- [ ] Detailed description (minimum 50 characters)
- [ ] Clear objective or goal
- [ ] No ambiguous requirements

#### Required for Bug Fixes:
- [ ] Steps to reproduce the bug
- [ ] Expected behavior
- [ ] Actual behavior
- [ ] Error messages or logs (if applicable)
- [ ] Environment details (if relevant)

#### Required for Features:
- [ ] Clear feature requirements
- [ ] Use cases or user stories
- [ ] Acceptance criteria
- [ ] Success metrics (optional but helpful)

#### Required for Enhancements:
- [ ] Description of current behavior
- [ ] Proposed improvement details
- [ ] Rationale for the change
- [ ] Expected impact

### Step 3: Extract Requirements

Parse the issue to extract structured requirements:

**From Checkboxes**:
```markdown
- [ ] Requirement 1
- [x] Requirement 2 (already done)
- [ ] Requirement 3
```

**From Numbered Lists**:
```markdown
1. First requirement
2. Second requirement
3. Third requirement
```

**From Acceptance Criteria**:
```markdown
## Acceptance Criteria
- User can login with OAuth
- Token refreshes automatically
- Session persists across page reloads
```

**From User Stories**:
```markdown
As a user, I want to...
So that I can...
```

### Step 4: Identify Affected Components

Look for mentions of:
- File paths: `src/auth/oauth.py`, `components/Login.tsx`
- Modules: "authentication module", "payment service"
- Functions/Classes: `processPayment()`, `UserController`
- APIs/Endpoints: `/api/auth/login`, `POST /users`
- Database tables: `users`, `transactions`

### Step 5: Find Related Issues

Extract references to other issues:
- Direct references: #123, #456
- Keywords: "related to", "depends on", "blocks", "duplicate of"

## Output Format

Generate a JSON file with the following structure:

```json
{
  "issueNumber": 123,
  "title": "Fix OAuth token refresh",
  "body": "Full issue description...",
  "type": "bug|feature|enhancement|documentation|unknown",
  "hasSufficientContext": true,
  "missingContext": [],
  "requirements": [
    {
      "description": "Token should refresh automatically when expired",
      "priority": "high|medium|low",
      "acceptanceCriteria": [
        "Token refreshes without user intervention",
        "No logout occurs during refresh",
        "Refresh happens 5 minutes before expiry"
      ]
    }
  ],
  "affectedComponents": [
    "src/auth/oauth.py",
    "src/middleware/auth.py",
    "src/config/oauth_config.py"
  ],
  "relatedIssues": [120, 115],
  "labels": ["bug", "authentication", "high-priority"],
  "contextAnalysis": {
    "hasReproductionSteps": true,
    "hasExpectedBehavior": true,
    "hasAcceptanceCriteria": true,
    "hasAffectedFiles": true,
    "clarityScore": 0.9
  }
}
```

## Missing Context Response

If `hasSufficientContext` is `false`, populate `missingContext` with specific items needed:

```json
{
  "hasSufficientContext": false,
  "missingContext": [
    "Steps to reproduce the bug",
    "Expected behavior vs actual behavior",
    "Error messages or stack traces",
    "Affected files or components (if known)"
  ]
}
```

## Priority Assignment

Assign priority based on:

**High Priority**:
- Security vulnerabilities
- Data loss bugs
- Critical functionality broken
- Blocking other work

**Medium Priority**:
- Non-critical bugs
- Feature requests with clear requirements
- Performance improvements
- UX enhancements

**Low Priority**:
- Minor bugs
- Nice-to-have features
- Documentation updates
- Code cleanup

## Examples

### Example 1: Well-Defined Bug

**Issue**:
```markdown
Title: OAuth token refresh fails after 1 hour

Description:
Users are getting logged out when their OAuth token expires after 1 hour.

Steps to reproduce:
1. Login with OAuth
2. Wait for token to expire (1 hour)
3. Try to make an API call
4. User gets logged out instead of token refreshing

Expected: Token should refresh automatically
Actual: User gets logged out

Error: "Token expired" in console

Affected files: src/auth/oauth.py, src/middleware/auth.py
```

**Analysis**:
```json
{
  "type": "bug",
  "hasSufficientContext": true,
  "missingContext": [],
  "requirements": [
    {
      "description": "Implement automatic token refresh",
      "priority": "high",
      "acceptanceCriteria": [
        "Token refreshes automatically before expiry",
        "No user logout during refresh",
        "Seamless user experience"
      ]
    }
  ],
  "affectedComponents": ["src/auth/oauth.py", "src/middleware/auth.py"]
}
```

### Example 2: Insufficient Context

**Issue**:
```markdown
Title: Fix the login bug

Description:
Login doesn't work
```

**Analysis**:
```json
{
  "type": "bug",
  "hasSufficientContext": false,
  "missingContext": [
    "Detailed description of the issue (at least 50 characters)",
    "Steps to reproduce the bug",
    "Expected behavior vs actual behavior",
    "Error messages or logs",
    "Which login method is affected (OAuth, email, etc.)"
  ]
}
```

### Example 3: Feature Request

**Issue**:
```markdown
Title: Add dark mode support

Description:
Add dark mode toggle to user settings

Requirements:
- Toggle in user settings page
- Persist preference in database
- Apply theme across all pages
- Default to system preference

Acceptance Criteria:
- [ ] Toggle visible in settings
- [ ] Theme persists across sessions
- [ ] All pages respect theme
- [ ] Tests added

Affected components:
- src/components/Settings.tsx
- src/styles/theme.ts
- src/hooks/useTheme.ts
```

**Analysis**:
```json
{
  "type": "feature",
  "hasSufficientContext": true,
  "missingContext": [],
  "requirements": [
    {
      "description": "Add dark mode toggle in settings",
      "priority": "medium",
      "acceptanceCriteria": [
        "Toggle visible in settings",
        "Theme persists across sessions",
        "All pages respect theme",
        "Tests added"
      ]
    }
  ],
  "affectedComponents": [
    "src/components/Settings.tsx",
    "src/styles/theme.ts",
    "src/hooks/useTheme.ts"
  ]
}
```

## Best Practices

1. **Be Thorough**: Check all sections of the issue (title, body, comments)
2. **Be Specific**: When context is missing, specify exactly what's needed
3. **Extract Structure**: Convert free-form text into structured requirements
4. **Identify Files**: Look for file paths, module names, component names
5. **Link Issues**: Find related issues for context
6. **Assess Clarity**: Rate how clear and actionable the issue is

## Notes

- If issue has comments, consider them for additional context
- Labels provide valuable classification hints
- Issue templates often structure information well
- Linked PRs may provide implementation clues
- Related issues can clarify requirements

---

**Generated by Fixium Issue Analyzer**