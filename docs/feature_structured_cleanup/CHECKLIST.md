# Implementation TODO Checklist

> **Daily working checklist** - Mark items as you complete them. This breaks the 9 phases into concrete, verifiable work items.

---

## Phase 1: Folder Structure & Templates (FOUNDATION)

- [ ] **P1.1** Create `/cleanup` directory at project root  
  - [ ] Verify path: `c:\Users\mrieben\Documents\cv_generator\cleanup`  
  - [ ] Add `.gitkeep` file to preserve empty folder  

- [ ] **P1.2** Create `/cleanup/runs` subdirectory  
  - [ ] Will hold timestamped run folders  

- [ ] **P1.3** Create `/cleanup/.gitignore` with rules  
  ```
  # Store cleanup reports in version control
  # But ignore very large temp archives
  !.gitkeep
  !cleanup_report.json
  !cleanup_report.md
  !deleted_files.log
  !archived_files.log
  *.tmp
  ```

- [ ] **P1.4** Create `/cleanup/template_report.json` as reference  
  - [ ] Document expected schema  
  - [ ] Include example analysis object  

- [ ] **P1.5** Create `/cleanup/README.md` explaining folder structure  
  - [ ] Document timestamp folder format (YYYY-MM-DD_HH-MM-SS)  
  - [ ] Explain immutability principle  
  - [ ] Show example run folder contents  

---

## Phase 2: Enums & Data Models (DATA STRUCTURE)

- [ ] **P2.1** Create `scripts/cleanup/__init__.py`  
  - [ ] Module initialization  
  - [ ] Import all public classes  

- [ ] **P2.2** Create `scripts/cleanup/models.py`  
  - [ ] Define `FileCategory` enum (10 values):  
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

  - [ ] Define `DecisionType` enum (3 values):  
    - [ ] DELETE_SAFE  
    - [ ] KEEP_REQUIRED  
    - [ ] REVIEW_REQUIRED  

  - [ ] Create `FileAnalysis` dataclass with fields:  
    - [ ] file_path: str  
    - [ ] category: FileCategory  
    - [ ] last_modified: str (ISO format)  
    - [ ] size_kb: float  
    - [ ] decision: DecisionType  
    - [ ] confidence: float (0.0 - 1.0)  
    - [ ] reasoning: List[str] (why decision was made)  
    - [ ] risk_assessment: str (what could break)  
    - [ ] recommended_action: str (what to do)  

  - [ ] Create `CleanupConfig` dataclass:  
    - [ ] age_threshold_days: int = 14  
    - [ ] confidence_threshold: float = 0.95  
    - [ ] protected_paths: List[str] = None  
    - [ ] required_artifacts: List[str] = None  
    - [ ] max_deletion_size_mb: float = 100.0  

  - [ ] Create `CleanupReport` dataclass:  
    - [ ] metadata: dict (timestamp, mode, summary)  
    - [ ] files: List[FileAnalysis]  
    - [ ] run_id: str (timestamp)  

- [ ] **P2.3** Add docstrings to all models  
  - [ ] Explain enum values  
  - [ ] Document field constraints  

- [ ] **P2.4** Create unit tests for models  
  - [ ] Test enum instantiation  
  - [ ] Test dataclass validation  
  - [ ] File: `tests/scripts/cleanup/test_models.py`  

---

## Phase 3: File Classification Engine (CORE LOGIC)

- [ ] **P3.1** Create `scripts/cleanup/classify.py`  

- [ ] **P3.2** Implement `classify_file(path: str) -> FileCategory` function  
  - [ ] Rules for SOURCE_CODE (`.py`, `.ts`, `.js`, `.md` not in docs/)  
  - [ ] Rules for CONFIG (`.yaml`, `.json` in root/config areas)  
  - [ ] Rules for PROMPT (files in `/prompts/` or named `*_prompt.txt`)  
  - [ ] Rules for INPUT_DATA (files in `/input/` or `/data/input/`)  
  - [ ] Rules for INTERMEDIATE_ARTIFACT (files in `/data/intermediate/`, `/tmp/`)  
  - [ ] Rules for GENERATED_OUTPUT (files in `/output/` with matching input templates)  
  - [ ] Rules for LOG_FILE (`.log`, in `/logs/`, size < 100MB)  
  - [ ] Rules for TEMP_FILE (`.tmp`, `.bak`, `.cache` extensions)  
  - [ ] Rules for EXPERIMENT (files with `_experiment_`, `_test_`, `_demo_` in name)  
  - [ ] Default fallback to UNKNOWN if no rules match  

