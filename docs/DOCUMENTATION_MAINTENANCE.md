# Documentation Maintenance Guide

**Version:** Phase 3 (January 2026)  
**Status:** Active Pre-Commit Hook enabled

---

## 📋 Overview

The CV Generator project uses a **pre-commit hook** to ensure documentation stays current with code changes. When you commit code changes, the system will warn you if related documentation wasn't updated.

---

## 🎯 Which Files to Update

### **COMPLETION_SUMMARY.txt**
Update when you:
- ✅ Add new features
- ✅ Fix significant bugs
- ✅ Refactor major components
- ✅ Change UI/UX
- ✅ Update dependencies

**What to document:**
- Brief description of changes
- Files modified
- Impact on users
- New capabilities (if any)

### **docs/ARCHITECTURE.md**
Update when you:
- ✅ Change system architecture
- ✅ Modify data flow
- ✅ Add/remove modules
- ✅ Change design patterns
- ✅ Update folder structure

**What to document:**
- Architecture diagrams (ASCII or describe)
- Component relationships
- Data flow changes
- Module responsibilities

### **docs/TODO.md**
Update when you:
- ✅ Complete tasks/features
- ✅ Identify new improvements needed
- ✅ Finish cleanup/refactoring work
- ✅ Resolve known issues

**What to document:**
- Mark completed items with ✅
- Add new pending tasks with ⏳
- Include effort estimates
- Link to related commits/PRs

---

## 🔄 Pre-Commit Hook Behavior

### ✅ When You Commit

```bash
$ git commit -m "Add new feature"

Running pre-commit checks...
============================================================
🔍 Checking translations.json for duplicate keys...
✅ No duplicates found

🔄 Updating test data artifacts...
✅ Test data updated

🔍 Checking documentation updates...
⚠️  WARNING: Code changes detected but documentation wasn't updated
Please consider updating one of these files:
  • COMPLETION_SUMMARY.txt - For new features/changes
  • docs/ARCHITECTURE.md - For architecture/structure changes
  • docs/TODO.md - For completed tasks/cleanup

🧪 Running tests...
✅ All tests passed

============================================================
✅ All checks passed! Proceeding with commit.
============================================================
```

### ⚠️ Important Notes

- **Documentation warnings are NOT blocking** - You can still commit
- **Tests are blocking** - If tests fail, commit is blocked
- The hook **encourages** but doesn't force documentation updates
- Use `git commit --no-verify` only in emergencies

---

## 💡 Best Practices

### Before Committing

1. **Run tests locally:**
   ```bash
   pytest -v
   ```

2. **Review your changes:**
   ```bash
   git diff
   ```

3. **Ask yourself:** "Does any documentation need updating?"
   - Is this a new feature? → Update COMPLETION_SUMMARY.txt
   - Did I change the architecture? → Update docs/ARCHITECTURE.md
   - Did I complete tasks? → Update docs/TODO.md

### When Committing

1. **Make code changes**
2. **Update relevant documentation**
3. **Stage both files:** `git add <code> <docs>`
4. **Commit together:** `git commit -m "..."`
5. **Follow commit message conventions**

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation update
- `refactor:` - Code restructuring
- `test:` - Test changes
- `chore:` - Maintenance

**Example:**
```bash
git commit -m "feat(batch): add offer generation for multiple CVs

- Integrated generate_angebot_word module
- Each candidate can create individual offers
- Full language support (DE, EN, FR)

Updated COMPLETION_SUMMARY.txt with new feature description"
```

---

## 📊 Documentation Checklist

### For Feature Additions
- [ ] Updated COMPLETION_SUMMARY.txt
- [ ] Updated docs/TODO.md (marked related tasks as done)
- [ ] Updated docs/ARCHITECTURE.md (if architecture changed)
- [ ] Added/updated code comments
- [ ] Updated relevant scripts or module docstrings

### For Bug Fixes
- [ ] Updated COMPLETION_SUMMARY.txt (if significant)
- [ ] Updated docs/TODO.md (marked related tasks)
- [ ] Added test cases to prevent regression
- [ ] Updated code comments explaining the fix

### For Refactoring
- [ ] Updated docs/ARCHITECTURE.md
- [ ] Updated module docstrings
- [ ] Updated COMPLETION_SUMMARY.txt
- [ ] Verified all tests pass
- [ ] Updated docs/TODO.md if scope changed

### For Documentation Changes
- [ ] Updated relevant .md file
- [ ] Checked for consistency with code
- [ ] Verified formatting (Markdown)
- [ ] Updated archive README (if moving files)

---

## 🔧 Disabling the Hook (Emergency Only)

If you **absolutely must** bypass the hook:

```bash
git commit --no-verify -m "Emergency fix - document later"
```

⚠️ **Warning:** Only use this in emergencies! Document the changes afterward.

---

## 📞 Questions?

- Check the **relevant .md file** (ARCHITECTURE.md, TODO.md, etc.)
- Review recent commits to see documentation examples
- Ask the team if unsure what to document

---

**Remember:** Good documentation saves time for everyone! 📚✨
