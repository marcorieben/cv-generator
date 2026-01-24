"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime


class FileCategory(str, Enum):
    """10-category classification for all files in the project."""

    SOURCE_CODE = "SOURCE_CODE"
    CONFIG = "CONFIG"
    PROMPT = "PROMPT"
    INPUT_DATA = "INPUT_DATA"
    INTERMEDIATE_ARTIFACT = "INTERMEDIATE_ARTIFACT"
    GENERATED_OUTPUT = "GENERATED_OUTPUT"
    LOG_FILE = "LOG_FILE"
    TEMP_FILE = "TEMP_FILE"
    EXPERIMENT = "EXPERIMENT"
    UNKNOWN = "UNKNOWN"


class DecisionType(str, Enum):
    """3-decision classification for cleanup actions."""

    DELETE_SAFE = "DELETE_SAFE"
    KEEP_REQUIRED = "KEEP_REQUIRED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"




@dataclass
class ReferenceInfo:
    """Information about a file reference."""

    file_path: str  # File that contains the reference
    line_number: int  # Line number where reference occurs
    context: str  # Code/text context around the reference
    is_indirect: bool = False  # True if indirect (e.g., dynamic import)
    reference_type: str = "direct"  # "direct", "import", "include", "call", etc.


@dataclass
class FileAnalysis:
    """Per-file analysis object with decision and reasoning."""

    file_path: str
    category: FileCategory
    last_modified: str  # ISO format
    size_kb: float
    decision: DecisionType
    confidence: float  # 0.0 - 1.0
    reasoning: List[str] = field(default_factory=list)  # Why this decision
    risk_assessment: str = ""  # What could break if deleted
    recommended_action: str = ""  # What to do next
    references: List[ReferenceInfo] = field(default_factory=list)  # Where is this file referenced
    file_purpose: str = ""  # Purpose extracted from header comment
    expected_lifetime: str = ""  # "temporary" or "permanent" from header
    created_date: str = ""  # Creation date from header (YYYY-MM-DD)
    last_updated_date: str = ""  # Last update date from header (YYYY-MM-DD)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "category": self.category.value,
            "last_modified": self.last_modified,
            "size_kb": round(self.size_kb, 2),
            "decision": self.decision.value,
            "confidence": round(self.confidence, 2),
            "reasoning": self.reasoning,
            "risk_assessment": self.risk_assessment,
            "recommended_action": self.recommended_action,
            "file_purpose": self.file_purpose,
            "expected_lifetime": self.expected_lifetime,
            "created_date": self.created_date,
            "last_updated_date": self.last_updated_date,
            "reference_count": len(self.references),
            "direct_references": len([r for r in self.references if not r.is_indirect]),
            "indirect_references": len([r for r in self.references if r.is_indirect]),
        }


@dataclass
class CleanupConfig:
    """Configuration for cleanup behavior."""

    age_threshold_days: int = 14
    confidence_threshold: float = 0.95
    protected_paths: List[str] = field(
        default_factory=lambda: [
            "/cleanup",
            "/scripts",
            "/tests",
            "/.git",
            "/.venv",
            "/docs",
            "/core",
        ]
    )
    required_artifacts: List[str] = field(
        default_factory=lambda: [
            "requirements.txt",
            "pytest.ini",
            "config.yaml",
            "app.py",
        ]
    )
    max_deletion_size_mb: float = 100.0


@dataclass
class CleanupReport:
    """Complete cleanup run report."""

    run_id: str  # Timestamp: YYYY-MM-DD_HH-MM-SS
    mode: str  # "analyze" or "apply"
    timestamp: str  # ISO format
    total_files: int
    files: List[FileAnalysis] = field(default_factory=list)

    @property
    def summary(self) -> dict:
        """Summary counts by decision type."""
        return {
            "delete_safe": sum(
                1 for f in self.files if f.decision == DecisionType.DELETE_SAFE
            ),
            "keep_required": sum(
                1 for f in self.files if f.decision == DecisionType.KEEP_REQUIRED
            ),
            "review_required": sum(
                1 for f in self.files if f.decision == DecisionType.REVIEW_REQUIRED
            ),
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": {
                "run_id": self.run_id,
                "mode": self.mode,
                "timestamp": self.timestamp,
                "total_files": self.total_files,
                "summary": self.summary,
            },
            "files": [f.to_dict() for f in self.files],
        }
