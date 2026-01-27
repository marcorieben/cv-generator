"""Tests for shared prompt rules module."""
import pytest
from scripts._shared.prompt_rules import (
    get_missing_marker,
    extract_hints_from_schema,
    get_language_name,
    build_common_rules_block,
    build_language_instruction,
    COMMON_RULES,
)


class TestMissingMarker:
    """Tests for get_missing_marker()"""

    def test_german(self):
        assert get_missing_marker("de") == "! bitte prüfen !"

    def test_english(self):
        assert get_missing_marker("en") == "! please check !"

    def test_french(self):
        assert get_missing_marker("fr") == "! à vérifier !"

    def test_fallback(self):
        assert get_missing_marker("xx") == "! bitte prüfen !"


class TestLanguageName:
    """Tests for get_language_name()"""

    def test_german(self):
        assert get_language_name("de") == "Deutsch"

    def test_english(self):
        assert get_language_name("en") == "English"

    def test_french(self):
        assert get_language_name("fr") == "Français"

    def test_fallback(self):
        assert get_language_name("xx") == "Deutsch"


class TestHintExtraction:
    """Tests for extract_hints_from_schema()"""

    def test_simple_hint(self):
        schema = {
            "field1": "value",
            "_hint_field1": "This is a hint"
        }
        hints = extract_hints_from_schema(schema)
        assert hints == {"field1": "This is a hint"}

    def test_nested_hint(self):
        schema = {
            "section": {
                "field1": "",
                "_hint_field1": "Nested hint"
            }
        }
        hints = extract_hints_from_schema(schema)
        assert hints["section"]["field1"] == "Nested hint"

    def test_empty_schema(self):
        assert extract_hints_from_schema({}) == {}

    def test_no_hints(self):
        schema = {"field1": "value", "field2": 42}
        assert extract_hints_from_schema(schema) == {}

    def test_list_in_schema(self):
        schema = {
            "items": [
                {"name": "", "_hint_name": "Enter name"}
            ]
        }
        hints = extract_hints_from_schema(schema)
        # List items are processed - hints from list contents bubble up via the parent key
        assert hints["items"]["name"] == "Enter name"


class TestBuildLanguageInstruction:
    """Tests for build_language_instruction()"""

    def test_german(self):
        result = build_language_instruction("de")
        assert "Deutsch" in result
        assert "ZIELSPRACHE" in result

    def test_english(self):
        result = build_language_instruction("en")
        assert "English" in result


class TestBuildCommonRulesBlock:
    """Tests for build_common_rules_block()"""

    def test_returns_list(self):
        result = build_common_rules_block("! bitte prüfen !")
        assert isinstance(result, list)
        assert len(result) == 4

    def test_contains_marker(self):
        marker = "! test marker !"
        result = build_common_rules_block(marker)
        assert any(marker in rule for rule in result)

    def test_contains_all_common_rules(self):
        result = build_common_rules_block("marker")
        combined = " ".join(result)
        assert "Schema" in combined
        assert "erfinden" in combined
        assert "RECHTSCHREIBUNG" in combined


class TestCommonRules:
    """Tests for COMMON_RULES dict"""

    def test_has_required_keys(self):
        assert "swiss_spelling" in COMMON_RULES
        assert "no_invention" in COMMON_RULES
        assert "missing_marker" in COMMON_RULES
        assert "strict_schema" in COMMON_RULES

    def test_missing_marker_has_placeholder(self):
        assert "{marker}" in COMMON_RULES["missing_marker"]
