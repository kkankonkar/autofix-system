# Fixium Review Output Schema

This directory contains the canonical JSON schema for code review output produced by Bob Shell and consumed by the Fixium Python runner.

## Schema File

**[`review_output.schema.json`](review_output.schema.json)** - JSON Schema (Draft 07) defining the structure of review output files.

## Purpose

This schema ensures consistency between:
- **Producer**: Bob Shell code review prompts that generate JSON output
- **Consumer**: Fixium Python runner that processes review results

## Schema Overview

### Required Fields

```json
{
  "pr_number": 123,
  "files_reviewed": ["file1.go", "file2.go"],
  "review_summary": {
    "total_findings": 8,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 2
  },
  "findings": [...]
}
```

### Field Naming Convention

**IMPORTANT**: All field names use **snake_case** (not camelCase):
- ✅ `total_findings`
- ✅ `review_summary`
- ❌ `totalFindings`
- ❌ `reviewSummary`

### Severity Levels

Valid severity values (enum):
- `critical` - Security vulnerabilities, data loss risks
- `high` - Bugs, broken functionality
- `medium` - Maintainability issues, code smells
- `low` - Style issues, minor improvements

### Finding Types

Valid type values (enum):
- `security` - Security vulnerabilities
- `bug` - Functional bugs
- `maintainability` - Code quality issues
- `performance` - Performance problems
- `style` - Code style issues

## Usage

### For Bob Shell Prompts

When creating review prompts, reference this schema:

```markdown
**Output Requirements:**
Generate JSON output conforming to `schema/review_output.schema.json`
```

See [`prompts/code-review.md`](../prompts/code-review.md) for the complete prompt template.

### For Python Code

The Python runner expects this exact schema:

```python
# Read review data
with open(output_path) as f:
    review_data = json.load(f)

# Extract summary (must use 'review_summary' key)
summary_data = review_data.get('review_summary', {})
total_findings = summary_data.get('total_findings', 0)
```

See [`fixium/main.py`](../fixium/main.py) for implementation details.

### For Tests

Tests validate against this schema:

```python
# Verify required fields exist
assert "pr_number" in review_data
assert "files_reviewed" in review_data
assert "review_summary" in review_data
assert "findings" in review_data
```

See [`tests/test_main_json_formats.py`](../tests/test_main_json_formats.py) for validation tests.

## Schema Validation

To validate a review JSON file against the schema:

```bash
# Using Python jsonschema library
python3 -c "
import json
import jsonschema

with open('schema/review_output.schema.json') as f:
    schema = json.load(f)

with open('review_pr3.json') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print('✅ Valid')
"
```

## Example Output

Complete example conforming to the schema:

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
      "file": "README.md",
      "line": 267,
      "column": 1,
      "severity": "critical",
      "type": "security",
      "title": "Database Password Exposed",
      "description": "Hardcoded password in documentation",
      "details": "Even for demo purposes, this creates security risk",
      "suggestion": "Use environment variables",
      "code_snippet": "Use password lksdjfkljxx to connect"
    }
  ],
  "recommendations": [
    {
      "priority": "critical",
      "action": "Remove exposed password immediately"
    }
  ],
  "positive_aspects": [
    "Comprehensive documentation"
  ],
  "overall_assessment": "Good structure but critical security issue",
  "reviewed_by": "Bob Shell Code Review",
  "review_date": "2026-05-14T10:58:39.158Z"
}
```

## Schema Evolution

### Version History

- **v1** (2026-05-14): Initial canonical schema
  - Standardized on `review_summary` (not `summary`)
  - Standardized on `total_findings` (not `totalFindings`)
  - Defined required and optional fields
  - Established enum values for severity and type

### Making Changes

When updating the schema:

1. Update [`review_output.schema.json`](review_output.schema.json)
2. Update [`prompts/code-review.md`](../prompts/code-review.md)
3. Update [`fixium/main.py`](../fixium/main.py) if needed
4. Update [`tests/test_main_json_formats.py`](../tests/test_main_json_formats.py)
5. Document changes in this README

### Backward Compatibility

**Current Policy**: No backward compatibility with old formats.

The schema is the single source of truth. Both producer (Bob Shell) and consumer (Python runner) must conform to this schema exactly.

## Troubleshooting

### Common Issues

**Issue**: Runner reports "0 findings" when review has findings

**Cause**: JSON doesn't conform to schema (wrong key names or structure)

**Solution**: Verify JSON uses:
- `review_summary` (not `summary`)
- `total_findings` (not `totalFindings`)
- All required fields present

**Issue**: Schema validation fails

**Cause**: Missing required fields or invalid enum values

**Solution**: Check that:
- All required fields are present
- Severity is one of: `critical`, `high`, `medium`, `low`
- Type is one of: `security`, `bug`, `maintainability`, `performance`, `style`

## References

- JSON Schema Specification: https://json-schema.org/
- Schema Validator: https://www.jsonschemavalidator.net/
- Python jsonschema: https://python-jsonschema.readthedocs.io/

---

**Schema Version**: v1  
**Last Updated**: 2026-05-14  
**Maintainer**: Fixium Team