- [ ] **P3.3** Implement `get_file_age_days(path: str) -> float` helper  
  - [ ] Return days since last modification  
  - [ ] Handle missing files gracefully  

- [ ] **P3.4** Implement `get_file_size_kb(path: str) -> float` helper  
  - [ ] Return file size in KB  
  - [ ] Handle missing files  

- [ ] **P3.5** Create classification rules documentation  
  - [ ] File: `scripts/cleanup/CLASSIFICATION_RULES.md`  
  - [ ] Explain each category with examples  
  - [ ] Document precedence rules  

- [ ] **P3.6** Create unit tests for classification  
  - [ ] Test each category with sample filenames  
  - [ ] Test edge cases (ambiguous names)  
  - [ ] File: `tests/scripts/cleanup/test_classify.py`  

- [ ] **P3.7** Test against actual project structure  
  - [ ] Run classifier on real files  
  - [ ] Verify categories match expectations  
  - [ ] Document surprises  

---

## Phase 4: Decision Rules Engine (DECISION LOGIC)

- [ ] **P4.1** Create `scripts/cleanup/decisions.py`  

- [ ] **P4.2** Implement `analyze_file(path: str, config: CleanupConfig) -> FileAnalysis`  
  - [ ] Get file metadata (path, category, size, age)  
  - [ ] Generate initial reasoning list (empty)  
  - [ ] Apply decision rules (separate function)  
  - [ ] Return complete FileAnalysis object  

- [ ] **P4.3** Implement `apply_decision_rules(analysis: FileAnalysis, config: CleanupConfig) -> FileAnalysis`  
  - [ ] **For DELETE_SAFE decision** (all must be true):  
    - [ ] Category in [TEMP_FILE, LOG_FILE, INTERMEDIATE_ARTIFACT]  
    - [ ] Path in protected list: [/cleanup, /scripts, /tests]  
    - [ ] File age >= config.age_threshold_days  
    - [ ] No references found in source code (see P5)  
    - [ ] Not in required artifacts list  
    - [ ] Set confidence >= 0.95 if all true  
    - [ ] Add reasoning for each check  

  - [ ] **For KEEP_REQUIRED decision** (if applicable):  
    - [ ] Category = SOURCE_CODE (never delete)  
    - [ ] Category = CONFIG (never delete)  
    - [ ] File in required_artifacts  
    - [ ] Found references in source code  
    - [ ] Set confidence = 1.0  

  - [ ] **For REVIEW_REQUIRED decision** (fallback):  
    - [ ] Anything that doesn't clearly match above  
    - [ ] Category = UNKNOWN  
    - [ ] Confidence < 0.95  
    - [ ] Add detailed risk_assessment  
    - [ ] Add recommended_action  

- [ ] **P4.4** Implement `find_references_in_source(path: str) -> List[str]` helper  
  - [ ] Search source code for filename references  
  - [ ] Search config files for path references  
  - [ ] Return list of files where references found  
  - [ ] Use grep_search pattern matching  

- [ ] **P4.5** Implement `assess_risk(analysis: FileAnalysis) -> str` helper  
  - [ ] Explain what could break if file deleted  
  - [ ] Mention any potential module imports  
  - [ ] Mention any data dependencies  
  - [ ] Be explicit, not vague  

- [ ] **P4.6** Create decision rule documentation  
  - [ ] File: `scripts/cleanup/DECISION_RULES.md`  
  - [ ] Flowchart for decision logic  
  - [ ] Examples for each decision type  

- [ ] **P4.7** Create unit tests for decision rules  
  - [ ] Test DELETE_SAFE scenarios (should succeed)  
  - [ ] Test KEEP_REQUIRED scenarios  
  - [ ] Test REVIEW_REQUIRED scenarios  
  - [ ] Test edge cases (confidence < 0.95)  
  - [ ] File: `tests/scripts/cleanup/test_decisions.py`  

---

## Phase 5: Dependency Analysis (CRITICAL)

- [ ] **P5.1** Create `scripts/cleanup/dependencies.py`  

- [ ] **P5.2** Implement `scan_source_code_for_references(filepath: str) -> List[tuple]`  
  - [ ] Search all `.py` files for filename/path imports  
  - [ ] Search all `.yaml` files for path references  
  - [ ] Search all `.json` files for data references  
  - [ ] Return list of (source_file, line_number, match_text)  

- [ ] **P5.3** Implement `find_generated_output_sources(output_path: str) -> List[str]`  
  - [ ] Check if file in /output/ has matching generator in scripts/  
  - [ ] Return list of generating scripts  

