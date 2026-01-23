# Cleanup Report

**Run ID:** `2026-01-23_07-53-48`
**Mode:** ANALYZE
**Timestamp:** 2026-01-23T07:53:48.401571
**Total Files Analyzed:** 516

## Summary

| Decision | Count |
|----------|-------|
| DELETE_SAFE | 0 |
| KEEP_REQUIRED | 97 |
| REVIEW_REQUIRED | 419 |

## ⚠️  REVIEW_REQUIRED Files

**Count:** 419

Files that need human review before any action:

| File | Category | Confidence | Risk |
|------|----------|------------|------|
| `.coverage` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `.env` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `.env.example` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `.gitignore` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `app.py.backup` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `requirements-dev.txt` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `run_1_pipeline.bat` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `run_2_cv_only.bat` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `run_app.bat` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `run_streamlit_app.bat` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| ... | | | 409 more files |

### Detailed Review Items

#### `.coverage`

- **Category:** UNKNOWN
- **Size:** 52.0 KB
- **Confidence:** 50%
- **Risk:** Cannot determine file purpose or dependencies. Manual inspection needed to verify file is safe to delete.
- **Action:** Review file manually. Check if it's imported anywhere. If purpose unclear, archive rather than delete.

#### `.env`

- **Category:** UNKNOWN
- **Size:** 0.2 KB
- **Confidence:** 50%
- **Risk:** Cannot determine file purpose or dependencies. Manual inspection needed to verify file is safe to delete.
- **Action:** Review file manually. Check if it's imported anywhere. If purpose unclear, archive rather than delete.

#### `.env.example`

- **Category:** UNKNOWN
- **Size:** 0.1 KB
- **Confidence:** 50%
- **Risk:** Cannot determine file purpose or dependencies. Manual inspection needed to verify file is safe to delete.
- **Action:** Review file manually. Check if it's imported anywhere. If purpose unclear, archive rather than delete.

#### `.gitignore`

- **Category:** UNKNOWN
- **Size:** 0.9 KB
- **Confidence:** 50%
- **Risk:** Cannot determine file purpose or dependencies. Manual inspection needed to verify file is safe to delete.
- **Action:** Review file manually. Check if it's imported anywhere. If purpose unclear, archive rather than delete.

#### `app.py.backup`

- **Category:** UNKNOWN
- **Size:** 48.9 KB
- **Confidence:** 50%
- **Risk:** Cannot determine file purpose or dependencies. Manual inspection needed to verify file is safe to delete.
- **Action:** Review file manually. Check if it's imported anywhere. If purpose unclear, archive rather than delete.

## 🔒 KEEP_REQUIRED Files

**Count:** 97

These files must be kept (source code, config, protected paths).

## Notes

✅ **Analyze Mode:** No files were deleted or modified.

To apply cleanup (DELETE_SAFE files will be deleted):
```bash
python -m scripts.cleanup apply
```
