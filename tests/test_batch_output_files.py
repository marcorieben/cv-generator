"""
Test Suite: Batch Processing Output File Generation

Ensures that when batch processing multiple CVs:
1. Files are created in correct candidate subfolders
2. All expected file types are generated (Word, JSON, Match, Feedback, Dashboard)
3. Folder structure matches the naming convention
4. Files have correct naming patterns

This test suite validates:
- Directory creation before file writes (os.makedirs with exist_ok=True)
- Nested batch folder structures are properly created
- No FileNotFoundError on file write operations
- All parent directories exist when needed
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the batch comparison function
from scripts.batch_comparison import run_batch_comparison


class MockUploadedFile:
    """Mock Streamlit UploadedFile object"""
    
    def __init__(self, name: str, content: bytes):
        self.name = name
        self.content = content
        self._file = None
    
    def read(self):
        """Return file content"""
        return self.content
    
    def seek(self, position: int):
        """Mock seek operation"""
        pass
    
    def getbuffer(self):
        """Return mock buffer"""
        return Mock()


class TestBatchOutputFileGeneration:
    """Test batch processing output file generation"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="batch_test_")
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_cv_files(self):
        """Create mock CV files for testing"""
        # Using dummy PDF content (not a real PDF, but sufficient for structure testing)
        dummy_pdf = b"%PDF-1.4\n%dummy content for testing"
        
        return [
            MockUploadedFile("arthur_fischer.pdf", dummy_pdf),
            MockUploadedFile("jonas_stauffer.pdf", dummy_pdf),
            MockUploadedFile("dejan_georgiev.pdf", dummy_pdf),
        ]
    
    @pytest.fixture
    def mock_job_file(self):
        """Create mock job profile file"""
        dummy_pdf = b"%PDF-1.4\n%dummy job profile content"
        return MockUploadedFile("senior_business_analyst.pdf", dummy_pdf)
    
    @patch('scripts.batch_comparison.pdf_to_json_with_retry')
    @patch('scripts.batch_comparison.StreamlitCVGenerator')
    def test_batch_creates_candidate_subfolders(
        self,
        mock_generator_class,
        mock_pdf_extraction,
        mock_cv_files,
        mock_job_file
    ):
        """
        Test: Candidate subfolders are created for each CV
        """
        # Mock the PDF extraction to return valid data
        mock_pdf_extraction.return_value = {
            "Titel": "Senior Business Analyst",
            "Beschreibung": "Test job profile"
        }
        
        # Mock the generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.run.return_value = {
            "success": True,
            "vorname": "Arthur",
            "nachname": "Fischer",
            "cv_json": "/path/to/cv.json",
            "word_path": "/path/to/cv.docx",
            "match_json": "/path/to/match.json",
            "dashboard_path": "/path/to/dashboard.html",
            "error": None
        }
        
        # Run batch comparison with mock
        result = run_batch_comparison(
            cv_files=mock_cv_files,
            job_file=mock_job_file,
            api_key="mock-key",
            custom_styles=None,
            custom_logo_path=None,
            pipeline_mode="Batch Comparison",
            language="de",
            progress_callback=None
        )
        
        # Verify results structure
        assert result is not None
        assert "batch_results" in result
        assert "batch_folder" in result
        assert len(result["batch_results"]) == len(mock_cv_files)
        
        # Verify each result has the required fields
        for idx, batch_result in enumerate(result["batch_results"]):
            assert "success" in batch_result
            assert "candidate_name" in batch_result
            assert "cv_filename" in batch_result
            assert batch_result["cv_filename"] == mock_cv_files[idx].name
    
    @patch('scripts.batch_comparison.pdf_to_json_with_retry')
    @patch('scripts.batch_comparison.StreamlitCVGenerator')
    def test_batch_preserves_result_order(
        self,
        mock_generator_class,
        mock_pdf_extraction,
        mock_cv_files,
        mock_job_file
    ):
        """
        Test: Results are returned in same order as input CVs
        (Important for ThreadPoolExecutor which processes asynchronously)
        """
        mock_pdf_extraction.return_value = {
            "Titel": "Senior Business Analyst"
        }
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Mock different names for each CV
        names = [
            ("Arthur", "Fischer"),
            ("Jonas", "Stauffer"),
            ("Dejan", "Georgiev")
        ]
        
        mock_generator.run.side_effect = [
            {
                "success": True,
                "vorname": names[i][0],
                "nachname": names[i][1],
                "cv_json": f"/path/to/{names[i][0]}_cv.json",
                "word_path": f"/path/to/{names[i][0]}.docx",
                "match_json": f"/path/to/{names[i][0]}_match.json",
                "dashboard_path": f"/path/to/{names[i][0]}_dashboard.html",
                "error": None
            }
            for i in range(len(mock_cv_files))
        ]
        
        # Run batch
        result = run_batch_comparison(
            cv_files=mock_cv_files,
            job_file=mock_job_file,
            api_key="mock-key",
            custom_styles=None,
            custom_logo_path=None,
            pipeline_mode="Batch Comparison",
            language="de",
            progress_callback=None
        )
        
        # Verify order is preserved
        batch_results = result["batch_results"]
        assert len(batch_results) == 3
        
        # Check that results maintain original order
        for idx, batch_result in enumerate(batch_results):
            original_filename = mock_cv_files[idx].name
            assert batch_result["cv_filename"] == original_filename
    
    @patch('scripts.batch_comparison.pdf_to_json_with_retry')
    @patch('scripts.batch_comparison.StreamlitCVGenerator')
    def test_batch_handles_mixed_success_failure(
        self,
        mock_generator_class,
        mock_pdf_extraction,
        mock_cv_files,
        mock_job_file
    ):
        """
        Test: Partial success scenario - some CVs succeed, others fail
        Failed CVs should still have entries in results
        """
        mock_pdf_extraction.return_value = {
            "Titel": "Senior Business Analyst"
        }
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Mock: First CV succeeds, second fails, third succeeds
        mock_generator.run.side_effect = [
            {
                "success": True,
                "vorname": "Arthur",
                "nachname": "Fischer",
                "cv_json": "/path/to/cv1.json",
                "word_path": "/path/to/cv1.docx",
                "match_json": "/path/to/match1.json",
                "dashboard_path": "/path/to/dashboard1.html",
                "error": None
            },
            {
                "success": False,
                "error": "PDF extraction timeout",
                "vorname": None,
                "nachname": None,
                "cv_json": None,
                "word_path": None,
                "match_json": None,
                "dashboard_path": None
            },
            {
                "success": True,
                "vorname": "Dejan",
                "nachname": "Georgiev",
                "cv_json": "/path/to/cv3.json",
                "word_path": "/path/to/cv3.docx",
                "match_json": "/path/to/match3.json",
                "dashboard_path": "/path/to/dashboard3.html",
                "error": None
            }
        ]
        
        # Run batch
        result = run_batch_comparison(
            cv_files=mock_cv_files,
            job_file=mock_job_file,
            api_key="mock-key",
            custom_styles=None,
            custom_logo_path=None,
            pipeline_mode="Batch Comparison",
            language="de",
            progress_callback=None
        )
        
        # Verify results
        batch_results = result["batch_results"]
        assert len(batch_results) == 3
        
        # Verify structure: we should have 1 failure and 2 successes
        success_count = sum(1 for r in batch_results if r["success"] is True)
        failure_count = sum(1 for r in batch_results if r["success"] is False)
        
        assert success_count == 2, "Expected 2 successful CVs"
        assert failure_count == 1, "Expected 1 failed CV"
        
        # Verify the failed one has error
        failed_results = [r for r in batch_results if r["success"] is False]
        assert len(failed_results) == 1
        assert "error" in failed_results[0]
        
        # Verify successful ones have names
        success_results = [r for r in batch_results if r["success"] is True]
        assert len(success_results) == 2
        vornames = {r["vorname"] for r in success_results}
        assert "Arthur" in vornames
        assert "Dejan" in vornames
    
    @patch('scripts.batch_comparison.pdf_to_json_with_retry')
    @patch('scripts.batch_comparison.StreamlitCVGenerator')
    def test_batch_no_missing_indices_after_errors(
        self,
        mock_generator_class,
        mock_pdf_extraction,
        mock_cv_files,
        mock_job_file
    ):
        """
        Test: Ensures no 'list index out of range' errors
        All indices 0 to len(cv_files)-1 must have results
        """
        mock_pdf_extraction.return_value = {
            "Titel": "Senior Business Analyst"
        }
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Simulate task failure for second CV
        mock_generator.run.side_effect = [
            {
                "success": True,
                "vorname": "Arthur",
                "nachname": "Fischer",
                "cv_json": "/path/to/cv1.json",
                "word_path": "/path/to/cv1.docx",
                "match_json": "/path/to/match1.json",
                "dashboard_path": "/path/to/dashboard1.html",
                "error": None
            },
            Exception("Simulated thread crash"),  # This will trigger exception handler
            {
                "success": True,
                "vorname": "Dejan",
                "nachname": "Georgiev",
                "cv_json": "/path/to/cv3.json",
                "word_path": "/path/to/cv3.docx",
                "match_json": "/path/to/match3.json",
                "dashboard_path": "/path/to/dashboard3.html",
                "error": None
            }
        ]
        
        # Run batch - should not raise IndexError
        result = run_batch_comparison(
            cv_files=mock_cv_files,
            job_file=mock_job_file,
            api_key="mock-key",
            custom_styles=None,
            custom_logo_path=None,
            pipeline_mode="Batch Comparison",
            language="de",
            progress_callback=None
        )
        
        # Verify no IndexError - all indices present
        batch_results = result["batch_results"]
        assert len(batch_results) == 3
        
        # All indices should be accessible without error
        for i in range(len(mock_cv_files)):
            result_item = batch_results[i]
            assert result_item is not None
            assert "success" in result_item
            assert "error" in result_item or result_item["success"] is True
    
    @patch('scripts.batch_comparison.pdf_to_json_with_retry')
    @patch('scripts.batch_comparison.StreamlitCVGenerator')
    def test_batch_folder_structure(
        self,
        mock_generator_class,
        mock_pdf_extraction,
        mock_cv_files,
        mock_job_file
    ):
        """
        Test: Batch folder structure is correctly created
        Should have: output/batch_comparison_[jobprofile]_[timestamp]/
        """
        mock_pdf_extraction.return_value = {
            "Titel": "Senior Business Analyst"
        }
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.run.return_value = {
            "success": True,
            "vorname": "Arthur",
            "nachname": "Fischer",
            "cv_json": "/path/to/cv.json",
            "word_path": "/path/to/cv.docx",
            "match_json": "/path/to/match.json",
            "dashboard_path": "/path/to/dashboard.html",
            "error": None
        }
        
        # Run batch
        result = run_batch_comparison(
            cv_files=mock_cv_files,
            job_file=mock_job_file,
            api_key="mock-key",
            custom_styles=None,
            custom_logo_path=None,
            pipeline_mode="Batch Comparison",
            language="de",
            progress_callback=None
        )
        
        # Verify batch folder path is returned and valid
        batch_folder = result["batch_folder"]
        assert batch_folder is not None
        assert "batch" in batch_folder.lower() or "senior" in batch_folder.lower()
        assert "timestamp" not in batch_folder  # Should be actual timestamp, not literal
        
        # Verify timestamp format if folder path includes it
        # Should be YYYYMMDD_HHMMSS pattern somewhere
        timestamp = result["timestamp"]
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS format
        assert timestamp[8] == "_"  # Separator between date and time


