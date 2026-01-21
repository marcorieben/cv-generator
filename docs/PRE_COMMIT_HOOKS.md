# Git Pre-Commit Hooks - Structured Documentation & Cleanup
## Setup Guide (Januar 2026)

---

## 🎯 Overview

Two integrated pre-commit hooks for maintaining code quality and documentation:

1. **Pre-Commit Hook** (`pre_commit_hook.py`)
   - Validates commit messages
   - Extracts structured metadata (icon, feature name, details)
   - Scans for unused files
   - Generates in-app documentation JSON

2. **Cleanup Script** (`cleanup_unused.py`)
   - Interactive file archiving
   - Identifies files older than 180 days
   - Manages `archive/unused/` directory

---

## 📋 Installation

### Option 1: Automatic Setup
```bash
cd cv_generator
bash scripts/install_hooks.sh
```

### Option 2: Manual Setup
```bash
# Create hook file
mkdir -p .git/hooks

# Copy pre-commit hook
cp scripts/pre_commit_hook.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 📊 Commit Metadata Structure

The hook extracts and stores **structured metadata** for each commit:

```json
{
  "icon": "feature",           // feature, bug, docs, refactor, test, etc.
  "feature_name": "Lean MVP",
  "feature_details": "Heroku deployment guide",
  "commit_message": "docs: Add Lean MVP architecture...",
  "timestamp": "2026-01-21T10:48:05.123456",
  "commit_hash": "9ab37f8",
  "author": "Marco Rieben"
}
```

**Saved to:** `scripts/commit_metadata.json` (last 100 commits)

---

## 💡 How to Use

### Commit with Metadata

Write commits following this format for automatic extraction:

```bash
git commit -m "✨(feature): Feature Name - Detailed description here"
```

**Icon Examples:**
- `✨` (feature)
- `🐛` (bug)
- `📝` (docs)
- `♻️` (refactor)
- `🧪` (test)
- `🔧` (chore)
- `🚀` (feature)
- `⚡` (performance)
- `🔒` (security)

**Examples:**

```bash
# New feature
git commit -m "✨(feature): Lean MVP Architecture - Heroku deployment guide"

# Bug fix
git commit -m "🐛(bug): Fix timeout issue - Add connection pooling"

# Documentation
git commit -m "📝(docs): Update API documentation - Add auth examples"

# Refactoring
git commit -m "♻️(refactor): Simplify batch processing - Reduce complexity"
```

### What the Hook Does

When you commit:

1. **Validates message** - Checks format, length, structure
2. **Extracts metadata** - Parses icon, feature name, details
3. **Scans for unused files** - Identifies files > 180 days old
4. **Generates documentation** - Saves to `scripts/commit_metadata.json`

**Output example:**
```
============================================================
🔍 PRE-COMMIT HOOK: Cleanup & Documentation
============================================================

📝 Reading commit message...
✅ Message: docs: Add Lean MVP architecture...

📋 Validating commit message...
  ✅ Commit message format OK

📊 Extracting metadata...
  📌 Type: docs
  📝 Feature: Add Lean MVP architecture
  ✍️  Author: Marco Rieben
  🕐 Timestamp: 2026-01-21T10:48:05.123456

📦 Scanning for unused files...
  ✅ No unused files found

📚 Generating in-app documentation...
  ✅ Documentation saved to scripts/commit_metadata.json

============================================================
✅ PRE-COMMIT CHECKS PASSED
============================================================
```

---

## 🧹 Cleanup: Archive Unused Files

### Interactive Mode
```bash
python scripts/cleanup_unused.py
```

Walks through each old file and asks:
```
📄 old_file.py
   Last modified: 200 days ago
   Archive? (y/n/all/skip):
```

### Non-Interactive Mode (Archive All)
```bash
python scripts/cleanup_unused.py --all
```

Files are moved to `archive/unused/` with original directory structure preserved.

---

## 📚 In-App Documentation Usage

### Access Commit History in App

```python
# In Streamlit app or other modules
import json

