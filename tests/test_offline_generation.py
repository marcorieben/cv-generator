"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2025-12-24
Last Updated: 2026-01-24
"""
import os
import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts._2_extraction_cv.cv_word import generate_cv
from scripts._6_output_dashboard.dashboard_generator import generate_dashboard

class TestOfflineGeneration:
    """
    Tests the generation of artifacts (Word, HTML) from existing JSON data.
    This ensures we can test the visual output logic without incurring AI costs.
    """

    @pytest.fixture
    def test_data_dir(self):
        return Path(__file__).parent / "test_data" / "complete_run"

    @pytest.fixture
    def output_dir(self, tmp_path):
        return tmp_path

    def test_generate_cv_from_json(self, test_data_dir, output_dir):
        """Test generating a Word CV from a saved JSON file."""
        # Find the CV JSON file
        cv_json_files = list(test_data_dir.glob("*_Mustermann_*.json"))
        # Filter out Match, Feedback, Stellenprofil
        cv_json_path = next(
            f for f in cv_json_files 
            if not f.name.startswith("Match_") 
            and not f.name.startswith("CV_Feedback_") 
            and not f.name.startswith("Stellenprofil_")
            and not f.name.startswith("Angebot_")
        )
        
        assert cv_json_path.exists(), "CV JSON file not found in test data"

        # Run generation
        # generate_cv expects an output DIRECTORY, not a file path
        generate_cv(str(cv_json_path), str(output_dir), interactive=False)

        # Check if any .docx file was created in the output directory
        docx_files = list(output_dir.glob("*.docx"))
        assert len(docx_files) > 0, "No .docx file created"
        assert docx_files[0].stat().st_size > 0

    def test_generate_dashboard_from_json(self, test_data_dir, output_dir):
        """Test generating the HTML dashboard from saved JSON files."""
        # Locate files
        cv_json = next(f for f in test_data_dir.glob("*_Mustermann_*.json") if "Match" not in f.name and "Feedback" not in f.name and "Stellenprofil" not in f.name)
        match_json = next(test_data_dir.glob("Match_*.json"))
        feedback_json = next(test_data_dir.glob("CV_Feedback_*.json"))
        
        # F003: generate_dashboard now returns (bytes, filename) tuple
        dashboard_bytes, dashboard_filename = generate_dashboard(
            str(cv_json),
            str(match_json),
            str(feedback_json),
            str(output_dir)
        )

        assert isinstance(dashboard_bytes, bytes)
        assert len(dashboard_bytes) > 0
        assert dashboard_filename.endswith(".html")
        
        content = dashboard_bytes.decode('utf-8')
        assert "Dashboard" in content
        assert "CV Analyse" in content
