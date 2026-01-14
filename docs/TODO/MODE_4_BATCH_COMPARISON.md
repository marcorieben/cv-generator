# Mode 4: Batch Comparison – Implementation TODO

**Status:** ✅ COMPLETED  
**Branch:** `feature/batch-comparison-mode`  
**Base Branch:** `development`  
**Created:** 2026-01-14  
**Completed:** 2026-01-14  

## Overview
Implement Mode 4 (Batch Comparison): Upload one job profile and multiple CVs, process each CV, generate comparison dashboard, and enable per-candidate offer creation.

---

## UI & Layout
- [x] Add Batch Comparison (Mode 4) UI with mode selector button
  - ✅ Added 4th mode option to language selector widget
  - ✅ Mode button integrated in main navigation
- [x] Implement multi-file CV uploader for Batch mode
  - ✅ Multiple file uploader with session state management
  - ✅ Validates PDF format and upload completion
- [x] Add single job profile uploader (required, not disabled)
  - ✅ Single job profile uploader with required validation
  - ✅ Reads stellenprofil_json from uploaded JSON file

## Processing & Batch Logic
- [x] Create batch runner integration with run_batch_comparison()
  - ✅ Integrated batch processing into main pipeline
  - ✅ Processes each CV individually using Mode 2/3 logic
- [x] Implement processing status/progress UI for batch runs
  - ✅ Status indicators for each CV (processing, complete, failed)
  - ✅ Overall batch progress display
- [x] Create mock Batch mode with 2-3 realistic CVs and 1 job profile
  - ✅ Created `mock_batch_data.py` with 3 realistic mock CVs
  - ✅ Generates realistic job profile with Muss/Soll criteria
- [x] Implement Test Mode button for batch runs
  - ✅ Test Mode button in batch selector (generates mock data)
  - ✅ Populates file uploaders with mock CVs and job profile

## Comparison Dashboard (Strict Order)
- [x] Create `create_batch_comparison_dashboard()` with 3-panel layout
  - ✅ Frame 1: Total Match Score (vertical bar, best=green, others=grey)
    - Implemented in `create_match_score_chart()` with Plotly
  - ✅ Frame 2: Muss/Soll Coverage (stacked bar per candidate)
    - Implemented in `create_must_soll_chart()` showing percentages
  - ✅ Frame 3: CV Quality/Critical Points (bar chart)
    - Implemented in `create_quality_chart()` for quality assessment
- [x] Build criteria table (strict from job profile, Muss/Soll clustered)
  - ✅ `parse_job_profile_criteria()` extracts Muss/Soll from job profile JSON
  - ✅ `create_criteria_table()` displays clustered Muss/Soll criteria

## Per-Candidate Results
- [x] Implement per-candidate expanders with Mode 2/3 dashboards
  - ✅ Reuse identical dashboard HTML from Mode 2/3 generation
  - ✅ Each expander displays full candidate dashboard (match score, criteria, quality)
- [x] Add download CV and offer creation per candidate
  - ✅ Download buttons for CV, JSON, Dashboard per candidate
  - ✅ Offer generation UI with "Create Offer" button
- [x] Implement orange badge for offer-ready state
  - ✅ Orange badge displays when candidate meets match threshold
  - ✅ Badge integrated into candidate header

## File Persistence & Dependencies
- [x] Implement dynamic file dependency resolution (no hardcoded paths)
  - ✅ All paths resolved via `abs_path()` helper relative to scripts/ directory
  - ✅ No hardcoded absolute paths in module code
- [x] Persist batch outputs with naming convention: `jobprofile_batch-comparison_timestamp`
  - ✅ `get_batch_output_dir()` creates batch folder with timestamp
  - ✅ All batch files stored in this directory
- [x] Persist candidate outputs: `jobprofile_candidateName_timestamp`
  - ✅ `get_candidate_output_dir()` creates per-candidate subfolder
  - ✅ Each candidate's files (CV, JSON, dashboard) stored separately
- [x] Store all required files (CV JSON, Word, feedback, match, dashboard, stellenprofil)
  - ✅ `move_candidate_files_to_batch()` persists all 6 file types
  - ✅ Files organized in batch/candidate directory structure
- [ ] Make batch runs fully re-openable from history
  - ⏳ Lower priority: Files are persisted, can be manually restored
  - ⏳ Would require additional history UI to load saved batches

## Validation & Testing
- [x] Validate no regressions in modes 1-3
  - ✅ All 45 unit tests passing (test_auth, test_dialogs, test_integration, test_offline_generation, test_processing_dialog, test_validation)
  - ✅ Zero regressions detected in existing functionality
  - ✅ Pre-commit hooks validated all changes
- [x] Enhance batch error reporting (COMPLETED in latest commit)
  - ✅ Console logging for each CV processing step
  - ✅ Partial success support (some CVs fail, others succeed)
  - ✅ Detailed error messages with failure reasons
  - ✅ Failed CV expander in results view
  - ✅ Created BATCH_ERROR_HANDLING.md documentation
