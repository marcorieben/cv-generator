"""
Unit tests for build_output_path() function.

Tests all modes and variations of the new centralized naming function.
"""

import pytest
from scripts.naming_conventions import build_output_path


class TestBuildOutputPathBasicMode:
    """Tests for BASIC mode (CV only, single)"""
    
    def test_basic_mode_cv_generates_correct_folder(self):
        """Test basic mode generates correct folder structure"""
        result = build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv',
            timestamp='20260119_114357'
        )
        
        assert result['mode'] == 'basic'
        assert result['is_batch'] == False
        assert result['folder_name'] == 'fischer_arthur_20260119_114357'
        assert 'fischer_arthur_cv_20260119_114357' in result['file_name']
    
    def test_basic_mode_dashboard(self):
        """Test basic mode with dashboard artifact"""
        result = build_output_path(
            mode='basic',
            candidate_name='mueller_hans',
            artifact_type='dashboard',
            timestamp='20260119_114357'
        )
        
        assert result['file_name'] == 'mueller_hans_dashboard_20260119_114357'
    
    def test_basic_mode_handles_special_characters(self):
        """Test that special characters in candidate name are sanitized"""
        result = build_output_path(
            mode='basic',
            candidate_name='Müller-Hans Krämer',
            artifact_type='cv',
            timestamp='20260119_114357'
        )
        
        # Should be normalized (spaces converted to underscores, hyphens removed)
        assert '_' in result['file_name']
        assert 'hans' in result['file_name'].lower()  # Part of the name should remain


class TestBuildOutputPathProfessionalAnalysisSingle:
    """Tests for PROFESSIONAL_ANALYSIS mode (Single CV)"""
    
    def test_single_cv_cv_artifact(self):
        """Test single CV mode with CV artifact"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        assert result['mode'] == 'professional_analysis'
        assert result['is_batch'] == False
        assert result['folder_name'] == 'senior_business_analyst_fischer_arthur_20260119_114357'
        assert result['file_name'] == 'senior_business_analyst_fischer_arthur_cv_20260119_114357'
    
    def test_single_cv_match_artifact(self):
        """Test single CV mode with match artifact"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='match',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        assert 'match' in result['file_name']
        assert 'senior_business_analyst_fischer_arthur_match_20260119_114357' == result['file_name']
    
    def test_single_cv_feedback_artifact(self):
        """Test single CV mode with feedback artifact"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='feedback',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        assert 'feedback' in result['file_name']
    
    def test_single_cv_dashboard_artifact(self):
        """Test single CV mode with dashboard artifact"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='dashboard',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        assert 'dashboard' in result['file_name']
    
    def test_single_cv_requires_job_profile_name(self):
        """Test that professional analysis mode requires job_profile_name"""
        with pytest.raises(ValueError):
            build_output_path(
                mode='professional_analysis',
                candidate_name='fischer_arthur',
                job_profile_name='',  # Missing!
                artifact_type='cv',
                is_batch=False,
                timestamp='20260119_114357'
            )
    
    def test_single_cv_special_char_sanitization(self):
        """Test that special characters are properly sanitized"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='Müller-Hans',
            job_profile_name='Senior-Business-Analyst',
            artifact_type='cv',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        # Should NOT contain: hyphens as separators (converted to underscores)
        assert '-' not in result['folder_name']
        assert 'hans' in result['folder_name'].lower()  # Part of candidate name should remain


class TestBuildOutputPathProfessionalAnalysisBatch:
    """Tests for PROFESSIONAL_ANALYSIS mode (Batch)"""
    
    def test_batch_mode_folder_structure(self):
        """Test batch mode creates correct folder hierarchy"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        assert result['is_batch'] == True
        assert result['batch_folder_name'] == 'batch_comparison_senior_business_analyst_20260119_114357'
        assert result['candidate_subfolder_name'] == 'senior_business_analyst_fischer_arthur_20260119_114357'
    
    def test_batch_mode_job_profile_at_root(self):
        """Test that job profile JSON is created at batch folder root"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        assert result['job_profile_file_name'] == 'senior_business_analyst_20260119_114357'
        assert 'batch_comparison_senior_business_analyst_20260119_114357' in result['job_profile_file_path']
        assert 'fischer_arthur' not in result['job_profile_file_path']  # Not in subfolder
    
    def test_batch_mode_cv_artifact(self):
        """Test batch mode with CV artifact"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        assert result['file_name'] == 'senior_business_analyst_fischer_arthur_cv_20260119_114357'
        assert 'senior_business_analyst_fischer_arthur_20260119_114357' in result['folder_path']
    
    def test_batch_mode_multiple_candidates(self):
        """Test that batch mode generates different paths for different candidates"""
        result1 = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        result2 = build_output_path(
            mode='professional_analysis',
            candidate_name='mueller_hans',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        # Both should have SAME batch folder
        assert result1['batch_folder_name'] == result2['batch_folder_name']
        
        # But different candidate subfolders
        assert result1['candidate_subfolder_name'] != result2['candidate_subfolder_name']
        assert 'fischer_arthur' in result1['candidate_subfolder_name']
        assert 'mueller_hans' in result2['candidate_subfolder_name']
    
    def test_batch_mode_all_artifact_types(self):
        """Test batch mode with all artifact types"""
        artifacts = ['cv', 'match', 'feedback', 'dashboard']
        
        for artifact in artifacts:
            result = build_output_path(
                mode='professional_analysis',
                candidate_name='fischer_arthur',
                job_profile_name='senior_business_analyst',
                artifact_type=artifact,
                is_batch=True,
                timestamp='20260119_114357'
            )
            
            assert artifact in result['file_name']
            assert result['is_batch'] == True


class TestBuildOutputPathValidation:
    """Tests for input validation and error handling"""
    
    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError"""
        with pytest.raises(ValueError):
            build_output_path(
                mode='invalid_mode',
                candidate_name='fischer_arthur',
                artifact_type='cv'
            )
    
    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided"""
        result = build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv'
        )
        
        assert 'timestamp' in result
        assert len(result['timestamp']) == 15  # YYYYMMDD_HHMMSS
    
    def test_timestamp_format_preserved(self):
        """Test that provided timestamp is used as-is"""
        custom_ts = '20260119_114357'
        result = build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv',
            timestamp=custom_ts
        )
        
        assert result['timestamp'] == custom_ts
    
    def test_base_output_dir_respected(self):
        """Test that custom base output directory is respected"""
        result = build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv',
            timestamp='20260119_114357',
            base_output_dir='custom/output/path'
        )
        
        assert 'custom/output/path' in result['folder_path']


