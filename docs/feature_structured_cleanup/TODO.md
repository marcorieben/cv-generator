# Detailed TODO Checklist

## Phase 1: Architecture & Folder Structure

### 1.1 Cleanup Directory Structure
- [ ] Create `./cleanup/` directory (root level, never cleaned)
- [ ] Create `.gitkeep` in cleanup/ to preserve it
- [ ] Document directory as protected in `.gitignore`
- [ ] Create run folder template: `cleanup/runs/`
- [ ] Create first test run folder: `cleanup/runs/2026-01-23_000000/`

### 1.2 Output File Templates
- [ ] Create template for `cleanup_report.json`
- [ ] Create template for `cleanup_report.md`
- [ ] Create template for `deleted_files.log`
- [ ] Create template for `archived_files.log`
- [ ] Add metadata schema (timestamp, mode, file_count, etc.)

### 1.3 Documentation
- [ ] Document folder structure in ARCHITECTURE.md
- [ ] Document immutable history rules
- [ ] Document timestamp format: YYYY-MM-DD_HH-MM-SS
- [ ] Create .gitkeep in cleanup/runs/

**Status:** Not Started  
**Estimated Time:** 1-2 hours

---

## Phase 2: File Classification System

### 2.1 Define Enums
- [ ] Create `FILE_CATEGORY` enum with 10 types
  - [ ] SOURCE_CODE
  - [ ] CONFIG
  - [ ] PROMPT
  - [ ] INPUT_DATA
  - [ ] INTERMEDIATE_ARTIFACT
  - [ ] GENERATED_OUTPUT
  - [ ] LOG_FILE
  - [ ] TEMP_FILE
  - [ ] EXPERIMENT
  - [ ] UNKNOWN
- [ ] Create `DECISION_TYPE` enum with 3 types
  - [ ] DELETE_SAFE
  - [ ] KEEP_REQUIRED
  - [ ] REVIEW_REQUIRED

### 2.2 File Type Mapping
- [ ] Map file extensions → categories
  - [ ] .py, .json, .yaml → SOURCE_CODE/CONFIG
  - [ ] .log → LOG_FILE
  - [ ] .tmp, .bak → TEMP_FILE
  - [ ] Others → UNKNOWN
- [ ] Create mapping dictionary
- [ ] Handle edge cases

### 2.3 Category Detection Logic
- [ ] Implement path-based detection
- [ ] Implement extension-based detection
- [ ] Implement content-based detection (if needed)
- [ ] Add fallback to UNKNOWN

**Status:** Not Started  
**Estimated Time:** 2-3 hours

---

## Phase 3: Per-File Analysis Engine

### 3.1 Analysis Object Structure
- [ ] Define `FileAnalysis` dataclass/TypedDict:
  ```
  file_path: str
  category: str
  last_modified: str (ISO format)
  size_kb: float
  decision: str
  confidence: float (0.0-1.0)
  reasoning: list[str]
  risk_assessment: str
  recommended_action: str
  ```
- [ ] Add validation
- [ ] Add serialization methods (to JSON)

### 3.2 File Scanning Engine
- [ ] Create recursive file scanner
- [ ] Exclude system files (.git, __pycache__, etc.)
- [ ] Get file metadata (mtime, size)
- [ ] Convert to analysis objects
- [ ] Handle permission errors gracefully

### 3.3 Dependency Detection
- [ ] Create reference scanner for source code files
- [ ] Check for file references in Python code
- [ ] Check for file references in JSON/YAML configs
- [ ] Check for file references in documentation
- [ ] Return list of referencing files

### 3.4 Confidence Scoring
- [ ] Define scoring rules (0.0-1.0)
- [ ] Clear category → high confidence
- [ ] Unknown category → low confidence
- [ ] Found references → lower confidence
- [ ] Recent files → lower confidence

**Status:** Not Started  
**Estimated Time:** 4-5 hours

---

## Phase 4: Decision Rules Engine

### 4.1 DELETE_SAFE Rules
- [ ] Category must be one of: TEMP_FILE, LOG_FILE, INTERMEDIATE_ARTIFACT
- [ ] Path must be in: /tmp, /logs, /data/intermediate
- [ ] File age must exceed threshold (default 14 days)
- [ ] No references in source code
- [ ] No references in config files
- [ ] Not listed in required artifacts
- [ ] Confidence >= 0.95
- [ ] All rules must be true (AND logic)

### 4.2 KEEP_REQUIRED Rules
- [ ] File is in source code (*.py, *.json in source dirs)
- [ ] File is in config directory
- [ ] File is in critical manifests (requirements.txt, etc.)
- [ ] File has references from other files
- [ ] File is in protected paths list
- [ ] Any reference found = KEEP

### 4.3 REVIEW_REQUIRED Rules
- [ ] Any rule fails for DELETE_SAFE
- [ ] Category is UNKNOWN
- [ ] Confidence < 0.95
- [ ] Uncertain dependencies
- [ ] Any ambiguity → REVIEW

### 4.4 Explanation Requirements
- [ ] For REVIEW_REQUIRED: mandatory detailed explanation
  - [ ] Why uncertain?
  - [ ] What dependencies at risk?
  - [ ] What could break?
  - [ ] Clear recommendation
- [ ] All reasoning must be concrete (no guesses)

**Status:** Not Started  
**Estimated Time:** 3-4 hours

---

## Phase 5: Report Generation

### 5.1 JSON Report (`cleanup_report.json`)
- [ ] Generate run metadata:
  - [ ] timestamp
  - [ ] mode (analyze/apply)
  - [ ] total_files_analyzed
  - [ ] summary counts
- [ ] Generate per-file analysis array
- [ ] Generate summary statistics
- [ ] Pretty-print with indentation
- [ ] Ensure valid JSON