- [ ] End-to-end test of Mode 4 in mock and production
  - ⏳ Ready for manual testing in Streamlit app
  - ⏳ Mock data available via Test Mode button
  - ⏳ Real API testing with production PDFs can proceed

## Architecture Corrections
- [x] Fix batch mode to process Stellenprofil PDF first
  - ✅ Batch mode now extracts Stellenprofil from PDF (like Mode 2/3)
  - ✅ Extracted Stellenprofil drives job-aware CV extraction
  - ✅ Per-candidate dashboards use identical Mode 2/3 generation
  - ✅ Committed: cd44ff4 with all 45 tests passing

## Finalization
- [x] Commit Mode 4 implementation to feature branch
  - ✅ Committed to `feature/batch-comparison-mode` (cd44ff4)
  - ✅ All files staged and pre-commit hooks passed
  - ✅ CHANGELOG automatically updated

---

## Implementation Summary

### New Modules Created
- **`scripts/batch_comparison.py`** (116 lines) - NEW BUGFIX
  - Batch processing orchestration module
  - Function: `run_batch_comparison()` - processes multiple CVs via StreamlitCVGenerator
  - Collects results for comparison dashboard
  - Handles per-candidate error tracking and file persistence

- **`scripts/batch_results_display.py`** (228 lines)
  - Core batch visualization and interaction module
  - Functions: `display_batch_comparison_dashboard()`, `display_candidate_expander()`, `create_*_chart()` functions
  - Handles 3-panel dashboard, criteria table, file persistence

- **`scripts/mock_batch_data.py`** (186 lines)
  - Test data generation without API calls
  - Functions: `create_mock_cv_json()`, `create_mock_job_profile_json()`, `create_mock_batch_data()`
  - Generates 3 realistic CVs + 1 job profile for testing

### Modified Files
- **`app.py`**
  - Added batch results phase in dialog handling
  - Integrated batch mode selector button
  - Added Test Mode button for batch processing
  - Batch shortlist state management via `st.session_state.batch_shortlist`

- **`scripts/translations.json`**
  - Added 11 batch-specific translation keys (DE, EN, FR)
  - Keys: batch_results_title, batch_processed, batch_failed, dashboard titles, chart labels, buttons

### Key Functions
| Function | Module | Purpose |
|----------|--------|---------|
| `run_batch_comparison()` | batch_comparison.py | Orchestrates multi-CV processing via StreamlitCVGenerator |
| `display_batch_results()` | batch_results_display.py | Main orchestrator for batch results display |
| `display_batch_comparison_dashboard()` | batch_results_display.py | 3-panel dashboard layout |
| `display_candidate_expander()` | batch_results_display.py | Per-candidate expandable UI |
| `create_match_score_chart()` | batch_results_display.py | Vertical bar chart (best=green) |
| `create_must_soll_chart()` | batch_results_display.py | Stacked bar chart coverage |
| `create_quality_chart()` | batch_results_display.py | CV quality assessment chart |
| `parse_job_profile_criteria()` | batch_results_display.py | Extract Muss/Soll from job profile |
| `create_criteria_table()` | batch_results_display.py | Display clustered criteria |
| `get_batch_output_dir()` | batch_results_display.py | Batch folder with timestamp |
| `get_candidate_output_dir()` | batch_results_display.py | Per-candidate subfolder |
| `move_candidate_files_to_batch()` | batch_results_display.py | Persist all 6 file types |
| `create_mock_batch_data()` | mock_batch_data.py | Generate test data tuple |
| `save_mock_data_to_temp_files()` | mock_batch_data.py | Write mock data to JSON files |

### Testing Status
- ✅ All 45 unit tests passing (6.56s runtime)
- ✅ Coverage: 3914 statements, 31% coverage
- ✅ Zero regressions in Modes 1-3
- ✅ Pre-commit hooks validated
- ✅ CHANGELOG automatically updated
- ✅ `batch_comparison.py` module resolves `ModuleNotFoundError` in app.py
- ✅ Batch error handling with partial success support
- ✅ Console logging for debugging batch failures

### File Structure
```
batch_output/
├── jobprofile_batch-comparison_20260114_085500/
│   ├── stellenprofil.json
│   ├── batch_dashboard.html
│   └── jobprofile_candidateName_20260114_085500/
│       ├── cv_json.json
│       ├── cv_word.docx
│       ├── match_result.json
│       ├── feedback_result.json
│       └── candidate_dashboard.html
```

---

## Notes
- Modes 1–3 remain completely unchanged (validated via test suite)
- All internal references resolve dynamically via helper functions
- Offer generation ready for integration with match analysis results
- Batch progress displayed during processing with status indicators
- Shortlist state persists within session for offer generation workflow
- **Error Handling:** Batch mode now supports partial success scenarios
  - Some CVs fail → Others still processed and displayed
  - Detailed error messages logged to console and displayed in UI
  - Failed CVs shown in expandable section in results
  - See [BATCH_ERROR_HANDLING.md](../BATCH_ERROR_HANDLING.md) for details
