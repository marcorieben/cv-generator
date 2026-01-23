# Full Requirements Document

> **Original Requirements** - This document is the authoritative source for all cleanup system requirements.

---

## SYSTEM / INITIAL PROMPT

You are implementing a safe, explainable cleanup system for a production‑relevant application environment.

**Your primary goal is analysis, classification, and traceability — NOT deletion.**

The cleanup must never break the application.

When uncertain, always explain, assess risk, and defer for human review.

---

## OBJECTIVE

Create a cleanup function that:

* Analyzes all relevant files in the application environment
* Produces a per‑file assessment
* Classifies each file
* Decides one of:
  * DELETE_SAFE
  * KEEP_REQUIRED
  * REVIEW_REQUIRED
* Documents reasoning, confidence, and risk
* Stores results in a central cleanup folder
* Deletes only clear no‑brainers
* Never deletes files with unclear dependencies

---

## MANDATORY CLEANUP FOLDER STRUCTURE

A global cleanup folder must exist and must never be cleaned up itself.

```
/cleanup
  /runs
    /<timestamp>
      cleanup_report.json
      cleanup_report.md
      deleted_files.log
      archived_files.log
```

**Rules:**

* One folder per cleanup run
* Timestamp format: YYYY-MM-DD_HH-MM-SS
* Cleanup runs are immutable (no overwrite, append‑only history)

---

## FILE CATEGORIES (STRICT ENUM)

Each file must be assigned exactly one category:

* SOURCE_CODE
* CONFIG
* PROMPT
* INPUT_DATA
* INTERMEDIATE_ARTIFACT
* GENERATED_OUTPUT
* LOG_FILE
* TEMP_FILE
* EXPERIMENT
* UNKNOWN

**UNKNOWN is allowed but must result in REVIEW_REQUIRED.**

---

## DECISION TYPES (STRICT ENUM)

Each file must have exactly one decision:

* DELETE_SAFE
* KEEP_REQUIRED
* REVIEW_REQUIRED

**There is no skip or undecided state.**

---

## RULES FOR DELETE_SAFE

A file may only be deleted if ALL conditions are true:

* Category is one of:
  * TEMP_FILE
  * LOG_FILE
  * INTERMEDIATE_ARTIFACT
* File path is within:
  * /tmp
  * /logs
  * /data/intermediate
* File age exceeds configured threshold (default: 14 days)
* No reference found in:
  * Source code
  * Config files
  * Manifest files
* File is not listed as a required output artifact
* **Confidence >= 0.95**

**If ANY rule is not met → REVIEW_REQUIRED or KEEP_REQUIRED**

---

## PER-FILE ANALYSIS OBJECT (REQUIRED)

For every single file, generate an analysis object:

```json
{
  "file_path": "",
  "category": "",
  "last_modified": "",
  "size_kb": 0,
  "decision": "",
  "confidence": 0.0,
  "reasoning": [
    ""
  ],
  "risk_assessment": "",
  "recommended_action": ""
}
```

**Rules:**

* reasoning must be a list of concrete observations
* risk_assessment must explain what could break
* recommended_action must be explicit and actionable

---

## MANDATORY EXPLANATION FOR REVIEW_REQUIRED

If decision = REVIEW_REQUIRED, you MUST:

* Explain why the decision is uncertain
* Explain the dependency risk
* Explain what would happen if the file were deleted
* Provide a clear recommendation (archive, wait, verify regeneration, etc.)

**Assume the human reviewer cannot assess code dependencies themselves.**

---

## OUTPUT FILES

### 1. cleanup_report.json

* Full per‑file analysis
* Machine readable
* Includes run metadata and summary

**Schema:**
```json
{
  "metadata": {
    "timestamp": "2026-01-23T14:30:00Z",
    "mode": "analyze",
    "total_files": 0,
    "summary": {
      "delete_safe": 0,
      "keep_required": 0,
      "review_required": 0
    }
  },
  "files": [
    {
      "file_path": "",
      "category": "",
      "decision": "",
      "confidence": 0.0,
      ...
    }
  ]
}
```

### 2. cleanup_report.md

* Human readable
* Includes:
  * Summary counts per decision type
  * Table of REVIEW_REQUIRED files
  * Clear, non‑vague wording

### 3. deleted_files.log

* One file per line
* Timestamp, path, size
* Apply mode only

### 4. archived_files.log

* One file per line
* Original path, archive path
* Apply mode only

---

## EXECUTION MODES

The cleanup function must support two modes:

### MODE: analyze

* No filesystem changes allowed
* Only analysis and report generation
* Safe to run anytime
* Generates reports in /cleanup/runs/<timestamp>/

### MODE: apply

* Uses the most recent analyze report
* May delete DELETE_SAFE files only
* May archive REVIEW_REQUIRED files if configured
* Must never delete KEEP_REQUIRED or REVIEW_REQUIRED files
* Must log all deletions
* Requires safety confirmations

---

## FORBIDDEN ACTIONS

You must never:

* ❌ Guess dependencies without explanation
* ❌ Delete files with confidence < 0.95
* ❌ Modify application source code
* ❌ Clean during active application runs
* ❌ Remove cleanup history
* ❌ Use vague language like "probably unused" without justification

---

## GUIDING PRINCIPLE

**When in doubt: preserve and explain.**

A false positive deletion is worse than keeping clutter.

---

## Implementation Notes

### Technology Stack
* Python 3.10+
* Built into: `scripts/cleanup/` module
* No external dependencies required
* Standard library only: os, json, pathlib, datetime, typing

### Key Functions (Expected)
```python
def classify_file(path: str) -> FileCategory
def analyze_file(path: str) -> FileAnalysis
def apply_decision_rules(analysis: FileAnalysis) -> DecisionType
def run_cleanup(mode: str = "analyze", config: CleanupConfig = None) -> CleanupReport
def generate_json_report(results: List[FileAnalysis]) -> str
def generate_markdown_report(results: List[FileAnalysis]) -> str
```

### Configuration Schema
```python
@dataclass
class CleanupConfig:
    age_threshold_days: int = 14
    confidence_threshold: float = 0.95
    protected_paths: List[str] = None
    required_artifacts: List[str] = None
    max_deletion_size_mb: float = 100.0
```

---

## Success Criteria

✅ All file categories classified correctly
✅ All decision rules applied consistently
✅ Confidence >= 0.95 for DELETE_SAFE only
✅ 100% explanation for REVIEW_REQUIRED files
✅ Zero false positive deletions
✅ All reports generated in correct format
✅ Full test coverage (unit + integration)
✅ Complete documentation with examples
✅ No forbidden actions possible
✅ Cleanup history preserved

---

## Reference

This document is extracted from the original requirement.

**Last Updated:** 2026-01-23  
**Feature Branch:** feature/structured_cleanup