- [ ] **P5.4** Implement `is_artifact_regenerable(path: str) -> bool`  
  - [ ] Check if generator script still exists  
  - [ ] Return True if can be regenerated, False if permanent  

- [ ] **P5.5** Create tests for dependency detection  
  - [ ] Test finding imports in source  
  - [ ] Test finding config references  
  - [ ] File: `tests/scripts/cleanup/test_dependencies.py`  

---

## Phase 6: Report Generation (OUTPUT)

- [ ] **P6.1** Create `scripts/cleanup/reports.py`  

- [ ] **P6.2** Implement `generate_json_report(analyses: List[FileAnalysis], run_id: str) -> str`  
  - [ ] Create metadata dict with:  
    - [ ] timestamp (ISO format)  
    - [ ] mode (analyze/apply)  
    - [ ] total_files count  
    - [ ] summary counts (delete_safe, keep_required, review_required)  
  - [ ] Create files array with all analyses  
  - [ ] Convert to JSON with 2-space indent  
  - [ ] Return JSON string  

- [ ] **P6.3** Implement `generate_markdown_report(analyses: List[FileAnalysis]) -> str`  
  - [ ] Generate header with summary counts  
  - [ ] Create table of REVIEW_REQUIRED files with:  
    - [ ] File path  
    - [ ] Category  
    - [ ] Confidence  
    - [ ] Risk assessment (2-3 lines)  
  - [ ] Create summary section  
  - [ ] Generate human-readable output  

- [ ] **P6.4** Implement `save_reports(report_json: str, report_md: str, run_id: str, mode: str)`  
  - [ ] Create /cleanup/runs/<run_id> folder if not exists  
  - [ ] Save cleanup_report.json  
  - [ ] Save cleanup_report.md  
  - [ ] If mode=apply, create deleted_files.log  
  - [ ] If mode=apply, create archived_files.log  

- [ ] **P6.5** Create integration tests for report generation  
  - [ ] Test JSON output schema  
  - [ ] Test markdown output format  
  - [ ] Verify files saved to correct paths  
  - [ ] File: `tests/scripts/cleanup/test_reports.py`  

---

## Phase 7: Execution Modes (ORCHESTRATION)

- [ ] **P7.1** Create `scripts/cleanup/executor.py`  

- [ ] **P7.2** Implement `run_cleanup(mode: str = "analyze", config: CleanupConfig = None) -> CleanupReport`  
  - [ ] **If mode not in ["analyze", "apply"], raise ValueError**  
  - [ ] **Load config or use defaults**  
  - [ ] **Scan filesystem for all files in project**  
  - [ ] **For each file:**  
    - [ ] Call `analyze_file(path, config)`  
    - [ ] Collect FileAnalysis objects  
  - [ ] **Generate reports**  
  - [ ] **If mode = analyze:**  
    - [ ] Save reports to /cleanup/runs/<timestamp>/  
    - [ ] Return report object  
    - [ ] No filesystem changes  
  - [ ] **If mode = apply:**  
    - [ ] Load most recent analyze report  
    - [ ] Confirm deletion safety (< 100 files, < 100MB total)  
    - [ ] Delete only DELETE_SAFE files  
    - [ ] Archive REVIEW_REQUIRED files (if configured)  
    - [ ] Log all actions  
    - [ ] Return report with applied changes  

- [ ] **P7.3** Implement file deletion logic (for apply mode)  
  - [ ] Before deleting any file: read, backup path to log  
  - [ ] Never delete if confidence < 0.95  
  - [ ] Never delete REVIEW_REQUIRED files  
  - [ ] Log each deletion with timestamp and size  

- [ ] **P7.4** Implement archival logic (optional for apply mode)  
  - [ ] Move REVIEW_REQUIRED files to /cleanup/archived/<timestamp>/  
  - [ ] Preserve original directory structure  
  - [ ] Log original→archive path mapping  

- [ ] **P7.5** Add confirmation dialogs (for apply mode)  
  - [ ] Show summary of files to delete  
  - [ ] Show total size  
  - [ ] Require user confirmation before proceeding  
  - [ ] Use existing `dialogs.py` module if available  

- [ ] **P7.6** Create integration tests for execution  
  - [ ] Test analyze mode (no changes)  
  - [ ] Test apply mode (with test files)  
  - [ ] Verify reports created correctly  
  - [ ] File: `tests/scripts/cleanup/test_executor.py`  

---

## Phase 8: Configuration & CLI (INTERFACE)

- [ ] **P8.1** Create `scripts/cleanup/cli.py`  