def load_commit_metadata():
    """Load structured commit metadata"""
    try:
        with open('scripts/commit_metadata.json', 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return None

# Display in UI
metadata = load_commit_metadata()
if metadata:
    st.write("📋 Recent Changes:")
    for change in metadata['changes'][:10]:
        icon = change['icon'] or '📝'
        st.write(f"  {icon} {change['feature_name']} - {change['timestamp']}")
```

### Display by Type

```python
metadata = load_commit_metadata()
index = metadata['index_by_type']

# Show all features
for feature in index.get('feature', []):
    st.write(f"✨ {feature['name']}")

# Show all bug fixes
for fix in index.get('bug', []):
    st.write(f"🐛 {fix['name']}")
```

---

## ⚙️ Configuration

Edit `scripts/pre_commit_hook.py`:

```python
# Unused file threshold (days)
UNUSED_THRESHOLD_DAYS = 180

# Directories to ignore
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', 'htmlcov', '.venv'}

# File extensions to ignore
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.o'}

# Archive location
ARCHIVE_DIR = 'archive/unused'
```

---

## 🔒 Disabling the Hook (Emergency)

If you need to bypass the hook for a commit:

```bash
# Skip pre-commit hook
git commit --no-verify -m "Emergency fix..."
```

To temporarily disable the hook:
```bash
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
# Later: mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

---

## 📊 Metadata JSON Structure

**File:** `scripts/commit_metadata.json`

```json
{
  "generated_at": "2026-01-21T10:48:05.123456",
  "total_changes": 150,
  "changes": [
    {
      "icon": "feature",
      "feature_name": "Lean MVP Architecture",
      "feature_details": "Heroku deployment guide",
      "commit_message": "docs: Add Lean MVP architecture documentation for meeting",
      "timestamp": "2026-01-21T10:48:05.123456",
      "commit_hash": "9ab37f8",
      "author": "Marco Rieben"
    },
    ...
  ],
  "index_by_type": {
    "feature": [
      {
        "name": "Lean MVP Architecture",
        "timestamp": "2026-01-21T10:48:05.123456",
        "hash": "9ab37f8"
      },
      ...
    ],
    "bug": [...],
    "docs": [...]
  }
}
```

---

## 🎯 Best Practices

### Commit Message Format
```
<icon>(<type>): <feature-name> - <details>

<body> (optional)

<footer> (optional)
```

### Examples

✅ **Good:**
```bash
git commit -m "✨(feature): Lean MVP Architecture - Heroku deployment guide with cost analysis"
```

✅ **Good:**
```bash
git commit -m "🐛(bug): Fix batch processing timeout - Add connection pooling and retry logic"
```

❌ **Avoid:**
```bash
git commit -m "fix stuff"
```

---

## 🔍 Troubleshooting

### Hook not running?
```bash
# Check if executable
ls -la .git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit

# Test manually
python scripts/pre_commit_hook.py
```

### Permission denied?
```bash
chmod +x scripts/pre_commit_hook.py
chmod +x scripts/cleanup_unused.py
chmod +x scripts/install_hooks.sh
```

### Python version issue?
```bash
# Ensure Python 3.7+ is available
python --version
python3 --version
```

---

## 📝 Related Files

- `scripts/pre_commit_hook.py` - Main hook logic
- `scripts/cleanup_unused.py` - Cleanup utility
- `scripts/install_hooks.sh` - Hook installer
- `scripts/commit_metadata.json` - Generated metadata (JSON)
- `archive/unused/` - Archived old files
- `docs/DOCUMENTATION_MAINTENANCE.md` - Overall documentation guide

---

## 💡 Future Enhancements

Planned improvements:

- [ ] Web UI for viewing commit history
- [ ] Automatic changelog generation from metadata
- [ ] Integration with GitHub releases
- [ ] Commit statistics dashboard
- [ ] Automated backup of archived files
- [ ] Email digest of recent changes

---

**Last Updated:** January 21, 2026  
**Status:** ✅ Active  
**Maintainer:** Development Team