class TestBuildOutputPathPathConsistency:
    """Tests to ensure path consistency across different scenarios"""
    
    def test_paths_are_consistent_basic(self):
        """Test that paths are internally consistent in basic mode"""
        result = build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv',
            timestamp='20260119_114357'
        )
        
        # folder_path should contain folder_name
        assert result['folder_name'] in result['folder_path']
    
    def test_paths_are_consistent_single(self):
        """Test that paths are internally consistent in single CV mode"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        assert result['folder_name'] in result['folder_path']
        assert result['file_name'] in result['file_path']
    
    def test_paths_are_consistent_batch(self):
        """Test that paths are internally consistent in batch mode"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        assert result['candidate_subfolder_name'] in result['candidate_subfolder_path']
        assert result['batch_folder_name'] in result['batch_folder_path']
        assert result['file_name'] in result['file_path']


class TestBuildOutputPathNoHardcodedStrings:
    """Tests to ensure no hardcoded strings from old system remain"""
    
    def test_basic_mode_no_jobprofile(self):
        """Test that 'jobprofile' does not appear in basic mode names"""
        result = build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv',
            timestamp='20260119_114357'
        )
        
        assert 'jobprofile' not in result['folder_name']
        assert 'jobprofile' not in result['file_name']
    
    def test_single_mode_no_hardcoded_names(self):
        """Test that no hardcoded strings appear in single CV mode"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=False,
            timestamp='20260119_114357'
        )
        
        assert 'jobprofile' not in result['folder_name']
        assert 'batch-comparison' not in result['folder_name']
        assert 'stellenprofil' not in result['file_name']
    
    def test_batch_mode_no_hardcoded_names(self):
        """Test that no hardcoded strings appear in batch mode"""
        result = build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            job_profile_name='senior_business_analyst',
            artifact_type='cv',
            is_batch=True,
            timestamp='20260119_114357'
        )
        
        # 'batch_comparison' is OK (it's a fixed structure), but 'batch-comparison' is OLD
        assert 'batch-comparison' not in result['batch_folder_name']
        assert 'jobprofile' not in result['file_name']
        assert 'stellenprofil' not in result['file_name']  # Should use stellenprofil variable value
