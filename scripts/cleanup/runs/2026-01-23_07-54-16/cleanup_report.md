# Cleanup Report

**Run ID:** `2026-01-23_07-54-16`
**Mode:** ANALYZE
**Timestamp:** 2026-01-23T07:54:16.930194
**Total Files Analyzed:** 518

## Summary

| Decision | Count |
|----------|-------|
| DELETE_SAFE | 0 |
| KEEP_REQUIRED | 104 |
| REVIEW_REQUIRED | 414 |

## ⚠️  REVIEW_REQUIRED Files

**Count:** 414

Files that need human review before any action:

| File | Category | Confidence | Risk |
|------|----------|------------|------|
| `app.py.backup` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `run_1_pipeline.bat` | PROMPT | 60% | Uncertain how this PROMPT file is used... |
| `run_2_cv_only.bat` | PROMPT | 60% | Uncertain how this PROMPT file is used... |
| `run_app.bat` | PROMPT | 60% | Uncertain how this PROMPT file is used... |
| `run_streamlit_app.bat` | PROMPT | 60% | Uncertain how this PROMPT file is used... |
| `test_output.txt` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `.devcontainer/devcontainer.json` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `.streamlit/config.toml` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `.vscode/tasks.json` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| `01_Anfoderung/.$cv_generator_diagram.drawio.bkp` | UNKNOWN | 50% | Cannot determine file purpose or dependencies... |
| ... | | | 404 more files |

### Detailed Review Items

#### `app.py.backup`

- **Category:** UNKNOWN
- **Size:** 48.9 KB
- **Confidence:** 50%
- **Risk:** Cannot determine file purpose or dependencies. Manual inspection needed to verify file is safe to delete.
- **Action:** Review file manually. Check if it's imported anywhere. If purpose unclear, archive rather than delete.

#### `run_1_pipeline.bat`

- **Category:** PROMPT
- **Size:** 0.3 KB
- **Confidence:** 60%
- **Risk:** Uncertain how this PROMPT file is used. Manual inspection recommended before deletion.
- **Action:** Search codebase for file references. If no references found and file is not critical to application startup, can archive. If uncertain, keep the file.

#### `run_2_cv_only.bat`

- **Category:** PROMPT
- **Size:** 0.1 KB
- **Confidence:** 60%
- **Risk:** Uncertain how this PROMPT file is used. Manual inspection recommended before deletion.
- **Action:** Search codebase for file references. If no references found and file is not critical to application startup, can archive. If uncertain, keep the file.

#### `run_app.bat`

- **Category:** PROMPT
- **Size:** 0.1 KB
- **Confidence:** 60%
- **Risk:** Uncertain how this PROMPT file is used. Manual inspection recommended before deletion.
- **Action:** Search codebase for file references. If no references found and file is not critical to application startup, can archive. If uncertain, keep the file.

#### `run_streamlit_app.bat`

- **Category:** PROMPT
- **Size:** 0.1 KB
- **Confidence:** 60%
- **Risk:** Uncertain how this PROMPT file is used. Manual inspection recommended before deletion.
- **Action:** Search codebase for file references. If no references found and file is not critical to application startup, can archive. If uncertain, keep the file.

## 🔒 KEEP_REQUIRED Files

**Count:** 104

These files must be kept (source code, config, protected paths).

## Notes

✅ **Analyze Mode:** No files were deleted or modified.

To apply cleanup (DELETE_SAFE files will be deleted):
```bash
python -m scripts.cleanup apply
```
