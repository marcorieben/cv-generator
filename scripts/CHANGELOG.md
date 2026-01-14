2026-01-05 17:19:20 | CHORE | update scripts/requirements.txt
2026-01-05 17:22:55 | UI | enhance changelog with expandable commit details
2026-01-05 17:24:42 | UI | use full timestamp in changelog history
2026-01-07 09:03:00 | FEATURE | enhance CV extraction completeness, harden matchmaking criteria & finalize offer table layout
2026-01-07 16:10:57 | REFACTOR | Harmonize status values across Dashboard and Word, update criteria table layout, and refine document styling and correspondence formatting
2026-01-07 16:20:23 | REFACTOR | Harmonize status values across Dashboard and Word, update criteria table layout, and refine document styling and correspondence formatting
2026-01-07 16:37:10 | DOCS | add roadmap for multi-language support (DE/EN/FR)
2026-01-07 17:56:54 | FEATURE | finalize localization, fix app initialization crash and update language selectors to DE/EN/FR codes
2026-01-07 17:57:30 | CHORE | update changelog
2026-01-07 17:59:26 | UI | add detailed info to changelog for multi-language update
2026-01-14 07:16:49 | BUGFIX | skip merge commits in changelog updates to keep branches synchronized
2026-01-14 08:44:52 | FEATURE | add Mode 4 (Batch Comparison) UI with multi-file CV uploader
2026-01-14 08:49:38 | FEATURE | add batch results display module with dashboard and expanders
2026-01-14 08:54:55 | FEATURE | add shortlist functionality, test mode, and UI improvements for batch
2026-01-14 08:56:05 | FEATURE | complete Mode 4 (Batch Comparison) implementation
2026-01-14 09:01:59 | BUGFIX | add missing batch_comparison.py module for batch processing orchestration
2026-01-14 09:05:01 | IMPROVE | enhance batch processing error reporting and partial success handling
2026-01-14 09:06:15 | DOCS | add batch error handling guide and update TODO documentation
2026-01-14 09:12:39 | BUGFIX | correct batch processing pipeline output mapping and file pointer handling
2026-01-14 09:20:34 | IMPROVE | add detailed batch processing diagnostics and progress tracking
2026-01-14 09:22:42 | BUGFIX | reset job_file pointer before reading in batch comparison
2026-01-14 09:33:24 | BUGFIX | implement correct batch mode architecture - process stellenprofil PDF first
2026-01-14 09:55:26 | REFACTOR | per-candidate dashboards now identical to Mode 2/3, remove shortlist button
2026-01-14 10:09:54 | REFACTOR | unified file naming convention across all modes (2, 3, 4)
2026-01-14 10:13:39 | FEATURE | batch runs now visible in history with batch folder details
2026-01-14 10:33:14 | REFACTOR | implement nested batch folder structure with dynamic naming
2026-01-14 10:33:57 | DOCS | add Phase 8 implementation documentation
2026-01-14 10:34:46 | DOCS | add comprehensive Mode 4 completion summary
2026-01-14 10:36:17 | DOCS | add completion summary for Mode 4 implementation
2026-01-14 10:36:46 | DOCS | completion summary for Mode 4 implementation
2026-01-14 10:44:44 | BUGFIX | correct dashboard path key in batch results
2026-01-14 10:49:11 | REFACTOR | batch runs now display as single history entry with all candidate results
2026-01-14 10:57:46 | BUGFIX | remove UploadedFile object from batch results to prevent JSON serialization error
2026-01-14 11:11:21 | FEATURE | implement dynamic naming for Mode 3 folder structure
2026-01-14 12:18:02 | BUGFIX | skip pipeline rerun when loading Mode 3 results from history
2026-01-14 12:26:05 | BUGFIX | prevent pipeline rerun when viewing results in Mode 3
