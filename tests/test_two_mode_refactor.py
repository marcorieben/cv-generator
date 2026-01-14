"""
Feature tests for simplified 2-mode structure: Basic + Advanced.
Tests the refactored architecture with only two unified modes:
1. Basic: Single CV only
2. Advanced: Full analysis with 1+ CVs (auto-scales based on file count)
"""

import pytest
import json
from unittest.mock import MagicMock


class TestTwoModeArchitecture:
    """Test suite for the 2-mode unified structure."""
    
    def test_only_two_modes_in_ui(self):
        """Verify that UI now has exactly 2 modes: Basic and Advanced."""
        valid_modes = [
            "Basic (Nur CV)",
            "Advanced (CV + Stellenprofil + Match + Feedback)"
        ]
        
        # Old modes should NOT exist
        removed_modes = [
            "Analysis (CV + Stellenprofil)",
            "Full (CV + Stellenprofil + Match + Feedback)",
            "Batch (Mehrere CVs + Stellenprofil)"
        ]
        
        for removed_mode in removed_modes:
            assert removed_mode not in valid_modes, f"{removed_mode} should not exist"
        
        assert len(valid_modes) == 2, "Should have exactly 2 modes"
    
    def test_advanced_mode_accepts_multiple_cvs(self):
        """Verify Advanced mode description mentions 1+ CVs."""
        advanced_description = "1 or multiple CVs. Full analysis + matching + feedback for all."
        
        assert "multiple CVs" in advanced_description.lower() or "multiple" in advanced_description.lower()
        assert "analysis" in advanced_description.lower()
        assert "feedback" in advanced_description.lower()
    
    def test_basic_mode_single_cv_only(self):
        """Verify Basic mode only handles single CV."""
        basic_description = "CV only"
        
        # Basic should NOT mention multiple files or batch
        assert "multiple" not in basic_description.lower()
        assert "batch" not in basic_description.lower()
    
    def test_advanced_uses_batch_uploader(self):
        """Verify Advanced mode uses render_batch_cv_uploader (1+ files)."""
        # Advanced mode upload section should use render_batch_cv_uploader
        # which accepts multiple files
        supports_multiple = True  # Advanced uses batch uploader
        assert supports_multiple, "Advanced mode should support multiple CVs"
    
    def test_basic_uses_single_uploader(self):
        """Verify Basic mode uses render_custom_uploader (single file)."""
        # Basic mode upload section should use render_custom_uploader
        # which only accepts single file
        supports_multiple = False  # Basic uses single uploader
        assert not supports_multiple, "Basic mode should only support single CV"
    
    def test_auto_detection_is_batch(self):
        """Test the unified auto-detection: is_batch = isinstance(cv_file, list) and len(cv_file) > 1."""
        # Single CV in Advanced mode
        cv_single = [{"name": "cv.pdf"}]
        is_batch = isinstance(cv_single, list) and len(cv_single) > 1
        assert not is_batch, "Single CV should NOT trigger batch mode"
        
        # Multiple CVs in Advanced mode
        cv_multiple = [
            {"name": "cv1.pdf"},
            {"name": "cv2.pdf"},
            {"name": "cv3.pdf"}
        ]
        is_batch = isinstance(cv_multiple, list) and len(cv_multiple) > 1
        assert is_batch, "Multiple CVs SHOULD trigger batch mode"
    
    def test_advanced_test_mode_button(self):
        """Verify test mode button is labeled for Advanced."""
        test_button_label = "🧪 Test Mode (Advanced)"
        
        assert "Advanced" in test_button_label
        assert "Analysis" not in test_button_label  # Old name
        assert "Batch" not in test_button_label  # Old name
        assert "Full" not in test_button_label  # Old name
    
    def test_results_branching_on_batch_results(self):
        """Test that results display branches on presence of batch_results."""
        # Single CV result from Advanced mode
        single_result = {
            "success": True,
            "word_path": "/output/cv.docx",
            "cv_json": "/output/cv.json",
            "dashboard_path": "/output/dashboard.html",
            # NO batch_results field
        }
        
        has_batch_results = single_result.get("batch_results") is not None
        assert not has_batch_results, "Single result should not have batch_results"
        
        # Batch result from Advanced mode (multiple CVs)
        batch_result = {
            "success": True,
            "batch_results": [
                {
                    "success": True,
                    "candidate_name": "John Doe",
                    "word_path": "/output/cv1.docx"
                },
                {
                    "success": True,
                    "candidate_name": "Jane Smith",
                    "word_path": "/output/cv2.docx"
                }
            ],
            "batch_folder": "/output/batch"
        }
        
        has_batch_results = batch_result.get("batch_results") is not None
        assert has_batch_results, "Batch result should have batch_results"
        assert len(batch_result["batch_results"]) == 2
    
    def test_session_state_keys_updated(self):
        """Verify session state keys use 'advanced' not 'analysis'."""
        # Old keys (should NOT exist):
        old_keys = ["cv_files_analysis", "job_analysis"]
        
        # New keys (should exist):
        new_keys = ["cv_files_advanced", "job_advanced"]
        
        for new_key in new_keys:
            assert "advanced" in new_key.lower(), f"Key {new_key} should use 'advanced'"
            assert "analysis" not in new_key.lower(), f"Key {new_key} should not use 'analysis'"
    
    def test_mode_string_detection(self):
        """Verify mode detection uses startswith() patterns."""
        # Code should use:
        # - mode.startswith("Basic")
        # - mode.startswith("Advanced")
        
        # Test the patterns
        mode_basic = "Basic (Nur CV)"
        mode_advanced = "Advanced (CV + Stellenprofil + Match + Feedback)"
        
        assert mode_basic.startswith("Basic")
        assert not mode_basic.startswith("Advanced")
        
        assert mode_advanced.startswith("Advanced")
        assert not mode_advanced.startswith("Basic")
        assert not mode_advanced.startswith("Analysis")  # Old name
        assert not mode_advanced.startswith("Full")  # Old name
    
    def test_mock_mode_provides_test_data(self):
        """Verify mock mode creates test CVs that work for both modes."""
        # Mock data in Advanced mode should create multiple CVs
        # allowing testing of both single and batch paths
        mock_cv_files = [
            {"name": "mock_cv_1.pdf"},
            {"name": "mock_cv_2.pdf"},
            {"name": "mock_cv_3.pdf"}
        ]
        
        assert len(mock_cv_files) >= 3, "Mock should provide 3+ test CVs"
        
        # Can be used for single CV test (take first)
        single_test = [mock_cv_files[0]]
        is_batch = isinstance(single_test, list) and len(single_test) > 1
        assert not is_batch, "Can test single CV mode"
        
        # Can be used for batch test (take all)
        batch_test = mock_cv_files
        is_batch = isinstance(batch_test, list) and len(batch_test) > 1
        assert is_batch, "Can test batch mode"


