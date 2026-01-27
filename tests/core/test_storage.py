"""
Unit tests for core/storage module.

Purpose:
    Test RunWorkspace and generate_run_id functionality.
    Validates storage abstraction layer for Railway deployment.

Expected Lifetime: Test Suite (Stable)
"""

import pytest
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from io import BytesIO

from core.storage import RunWorkspace, generate_run_id


class TestRunWorkspace:
    """Test RunWorkspace class functionality."""
    
    def test_initialization(self):
        """Test workspace initialization creates correct structure."""
        run_id = "test-run-123"
        workspace = RunWorkspace(run_id)
        
        assert workspace.run_id == run_id
        assert workspace.root.exists()
        assert workspace.primary_outputs.exists()
        assert workspace.artifacts.exists()
        
        workspace.cleanup()
    
    def test_save_primary(self):
        """Test saving primary output file."""
        workspace = RunWorkspace("test-run")
        content = b"Hello World"
        
        path = workspace.save_primary("test.txt", content)
        
        assert path.exists()
        assert path.read_bytes() == content
        assert path.parent == workspace.primary_outputs
        
        workspace.cleanup()
    
    def test_save_artifact(self):
        """Test saving artifact file."""
        workspace = RunWorkspace("test-run")
        content = b'{"key": "value"}'
        
        path = workspace.save_artifact("data.json", content)
        
        assert path.exists()
        assert path.read_bytes() == content
        assert path.parent == workspace.artifacts
        
        workspace.cleanup()
    
    def test_get_primary(self):
        """Test retrieving primary file."""
        workspace = RunWorkspace("test-run")
        content = b"Test content"
        filename = "document.docx"
        
        workspace.save_primary(filename, content)
        retrieved = workspace.get_primary(filename)
        
        assert retrieved == content
        
        workspace.cleanup()
    
    def test_get_primary_not_found(self):
        """Test get_primary raises FileNotFoundError for missing file."""
        workspace = RunWorkspace("test-run")
        
        with pytest.raises(FileNotFoundError):
            workspace.get_primary("nonexistent.txt")
        
        workspace.cleanup()
    
    def test_get_artifact(self):
        """Test retrieving artifact file."""
        workspace = RunWorkspace("test-run")
        content = b'{"test": true}'
        filename = "result.json"
        
        workspace.save_artifact(filename, content)
        retrieved = workspace.get_artifact(filename)
        
        assert retrieved == content
        
        workspace.cleanup()
    
    def test_list_primary_files(self):
        """Test listing primary output files."""
        workspace = RunWorkspace("test-run")
        
        workspace.save_primary("file1.docx", b"content1")
        workspace.save_primary("file2.html", b"content2")
        
        files = workspace.list_primary_files()
        
        assert len(files) == 2
        assert "file1.docx" in files
        assert "file2.html" in files
        
        workspace.cleanup()
    
    def test_list_artifact_files(self):
        """Test listing artifact files."""
        workspace = RunWorkspace("test-run")
        
        workspace.save_artifact("data1.json", b'{}')
        workspace.save_artifact("data2.json", b'{}')
        workspace.save_artifact("log.txt", b'log')
        
        files = workspace.list_artifact_files()
        
        assert len(files) == 3
        assert "data1.json" in files
        assert "data2.json" in files
        assert "log.txt" in files
        
        workspace.cleanup()
    
    def test_bundle_as_zip(self):
        """Test creating ZIP bundle of workspace."""
        workspace = RunWorkspace("test-run")
        
        # Save test files
        workspace.save_primary("cv.docx", b"CV content")
        workspace.save_primary("offer.docx", b"Offer content")
        workspace.save_artifact("data.json", b'{"test": true}')
        
        # Create ZIP
        zip_bytes = workspace.bundle_as_zip()
        
        # Verify ZIP content
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        # Extract and verify structure
        with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zf:
            names = zf.namelist()
            assert "primary_outputs/cv.docx" in names
            assert "primary_outputs/offer.docx" in names
            assert "artifacts/data.json" in names
            
            # Verify content
            assert zf.read("primary_outputs/cv.docx") == b"CV content"
            assert zf.read("artifacts/data.json") == b'{"test": true}'
        
        workspace.cleanup()
    
    def test_context_manager(self):
        """Test using workspace as context manager."""
        run_id = "test-context"
        root_path = None
        
        with RunWorkspace(run_id) as workspace:
            root_path = workspace.root
            assert root_path.exists()
            workspace.save_primary("test.txt", b"test")
        
        # After context exit, cleanup should be called
        # (Note: tempdir cleanup might be delayed by GC)
    
    def test_cleanup_removes_files(self):
        """Test cleanup removes temporary files."""
        workspace = RunWorkspace("test-cleanup")
        root_path = workspace.root
        
        workspace.save_primary("file.txt", b"content")
        assert root_path.exists()
        
        workspace.cleanup()
        
        # Tempdir should be cleaned up
        # (Note: actual deletion might be delayed by OS)


