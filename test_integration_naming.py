#!/usr/bin/env python
"""
Integration test for build_output_path() function across all modes.
Validates that the centralized naming convention works in all scenarios.
"""

import os
import sys

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from naming_conventions import build_output_path


def test_basic_mode():
    """Test BASIC mode naming"""
    print("\n[TEST 1] Basic Mode")
    result = build_output_path(
        mode='basic',
        candidate_name='fischer_arthur',
        artifact_type='cv',
        timestamp='20260119_114357'
    )
    
    assert result['mode'] == 'basic'
    assert result['is_batch'] == False
    assert 'fischer_arthur_cv_20260119_114357' in result['file_name']
    assert 'fischer_arthur_20260119_114357' in result['folder_name']
    print(f"  ✓ Folder: {result['folder_name']}")
    print(f"  ✓ File: {result['file_name']}")
    return True


def test_single_cv_mode():
    """Test PROFESSIONAL_ANALYSIS mode (single CV)"""
    print("\n[TEST 2] Professional Analysis Mode - Single CV")
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
    assert 'senior_business_analyst_fischer_arthur_cv_20260119_114357' == result['file_name']
    assert 'senior_business_analyst_fischer_arthur_20260119_114357' == result['folder_name']
    print(f"  ✓ Folder: {result['folder_name']}")
    print(f"  ✓ File: {result['file_name']}")
    return True


def test_batch_mode():
    """Test PROFESSIONAL_ANALYSIS mode (batch)"""
    print("\n[TEST 3] Professional Analysis Mode - Batch")
    result = build_output_path(
        mode='professional_analysis',
        candidate_name='fischer_arthur',
        job_profile_name='senior_business_analyst',
        artifact_type='cv',
        is_batch=True,
        timestamp='20260119_114357'
    )
    
    assert result['mode'] == 'professional_analysis'
    assert result['is_batch'] == True
    assert result['batch_folder_name'] == 'batch_comparison_senior_business_analyst_20260119_114357'
    assert result['candidate_subfolder_name'] == 'senior_business_analyst_fischer_arthur_20260119_114357'
    assert result['file_name'] == 'senior_business_analyst_fischer_arthur_cv_20260119_114357'
    print(f"  ✓ Batch Folder: {result['batch_folder_name']}")
    print(f"  ✓ Candidate Subfolder: {result['candidate_subfolder_name']}")
    print(f"  ✓ File: {result['file_name']}")
    print(f"  ✓ Job Profile File: {result['job_profile_file_name']}")
    return True


def test_all_artifact_types():
    """Test all artifact types in batch mode"""
    print("\n[TEST 4] All Artifact Types")
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
        print(f"  ✓ {artifact:10s}: {result['file_name']}")
    
    return True


def test_no_hardcoded_strings():
    """Verify no hardcoded 'jobprofile' or 'batch-comparison' strings with hyphens"""
    print("\n[TEST 5] No Hardcoded Strings")
    
    # Basic mode
    result = build_output_path(mode='basic', candidate_name='fischer_arthur')
    assert 'jobprofile' not in result['file_name']
    assert 'jobprofile' not in result['folder_name']
    print(f"  ✓ Basic mode: no hardcoded strings")
    
    # Single CV mode
    result = build_output_path(
        mode='professional_analysis',
        candidate_name='fischer_arthur',
        job_profile_name='senior_business_analyst',
        is_batch=False
    )
    assert 'jobprofile' not in result['file_name']
    assert 'batch-comparison' not in result['folder_name']
    print(f"  ✓ Single CV mode: no hardcoded strings")
    
    # Batch mode
    result = build_output_path(
        mode='professional_analysis',
        candidate_name='fischer_arthur',
        job_profile_name='senior_business_analyst',
        is_batch=True
    )
    assert 'jobprofile' not in result['file_name']
    assert 'batch-comparison' not in result['batch_folder_name']  # old hyphen format
    assert 'batch_comparison' in result['batch_folder_name']      # new underscore format
    print(f"  ✓ Batch mode: correct naming (batch_comparison, not batch-comparison)")
    
    return True


def test_variable_standardization():
    """Verify all variables are in English"""
    print("\n[TEST 6] Variable Standardization (English)")
    
    result = build_output_path(
        mode='professional_analysis',
        candidate_name='fischer_arthur',
        job_profile_name='senior_business_analyst',  # English, not stellenprofil
        artifact_type='cv',
        is_batch=True
    )
    
    # Check that return dict uses English names
    expected_keys = [
        'mode', 'is_batch', 'timestamp',
        'batch_folder_name', 'batch_folder_path',
        'job_profile_file_name', 'job_profile_file_path',  # English, not stellenprofil
        'candidate_subfolder_name', 'candidate_subfolder_path',
        'folder_name', 'folder_path', 'file_name', 'file_with_ext', 'file_path'
    ]
    
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
    
    # Verify no German names in return dict
    for key in result.keys():
        assert 'stellenprofil' not in key, f"Found German variable: {key}"
    
    print(f"  ✓ All variables standardized to English")
    print(f"  ✓ 'job_profile_name' used (not 'stellenprofil')")
    
    return True


def main():
    """Run all integration tests"""
    print("=" * 70)
    print("INTEGRATION TEST: build_output_path() Function")
    print("=" * 70)
    
    tests = [
        test_basic_mode,
        test_single_cv_mode,
        test_batch_mode,
        test_all_artifact_types,
        test_no_hardcoded_strings,
        test_variable_standardization,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
