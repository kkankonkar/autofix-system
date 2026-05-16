# Ask for File Locations Rule

## Rule: Always Ask for File Locations When Uncertain

### Purpose
Prevent wasted operations and incorrect assumptions by asking the user for file locations when they are not in the current workspace or when uncertain about their location.

### When This Rule Applies

**Always ask before assuming file locations for:**
- 🗂️ Files outside the current workspace directory
- 📁 Configuration files in parent directories
- 🔧 Workflow files (GitHub Actions, CI/CD configs)
- 🏗️ Project-specific files in related repositories
- 📦 Dependency files or external resources
- 🔗 Files referenced but not visible in workspace

### What to Do Instead

1. **Check current workspace first** - Use `list_files` to verify
2. **Ask user for location** - Use `ask_followup_question` with clear context
3. **Provide context** - Explain why you need the file
4. **Suggest likely locations** - Give user options to choose from

### Examples

#### ❌ Bad (Assuming)
```
Let me check the GitHub Actions workflow...
<list_files>
<path>.github/workflows</path>
</list_files>
```

#### ✅ Good (Asking)
```
I need to update the GitHub Actions workflow file to add the required permissions 
for git push. Where is the workflow file located?

Options:
1. In this repository: .github/workflows/
2. In a parent directory: ~/project/.github/workflows/
3. In a different repository (please provide path)
4. Not created yet (I can help create it)
```

### Common Scenarios

**GitHub Actions Workflows:**
- ✅ Ask: "Where is your GitHub Actions workflow file located?"
- ❌ Don't assume: `.github/workflows/` in current workspace

**Configuration Files:**
- ✅ Ask: "Where is your config file? (e.g., config/, ../config/, etc.)"
- ❌ Don't assume: `config/` in current directory

**Related Repositories:**
- ✅ Ask: "Is this file in the current repo or a related one?"
- ❌ Don't assume: Same repository

**Parent Directories:**
- ✅ Ask: "Is this file in a parent directory? If so, what's the path?"
- ❌ Don't assume: Current workspace only

### Question Template

```
I need to [action] the [file type]. Where is it located?

Options:
1. [Most likely location based on context]
2. [Alternative common location]
3. [Parent directory option]
4. [Not created yet / doesn't exist]

Please provide the full path if it's in a different location.
```

### Benefits

- ✅ Prevents failed operations on non-existent files
- ✅ Saves time by getting correct path immediately
- ✅ Shows respect for user's project structure
- ✅ Avoids making incorrect assumptions
- ✅ Reduces back-and-forth corrections

### Related Rules

- See [`verify-before-assuming.md`](verify-before-assuming.md) - For general verification practices
- See [`concise-responses.md`](concise-responses.md) - For keeping questions focused

---

**Rule Status**: Active  
**Last Updated**: 2026-05-15  
**Enforcement**: Automatic via Bob AI Assistant  
**Priority**: High (prevents wasted operations)