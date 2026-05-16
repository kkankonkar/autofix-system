# Verify Before Assuming Rule

## Rule: Ask Questions About File Locations Instead of Assuming

### Purpose
Prevent incorrect assumptions about file locations, URLs, or resource availability by asking the user first.

### When This Rule Applies

**Always ask before assuming:**
- 📁 File locations and paths
- 🌐 Download URLs or API endpoints
- 📦 Package/binary availability
- 🔗 External resource locations
- ⚙️ Configuration values
- 🗂️ Directory structures for new files

### What to Do Instead

1. **Check workspace first** - Use `list_files` or `search_files` to verify
2. **Ask if uncertain** - Use `ask_followup_question` with suggestions
3. **Provide options** - Give user multiple choices when possible
4. **Verify existence** - Confirm files/resources exist before using them

### Examples

#### ❌ Bad (Assuming)
```dockerfile
# Assuming GitHub releases URL without checking
RUN curl -fsSL https://github.com/IBM/bob/releases/download/v1.105.1/IBM-Bob.deb
```

#### ✅ Good (Verifying)
```
First, let me check if the Bob .deb file exists locally:
[Uses list_files to check workspace]

Found: IBM-Bob-linux-amd64-1.109.5+bob1.0.2.deb

Using local file in Dockerfile.
```

#### ✅ Good (Asking)
```
I need the Bob CLI .deb file for the Dockerfile. Should I:
1. Use a local .deb file (if you have one)
2. Download from a specific URL (please provide)
3. Install from a package repository
```

### Common Scenarios

**File Locations:**
- ✅ Check workspace with `list_files` first
- ✅ Ask user if file not found
- ❌ Don't assume standard locations like `/usr/local/bin`

**URLs and Endpoints:**
- ✅ Ask for actual URL/endpoint
- ✅ Provide example format
- ❌ Don't assume GitHub releases or public URLs

**Configuration Values:**
- ✅ Check existing config files first
- ✅ Ask user for missing values
- ❌ Don't use placeholder values without notifying

**Binary/Package Names:**
- ✅ Ask for exact package name and version
- ✅ Verify availability before using
- ❌ Don't assume package names or versions

### Question Template

```
I need [resource] for [purpose]. I can see [what I found/didn't find].

Options:
1. [Option 1 with details]
2. [Option 2 with details]
3. [Option 3 with details]

Which would you prefer?
```

### Verification Steps

Before using any external resource:
1. **Search workspace** - `list_files` or `search_files`
2. **Check documentation** - Read README, config files
3. **Ask user** - If still uncertain
4. **Confirm** - Verify the resource works

### Benefits

- ✅ Prevents broken builds/deployments
- ✅ Saves time (no rework from wrong assumptions)
- ✅ Better user experience
- ✅ More accurate implementations
- ✅ Builds trust through verification

### Related Rules

- See `todo-management.md` - For handling incomplete information
- See `concise-responses.md` - For keeping questions focused

---

**Rule Status**: Active  
**Last Updated**: 2026-05-07  
**Enforcement**: Automatic via Bob AI Assistant  
**Priority**: High (prevents implementation errors)