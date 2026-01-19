# Variable Naming Rules & Conventions

## CRITICAL RULE: Use Only TWO Variables for Job Profile Information

### ✅ ALLOWED Variables

#### 1. **`stellenprofil_data`** - RAW JSON Input
- **Type:** `Dict[str, Any]` (or `None`)
- **Source:** Directly from PDF extraction via LLM
- **Content:** Complete Stellenprofil data as returned by `pdf_to_json()`
- **Lifecycle:** Input → Storage → Context passing
- **Examples:**
  ```python
  {
    "stellenprofilId": "gdjob_12881",
    "Stelle": {"Position": "Senior Business Analyst"},
    "Unternehmen": {"Name": "TechCorp"}
  }
  ```

**Usage Patterns:**
- Pass to `extract_job_profile_name(stellenprofil_data)` 
- Save to JSON file: `job_profile_{timestamp}.json`
- Pass as context to CV pipeline: `job_profile_context=stellenprofil_data`
- Use in offer generation: `generate_angebot(stellenprofil_data, ...)`

---

#### 2. **`job_profile_name`** - EXTRACTED & SANITIZED Name
- **Type:** `str`
- **Source:** `extract_job_profile_name(stellenprofil_data)` OR `extract_job_profile_name_from_file(filename)`
- **Content:** Normalized identifier for file/folder naming
- **Format:** Alphanumeric with underscores, max 30 chars
- **Fallback:** `"KEIN_PROFIL_ID"` (indicates missing data)
- **Examples:**
  - From data: `"gdjob_12881"` (preferred)
  - From position: `"sen_bus_ana"` (abbreviated)
  - From company: `"techcorp"` (company name)
  - Fallback: `"KEIN_PROFIL_ID"` (no data available)

**Usage Patterns:**
- Build output paths: `f"output/batch_run_{job_profile_name}_{timestamp}"`
- Create folder names
- Create file prefixes: `f"{job_profile_name}_{candidate_name}_cv_{timestamp}.json"`
- Check for failures: `if job_profile_name == "KEIN_PROFIL_ID"`

---

### ❌ FORBIDDEN Variables

#### **`jobprofile`** - HARDCODED String (DO NOT USE)
- This is a placeholder/fallback string
- **EVERYWHERE it appears, replace with intelligent logic**
- Common mistakes:
  ```python
  # ❌ WRONG - Hardcoded fallback
  job_profile_name = "jobprofile"
  
  # ✅ CORRECT - Use extraction functions with intelligent fallback
  job_profile_name = extract_job_profile_name(stellenprofil_data)
  if job_profile_name == "KEIN_PROFIL_ID":
      job_profile_name = extract_job_profile_name_from_file(filename)
  ```

---

## Extraction & Fallback Chain

### Priority Order for `job_profile_name`

```
1. Extract from stellenprofil_data:
   ├─ ID field (stellenprofilId, id, nummer, ...) → PREFERRED
   ├─ Position/Title abbreviated (sen_bus_ana)
   ├─ Company/Organization name
   └─ Any meaningful string field
   
2. If step 1 fails → extract from filename
   ├─ ID pattern (gdjob_12881) → PREFERRED
   └─ Abbreviated words (sen_bus_ana)
   
3. If all fails → KEIN_PROFIL_ID
```

### Implementation Example

```python
# Batch mode - Intelligent fallback chain
job_profile_name = extract_job_profile_name(stellenprofil_data)  # Try data first

if job_profile_name == "KEIN_PROFIL_ID":  # If data extraction failed
    job_profile_name = extract_job_profile_name_from_file(job_file.name)  # Try filename
    if job_profile_name != "KEIN_PROFIL_ID":
        print(f"[INFO] Using job profile name from filename: {job_profile_name}")
```

---

## Files Modified for Rule Compliance

### 1. **batch_comparison.py**
- ✅ Line 292-300: Replace `"jobprofile"` with `extract_job_profile_name_from_file()` fallback
- ✅ Line 308-318: Replace `"jobprofile"` with `extract_job_profile_name_from_file()` fallback
- ✅ Line 321-328: Add intelligent fallback chain (data → filename)

### 2. **streamlit_pipeline.py**
- ✅ Line 164: Replace `"jobprofile"` comparison with `"KEIN_PROFIL_ID"`
- ✅ Line 173: Replace `"jobprofile"` comparison with `"KEIN_PROFIL_ID"`
- ✅ Line 180: Replace `"jobprofile"` fallback with `"KEIN_PROFIL_ID"`

### 3. **app.py**
- ✅ Line 975: Replace `"jobprofile"` default with `"KEIN_PROFIL_ID"`

### 4. **naming_conventions.py**
- ✅ Updated all fallback strings to use `"KEIN_PROFIL_ID"` consistently
- ✅ Enhanced `extract_job_profile_name()` with 4-tier priority system
- ✅ Enhanced `extract_job_profile_name_from_file()` with better filename parsing

---

## Testing Checklist

- [ ] No file in codebase contains hardcoded `"jobprofile"` in variable assignment
- [ ] All `job_profile_name` comparisons use `"KEIN_PROFIL_ID"` not `"jobprofile"`
- [ ] `extract_job_profile_name()` called with `stellenprofil_data` dict
- [ ] `extract_job_profile_name_from_file()` called with filename string
- [ ] Intelligent fallback chain implemented: data → filename → KEIN_PROFIL_ID
- [ ] All 112 tests passing without regression

---

## Code Review Checklist

When reviewing code, ensure:

1. **No hardcoded `"jobprofile"`**
   ```python
   # ❌ WRONG
   job_name = "jobprofile"
   
   # ✅ CORRECT
   job_name = extract_job_profile_name(data) or "KEIN_PROFIL_ID"
   ```

2. **Correct function usage**
   ```python
   # ✅ extract_job_profile_name expects Dict
   name = extract_job_profile_name(stellenprofil_data)
   
   # ✅ extract_job_profile_name_from_file expects str
   name = extract_job_profile_name_from_file(job_file.name)
   ```

3. **Correct comparison for fallback**
   ```python
   # ✅ Compare against KEIN_PROFIL_ID, not jobprofile
   if name == "KEIN_PROFIL_ID":
       name = extract_job_profile_name_from_file(filename)
   ```

4. **No mixing of variables**
   ```python
   # ✅ Use either stellenprofil_data or job_profile_name, not both for naming
   folder = f"{job_profile_name}_{timestamp}"  # Use extracted name
   context = stellenprofil_data  # Use raw data for context
   ```

---

## Historical Issues (FIXED)

| Issue | Before | After | File | Status |
|-------|--------|-------|------|--------|
| Hardcoded "jobprofile" fallback | `return {"job_profile_name": "jobprofile"}` | `return {"job_profile_name": extract_job_profile_name_from_file(filename)}` | batch_comparison.py | ✅ FIXED |
| Comparing to "jobprofile" | `if name != "jobprofile"` | `if name != "KEIN_PROFIL_ID"` | streamlit_pipeline.py | ✅ FIXED |
| Default fallback | `"jobprofile"` | `"KEIN_PROFIL_ID"` | app.py | ✅ FIXED |

---

## Summary

**ONE RULE:** Only use `stellenprofil_data` (raw input) and `job_profile_name` (processed output). Never hardcode `"jobprofile"`. Use intelligent extraction with fallbacks to filename, then to `"KEIN_PROFIL_ID"`.
