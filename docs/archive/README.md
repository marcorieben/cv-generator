# Documentation Archive

This folder contains historical documentation and implementation details for previous development phases.

## Contents

### Mode 4 Implementation (Archived - Phase 3)
These documents describe the Mode 4 (Batch Comparison) implementation which has since been consolidated into the Advanced mode.

- **MODE_4_COMPLETE_SUMMARY.md** - Complete implementation summary for Mode 4 batch processing
- **PHASE_8_NESTED_BATCH_STRUCTURE.md** - Technical details on nested folder structure
- **MODE_4_BATCH_COMPARISON.md** - Batch comparison feature requirements and todos

### Dialog System Documentation (Archived - Superseded by DIALOGS_REFERENCE.md)
Older dialog documentation that has been superseded by the comprehensive `docs/DIALOGS_REFERENCE.md` and quick reference `docs/DIALOGS_QUICKREF.md`.

- **DIALOGS.md** - Original dialog documentation (see docs/DIALOGS_REFERENCE.md for current version)
- **DIALOG_UPDATE_SUMMARY.md** - Migration guide for modern dialog system (historical reference)
- **DIALOG_VISUAL_REFERENCE.md** - Visual mockups of dialog layouts (historical reference)

### Why Archived?

**Mode 4:** As of Phase 3 (January 2026), the CV Generator was refactored from a 3-mode architecture (Basic, Analysis, Full) to a 2-mode architecture (Basic, Advanced). The Mode 4 functionality has been integrated into the Advanced mode.

**Dialog Docs:** The dialog system documentation was consolidated into a single authoritative source (`docs/DIALOGS_REFERENCE.md`) to avoid duplication and confusion. The quick reference guide (`docs/DIALOGS_QUICKREF.md`) provides navigation and quick lookup.

### What Should Be Used Instead

- **For Dialog System:** See `/docs/DIALOGS_REFERENCE.md` (main reference) and `/docs/DIALOGS_QUICKREF.md` (quick navigation)
- **For Architecture:** See `/docs/ARCHITECTURE.md` for current 2-mode system
- **For Batch Processing:** Refer to the Advanced mode documentation and `/scripts/batch_comparison.py`

### Reference

These documents remain valuable as reference material for understanding:
- Historical development decisions
- Previous implementation approaches
- Git history and evolution of the project
- Batch processing architecture details
- File naming conventions

**Current Documentation:** See main documentation in `/docs/` for current architecture and features.
