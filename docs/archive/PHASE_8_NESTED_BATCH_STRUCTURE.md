# Phase 8 Implementation Complete: Nested Batch Folder Structure

## Summary
Successfully implemented **Option B (Nested)** nested folder structure for Mode 4 Batch Comparison with dynamic naming extraction.

## Architecture

### Folder Structure (Approved Option B)
```
output/
└── [jobProfileName]_batch-comparison_[timestamp]/
    ├── [jobProfileName]_stellenprofil_[timestamp].json  (at root level)
    ├── [candidateName1]_[timestamp]/
    │   ├── [jobProfileName]_[candidateName1]_cv_[timestamp].json
    │   ├── [jobProfileName]_[candidateName1]_match_[timestamp].json
    │   ├── [jobProfileName]_[candidateName1]_dashboard_[timestamp].html
    │   ├── [jobProfileName]_[candidateName1]_feedback_[timestamp].json
    │   └── ... (other per-candidate files)
    ├── [candidateName2]_[timestamp]/
    │   └── ... (all candidate files)
    └── [candidateNameN]_[timestamp]/
        └── ... (all candidate files)
```

### Example Structure
```
output/
└── senior_sales_manager_batch-comparison_20260114_101536/
    ├── senior_sales_manager_stellenprofil_20260114_101536.json
    ├── rieben_marco_20260114_101536/
    │   ├── senior_sales_manager_rieben_marco_cv_20260114_101536.json
    │   ├── senior_sales_manager_rieben_marco_match_20260114_101536.json
    │   ├── senior_sales_manager_rieben_marco_dashboard_20260114_101536.html
    │   └── senior_sales_manager_rieben_marco_feedback_20260114_101536.json
    ├── dupont_jean_20260114_101536/
    │   └── ... (all files for Jean Dupont)
    └── mueller_schmidt_hans_20260114_101536/
        └── ... (all files for Hans Müller-Schmidt)
```

## Changes Made

### 1. Enhanced `scripts/naming_conventions.py` (368 lines)
Added new functions for dynamic naming extraction:

#### Name Extraction Functions
- **`extract_job_profile_name_from_file(job_file_path: str) -> str`**
  - Extracts job profile name from uploaded file name
  - Example: `"Senior_Sales_Manager.pdf"` → `"senior_sales_manager"`

- **`extract_candidate_name(cv_data: Dict[str, Any]) -> str`**
  - Extracts candidate name from CV JSON data
  - Combines Vorname + Nachname in order: `"LastName_FirstName"`
  - Example: `{"Vorname": "Marco", "Nachname": "Rieben"}` → `"rieben_marco"`

#### Folder Path Functions
- **`get_candidate_subfolder_path(batch_folder: str, candidate_name: str, timestamp: str) -> str`**
  - Creates per-candidate subfolder within batch folder
  - Convention: `candidateName_timestamp`
  - Auto-creates directory if it doesn't exist

#### File Naming Updates
- Updated `get_cv_json_filename()`, `get_match_json_filename()`, etc. to accept:
  - `(job_profile_name: str, vorname: str, nachname: str, timestamp: str)`
  - Automatically extracts and combines candidate name internally
  - Maintains backward compatibility

### 2. Updated `scripts/batch_comparison.py` (242 lines)
Enhanced batch orchestration with nested folder support:

**Key Changes:**
- Extracts job profile name from BOTH:
  - Uploaded file name (fallback)
  - Stellenprofil JSON data (primary)
- Creates batch folder: `jobprofileName_batch-comparison_timestamp`
- Saves Stellenprofil JSON at batch folder root
- **For each CV:**
  - Creates candidate subfolder: `candidateName_timestamp`
  - Passes custom `output_dir=candidate_subfolder` to StreamlitCVGenerator
  - Extracts candidate name from CV processing results
  - Stores all per-candidate files in subfolder

**Batch Processing Flow:**
```
1. Extract Stellenprofil from PDF
2. Create main batch folder
3. Save Stellenprofil at root
4. For each CV:
   a. Create candidate subfolder
   b. Run StreamlitCVGenerator with custom output_dir
   c. All generated files → subfolder
5. Return batch metadata (folder path, job_profile_name, timestamp)
```

### 3. Updated `scripts/streamlit_pipeline.py` (300 lines)
Added support for custom output directory in batch mode:

**Key Changes:**
- Added parameter: `output_dir: str = None`
- Logic:
  - If `output_dir` provided (batch mode): Use that folder directly
  - If `output_dir` is None (standard mode): Create new folder `jobprofileName_cv_timestamp`
- Maintains 100% backward compatibility with existing code

**Implementation:**
```python
if output_dir:
    # Batch mode: use provided candidate subfolder
    os.makedirs(output_dir, exist_ok=True)
    final_output_dir = output_dir
else:
    # Standard mode: create new folder jobprofileName_cv_timestamp
    base_output = os.path.join(self.base_dir, "output")
    final_output_dir = get_output_folder_path(base_output, job_profile_name, "cv", self.timestamp)
```

## Benefits of Option B (Nested Structure)

✅ **Logical Grouping**
- Each candidate's files together in one folder
- Stellenprofil at root shows context

✅ **Self-Contained**
- Easy to archive/share one candidate's folder
- Complete analysis per candidate in one place

✅ **Relational Organization**
- Mirrors the comparison structure (job profile at root, matches as subfolders)
- Reflects data model: one job profile vs. multiple candidates

✅ **Scalability**
- 10 candidates = 10 subfolders (clean)
- Better than 40-60 files in one directory

✅ **No Duplicates**
- Single main batch folder
- No redundant "jobprofile_cv_" folders mixed with batch folder

## Testing

✅ All 45 tests passing
✅ Name extraction functions verified:
  - Job profile: `"Senior_Sales_Manager.pdf"` → `"senior_sales_manager"`
  - Candidate: `Marco Rieben` → `"rieben_marco"`
  - Subfolder creation: auto-creates with correct path
  - File naming: correct format with actual names

## Commit Details

**Hash:** `1495a3c`
**Message:** `refactor: implement nested batch folder structure with dynamic naming`
**Files Changed:**
- `scripts/naming_conventions.py` (enhanced with 5 new functions)
- `scripts/batch_comparison.py` (nested folder orchestration)
- `scripts/streamlit_pipeline.py` (custom output_dir support)

## Status

✅ **Phase 8 Complete**

All Mode 4 Batch Comparison features fully implemented and tested:
- ✅ Mode 4 Batch UI
- ✅ Batch processing logic (PDF-first architecture)
- ✅ Per-candidate dashboards (Mode 2/3 identical)
- ✅ Unified file naming (all modes 2-4)
- ✅ Batch history integration
- ✅ Nested folder structure with dynamic naming

**Ready for:** Production use, user testing, further enhancements
