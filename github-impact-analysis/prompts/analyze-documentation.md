# Documentation Analysis for Feature Changes

## Objective
Analyze PR changes and suggest documentation updates across ALL markdown files in the repository.

## Step 1: Discover Documentation Files

The system has already discovered all documentation files in the repository and categorized them by type:
- README files
- API reference documentation
- User guides and tutorials
- Developer guides
- Configuration documentation
- Architecture documentation
- FAQ and troubleshooting
- Other documentation

## Step 2: Classify PR Changes

Review the PR diff and classify changes:

### Major Changes (ANALYZE DOCS)
- **New Features**: New APIs, endpoints, functions, classes, modules
- **Significant Updates**: Behavior changes, breaking changes, deprecations
- **New Configuration**: New environment variables, config options, settings
- **Architecture Changes**: New components, design pattern changes

### Minor Changes (SKIP)
- Bug fixes (unless behavior significantly changes)
- Dependency/package upgrades
- Security vulnerability patches
- Internal refactoring without API changes
- Test-only changes
- Linting/formatting changes
- Comment updates

## Step 3: Analyze Each Documentation File

For each discovered documentation file, check if it needs updates based on PR changes:

### README.md
- Does it mention the new feature in the features list?
- Is the installation/setup section still accurate?
- Are usage examples up to date?
- Are quick start instructions current?

### API Reference Files (docs/api.md, docs/endpoints.md, etc.)
- Are new endpoints/functions documented?
- Are parameter changes reflected?
- Are return types updated?
- Are error codes documented?
- Are authentication requirements mentioned?

### User Guides (docs/user-guide.md, docs/getting-started.md, etc.)
- Do tutorials cover new features?
- Are screenshots/examples current?
- Are configuration steps accurate?
- Are prerequisites up to date?

### Developer Guides (docs/development.md, CONTRIBUTING.md, etc.)
- Are new development requirements mentioned?
- Is the architecture section current?
- Are build/test instructions accurate?
- Are coding standards updated?

### Configuration Documentation (docs/configuration.md, docs/settings.md, etc.)
- Are new config options documented?
- Are environment variables listed?
- Are default values correct?
- Are examples provided?

### Architecture Documentation (docs/architecture.md, docs/design.md, etc.)
- Do diagrams reflect new components?
- Are design decisions documented?
- Are dependencies updated?
- Are integration points described?

### Tutorial Files (docs/tutorial.md, docs/examples.md, etc.)
- Do examples use new features?
- Are code samples current?
- Are step-by-step instructions accurate?

### FAQ/Troubleshooting (docs/faq.md, docs/troubleshooting.md, etc.)
- Are common issues with new features addressed?
- Are error messages explained?
- Are workarounds documented?

## Step 4: Generate Specific Suggestions

For each documentation gap found, provide:

```json
{
  "file": "path/to/doc.md",
  "fileType": "api_reference|user_guide|readme|etc",
  "section": "Specific section name or 'New Section'",
  "priority": "critical|high|medium|low",
  "issue": "What's missing or outdated",
  "suggestion": "What to add/update",
  "exampleContent": "Sample markdown content to add",
  "relatedChanges": ["List of PR files that triggered this suggestion"]
}
```

### Priority Guidelines

- **Critical**: Missing documentation for new public APIs, breaking changes, security features
- **High**: Missing feature documentation, outdated setup instructions, incorrect examples
- **Medium**: Missing configuration options, incomplete tutorials, outdated screenshots
- **Low**: Minor improvements, additional examples, clarifications

## Output Format

Generate a JSON file with the following structure:

```json
{
  "prNumber": 123,
  "analysisDate": "2026-05-09T08:00:00Z",
  "discoveredDocs": {
    "readme": ["README.md"],
    "api_reference": ["docs/api.md", "docs/endpoints.md"],
    "user_guide": ["docs/getting-started.md", "docs/user-guide.md"],
    "developer_guide": ["docs/development.md", "CONTRIBUTING.md"],
    "configuration": ["docs/configuration.md"],
    "architecture": ["docs/architecture.md"],
    "tutorial": ["docs/tutorial.md"],
    "faq": ["docs/faq.md"],
    "other": ["docs/misc.md"]
  },
  "changeClassification": {
    "type": "major_feature|significant_update|minor_change",
    "confidence": "high|medium|low",
    "reasons": ["Reasons for classification"],
    "majorChanges": [
      {
        "file": "src/api/auth.py",
        "type": "new_api",
        "description": "OAuth2 authentication endpoints"
      }
    ]
  },
  "shouldUpdateDocs": true,
  "documentationGaps": [
    {
      "file": "README.md",
      "fileType": "readme",
      "section": "Features",
      "priority": "high",
      "issue": "New OAuth2 authentication not mentioned",
      "suggestion": "Add OAuth2 to features list and quick start",
      "exampleContent": "- **OAuth2 Authentication**: Secure API access with OAuth2 protocol. Supports authorization code flow and refresh tokens.",
      "relatedChanges": ["src/api/auth.py", "src/config/oauth.py"]
    },
    {
      "file": "docs/api.md",
      "fileType": "api_reference",
      "section": "Authentication Endpoints",
      "priority": "critical",
      "issue": "New /auth endpoints not documented",
      "suggestion": "Document POST /auth/login and POST /auth/token",
      "exampleContent": "### POST /auth/login\n\n**Description**: Authenticates user and returns access token.\n\n**Request Body**:\n```json\n{\n  \"username\": \"string\",\n  \"password\": \"string\"\n}\n```\n\n**Response**:\n```json\n{\n  \"access_token\": \"string\",\n  \"token_type\": \"Bearer\",\n  \"expires_in\": 3600\n}\n```",
      "relatedChanges": ["src/api/auth.py"]
    }
  ],
  "filesCheckedNoGaps": [
    {
      "file": "docs/architecture.md",
      "reason": "Already contains authentication system architecture"
    },
    {
      "file": "docs/faq.md",
      "reason": "No authentication-related FAQs need updating"
    }
  ],
  "summary": {
    "totalDocsDiscovered": 15,
    "totalDocsChecked": 12,
    "totalGaps": 5,
    "byPriority": {
      "critical": 1,
      "high": 3,
      "medium": 1,
      "low": 0
    },
    "byFileType": {
      "readme": 1,
      "api_reference": 1,
      "user_guide": 1,
      "configuration": 1,
      "developer_guide": 1
    }
  }
}
```

## Example Analysis Scenarios

### Scenario 1: New API Feature

**PR Changes:**
- Added OAuth2 authentication (src/api/auth.py)
- New config options (src/config/oauth.py)
- Updated middleware (src/middleware/auth.py)

**Documentation Gaps:**
1. **README.md** - Missing feature mention in features list
2. **docs/api.md** - New endpoints not documented
3. **docs/getting-started.md** - Setup instructions don't include OAuth2 configuration
4. **docs/configuration.md** - New environment variables not listed
5. **CONTRIBUTING.md** - New test requirements not mentioned

### Scenario 2: Bug Fix (Skip)

**PR Changes:**
- Fixed null pointer exception (src/utils/helper.py)
- Added test case (tests/test_helper.py)

**Result:** `shouldUpdateDocs: false` - Minor change, no documentation updates needed

### Scenario 3: Breaking Change

**PR Changes:**
- Removed deprecated API endpoint (src/api/legacy.py)
- Updated client library (src/client/api.py)

**Documentation Gaps:**
1. **README.md** - Migration guide needed (CRITICAL)
2. **docs/api.md** - Deprecation notice and alternatives (HIGH)
3. **docs/migration.md** - Step-by-step migration instructions (CRITICAL)

## Best Practices

1. **Be Specific**: Provide exact section names and line numbers when possible
2. **Provide Examples**: Include sample markdown content for each suggestion
3. **Link Changes**: Always reference the PR files that triggered each suggestion
4. **Prioritize Correctly**: Use priority levels to help developers focus on critical gaps
5. **Check Thoroughly**: Review ALL discovered documentation files, not just README
6. **Consider Context**: Understand the feature before suggesting documentation
7. **Be Actionable**: Suggestions should be clear and implementable

## Notes

- Skip CHANGELOG.md as it's typically auto-generated
- Focus on user-facing documentation for public APIs
- Internal implementation details may not need documentation
- Consider the audience for each documentation type (users vs developers)
- Suggest creating new documentation files if none exist for a major feature

---

**Generated by Fixium Documentation Analyzer**