### 5.2 Markdown Report (`cleanup_report.md`)
- [ ] Create human-readable summary section
- [ ] Create summary table:
  - [ ] DELETE_SAFE count
  - [ ] KEEP_REQUIRED count
  - [ ] REVIEW_REQUIRED count
- [ ] Create detailed table for REVIEW_REQUIRED files
  - [ ] File path
  - [ ] Category
  - [ ] Risk assessment
  - [ ] Recommendation
- [ ] Add risk level colors (if terminal support)
- [ ] Use clear, non-vague language

### 5.3 Log Files
- [ ] Create `deleted_files.log` template (apply mode)
  - [ ] One file per line
  - [ ] Include deletion timestamp
  - [ ] Include file size
- [ ] Create `archived_files.log` template (apply mode)
  - [ ] One file per line
  - [ ] Include archive path
  - [ ] Include original path

**Status:** Not Started  
**Estimated Time:** 3-4 hours

---

## Phase 6: Execution Modes

### 6.1 MODE: analyze
- [ ] Read configuration
- [ ] Scan all files
- [ ] Classify each file
- [ ] Apply decision rules
- [ ] Generate reports
- [ ] Create run folder with timestamp
- [ ] Save all reports to run folder
- [ ] Never modify filesystem
- [ ] Return analysis results

### 6.2 MODE: apply
- [ ] Load most recent analyze report
- [ ] Validate report integrity
- [ ] Filter for DELETE_SAFE only
- [ ] Delete files (with user confirmation?)
- [ ] Log deletions to deleted_files.log
- [ ] Archive REVIEW_REQUIRED (if configured)
- [ ] Never touch KEEP_REQUIRED or REVIEW_REQUIRED
- [ ] Create run documentation

### 6.3 Safety Checks
- [ ] Verify no active application processes
- [ ] Check file system permissions
- [ ] Validate paths before deletion
- [ ] Double-check confidence >= 0.95
- [ ] Create backup manifests

**Status:** Not Started  
**Estimated Time:** 3-4 hours

---

## Phase 7: Configuration & Constraints

### 7.1 Configuration Module
- [ ] Define `CleanupConfig` dataclass:
  - [ ] age_threshold_days (default: 14)
  - [ ] confidence_threshold (default: 0.95)
  - [ ] protected_paths (list)
  - [ ] required_artifacts (list)
  - [ ] max_deletion_size_mb (safety limit)
- [ ] Load from config file or defaults
- [ ] Validate configuration

### 7.2 Protected Paths
- [ ] Define paths never to clean:
  - [ ] /cleanup (cleanup system itself!)
  - [ ] /scripts (application code)
  - [ ] /.git (version control)
  - [ ] /app.py, /main files
  - [ ] Any user-defined paths
- [ ] Enforce at filesystem level

### 7.3 Required Artifacts
- [ ] List files that must never be deleted:
  - [ ] All source code
  - [ ] Config files
  - [ ] Database schemas
  - [ ] Generated outputs (if needed)
- [ ] Store in configuration

**Status:** Not Started  
**Estimated Time:** 2 hours

---

## Phase 8: Testing & Validation

### 8.1 Unit Tests
- [ ] Test FILE_CATEGORY classification
- [ ] Test DECISION_TYPE logic
- [ ] Test confidence scoring
- [ ] Test delete rules (each rule individually)
- [ ] Test keep rules
- [ ] Test review rules
- [ ] Test edge cases (empty files, special chars, etc.)

### 8.2 Integration Tests
- [ ] Test full analyze mode
- [ ] Test report generation
- [ ] Test folder structure creation
- [ ] Test timestamp handling
- [ ] Test with sample project

### 8.3 Validation Tests
- [ ] Run on real project files
- [ ] Verify no critical files marked DELETE_SAFE
- [ ] Verify all REVIEW_REQUIRED have explanations
- [ ] Verify confidence scores reasonable
- [ ] Verify no false positives

### 8.4 Safety Tests
- [ ] Dry-run apply mode (no actual deletion)
- [ ] Verify protected paths ignored
- [ ] Verify cleanup/ folder protected
- [ ] Test recovery from errors

**Status:** Not Started  
**Estimated Time:** 5-6 hours

---

## Phase 9: Documentation & Examples

### 9.1 API Documentation
- [ ] Document main entry point
- [ ] Document all function signatures
- [ ] Document all parameters
- [ ] Document return values
- [ ] Document exceptions
- [ ] Add docstrings to all functions

### 9.2 Usage Examples
- [ ] Example: Basic analyze
- [ ] Example: Apply with confirmation
- [ ] Example: Custom configuration
- [ ] Example: Protected paths
- [ ] Show output examples

### 9.3 Output Examples
- [ ] Sample `cleanup_report.json`
- [ ] Sample `cleanup_report.md`
- [ ] Sample `deleted_files.log`
- [ ] Sample `archived_files.log`

### 9.4 Safety Guide
- [ ] Best practices
- [ ] When to review before deleting
- [ ] How to recover deleted files
- [ ] How to add protected paths
- [ ] Troubleshooting guide

**Status:** Not Started  
**Estimated Time:** 3-4 hours

---

## Daily Progress Template

Use this to track daily work:

```
## Day 1: [Date]

### Completed
- [ ] Phase 1.1 - Directory structure
- [ ] Phase 1.2 - Output templates

### In Progress
- [ ] Phase 2.1 - Define enums

### Blocked / Issues
- None

### Next Day
- Phase 2.2 - File type mapping
```

---

## Notes

- Keep confidence threshold HIGH (0.95+) to avoid mistakes
- When uncertain: explain and defer to human review
- Never guess on dependencies
- Test thoroughly before apply mode
- Keep cleanup history immutable

---
