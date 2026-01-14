# CV Generator Roadmap

**Last Updated:** 2026-01-14

## Vision
Build a comprehensive, modular CV analysis and matching platform with batch processing, real-time pipeline orchestration, and offer generation capabilities.

---

## Completed Milestones ✅

### Phase 0: Foundation (Complete)
- ✅ Core CV extraction (PDF → JSON via OpenAI)
- ✅ CV document generation (JSON → Word with complex table layouts)
- ✅ Modes 1–3 (Basic, Analysis, Full)
- ✅ Job profile parsing and schema validation
- ✅ Git workflow setup (main, development, test branches)
- ✅ Post-commit hook CHANGELOG automation

### Phase 1: Process Improvement (Complete)
- ✅ CHANGELOG automation to skip merge commits (keep branches synchronized)
- ✅ Unified pipeline configuration via config.yaml
- ✅ Unit test suite (45 tests, all passing)
- ✅ Pre-commit hooks for lint/format validation
- ✅ Documentation (ARCHITECTURE.md, SETUP.md, TESTING.md)

---

## Active Work 🚀

### Phase 2: Batch Processing (In Progress)
**Branch:** `feature/batch-comparison-mode`

- Upload multiple CVs + 1 job profile
- Process all CVs in batch, show comparison dashboard
- Per-candidate offer creation
- Persistent batch storage with re-openable history
- Mock Mode for testing without API calls

**Target:** Complete by [TBD]

---

## Planned Milestones 📋

### Phase 3: Advanced Matching (Backlog)
- Skill gap analysis (required vs. detected)
- Weighted scoring by job profile criticality
- Candidate ranking algorithms
- Export reports (PDF/Excel)

### Phase 4: Deployment & Scale (Backlog)
- Docker containerization
- Cloud hosting (AWS/GCP)
- Multi-user authentication
- Batch API for enterprise customers

### Phase 5: AI Enhancements (Backlog)
- Fine-tuning extraction model on customer data
- Contextual offer generation (salary bands, role responsibilities)
- Interview question suggestions based on CV gaps

---

## Known Limitations & Debt

| Issue | Priority | Notes |
|-------|----------|-------|
| `use_container_width` deprecation | Low | Streamlit warnings; cosmetic only |
| Batch persistence file structure | Medium | May need refactoring for 100+ candidate batches |
| Mock data hardcoding | Low | Centralize mock datasets in separate module |

---

## How to Use This Roadmap
1. **Quarterly Planning:** Use this to prioritize phases and estimate effort
2. **Sprint Planning:** Break down active phases into 2-week tasks (see MODE_4_BATCH_COMPARISON.md for detailed checklist)
3. **Status Updates:** Update milestone checkboxes after completion; add new issues as they emerge
4. **Backlog Refinement:** Move items from Backlog → Active → Complete as priorities shift

---

## Quick Links
- [Mode 4 Implementation Checklist](./MODE_4_BATCH_COMPARISON.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [GitHub Issues](https://github.com/[repo])
