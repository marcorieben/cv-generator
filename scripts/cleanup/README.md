# Cleanup System

Safe, explainable file cleanup for the CV Generator project.

## Quick Start

### Analyze Mode (Safe - No Changes)
```bash
# From project root
python scripts/cleanup/cleanup.py

# Or as Windows batch
scripts\cleanup\cleanup.bat

# Or as Python module
python -m scripts.cleanup.cleanup
```

### Apply Mode (Destructive - Requires Confirmation)
```bash
python scripts/cleanup/cleanup.py apply
# or
scripts\cleanup\cleanup.bat apply
```

## Files in This Directory

- **`cleanup.py`** - Main entry point (Python script)
- **`cleanup.bat`** - Windows batch launcher
- **`QUICKSTART.md`** - User-friendly quick start guide
- **`__init__.py`** - Module initialization
- **`models.py`** - Data models (enums, dataclasses)
- **`classify.py`** - File classification engine
- **`decisions.py`** - Decision rules engine
- **`executor.py`** - Main orchestration logic
- **`reports.py`** - JSON/Markdown report generation

## Architecture

The cleanup system implements a safe, multi-stage file analysis:

1. **Classification** (`classify.py`)
   - Scans all project files
   - Assigns to 10 categories (SOURCE_CODE, CONFIG, LOG_FILE, etc.)
   - Based on file path and extension patterns

2. **Analysis** (`executor.py`)
   - Analyzes each file individually
   - Applies decision rules
   - Generates per-file analysis object

3. **Decision** (`decisions.py`)
   - DELETE_SAFE (≥99% confidence)
   - KEEP_REQUIRED (source code, config)
   - REVIEW_REQUIRED (uncertain cases)

4. **Reporting** (`reports.py`)
   - JSON report (machine-readable)
   - Markdown report (human-readable)
   - Saved to immutable `/cleanup/runs/<timestamp>/` folder

5. **Optional Execution** (`executor.py`)
   - Apply mode deletes only DELETE_SAFE files
   - Requires user confirmation
   - Logs all deletions

## File Categories (10)

| Category | Safe to Delete? |
|----------|-----------------|
| SOURCE_CODE | ❌ Never |
| CONFIG | ❌ Never |
| PROMPT | ❌ Never |
| INPUT_DATA | ❌ Never |
| INTERMEDIATE_ARTIFACT | ✅ If old |
| GENERATED_OUTPUT | ⚠️ Review needed |
| LOG_FILE | ✅ If old |
| TEMP_FILE | ✅ If old |
| EXPERIMENT | ⚠️ Review needed |
| UNKNOWN | ⚠️ Review needed |

## Decision Rules

### DELETE_SAFE
- Category in [TEMP_FILE, LOG_FILE, INTERMEDIATE_ARTIFACT]
- File age ≥ 14 days
- Not in protected paths
- Confidence ≥ 0.95

### KEEP_REQUIRED
- Category in [SOURCE_CODE, CONFIG]
- In required_artifacts list
- In protected paths

### REVIEW_REQUIRED
- Anything with low confidence
- Unknown categories
- Generated output without regenerator
- Experiment files with unclear usage

## Report Locations

```
scripts/cleanup/runs/
  └─ 2026-01-23_14-30-00/
     ├─ cleanup_report.json
     ├─ cleanup_report.md
     └─ deleted_files.log (apply mode only)
```

## Safety Guarantees

✅ **Analyze mode is 100% safe** - No filesystem changes  
✅ **DELETE_SAFE only has 99%+ confidence** - Minimal risk  
✅ **Confirmation required before deletion** - No surprises  
✅ **Immutable cleanup history** - Full traceability  
✅ **Protected paths** - source, tests, docs are safe  
✅ **Clear explanations** - Why each decision was made  

## Configuration

Edit in `models.py` → `CleanupConfig`:

```python
age_threshold_days = 14              # Minimum age for deletion
confidence_threshold = 0.95          # Minimum confidence
protected_paths = [...]              # Never delete
required_artifacts = [...]           # Always keep
max_deletion_size_mb = 100.0         # Deletion size limit
```

## Examples

### View Reports
```bash
# After running analyze
cat scripts/cleanup/runs/2026-01-23_14-30-00/cleanup_report.md
```

### Find REVIEW_REQUIRED Files
```bash
# Reports include detailed section on uncertain files
# Review risk_assessment and recommended_action
```

### Manual Cleanup
```bash
# 1. Run analyze
python scripts/cleanup/run.py

# 2. Review report in scripts/cleanup/runs/

# 3. If satisfied, apply
python scripts/cleanup/run.py apply
```

## Full Documentation

See also:
- [QUICKSTART.md](QUICKSTART.md) - User guide
- [../../docs/feature_structured_cleanup/REQUIREMENTS.md](../../docs/feature_structured_cleanup/REQUIREMENTS.md) - System requirements
- [../../docs/feature_structured_cleanup/README.md](../../docs/feature_structured_cleanup/README.md) - Implementation overview

## Testing

The cleanup system is designed to be test-safe:
- Always run `analyze` first
- Review reports thoroughly
- Run `apply` only when confident
- Check `deleted_files.log` afterwards
