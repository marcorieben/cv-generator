"""
Unit tests for naming conventions module.

Purpose: Test all naming utility functions
Expected Lifetime: Permanent
Category: TEST
Created: 2026-01-28
Last Updated: 2026-01-28
"""

import pytest
from core.utils.naming import (
    slugify,
    generate_jobprofile_slug,
    generate_candidate_name,
    generate_filename,
    generate_folder_name,
    validate_filename,
    validate_naming_pattern,
    extract_components_from_filename,
    FileType
)


class TestSlugify:
    """Test slugify function."""
    
    def test_basic_slugify(self):
        """Test basic text normalization."""
        assert slugify("Senior Java Developer") == "senior_java_developer"
    
    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        assert slugify("C++ & Python Expert!!!") == "c_python_expert"
    
    def test_german_umlauts_replaced(self):
        """Test that German umlauts are properly replaced."""
        assert slugify("Müller-Schmidt Ä Ö Ü") == "muller_schmidt_a_o_u"
        assert slugify("Straße") == "strasse"
    
    def test_multiple_spaces_normalized(self):
        """Test that multiple spaces become single underscore."""
        assert slugify("Too    Many     Spaces") == "too_many_spaces"
    
    def test_hyphens_to_underscores(self):
        """Test that hyphens are converted to underscores."""
        assert slugify("Senior-Developer-Java") == "senior_developer_java"
    
    def test_truncation(self):
        """Test that text is truncated to max_length."""
        long_text = "A" * 100
        result = slugify(long_text, max_length=20)
        assert len(result) == 20
    
    def test_trailing_underscores_removed(self):
        """Test that trailing underscores are stripped."""
        assert slugify("Test___", max_length=10) == "test"


class TestGenerateJobprofileSlug:
    """Test job profile slug generation."""
    
    def test_basic_generation(self):
        """Test basic job profile slug generation."""
        result = generate_jobprofile_slug(12881, "Senior Business Analyst")
        assert result == "gdjob_12881_senior_business_analyst"
    
    def test_with_special_characters(self):
        """Test job profile slug with special characters."""
        result = generate_jobprofile_slug(99, "C++ & Python Expert!!!")
        assert result == "gdjob_99_c_python_expert"
    
    def test_with_german_umlauts(self):
        """Test job profile slug with German umlauts."""
        result = generate_jobprofile_slug(1, "Entwickler für Web-Applikationen (m/w/d)")
        assert result == "gdjob_1_entwickler_fur_web_applikationen_mwd"
    
    def test_truncation(self):
        """Test that job profile name is truncated."""
        long_name = "A" * 100
        max_length = 30
        result = generate_jobprofile_slug(123, long_name, max_length=max_length)
        # Should be gdjob_123_ (9 chars) + max 30 chars
        assert len(result) <= 40  # gdjob_123_ + max 30 chars
        assert result.startswith("gdjob_123_")
        # Check that the name part is truncated
        name_part = result.replace("gdjob_123_", "")
        assert len(name_part) <= max_length
    
    def test_id_formats(self):
        """Test different ID formats."""
        assert generate_jobprofile_slug(1, "Test") == "gdjob_1_test"
        assert generate_jobprofile_slug(999999, "Test") == "gdjob_999999_test"


class TestGenerateCandidateName:
    """Test candidate name generation."""
    
    def test_basic_name(self):
        """Test basic candidate name."""
        assert generate_candidate_name("Marco", "Rieben") == "Marco_Rieben"
    
    def test_with_umlauts(self):
        """Test candidate name with German umlauts."""
        assert generate_candidate_name("Max", "Müller") == "Max_Mueller"
        assert generate_candidate_name("Jürgen", "Schäfer") == "Juergen_Schaefer"
    
    def test_with_special_characters(self):
        """Test candidate name with special characters."""
        assert generate_candidate_name("Jean-Claude", "Van Damme") == "JeanClaude_VanDamme"
        assert generate_candidate_name("O'Brien", "Smith") == "OBrien_Smith"
    
    def test_case_preservation(self):
        """Test that case is preserved."""
        assert generate_candidate_name("marco", "rieben") == "marco_rieben"
        assert generate_candidate_name("MARCO", "RIEBEN") == "MARCO_RIEBEN"


