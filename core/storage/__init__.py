"""
Storage abstraction layer for CV Generator pipelines.

Purpose:
    Railway-ready storage with ephemeral filesystem support.
    Provides RunWorkspace for isolated pipeline runs with automatic cleanup.

Expected Lifetime: Core Module (Stable)

Public API:
    - RunWorkspace: Main workspace class for pipeline runs
    - generate_run_id: Create business-meaningful run identifiers
"""

from .workspace import RunWorkspace
from .run_id import generate_run_id

__all__ = ["RunWorkspace", "generate_run_id"]
