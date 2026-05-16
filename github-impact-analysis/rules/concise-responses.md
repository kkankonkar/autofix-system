# Concise Response Rule

## Rule: Provide Summaries Only When Requested

### Purpose
Minimize token usage by keeping responses focused and concise unless the user explicitly requests detailed summaries or explanations.

### Default Response Behavior

**DO:**
- ✅ Confirm action taken briefly
- ✅ Report only essential information
- ✅ State next step if needed
- ✅ Ask clarifying questions when necessary

**DON'T:**
- ❌ Provide lengthy summaries unprompted
- ❌ Repeat information already known
- ❌ Include extensive statistics unless requested
- ❌ Add unnecessary context or background

### Response Examples

#### ✅ Good (Concise)
```
Created .bob/rules/todo-management.md with TODO notification requirements.
```

#### ❌ Bad (Verbose)
```
I have successfully created a comprehensive TODO management rule document 
in the .bob/rules/ directory. This file contains detailed guidelines about 
when and how to notify users about TODOs, including templates, formats, 
acceptable locations, and verification procedures. The document is 72 lines 
long and covers all aspects of TODO management...
```

### When to Provide Detailed Summaries

Provide comprehensive summaries ONLY when user explicitly requests:
- "Give me a summary"
- "What did we accomplish?"
- "Show me the statistics"
- "Provide a detailed report"
- "What's the status?"

### Summary Request Keywords

Trigger detailed responses when user says:
- `summary`
- `report`
- `status`
- `statistics`
- `overview`
- `recap`
- `what did we do`
- `show me everything`

### Token-Saving Techniques

1. **Confirm, don't explain** - "Done" vs "I have completed the task by..."
2. **List, don't elaborate** - Bullet points vs paragraphs
3. **Reference, don't repeat** - "See file X" vs copying content
4. **Ask, don't assume** - Short question vs long explanation

### Completion Messages

#### Standard Completion (Concise)
```
✅ Task complete. [Brief outcome]
```

#### Detailed Completion (Only when requested)
```
✅ Task Complete - Detailed Summary

[Comprehensive breakdown with statistics, 
file counts, changes made, etc.]
```

### Exception Cases

Always provide details for:
- ⚠️ Errors or failures (need context to fix)
- ⚠️ TODOs added (per todo-management.md rule)
- ⚠️ Breaking changes (user needs to know impact)
- ⚠️ Security issues (critical information)

### Rationale

- **Saves tokens** - Reduces API costs
- **Faster responses** - Less text to generate
- **Better UX** - User gets what they need, when they need it
- **Clearer communication** - Focus on essentials

---

**Rule Status**: Active  
**Last Updated**: 2026-05-07  
**Enforcement**: Automatic via Bob AI Assistant  
**Priority**: High (token cost optimization)