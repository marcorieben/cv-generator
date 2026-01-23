"""
Cleanup System Module

Safe, explainable file cleanup for the CV Generator project.
Analyzes, classifies, and optionally deletes files with full traceability.

Main exports:
- FileCategory: Enum of 10 file categories
- DecisionType: Enum of 3 decision types
- FileAnalysis: Per-file analysis object
- CleanupConfig: Configuration dataclass
- run_cleanup(): Main cleanup orchestration function

Usage:
    from scripts.cleanup import run_cleanup, CleanupConfig
    
    # Analyze only (safe, no changes)
    report = run_cleanup(mode="analyze")
    
    # Apply cleanup (requires confirmation)
    report = run_cleanup(mode="apply")
"""

from scripts.cleanup.models import (
    FileCategory,
    DecisionType,
    FileAnalysis,
    CleanupConfig,
    CleanupReport,
)
from scripts.cleanup.executor import run_cleanup

__all__ = [
    "FileCategory",
    "DecisionType",
    "FileAnalysis",
    "CleanupConfig",
    "CleanupReport",
    "run_cleanup",
]

__version__ = "0.1.0"