class TestGenerateFilename:
    """Test filename generation."""
    
    def test_cv_filename(self):
        """Test CV filename generation."""
        result = generate_filename(
            "gdjob_12881_senior_ba",
            "Marco_Rieben",
            FileType.CV,
            "20260119_170806",
            "docx"
        )
        assert result == "gdjob_12881_senior_ba_Marco_Rieben_cv_20260119_170806.docx"
    
    def test_offer_filename(self):
        """Test offer filename generation."""
        result = generate_filename(
            "gdjob_99_python_dev",
            "Max_Muller",
            FileType.OFFER,
            "20260120_093000",
            "docx"
        )
        assert result == "gdjob_99_python_dev_Max_Muller_offer_20260120_093000.docx"
    
    def test_dashboard_filename(self):
        """Test dashboard filename generation."""
        result = generate_filename(
            "gdjob_1_dev",
            "Test_User",
            FileType.DASHBOARD,
            "20260119_120000",
            "html"
        )
        assert result == "gdjob_1_dev_Test_User_dashboard_20260119_120000.html"
    
    def test_json_files(self):
        """Test JSON filename generation."""
        result = generate_filename(
            "gdjob_1_test",
            "User_Name",
            FileType.MATCH,
            "20260119_120000",
            "json"
        )
        assert result == "gdjob_1_test_User_Name_match_20260119_120000.json"
    
    def test_filetype_lowercase_conversion(self):
        """Test that filetype is converted to lowercase."""
        result = generate_filename(
            "gdjob_1_test",
            "User_Name",
            "CV",  # Uppercase
            "20260119_120000",
            "docx"
        )
        assert "_cv_" in result  # Should be lowercase
    
    def test_extension_dot_handling(self):
        """Test that dots in extension are handled correctly."""
        result1 = generate_filename("gdjob_1_test", "User_Name", "cv", "20260119_120000", "docx")
        result2 = generate_filename("gdjob_1_test", "User_Name", "cv", "20260119_120000", ".docx")
        assert result1 == result2  # Both should work


class TestGenerateFolderName:
    """Test folder name generation."""
    
    def test_basic_folder_name(self):
        """Test basic folder name generation."""
        result = generate_folder_name(
            "gdjob_12881_senior_ba",
            "Marco_Rieben",
            "20260119_170806"
        )
        assert result == "gdjob_12881_senior_ba_Marco_Rieben_20260119_170806"
    
    def test_no_extension(self):
        """Test that folder name has no extension."""
        result = generate_folder_name("gdjob_1_test", "User_Name", "20260119_120000")
        assert "." not in result


class TestValidateFilename:
    """Test filename validation."""
    
    def test_valid_filename(self):
        """Test validation of valid filename."""
        is_valid, error = validate_filename("gdjob_123_test_Marco_Rieben_cv_20260119_170806.docx")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_characters(self):
        """Test detection of invalid characters."""
        is_valid, error = validate_filename("invalid@file#name.docx")
        assert is_valid is False
        assert "invalid characters" in error.lower()
    
    def test_spaces_not_allowed(self):
        """Test that spaces are not allowed."""
        is_valid, error = validate_filename("invalid file name.docx")
        assert is_valid is False
        # Spaces trigger "invalid characters" error
        assert "invalid characters" in error.lower() or "spaces" in error.lower()
    
    def test_double_underscores_not_allowed(self):
        """Test that double underscores are not allowed."""
        is_valid, error = validate_filename("invalid__double__underscore.docx")
        assert is_valid is False
        assert "double underscores" in error.lower()
    
    def test_minimum_length(self):
        """Test minimum length validation."""
        is_valid, error = validate_filename("short.txt")
        assert is_valid is False
        assert "too short" in error.lower()
    
    def test_maximum_length(self):
        """Test maximum length validation."""
        long_filename = "a" * 300 + ".txt"
        is_valid, error = validate_filename(long_filename)
        assert is_valid is False
        assert "too long" in error.lower()


