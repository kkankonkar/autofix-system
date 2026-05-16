# TODO Management Rule

## Rule: Always Notify User When Adding TODOs

### When This Rule Applies
Any time a TODO, FIXME, XXX, HACK, or NOTE comment is added to code files.

### Required Actions

1. **Explicitly inform the user** that a TODO has been added
2. **Explain why** it was added
3. **Provide context** on what needs to be completed
4. **Ask for resolution** - should it be resolved now or documented for later?

### Notification Template

```
⚠️ TODO ADDED: I've added a TODO comment in [filename] at line [X] because [reason].

The TODO is: "[TODO text]"

Would you like me to:
1. Resolve it now (if you can provide the information)
2. Document it in a tracking file
3. Leave it as-is for later
```

### TODO Comment Format

When TODOs must be added, use this format:

```
# TODO(date): Description of what needs to be done
# Context: Why this is needed
# Blocker: What information/resource is needed to complete this
```

**Example:**
```python
# TODO(2026-05-07): Replace with actual API endpoint
# Context: Waiting for production API URL
# Blocker: Need PROD_API_URL from DevOps team
API_ENDPOINT = "https://placeholder.example.com"
```

### Acceptable TODO Locations

TODOs are acceptable in:
- ✅ Planning documents (*.md files in planning phase)
- ✅ Example code (clearly marked as examples)
- ✅ Documentation (when documenting future features)

### Prohibited TODO Locations

TODOs should be **avoided** in:
- ❌ Production code
- ❌ Configuration files
- ❌ Dockerfiles
- ❌ CI/CD workflows
- ❌ Test files

### Verification Before Completion

Before marking any task as "Complete":
1. Run `search_files` with regex `TODO|FIXME|XXX|HACK`
2. Verify no TODOs exist in production code
3. Document any necessary TODOs in a separate tracking file

### Rationale

- Prevents forgotten TODOs from accumulating
- Ensures user awareness of incomplete work
- Allows immediate resolution when possible
- Maintains code quality standards
- Creates accountability for unfinished work

---

**Rule Status**: Active  
**Last Updated**: 2026-05-07  
**Enforcement**: Automatic via Bob AI Assistant