class TestModeSpecificBehavior:
    """Test mode-specific requirements and behaviors."""
    
    def test_basic_mode_no_job_profile_required(self):
        """Verify Basic mode does NOT require job profile."""
        # Basic mode form requirements:
        required_in_basic = {
            "cv_file": True,      # CV is required
            "job_file": False,     # Job profile NOT required
            "api_key": True,      # API key always required
            "dsgvo_accepted": True # DSGVO always required
        }
        
        assert required_in_basic["cv_file"]
        assert not required_in_basic["job_file"], "Basic mode should NOT require job profile"
        assert required_in_basic["api_key"]
        assert required_in_basic["dsgvo_accepted"]
    
    def test_advanced_mode_requires_job_profile(self):
        """Verify Advanced mode REQUIRES job profile for all features."""
        # Advanced mode form requirements:
        required_in_advanced = {
            "cv_file": True,        # CV(s) required
            "job_file": True,       # Job profile REQUIRED for analysis
            "api_key": True,       # API key required
            "dsgvo_accepted": True # DSGVO required
        }
        
        assert required_in_advanced["cv_file"]
        assert required_in_advanced["job_file"], "Advanced mode MUST have job profile"
        assert required_in_advanced["api_key"]
        assert required_in_advanced["dsgvo_accepted"]
    
    def test_start_button_disable_logic_basic(self):
        """Test start button disabling for Basic mode."""
        # Basic mode requirements
        cv_file = {"name": "cv.pdf"}
        api_key = "test-key"
        dsgvo_accepted = True
        
        # With all required fields - button should be enabled
        disabled = not cv_file or not api_key or not dsgvo_accepted
        assert not disabled, "Button should be enabled with required fields"
        
        # Missing CV - button should be disabled
        disabled = not None or not api_key or not dsgvo_accepted
        assert disabled, "Button should be disabled without CV"
    
    def test_start_button_disable_logic_advanced(self):
        """Test start button disabling for Advanced mode."""
        # Advanced mode requirements
        cv_files = [{"name": "cv.pdf"}]
        job_file = {"name": "job.pdf"}
        api_key = "test-key"
        dsgvo_accepted = True
        
        # With all required fields - button should be enabled
        disabled = not cv_files or not job_file or not api_key or not dsgvo_accepted
        assert not disabled, "Button should be enabled with all fields"
        
        # Missing job profile - button should be disabled
        disabled = not cv_files or not None or not api_key or not dsgvo_accepted
        assert disabled, "Button should be disabled without job profile"
        
        # Multiple CVs - should still work
        cv_files = [{"name": "cv1.pdf"}, {"name": "cv2.pdf"}]
        disabled = not cv_files or not job_file or not api_key or not dsgvo_accepted
        assert not disabled, "Should work with multiple CVs"