class TestValidateNamingPattern:
    """Test naming pattern validation."""
    
    def test_valid_primary_pattern_cv(self):
        """Test validation of valid CV filename pattern."""
        is_valid, error = validate_naming_pattern(
            "gdjob_123_test_Marco_Rieben_cv_20260119_170806.docx",
            "primary"
        )
        assert is_valid is True
        assert error == ""
    
    def test_valid_primary_pattern_offer(self):
        """Test validation of valid offer filename pattern."""
        is_valid, error = validate_naming_pattern(
            "gdjob_456_senior_dev_Max_Muller_offer_20260120_093000.docx",
            "primary"
        )
        assert is_valid is True
    
    def test_valid_folder_pattern(self):
        """Test validation of valid folder name pattern."""
        is_valid, error = validate_naming_pattern(
            "gdjob_123_test_Marco_Rieben_20260119_170806",
            "folder"
        )
        assert is_valid is True
        assert error == ""
    
    def test_invalid_primary_pattern(self):
        """Test detection of invalid primary pattern."""
        is_valid, error = validate_naming_pattern("invalid_name.docx", "primary")
        assert is_valid is False
        assert "doesn't match" in error.lower()
    
    def test_invalid_folder_pattern(self):
        """Test detection of invalid folder pattern."""
        is_valid, error = validate_naming_pattern("invalid_folder", "folder")
        assert is_valid is False
        assert "doesn't match" in error.lower()
    
    def test_all_filetypes(self):
        """Test that all defined filetypes pass validation."""
        for filetype in FileType.all_types():
            filename = f"gdjob_1_test_User_Name_{filetype}_20260119_120000.json"
            is_valid, error = validate_naming_pattern(filename, "primary")
            assert is_valid is True, f"Filetype {filetype} should be valid"


class TestExtractComponentsFromFilename:
    """Test component extraction from filename."""
    
    def test_extract_cv_components(self):
        """Test extraction of components from CV filename."""
        components = extract_components_from_filename(
            "gdjob_123_senior_dev_Marco_Rieben_cv_20260119_170806.docx"
        )
        assert components is not None
        assert components['jobprofile_id'] == '123'
        assert components['jobprofile_name'] == 'senior_dev'
        assert components['candidate_name'] == 'Marco_Rieben'
        assert components['filetype'] == 'cv'
        assert components['timestamp'] == '20260119_170806'
        assert components['extension'] == 'docx'
    
    def test_extract_offer_components(self):
        """Test extraction of components from offer filename."""
        components = extract_components_from_filename(
            "gdjob_456_python_expert_Max_Muller_offer_20260120_093000.docx"
        )
        assert components is not None
        assert components['jobprofile_id'] == '456'
        assert components['jobprofile_name'] == 'python_expert'
    
    def test_invalid_filename_returns_none(self):
        """Test that invalid filename returns None."""
        components = extract_components_from_filename("invalid_filename.docx")
        assert components is None
    
    def test_missing_components_returns_none(self):
        """Test that filename with missing components returns None."""
        components = extract_components_from_filename("gdjob_123_test.docx")
        assert components is None


class TestFileType:
    """Test FileType class."""
    
    def test_all_types_defined(self):
        """Test that all file types are defined."""
        types = FileType.all_types()
        assert FileType.CV in types
        assert FileType.OFFER in types
        assert FileType.DASHBOARD in types
        assert FileType.MATCH in types
        assert FileType.FEEDBACK in types
        assert FileType.JOBPROFILE in types
    
    def test_all_types_lowercase(self):
        """Test that all file types are lowercase."""
        types = FileType.all_types()
        for filetype in types:
            assert filetype == filetype.lower()
