"""Tests for CV extraction prompt module."""
import pytest
from scripts._2_extraction_cv.cv_prompt import (
    build_cv_system_prompt,
    build_cv_user_prompt,
    CV_EXTRACTION_RULES,
)


class TestCVPromptRules:
    """Tests for CV_EXTRACTION_RULES"""

    def test_rules_not_empty(self):
        assert len(CV_EXTRACTION_RULES) > 0

    def test_rules_are_strings(self):
        for rule in CV_EXTRACTION_RULES:
            assert isinstance(rule, str)


class TestBuildCVSystemPrompt:
    """Tests for build_cv_system_prompt()"""

    @pytest.fixture
    def sample_schema(self):
        return {
            "Vorname": "",
            "_hint_Vorname": "First name",
            "Nachname": ""
        }

    def test_returns_string(self, sample_schema):
        result = build_cv_system_prompt(sample_schema)
        assert isinstance(result, str)

    def test_contains_swiss_spelling_rule(self, sample_schema):
        result = build_cv_system_prompt(sample_schema)
        assert "RECHTSCHREIBUNG" in result

    def test_contains_schema(self, sample_schema):
        result = build_cv_system_prompt(sample_schema)
        assert "Vorname" in result

    def test_language_german(self, sample_schema):
        result = build_cv_system_prompt(sample_schema, "de")
        assert "Deutsch" in result

    def test_language_english(self, sample_schema):
        result = build_cv_system_prompt(sample_schema, "en")
        assert "English" in result

    def test_contains_missing_marker(self, sample_schema):
        marker = "! bitte prüfen !"
        result = build_cv_system_prompt(sample_schema, missing_marker=marker)
        assert marker in result

    def test_contains_cv_specific_rules(self, sample_schema):
        result = build_cv_system_prompt(sample_schema)
        assert "SPRACHEN" in result
        assert "REFERENZPROJEKTE" in result
        assert "ZERTIFIKATE" in result
        assert "KURZPROFIL" in result

    def test_contains_numbered_rules(self, sample_schema):
        result = build_cv_system_prompt(sample_schema)
        assert "1. " in result
        assert "2. " in result


class TestBuildCVUserPrompt:
    """Tests for build_cv_user_prompt()"""

    def test_basic_prompt(self):
        result = build_cv_user_prompt("Some CV text", "de")
        assert "Some CV text" in result
        assert "DE" in result

    def test_with_job_profile_context(self):
        context = {"titel": "Software Engineer"}
        result = build_cv_user_prompt("CV text", "de", context)
        assert "KONTEXT" in result
        assert "Software Engineer" in result
        assert "CV text" in result

    def test_without_job_profile_context(self):
        result = build_cv_user_prompt("CV text", "de", None)
        assert "KONTEXT" not in result
        assert "CV text" in result
