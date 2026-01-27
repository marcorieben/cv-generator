"""
RunWorkspace - Lightweight workspace for single pipeline run.

Purpose:
    Provides isolated storage for each pipeline execution with automatic cleanup.
    Railway-ready (tempfile-based), Supabase-swappable in future.

Expected Lifetime: Core Module (Stable)

Architecture:
    - Uses Python's tempfile for automatic cleanup
    - Two-folder structure: primary_outputs/ and artifacts/
    - Methods for saving, retrieving, and bundling files

Usage:
    workspace = RunWorkspace(run_id)
    workspace.save_primary("cv.docx", cv_bytes)
    zip_bytes = workspace.bundle_as_zip()
"""

from pathlib import Path
import tempfile
import zipfile
from io import BytesIO
from typing import Optional


class RunWorkspace:
    """
    Lightweight workspace for single pipeline run.
    Railway-ready (tempfile), Supabase-swappable later.
    """
    
    def __init__(self, run_id: str):
        """
        Initialize workspace with unique run ID.
        
        Args:
            run_id: Unique identifier for this run (e.g., "Senior-Java-Developer_Marco-Rieben_20260127-142305")
        """
        self.run_id = run_id
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name) / run_id
        self.root.mkdir(parents=True, exist_ok=True)
        
        # Two subdirectories: primary outputs (user-facing) and artifacts (technical)
        self.primary_outputs = self.root / "primary_outputs"
        self.artifacts = self.root / "artifacts"
        self.primary_outputs.mkdir(exist_ok=True)
        self.artifacts.mkdir(exist_ok=True)
    
    def save_primary(self, filename: str, content: bytes) -> Path:
        """
        Save user-facing output (CV, Offer, Dashboard).
        
        Args:
            filename: Name of file to save
            content: File content as bytes
            
        Returns:
            Path to saved file
        """
        path = self.primary_outputs / filename
        path.write_bytes(content)
        return path
    
    def save_artifact(self, filename: str, content: bytes) -> Path:
        """
        Save technical artifact (JSON, logs, reports).
        
        Args:
            filename: Name of file to save
            content: File content as bytes
            
        Returns:
            Path to saved file
        """
        path = self.artifacts / filename
        path.write_bytes(content)
        return path
    
    def get_primary(self, filename: str) -> bytes:
        """
        Retrieve individual primary file (for dashboard download buttons).
        
        Args:
            filename: Name of file to retrieve
            
        Returns:
            File content as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = self.primary_outputs / filename
        return path.read_bytes()
    
    def get_artifact(self, filename: str) -> bytes:
        """
        Retrieve individual artifact file.
        
        Args:
            filename: Name of file to retrieve
            
        Returns:
            File content as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = self.artifacts / filename
        return path.read_bytes()
    
    def list_primary_files(self) -> list[str]:
        """
        List all primary output files.
        
        Returns:
            List of filenames
        """
        return [f.name for f in self.primary_outputs.iterdir() if f.is_file()]
    
    def list_artifact_files(self) -> list[str]:
        """
        List all artifact files.
        
        Returns:
            List of filenames
        """
        return [f.name for f in self.artifacts.iterdir() if f.is_file()]
    
    def bundle_as_zip(self) -> bytes:
        """
        Create ZIP of entire workspace for download.
        
        Returns:
            ZIP file content as bytes
        """
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in self.root.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(self.root)
                    zf.write(file, arcname)
        buffer.seek(0)
        return buffer.read()
    
    def cleanup(self):
        """
        Cleanup tempdir (automatic on Railway container exit).
        Explicitly calling this is optional - Python GC handles it.
        """
        self._tempdir.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup()
        return False
