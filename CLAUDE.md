## 🔍 Documentation

@./docs/architecture/coding-standards.md
@./docs/architecture/error-handling-strategy.md
@./docs/front-end-spec.md

## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## 📚 Documentation Consistency Rules

**CRITICAL**: When modifying stories, epics, or architecture documents, ALWAYS:

### 1. Cross-Reference Check
- **Story ↔ Epic Alignment**: Verify story changes match epic acceptance criteria
- **Architecture Consistency**: Ensure technical decisions align with architecture docs
- **Related Documents**: Check dual-storage-architecture.md, data-models.md, components.md for conflicts

### 2. Update All Related Files
- **Epic files**: Update acceptance criteria if story changes affect requirements
- **Architecture docs**: Update if new patterns or technical decisions are made
- **Test strategies**: Update test organization when changing implementation approach

### 3. Changelog Maintenance
- **ALWAYS update story changelogs** when making significant changes
- **Include version number** (increment by 0.1 for minor changes, 1.0 for major architectural changes)
- **Be specific** about what changed (e.g., "PersonalContext.is_complete as single source of truth")
- **Date all entries** for tracking

### 4. Consistency Check Commands
When updating stories, run these checks:
```bash
# Check for completion logic consistency
grep -r "profile_complete\|is_complete" docs/
# Check for endpoint consistency
grep -r "/conversation/onboarding\|PersonalContext" docs/
# Check for architectural references
grep -r "single source of truth\|completion state" docs/
```

### 5. Architectural Decision Recording
- **Document WHY**: Not just what changed, but architectural rationale
- **Reference source**: Always cite architecture docs when making technical decisions
- **Update patterns**: If creating new patterns, update architecture docs first