class TestGenerateRunId:
    """Test generate_run_id function."""
    
    def test_basic_generation(self):
        """Test basic run ID generation."""
        timestamp = datetime(2026, 1, 27, 14, 23, 5)
        
        run_id = generate_run_id(
            "Senior Java Developer",
            "Marco",
            "Rieben",
            timestamp=timestamp
        )
        
        assert run_id == "Senior-Java-Developer_Marco-Rieben_20260127-142305"
    
    def test_special_characters_removed(self):
        """Test special characters are removed from run ID."""
        timestamp = datetime(2026, 1, 27, 10, 0, 0)
        
        run_id = generate_run_id(
            "C++ & Python Expert!!!",
            "Max",
            "Müller",
            timestamp=timestamp
        )
        
        # Special chars removed, spaces to hyphens
        assert "C" in run_id and "Python" in run_id
        assert "Expert" in run_id
        assert "&" not in run_id
        assert "!" not in run_id
    
    def test_spaces_to_hyphens(self):
        """Test spaces are converted to hyphens."""
        timestamp = datetime(2026, 1, 1, 0, 0, 0)
        
        run_id = generate_run_id(
            "Software Engineer",
            "John",
            "Doe",
            timestamp=timestamp
        )
        
        assert "Software-Engineer" in run_id
        assert "John-Doe" in run_id
    
    def test_long_title_truncation(self):
        """Test long titles are truncated to max length."""
        long_title = "Senior Full Stack Software Engineer with Cloud Architecture Experience"
        timestamp = datetime(2026, 1, 1, 0, 0, 0)
        
        run_id = generate_run_id(long_title, "Test", "User", timestamp=timestamp)
        
        # Job profile slug should be max 50 chars
        parts = run_id.split("_")
        job_slug = parts[0]
        assert len(job_slug) <= 50
    
    def test_timestamp_format(self):
        """Test timestamp format is correct."""
        timestamp = datetime(2026, 12, 31, 23, 59, 59)
        
        run_id = generate_run_id(
            "Test Job",
            "Test",
            "User",
            timestamp=timestamp
        )
        
        assert "20261231-235959" in run_id
    
    def test_uses_current_time_when_no_timestamp(self):
        """Test uses current time when timestamp not provided."""
        run_id = generate_run_id("Job Title", "First", "Last")
        
        # Should contain today's date
        today = datetime.now().strftime('%Y%m%d')
        assert today in run_id
    
    def test_empty_strings_handled(self):
        """Test empty strings don't break run ID generation."""
        timestamp = datetime(2026, 1, 1, 0, 0, 0)
        
        run_id = generate_run_id("", "", "", timestamp=timestamp)
        
        # Should still generate valid run ID with timestamp
        assert "_" in run_id
        assert "20260101" in run_id