- [ ] **P8.2** Implement `main()` function  
  - [ ] Accept command-line arguments  
  - [ ] Support: `python -m scripts.cleanup analyze`  
  - [ ] Support: `python -m scripts.cleanup apply`  
  - [ ] Support: `python -m scripts.cleanup --help`  
  - [ ] Support: `python -m scripts.cleanup analyze --config custom_config.yaml`  

- [ ] **P8.3** Create default config file  
  - [ ] File: `scripts/cleanup/default_config.yaml`  
  - [ ] Document all configurable parameters:  
    - [ ] age_threshold_days  
    - [ ] confidence_threshold  
    - [ ] protected_paths  
    - [ ] required_artifacts  
    - [ ] max_deletion_size_mb  

- [ ] **P8.4** Implement config loading  
  - [ ] Load from file if provided  
  - [ ] Validate config schema  
  - [ ] Use defaults for missing values  
  - [ ] Support environment variable overrides  

- [ ] **P8.5** Add logging  
  - [ ] Info level: "Starting cleanup in analyze mode"  
  - [ ] Debug level: "Analyzing file X with category Y"  
  - [ ] Warning level: "File X has low confidence decision"  
  - [ ] Error level: "Could not read file X: permission denied"  

---

## Phase 9: Testing, Docs & Examples (VALIDATION)

- [ ] **P9.1** Write comprehensive README  
  - [ ] File: `scripts/cleanup/README.md`  
  - [ ] Document purpose  
  - [ ] Show usage examples  
  - [ ] Explain each mode  
  - [ ] Warn about apply mode safety  

- [ ] **P9.2** Create example cleanup scenarios  
  - [ ] Scenario 1: Clean old log files (DELETE_SAFE)  
  - [ ] Scenario 2: Analyze test artifacts (REVIEW_REQUIRED)  
  - [ ] Scenario 3: Protect source code (KEEP_REQUIRED)  
  - [ ] Save examples to: `scripts/cleanup/examples/`  

- [ ] **P9.3** Run full test suite  
  - [ ] All unit tests pass  
  - [ ] All integration tests pass  
  - [ ] Code coverage > 80%  
  - [ ] No linting errors  

- [ ] **P9.4** Test with real project structure  
  - [ ] Run analyze mode on actual cv_generator  
  - [ ] Review generated reports  
  - [ ] Verify categories match expectations  
  - [ ] Fix any edge cases  

- [ ] **P9.5** Create safety checklist  
  - [ ] File: `scripts/cleanup/SAFETY_CHECKLIST.md`  
  - [ ] Document all forbidden actions  
  - [ ] Document verification steps before apply mode  

- [ ] **P9.6** Documentation review  
  - [ ] All functions have docstrings  
  - [ ] All classes documented  
  - [ ] All enums explained  
  - [ ] Examples provided for complex logic  

- [ ] **P9.7** Commit and push  
  - [ ] Stage all new files: `git add scripts/cleanup/`  
  - [ ] Commit: `git commit -m "feat: Implement structured cleanup system - all phases complete"`  
  - [ ] Push: `git push origin feature/structured_cleanup`  

---

## Verification Checklist (Before Marking Complete)

- [ ] All 9 phases implemented  
- [ ] All forbidden actions impossible (code review)  
- [ ] All required fields in FileAnalysis populated  
- [ ] All decision types (DELETE_SAFE, KEEP_REQUIRED, REVIEW_REQUIRED) working  
- [ ] Confidence >= 0.95 enforced for DELETE_SAFE  
- [ ] Explanations mandatory for REVIEW_REQUIRED  
- [ ] Test coverage > 80%  
- [ ] Apply mode requires confirmation  
- [ ] Cleanup history immutable in /cleanup/runs/  
- [ ] No test failures  
- [ ] Documentation complete  

---

## Notes & Tracking

Use the space below to track progress and notes:

```
Phase 1: [ ] Started [ ] In Progress [✓] Complete
Phase 2: [ ] Started [ ] In Progress [ ] Complete
Phase 3: [ ] Started [ ] In Progress [ ] Complete
Phase 4: [ ] Started [ ] In Progress [ ] Complete
Phase 5: [ ] Started [ ] In Progress [ ] Complete
Phase 6: [ ] Started [ ] In Progress [ ] Complete
Phase 7: [ ] Started [ ] In Progress [ ] Complete
Phase 8: [ ] Started [ ] In Progress [ ] Complete
Phase 9: [ ] Started [ ] In Progress [ ] Complete

Overall: [ ] Started [ ] In Progress [ ] Complete

Total items: 75+
```
