"""Tests for Offer generation prompt module."""
import pytest
from scripts._5_generation_offer.offer_prompt import (
    build_offer_system_prompt,
    build_offer_user_prompt,
    OFFER_GENERATION_RULES,
)


class TestOfferPromptRules:
    """Tests for OFFER_GENERATION_RULES"""

    def test_rules_not_empty(self):
        assert len(OFFER_GENERATION_RULES) > 0

    def test_rules_are_strings(self):
        for rule in OFFER_GENERATION_RULES:
            assert isinstance(rule, str)

    def test_contains_we_form_rule(self):
        combined = " ".join(OFFER_GENERATION_RULES)
        assert "Wir-Form" in combined

    def test_contains_positive_rule(self):
        combined = " ".join(OFFER_GENERATION_RULES)
        assert "POSITIV" in combined


class TestBuildOfferSystemPrompt:
    """Tests for build_offer_system_prompt()"""

    @pytest.fixture
    def sample_schema(self):
        return {
            "stellenbezug": {
                "kurzkontext": "",
                "_hint_kurzkontext": "Persönliche Einleitung"
            },
            "gesamtbeurteilung": {
                "zusammenfassung": "",
                "_hint_zusammenfassung": "Detaillierte Argumentation"
            }
        }

    def test_returns_string(self, sample_schema):
        result = build_offer_system_prompt(sample_schema)
        assert isinstance(result, str)

    def test_contains_language_name(self, sample_schema):
        result = build_offer_system_prompt(sample_schema, "de")
        assert "Deutsch" in result

    def test_extracts_hints(self, sample_schema):
        result = build_offer_system_prompt(sample_schema)
        assert "kurzkontext" in result
        assert "Persönliche Einleitung" in result

    def test_contains_bold_instruction(self, sample_schema):
        result = build_offer_system_prompt(sample_schema)
        assert "Fettschrift" in result

    def test_contains_numbered_rules(self, sample_schema):
        result = build_offer_system_prompt(sample_schema)
        assert "1. " in result
        assert "WIR-FORM" in result


class TestBuildOfferUserPrompt:
    """Tests for build_offer_user_prompt()"""

    def test_basic_prompt(self):
        context = {"kandidat": {"name": "Max Mustermann"}}
        result = build_offer_user_prompt(context)
        assert "Max Mustermann" in result
        assert "Angebotserstellung" in result

    def test_returns_string(self):
        result = build_offer_user_prompt({"key": "value"})
        assert isinstance(result, str)