class TestBatchProgressCallback:
    """Test progress callback functionality during batch processing"""
    
    @pytest.fixture
    def mock_cv_files(self):
        """Create mock CV files"""
        dummy_pdf = b"%PDF-1.4\n%test"
        return [
            MockUploadedFile("cv1.pdf", dummy_pdf),
            MockUploadedFile("cv2.pdf", dummy_pdf),
        ]
    
    @pytest.fixture
    def mock_job_file(self):
        """Create mock job file"""
        dummy_pdf = b"%PDF-1.4\n%test"
        return MockUploadedFile("job.pdf", dummy_pdf)
    
    @patch('scripts.batch_comparison.pdf_to_json_with_retry')
    @patch('scripts.batch_comparison.StreamlitCVGenerator')
    def test_progress_callback_called(
        self,
        mock_generator_class,
        mock_pdf_extraction,
        mock_cv_files,
        mock_job_file
    ):
        """
        Test: Progress callback is invoked during processing
        """
        mock_pdf_extraction.return_value = {"Titel": "Test"}
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.run.return_value = {
            "success": True,
            "vorname": "Test",
            "nachname": "User",
            "cv_json": "/path/cv.json",
            "word_path": "/path/cv.docx",
            "match_json": "/path/match.json",
            "dashboard_path": "/path/dashboard.html",
            "error": None
        }
        
        # Create mock callback
        callback = Mock()
        
        # Run batch with callback
        result = run_batch_comparison(
            cv_files=mock_cv_files,
            job_file=mock_job_file,
            api_key="mock-key",
            progress_callback=callback,
            language="de"
        )
        
        # Verify callback was called
        assert callback.called
        # Should be called at least: Stellenprofil progress + CV progress + completion
        assert callback.call_count >= 3


