"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2025-12-17
Last Updated: 2026-01-24
"""
import json
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_cv import validate_json_structure, is_valid_level, parse_level


class TestValidateJsonStructure:
    """Tests for validate_json_structure function"""
    
    @pytest.fixture
    def valid_cv_data(self):
        """Load valid CV fixture"""
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'valid_cv.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def invalid_cv_data(self):
        """Load invalid CV fixture"""
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'invalid_cv_missing_fields.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_valid_cv_passes_validation(self, valid_cv_data):
        """Test that a valid CV passes validation without critical errors"""
        critical, info = validate_json_structure(valid_cv_data)
        
        assert len(critical) == 0, f"Valid CV should have no critical errors, got: {critical}"
        # Info warnings are acceptable
    
    def test_missing_required_fields(self):
        """Test that missing required fields are detected"""
        data = {
            "Vorname": "Test"
            # Missing all other required fields
        }
        
        critical, info = validate_json_structure(data)
        
        assert len(critical) > 0, "Missing required fields should produce critical errors"
        assert any("Nachname" in err for err in critical)
        assert any("Hauptrolle" in err for err in critical)
    
    def test_hauptrolle_structure(self):
        """Test that Hauptrolle must have correct structure"""
        data_missing_beschreibung = {
            "Vorname": "Test",
            "Nachname": "User",
            "Hauptrolle": {
                "Titel": "Developer"
                # Missing Beschreibung
            },
            "Nationalität": "Schweiz",
            "Hauptausbildung": "Bachelor",
            "Kurzprofil": "Test profile",
            "Fachwissen_und_Schwerpunkte": [],
            "Aus_und_Weiterbildung": [],
            "Trainings_und_Zertifizierungen": [],
            "Sprachen": [],
            "Ausgewählte_Referenzprojekte": []
        }
        
        critical, info = validate_json_structure(data_missing_beschreibung)
        
        assert any("Hauptrolle" in err and "Beschreibung" in err for err in critical)
    
    def test_wrong_field_types(self, invalid_cv_data):
        """Test that wrong field types are detected"""
        critical, info = validate_json_structure(invalid_cv_data)
        
        # Fachwissen_und_Schwerpunkte should be array, not string
        assert any("Fachwissen_und_Schwerpunkte" in err and "Array" in err for err in critical)
    
    def test_fachwissen_structure(self, valid_cv_data):
        """Test Fachwissen array structure validation"""
        # Modify fixture to have invalid Fachwissen structure
        data = valid_cv_data.copy()
        data["Fachwissen_und_Schwerpunkte"] = [
            {"Kategorie": "Test"}  # Missing "Inhalt" field
        ]
        
        critical, info = validate_json_structure(data)
        
        assert any("Fachwissen" in err and "Inhalt" in err for err in critical)
    
    def test_ausbildung_structure(self, valid_cv_data):
        """Test Ausbildung array structure validation"""
        data = valid_cv_data.copy()
        data["Aus_und_Weiterbildung"] = [
            {"Zeitraum": "2020"}  # Missing Institution and Abschluss
        ]
        
        critical, info = validate_json_structure(data)
        
        assert any("Aus_und_Weiterbildung" in err for err in critical)


class TestLanguageLevelValidation:
    """Tests for language level validation functions"""
    
    def test_valid_numeric_levels(self):
        """Test numeric levels 1-5 are valid"""
        for level in range(1, 6):
            assert is_valid_level(level) is True
    
    def test_invalid_numeric_levels(self):
        """Test numeric levels outside 1-5 are invalid"""
        assert is_valid_level(0) is False
        assert is_valid_level(6) is False
        assert is_valid_level(-1) is False
    
    def test_valid_text_levels(self):
        """Test valid text level descriptions"""
        valid_texts = [
            "Muttersprache",
            "Verhandlungssicher",
            "Sehr gute Kenntnisse",
            "Gute Kenntnisse",
            "Grundkenntnisse"
        ]
        
        for text in valid_texts:
            assert is_valid_level(text) is True
    
    def test_parse_level_from_text(self):
        """Test parsing levels from text"""
        assert parse_level("Muttersprache") == 5
        assert parse_level("Verhandlungssicher") == 4
        assert parse_level("Sehr gute Kenntnisse") == 3
        assert parse_level("Gute Kenntnisse") == 2
        assert parse_level("Grundkenntnisse") == 1
    
    def test_parse_level_from_number(self):
        """Test parsing levels from numbers"""
        assert parse_level(5) == 5
        assert parse_level(3) == 3
        assert parse_level(1) == 1
    
    def test_parse_level_from_string_number(self):
        """Test parsing levels from string numbers"""
        assert parse_level("5 - Muttersprache") == 5
        assert parse_level("4 - Verhandlungssicher") == 4
    
    def test_invalid_level_returns_zero(self):
        """Test that invalid levels return 0"""
        assert parse_level("Invalid") == 0
        assert parse_level("") == 0


class TestReferenzprojekteValidation:
    """Tests for project reference validation"""
    
    def test_referenzprojekte_required_fields(self):
        """Test that projects must have all required fields"""
        data = {
            "Vorname": "Test",
            "Nachname": "User",
            "Hauptrolle": {"Titel": "Dev", "Beschreibung": "Test description here"},
            "Nationalität": "CH",
            "Ausbildung": "Bachelor",
            "Kurzprofil": "Test profile text",
            "Fachwissen_und_Schwerpunkte": [],
            "Aus_und_Weiterbildung": [],
            "Trainings_und_Zertifizierungen": [],
            "Sprachen": [],
            "Ausgewählte_Referenzprojekte": [
                {
                    "Zeitraum": "2023",
                    # Missing Rolle, Kunde, Tätigkeiten
                }
            ]
        }
        
        critical, info = validate_json_structure(data)
        
        assert any("Referenzprojekte" in err and "Rolle" in err for err in critical)
        assert any("Referenzprojekte" in err and "Kunde" in err for err in critical)
        assert any("Referenzprojekte" in err and "Tätigkeiten" in err for err in critical)
    
    def test_taetigkeiten_must_be_array(self):
        """Test that Tätigkeiten must be an array"""
        data = {
            "Vorname": "Test",
            "Nachname": "User",
            "Hauptrolle": {"Titel": "Dev", "Beschreibung": "Test description"},
            "Nationalität": "CH",
            "Ausbildung": "Bachelor",
            "Kurzprofil": "Profile",
            "Fachwissen_und_Schwerpunkte": [],
            "Aus_und_Weiterbildung": [],
            "Trainings_und_Zertifizierungen": [],
            "Sprachen": [],
            "Ausgewählte_Referenzprojekte": [
                {
                    "Zeitraum": "2023",
                    "Rolle": "Developer",
                    "Kunde": "Company",
                    "Tätigkeiten": "Not an array"  # Should be array
                }
            ]
        }
        
        critical, info = validate_json_structure(data)
        
        assert any("Tätigkeiten" in err and "Array" in err for err in critical)
