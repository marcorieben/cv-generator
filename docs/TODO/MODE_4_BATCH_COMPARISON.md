# Mode 4: Batch Comparison – Implementation TODO

**Status:** In Progress  
**Branch:** `feature/batch-comparison-mode`  
**Base Branch:** `development`  
**Created:** 2026-01-14  

## Overview
Implement Mode 4 (Batch Comparison): Upload one job profile and multiple CVs, process each CV, generate comparison dashboard, and enable per-candidate offer creation.

---

## UI & Layout
- [ ] Add Batch Comparison (Mode 4) UI with mode selector button
- [ ] Implement multi-file CV uploader for Batch mode
- [ ] Add single job profile uploader (required, not disabled)

## Processing & Batch Logic
- [ ] Create batch runner integration with run_batch_comparison()
- [ ] Implement processing status/progress UI for batch runs
- [ ] Create mock Batch mode with 2-3 realistic CVs and 1 job profile
- [ ] Implement Test Mode button for batch runs

## Comparison Dashboard (Strict Order)
- [ ] Create `create_batch_comparison_dashboard()` with 3-panel layout
  - Frame 1: Total Match Score (vertical bar, best=green, others=grey)
  - Frame 2: Muss/Soll Coverage (stacked bar per candidate)
  - Frame 3: CV Quality/Critical Points (bar chart)
- [ ] Build criteria table (strict from job profile, Muss/Soll clustered)

## Per-Candidate Results
- [ ] Implement per-candidate expanders with full dashboards
- [ ] Add download CV and offer creation per candidate
- [ ] Implement orange badge for offer-ready state
- [ ] Add shortlist button and persistent shortlist state

## File Persistence & Dependencies
- [ ] Implement dynamic file dependency resolution (no hardcoded paths)
- [ ] Persist batch outputs with naming convention: `jobprofile_batch-comparison_timestamp`
- [ ] Persist candidate outputs: `jobprofile_candidateName_timestamp`
- [ ] Store all required files (CV JSON, Word, feedback, match, dashboard, stellenprofil)
- [ ] Make batch runs fully re-openable from history

## Validation & Testing
- [ ] Validate no regressions in modes 1-3
- [ ] End-to-end test of Mode 4 in mock and production

## Finalization
- [ ] Commit Mode 4 implementation to feature branch

---

## Key Requirements (from spec)
- **Input Layout:** Reuse exact layout from Mode 2/3
- **Processing:** Run full CV analysis per file using Mode 2/3 logic
- **Colouring:** Consistent per candidate (best=green, others=grey)
- **Criteria Table:** No mock data when real job profile exists
- **Naming Convention:**
  - Batch folder: `jobprofile_batch-comparison_timestamp`
  - Per-candidate: `jobprofile_candidateName_timestamp`
- **History:** Fully re-openable, restores comparison + candidate dashboards
- **Test Mode:** 2–3 realistic mock CVs + 1 job profile

---

## Notes
- Modes 1–3 remain unchanged (no regressions)
- All internal references must resolve dynamically
- Offer generation uses batch analysis results
- Batch progress shown during processing