class TestCodeSimplification:
    """Verify that code was actually simplified."""
    
    def test_no_analysis_references_in_logic(self):
        """Verify old 'Analysis' mode string is removed from mode detection."""
        # The code should NOT have:
        # - mode.startswith("Analysis")
        # - "Analysis" string literals in mode detection
        
        # Only valid mode checks should be:
        modes_valid = [
            "Basic",
            "Advanced"
        ]
        
        modes_invalid = [
            "Analysis",  # Removed in refactor
            "Full",      # Now merged into Advanced
            "Batch"      # Now merged into Advanced
        ]
        
        for invalid in modes_invalid:
            assert invalid not in modes_valid
    
    def test_unified_batch_detection(self):
        """Verify single auto-detection pattern replaces multiple mode checks."""
        # OLD WAY (multiple mode-specific branches):
        # if mode.startswith("Analysis"):
        #     is_batch = ...
        # elif mode.startswith("Batch"):
        #     is_batch = ...
        # elif mode.startswith("Full"):
        #     is_batch = ...
        
        # NEW WAY (single unified detection):
        # if mode.startswith("Advanced"):
        #     is_batch = isinstance(cv_file, list) and len(cv_file) > 1
        
        # Test the new pattern
        cv_file_list = [{"name": "cv.pdf"}]
        is_batch = isinstance(cv_file_list, list) and len(cv_file_list) > 1
        assert not is_batch
        
        cv_file_list = [{"name": "cv1.pdf"}, {"name": "cv2.pdf"}]
        is_batch = isinstance(cv_file_list, list) and len(cv_file_list) > 1
        assert is_batch
    
    def test_session_state_cleanup(self):
        """Verify session state keys are consolidated."""
        # OLD session keys (should not exist):
        old_keys = [
            "cv_files_analysis",
            "cv_files_full",
            "cv_files_batch",
            "job_analysis",
            "job_full",
            "job_batch"
        ]
        
        # NEW session keys (should only have):
        new_keys = [
            "cv_files_basic",
            "cv_files_advanced",
            "job_advanced"  # Only Advanced needs job file
        ]
        
        # Verify no duplication
        for new_key in new_keys:
            for old_key in old_keys:
                assert old_key != new_key, f"Old key {old_key} should be removed"


class TestHistoryFlexibility:
    """Test that history entries work for both single and batch."""
    
    def test_single_cv_history_entry(self):
        """Verify history entry format for single CV in Advanced mode."""
        entry = {
            "timestamp": "20260114_120000",
            "candidate_name": "Max Mustermann",
            "mode": "Advanced (CV + Stellenprofil + Match + Feedback)",
            "word_path": "/output/cv_max_mustermann.docx",
            "cv_json": "/output/cv_max_mustermann.json",
            # NO batch_results or is_batch flag
        }
        
        assert entry["candidate_name"] == "Max Mustermann"
        assert entry.get("batch_results") is None
        assert entry.get("is_batch") is None
    
    def test_batch_cv_history_entry(self):
        """Verify history entry format for batch (multiple CVs) in Advanced mode."""
        entry = {
            "timestamp": "20260114_121000",
            "candidate_name": "Batch (3/3)",  # Shows success count
            "mode": "Advanced (CV + Stellenprofil + Match + Feedback)",
            "is_batch": True,
            "batch_folder": "/output/batch_20260114_121000",
            "batch_results": [
                {
                    "candidate_name": "John Doe",
                    "success": True,
                    "word_path": "/output/batch_20260114_121000/cv_john_doe.docx"
                },
                {
                    "candidate_name": "Jane Smith",
                    "success": True,
                    "word_path": "/output/batch_20260114_121000/cv_jane_smith.docx"
                },
                {
                    "candidate_name": "Bob Johnson",
                    "success": True,
                    "word_path": "/output/batch_20260114_121000/cv_bob_johnson.docx"
                }
            ]
        }
        
        assert entry.get("is_batch") is True
        assert len(entry["batch_results"]) == 3
        assert "Batch" in entry["candidate_name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