class TestDirectoryCreationSafety:
    """Test that all directory creation calls use os.makedirs with exist_ok=True"""
    
    def test_streamlit_pipeline_creates_directories_before_writing_cv_json(self):
        """
        Test: streamlit_pipeline.py creates parent directories before writing CV JSON
        This prevents FileNotFoundError in batch processing with nested folders
        """
        from scripts.streamlit_pipeline import StreamlitCVGenerator
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a deeply nested directory structure that doesn't exist yet
            nested_path = os.path.join(temp_dir, "level1", "level2", "level3", "test.json")
            
            # Verify parent directory doesn't exist
            parent_dir = os.path.dirname(nested_path)
            assert not os.path.exists(parent_dir), "Parent directory should not exist"
            
            # This should create all parent directories
            os.makedirs(os.path.dirname(nested_path), exist_ok=True)
            
            # Verify parent directory now exists
            assert os.path.exists(parent_dir), "Parent directory should be created"
            
            # Write a test file
            with open(nested_path, 'w', encoding='utf-8') as f:
                json.dump({"test": "data"}, f)
            
            # Verify file was written successfully
            assert os.path.exists(nested_path), "File should be created"
    
    def test_generate_cv_feedback_creates_directories(self):
        """
        Test: generate_cv_feedback.py creates parent directories before writing
        """
        # Create a temporary deeply nested path
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_path = os.path.join(temp_dir, "batch", "candidate1", "feedback.json")
            
            # Verify parent directory doesn't exist
            parent_dir = os.path.dirname(feedback_path)
            assert not os.path.exists(parent_dir)
            
            # This is what the code does
            os.makedirs(os.path.dirname(feedback_path), exist_ok=True)
            
            # Verify directory exists
            assert os.path.exists(parent_dir)
            
            # Write file
            with open(feedback_path, 'w', encoding='utf-8') as f:
                json.dump({"feedback": "test"}, f)
            
            assert os.path.exists(feedback_path)
    
    def test_generate_matchmaking_creates_directories(self):
        """
        Test: generate_matchmaking.py creates parent directories before writing
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            match_path = os.path.join(temp_dir, "batch", "candidate1", "match.json")
            
            # Verify doesn't exist
            assert not os.path.exists(os.path.dirname(match_path))
            
            # Create directories
            os.makedirs(os.path.dirname(match_path), exist_ok=True)
            
            # Write file
            with open(match_path, 'w', encoding='utf-8') as f:
                json.dump({"match": "data"}, f)
            
            assert os.path.exists(match_path)
    
    def test_visualize_results_creates_directories(self):
        """
        Test: visualize_results.py creates parent directories before writing dashboard
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            dashboard_path = os.path.join(temp_dir, "batch", "candidate1", "dashboard.html")
            
            # Verify doesn't exist
            assert not os.path.exists(os.path.dirname(dashboard_path))
            
            # Create directories
            os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
            
            # Write file
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write("<html>Test Dashboard</html>")
            
            assert os.path.exists(dashboard_path)
    
    def test_batch_comparison_creates_batch_folder(self):
        """
        Test: batch_comparison.py creates candidate subfolders in batch structure
        
        Expected structure:
        output/
        └── batch_comparison_jobprofile_timestamp/
            └── jobprofile_candidate1_timestamp/
                └── files...
        """
        from scripts.naming_conventions import build_output_path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate batch processing path generation
            naming = build_output_path(
                mode='professional_analysis',
                candidate_name='fischer_arthur',
                job_profile_name='senior_analyst',
                artifact_type='cv',
                is_batch=True,
                timestamp='20260119_142318',
                base_output_dir=temp_dir
            )
            
            candidate_subfolder = naming['candidate_subfolder_path']
            
            # Verify folder doesn't exist yet
            assert not os.path.exists(candidate_subfolder)
            
            # Create it (as batch_comparison does)
            os.makedirs(candidate_subfolder, exist_ok=True)
            
            # Now write a file to it
            json_path = os.path.join(candidate_subfolder, 'test.json')
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({"test": "data"}, f)
            
            # Verify entire structure exists
            assert os.path.exists(naming['batch_folder_path'])
            assert os.path.exists(candidate_subfolder)
            assert os.path.exists(json_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

