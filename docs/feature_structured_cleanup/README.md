# Feature: Structured Cleanup System

**Status:** In Development  
**Branch:** `feature/structured_cleanup`  
**Created:** 2026-01-23  

---

## Overview

A safe, explainable cleanup system for production-relevant application environments.

**Core Principle:** Analysis → Classification → Traceability (NOT deletion)

The system analyzes all files, produces per-file assessments, and decides:
- `DELETE_SAFE` - Safe to delete
- `KEEP_REQUIRED` - Must keep
- `REVIEW_REQUIRED` - Human review needed

---

## Requirements Breakdown

### Phase 1: Architecture & Folder Structure
- [ ] Create `/cleanup` base directory (never cleaned)
- [ ] Define `/cleanup/runs/<YYYY-MM-DD_HH-MM-SS>` structure
- [ ] Create immutable run folders (append-only history)
- [ ] Define output files per run:
  - `cleanup_report.json`
  - `cleanup_report.md`
  - `deleted_files.log`
  - `archived_files.log`

**Deliverable:** Folder structure + documentation

---

### Phase 2: File Classification System
- [ ] Define FILE_CATEGORIES enum (10 types):
  - SOURCE_CODE
  - CONFIG
  - PROMPT
  - INPUT_DATA
  - INTERMEDIATE_ARTIFACT
  - GENERATED_OUTPUT
  - LOG_FILE
  - TEMP_FILE
  - EXPERIMENT
  - UNKNOWN

- [ ] Define DECISION_TYPES enum (3 types):
  - DELETE_SAFE
  - KEEP_REQUIRED
  - REVIEW_REQUIRED

- [ ] Create category → decision mapping rules

**Deliverable:** Enums + classification logic

---

### Phase 3: Per-File Analysis Engine
- [ ] Create analysis object structure:
  ```json
  {
    "file_path": "",
    "category": "",
    "last_modified": "",
    "size_kb": 0,
    "decision": "",
    "confidence": 0.0,
    "reasoning": [""],
    "risk_assessment": "",
    "recommended_action": ""
  }
  ```

- [ ] Implement classification logic for each category
- [ ] Implement dependency detection (source code references)
- [ ] Implement age threshold checking (default: 14 days)
- [ ] Calculate confidence scores (0.0 - 1.0)

**Deliverable:** Core analysis engine

---

### Phase 4: Decision Rules Engine
- [ ] Implement DELETE_SAFE rules:
  - Category must be: TEMP_FILE, LOG_FILE, or INTERMEDIATE_ARTIFACT
  - Path must be in: /tmp, /logs, /data/intermediate
  - Age must exceed threshold
  - No references in source code
  - No references in config files
  - Not listed as required artifact
  - Confidence >= 0.95

- [ ] Implement KEEP_REQUIRED logic:
  - Any file referenced in source code
  - Config files
  - Manifest files
  - Required outputs

- [ ] Implement REVIEW_REQUIRED for all edge cases

- [ ] Mandatory explanation for REVIEW_REQUIRED:
  - Why uncertain?
  - What dependency risks?
  - What could break?
  - Clear recommendation

**Deliverable:** Decision engine + tests

---

### Phase 5: Report Generation
- [ ] Generate `cleanup_report.json`:
  - Full per-file analysis
  - Run metadata (timestamp, mode, file count)
  - Summary (counts by decision type)
  - Machine readable

- [ ] Generate `cleanup_report.md`:
  - Human readable summary
  - Summary table (DELETE_SAFE, KEEP_REQUIRED, REVIEW_REQUIRED counts)
  - Detailed table for REVIEW_REQUIRED files
  - Clear, non-vague language
  - Risk assessments for each file

- [ ] Generate `deleted_files.log` (apply mode only)
- [ ] Generate `archived_files.log` (apply mode only)

**Deliverable:** Report generation system

---

### Phase 6: Execution Modes
- [ ] Implement MODE: `analyze`
  - No filesystem changes
  - Full analysis
  - Generate reports only
  - Safe to run anytime

- [ ] Implement MODE: `apply`
  - Read most recent analyze report
  - Delete only DELETE_SAFE files
  - Archive REVIEW_REQUIRED files (if configured)
  - Never delete KEEP_REQUIRED or REVIEW_REQUIRED
  - Log all deletions

**Deliverable:** Two-mode system

---

### Phase 7: Configuration & Constraints
- [ ] Define configurable parameters:
  - `age_threshold_days` (default: 14)
  - `confidence_threshold` (default: 0.95)
  - `protected_paths` (never clean)
  - `required_artifacts` (list of paths to preserve)

- [ ] Document forbidden actions (list below)
- [ ] Add safety checks

**Deliverable:** Configuration module

---

### Phase 8: Testing & Validation
- [ ] Unit tests for classification logic
- [ ] Unit tests for decision rules
- [ ] Integration tests (analyze mode)
- [ ] Dry-run tests (apply mode simulation)
- [ ] Test with real project files

**Deliverable:** Full test suite

---

### Phase 9: Documentation & Examples
- [ ] API documentation
- [ ] Usage examples
- [ ] Output examples (JSON + Markdown)
- [ ] Configuration guide
- [ ] Safety guidelines

**Deliverable:** Complete documentation

---

## Forbidden Actions

You must NEVER:
- ❌ Guess dependencies without explanation
- ❌ Delete files with confidence < 0.95
- ❌ Modify application source code
- ❌ Clean during active application runs
- ❌ Remove cleanup history
- ❌ Use vague language ("probably unused" without justification)

---

## File Organization

```
feature_structured_cleanup/
├── README.md (this file)
├── REQUIREMENTS.md (full requirement text)
├── TODO.md (detailed checklist)
├── ARCHITECTURE.md (system design)
├── API.md (function signatures)
└── examples/
    ├── sample_report.json
    └── sample_report.md
```

---

## Success Criteria

✅ All phases completed  
✅ All forbidden actions documented and prevented  
✅ Confidence >= 0.95 for all DELETE_SAFE decisions  
✅ 100% explanation for REVIEW_REQUIRED files  
✅ Zero false positive deletions in testing  
✅ Full test coverage  
✅ Complete documentation  

---

## Implementation Notes

- **Language:** Python 3.10+
- **Location:** `scripts/cleanup/` (new module)
- **Dependencies:** os, json, pathlib, datetime, typing
- **No external dependencies** (keep lightweight)

---

## Timeline

Phase 1-3: Foundation (Days 1-2)
Phase 4-6: Core Logic (Days 3-4)
Phase 7-9: Polish & Testing (Days 5)

---
