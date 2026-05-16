# Implementation Plan: `Fixium:updatedocs` Feature

**Feature**: Intelligent documentation update suggestions for PRs with major features  
**Date Created**: 2026-05-09  
**Status**: Planning Complete - Ready for Implementation

---

## Overview

Add intelligent documentation update suggestions for PRs containing major features, with **automatic discovery and analysis of ALL markdown documentation files** in the repository (README.md, docs/, wiki/, CONTRIBUTING.md, etc.), while filtering out minor changes like bug fixes, package upgrades, and vulnerability patches.

---

## Table of Contents

1. [Architecture Design](#architecture-design)
2. [Change Classification System](#change-classification-system)
3. [Documentation Discovery System](#documentation-discovery-system)
4. [Implementation Components](#implementation-components)
5. [Output Format](#output-format)
6. [Testing Strategy](#testing-strategy)
7. [Implementation Priority](#implementation-priority)

---

## Architecture Design

### High-Level Flow

```
User comments: "Fixium:updatedocs" on PR
         ↓
GitHub Actions triggers fixium-docs job
         ↓
Python: Parse command & authorize user
         ↓
Discover all .md files in repository
         ↓
Classify PR changes (major vs minor)
         ↓
If minor changes → Skip with explanation
         ↓
If major changes → Analyze all doc files
         ↓
Bob AI identifies documentation gaps
         ↓
Generate suggestions JSON
         ↓
Post formatted comment to PR
```

---

## Change Classification System

### Major Changes (Trigger Documentation Analysis)

- ✅ New public APIs, functions, classes, or modules
- ✅ New features or capabilities
- ✅ Significant behavior changes to existing features
- ✅ New configuration options or environment variables
- ✅ Breaking changes or deprecations
- ✅ New CLI commands or endpoints
- ✅ Architecture or design pattern changes

### Minor Changes (Skip Documentation Analysis)

- ❌ Bug fixes (unless they change behavior significantly)
- ❌ Package/dependency upgrades
- ❌ Security vulnerability patches
- ❌ Code refactoring without behavior changes
- ❌ Performance optimizations (internal)
- ❌ Test additions/updates
- ❌ Linting/formatting changes
- ❌ Comment updates

---

## Documentation Discovery System

Automatically discovers ALL .md files in repository:
- Root level: README.md, CONTRIBUTING.md, etc.
- docs/ directory and subdirectories
- wiki/ directory
- .github/ directory
- Any other directories containing .md files

Categorizes by type:
- README files
- API reference documentation
- User guides and tutorials
- Developer guides
- Configuration documentation
- Architecture documentation
- FAQ and troubleshooting

---

## Implementation Components

See detailed component specifications in sections below.

### Component Files to Create:

1. `fixium/doc_discoverer.py` - Documentation file discovery
2. `fixium/change_classifier.py` - PR change classification
3. `fixium/doc_runner.py` - Documentation analysis runner
4. `fixium/doc_main.py` - Main entry point
5. `prompts/analyze-documentation.md` - Analysis prompt template

### Files to Update:

1. `fixium/comment_parser.py` - Add `updatedocs` command
2. `review_workflow.sh` - Add `analyze-docs` function
3. `.github/workflows/fixium.yml` - Add `fixium-docs` job
4. `README.md` - Add usage documentation
5. `agents.md` - Add workflow documentation

---

## Output Format

### JSON Structure

```json
{
  "prNumber": 123,
  "analysisDate": "2026-05-09T08:00:00Z",
  "discoveredDocs": {
    "readme": ["README.md"],
    "api_reference": ["docs/api.md"],
    "user_guide": ["docs/getting-started.md"],
    "developer_guide": ["CONTRIBUTING.md"],
    "configuration": ["docs/configuration.md"]
  },
  "changeClassification": {
    "type": "major_feature|minor_change",
    "confidence": "high|medium|low",
    "reasons": ["List of reasons"],
    "majorChanges": [...]
  },
  "shouldUpdateDocs": true,
  "documentationGaps": [
    {
      "file": "README.md",
      "fileType": "readme",
      "section": "Features",
      "priority": "high",
      "issue": "Description of gap",
      "suggestion": "What to add",
      "exampleContent": "Sample markdown",
      "relatedChanges": ["src/file.py"]
    }
  ],
  "summary": {
    "totalDocsDiscovered": 15,
    "totalGaps": 5,
    "byPriority": {"critical": 1, "high": 2},
    "byFileType": {"readme": 1, "api_reference": 1}
  }
}
```

---

## Testing Strategy

### Unit Tests

- `tests/test_change_classifier.py` - Change classification logic
- `tests/test_doc_discoverer.py` - Documentation discovery
- `tests/test_doc_runner.py` - Analysis workflow

### Integration Tests

- Full workflow from PR comment to result posting
- Multi-file documentation analysis
- Classification accuracy validation

---

## Implementation Priority

### Phase 1: Core Components (Week 1)
1. Create `fixium/doc_discoverer.py`
2. Create `fixium/change_classifier.py`
3. Create `prompts/analyze-documentation.md`
4. Update `fixium/comment_parser.py`

### Phase 2: Integration (Week 2)
5. Create `fixium/doc_runner.py`
6. Create `fixium/doc_main.py`
7. Update `review_workflow.sh`
8. Update `.github/workflows/fixium.yml`

### Phase 3: Testing & Documentation (Week 3)
9. Create all unit tests
10. Create integration tests
11. Update README.md
12. Update agents.md

---

## Benefits

- ✅ **Smart Filtering**: Only analyzes major changes
- ✅ **Complete Coverage**: Checks ALL .md files
- ✅ **Specific Suggestions**: Actionable with examples
- ✅ **Time Saving**: Automated documentation review
- ✅ **Consistency**: Keeps docs current with code

---

**Status**: Ready for implementation  
**Next Step**: Begin Phase 1 - Core Components