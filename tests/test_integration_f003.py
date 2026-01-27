"""
Integration tests for F003 Storage Abstraction feature.

Tests the complete pipeline with bytes-based generators and RunWorkspace.

Purpose: Integration test
Expected Lifetime: Permanent (core functionality)
Last Updated: 2026-01-27
"""

import json
import os
import pytest
from pathlib import Path
from zipfile import ZipFile

from core.storage import RunWorkspace, generate_run_id
from scripts._2_extraction_cv import generate_cv_bytes
from scripts._5_generation_offer import generate_offer_bytes
from scripts._6_output_dashboard.dashboard_generator import generate_dashboard


class TestF003Integration:
    """Integration tests for F003 Storage Abstraction."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get path to test fixtures."""
        return Path(__file__).parent / "test_data" / "complete_run"
    
    @pytest.fixture
    def cv_data(self, test_data_dir):
        """Load test CV JSON data."""
        cv_json_path = test_data_dir / "Max_Mustermann_20251218_182547.json"
        with open(cv_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def match_data(self, test_data_dir):
        """Load test matchmaking JSON data."""
        match_json_path = test_data_dir / "Match_Max_Mustermann_20251218_182547.json"
        with open(match_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def feedback_data(self, test_data_dir):
        """Load test feedback JSON data."""
        feedback_json_path = test_data_dir / "CV_Feedback_Max_Mustermann_20251218_182547.json"
        with open(feedback_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_generate_run_id_from_cv_data(self, cv_data):
        """Test run ID generation with real CV data."""
        from datetime import datetime
        
        run_id = generate_run_id(
            jobprofile_title="Senior Python Developer",
            firstname=cv_data["Vorname"],
            lastname=cv_data["Nachname"],
            timestamp=datetime.now()
        )
        
        assert isinstance(run_id, str)
        assert "Max" in run_id or "max" in run_id.lower()
        assert "Mustermann" in run_id or "mustermann" in run_id.lower()
        assert len(run_id.split("_")) == 3  # jobprofile_candidate_timestamp
    
    def test_cv_generator_with_workspace(self, cv_data):
        """Test CV generator produces valid bytes and saves to workspace."""
        from datetime import datetime
        
        run_id = generate_run_id("Test-Job", cv_data["Vorname"], cv_data["Nachname"], datetime.now())
        
        with RunWorkspace(run_id) as workspace:
            # Generate CV
            cv_bytes, cv_filename = generate_cv_bytes(cv_data, language="de")
            
            # Save to workspace
            workspace.save_primary(cv_filename, cv_bytes)
            
            # Verify file exists
            primary_files = workspace.list_primary_files()
            assert cv_filename in primary_files
            
            # Retrieve and verify
            retrieved_bytes = workspace.get_primary(cv_filename)
            assert retrieved_bytes == cv_bytes
            assert len(retrieved_bytes) > 0
    
    def test_offer_generator_with_workspace(self, cv_data):
        """Test Offer generator produces valid bytes and saves to workspace."""
        from datetime import datetime
        
        # Create offer data structure
        offer_data = {
            "Kandidat": cv_data,
            "Kriterien_Match": {
                "Übereinstimmung": "85%",
                "Erfüllte_Kriterien": ["Python", "PostgreSQL"],
                "Teilweise_erfüllte_Kriterien": ["AWS"],
                "Nicht_erfüllte_Kriterien": []
            },
            "Konditionen": {
                "Verfügbarkeit": "Ab sofort",
                "Auslastung": "100%",
                "Stundensatz": "CHF 150"
            },
            "Bewertung": {
                "Stärken": ["Sehr gute Python-Kenntnisse"],
                "Entwicklungspotential": ["Cloud-Erfahrung ausbauen"]
            }
        }
        
        run_id = generate_run_id("Test-Job", cv_data["Vorname"], cv_data["Nachname"], datetime.now())
        
        with RunWorkspace(run_id) as workspace:
            # Generate Offer
            offer_bytes, offer_filename = generate_offer_bytes(offer_data, language="de")
            
            # Save to workspace
            workspace.save_primary(offer_filename, offer_bytes)
            
            # Verify file exists
            primary_files = workspace.list_primary_files()
            assert offer_filename in primary_files
            
            # Retrieve and verify
            retrieved_bytes = workspace.get_primary(offer_filename)
            assert retrieved_bytes == offer_bytes
            assert len(retrieved_bytes) > 0
    
    def test_dashboard_generator_with_workspace(self, test_data_dir, cv_data):
        """Test Dashboard generator produces valid HTML bytes and saves to workspace."""
        from datetime import datetime
        
        # Prepare paths for Dashboard generator
        cv_json_path = str(test_data_dir / "Max_Mustermann_20251218_182547.json")
        match_json_path = str(test_data_dir / "Match_Max_Mustermann_20251218_182547.json")
        feedback_json_path = str(test_data_dir / "CV_Feedback_Max_Mustermann_20251218_182547.json")
        output_dir = str(test_data_dir.parent.parent / "fixtures" / "output")
        
        run_id = generate_run_id("Test-Job", cv_data["Vorname"], cv_data["Nachname"], datetime.now())
        
        with RunWorkspace(run_id) as workspace:
            # Generate Dashboard (returns bytes, filename)
            dashboard_bytes, dashboard_filename = generate_dashboard(
                cv_json_path=cv_json_path,
                match_json_path=match_json_path,
                feedback_json_path=feedback_json_path,
                output_dir=output_dir
            )
            
            # Verify bytes
            assert isinstance(dashboard_bytes, bytes)
            assert len(dashboard_bytes) > 0
            
            # Save to workspace
            workspace.save_primary(dashboard_filename, dashboard_bytes)
            
            # Verify file exists
            primary_files = workspace.list_primary_files()
            assert dashboard_filename in primary_files
            
            # Retrieve and verify content
            retrieved_bytes = workspace.get_primary(dashboard_filename)
            assert retrieved_bytes == dashboard_bytes
            
            # Decode and check HTML structure
            html_content = retrieved_bytes.decode('utf-8')
            assert "Dashboard" in html_content
            assert "Max Mustermann" in html_content
    
    def test_complete_pipeline_with_zip_bundle(self, test_data_dir, cv_data):
        """Test complete pipeline: CV + Offer + Dashboard, then bundle as ZIP."""
        from datetime import datetime
        
        # Prepare Dashboard paths
        cv_json_path = str(test_data_dir / "Max_Mustermann_20251218_182547.json")
        match_json_path = str(test_data_dir / "Match_Max_Mustermann_20251218_182547.json")
        feedback_json_path = str(test_data_dir / "CV_Feedback_Max_Mustermann_20251218_182547.json")
        output_dir = str(test_data_dir.parent.parent / "fixtures" / "output")
        
        # Prepare Offer data
        offer_data = {
            "Kandidat": cv_data,
            "Kriterien_Match": {
                "Übereinstimmung": "90%",
                "Erfüllte_Kriterien": ["Python", "PostgreSQL", "Scrum"],
                "Teilweise_erfüllte_Kriterien": [],
                "Nicht_erfüllte_Kriterien": []
            },
            "Konditionen": {
                "Verfügbarkeit": "Ab sofort",
                "Auslastung": "100%",
                "Stundensatz": "CHF 150"
            },
            "Bewertung": {
                "Stärken": ["Hervorragende Fachkenntnisse", "Kommunikationsstark"],
                "Entwicklungspotential": ["Cloud-Architektur"]
            }
        }
        
        run_id = generate_run_id("Senior-Python-Dev", cv_data["Vorname"], cv_data["Nachname"], datetime.now())
        
        with RunWorkspace(run_id) as workspace:
            # Step 1: Generate and save CV
            cv_bytes, cv_filename = generate_cv_bytes(cv_data, language="de")
            workspace.save_primary(cv_filename, cv_bytes)
            
            # Step 2: Generate and save Offer
            offer_bytes, offer_filename = generate_offer_bytes(offer_data, language="de")
            workspace.save_primary(offer_filename, offer_bytes)
            
            # Step 3: Generate and save Dashboard
            dashboard_bytes, dashboard_filename = generate_dashboard(
                cv_json_path=cv_json_path,
                match_json_path=match_json_path,
                feedback_json_path=feedback_json_path,
                output_dir=output_dir
            )
            workspace.save_primary(dashboard_filename, dashboard_bytes)
            
            # Step 4: Save artifacts (JSON files)
            workspace.save_artifact("cv_data.json", json.dumps(cv_data, indent=2, ensure_ascii=False).encode('utf-8'))
            workspace.save_artifact("offer_data.json", json.dumps(offer_data, indent=2, ensure_ascii=False).encode('utf-8'))
            
            # Step 5: Create ZIP bundle
            zip_bytes = workspace.bundle_as_zip()
            
            # Verify ZIP
            assert isinstance(zip_bytes, bytes)
            assert len(zip_bytes) > 0
            
            # Generate expected filename
            zip_filename = f"{run_id}.zip"
            
            # Step 6: Validate ZIP contents
            from io import BytesIO
            zip_buffer = BytesIO(zip_bytes)
            with ZipFile(zip_buffer, 'r') as zipf:
                zip_contents = zipf.namelist()
                
                # Check primary outputs folder
                assert any('primary_outputs/' in name for name in zip_contents)
                assert any(cv_filename in name for name in zip_contents)
                assert any(offer_filename in name for name in zip_contents)
                assert any(dashboard_filename in name for name in zip_contents)
                
                # Check artifacts folder
                assert any('artifacts/' in name for name in zip_contents)
                assert any('cv_data.json' in name for name in zip_contents)
                assert any('offer_data.json' in name for name in zip_contents)
    
    def test_workspace_isolation(self, cv_data):
        """Test that multiple workspaces don't interfere with each other."""
        from datetime import datetime
        import time
        
        # Create two separate workspaces with different timestamps
        timestamp1 = datetime.now()
        time.sleep(0.01)  # Ensure different timestamps
        timestamp2 = datetime.now()
        
        run_id_1 = generate_run_id("Job-A", cv_data["Vorname"], cv_data["Nachname"], timestamp1)
        run_id_2 = generate_run_id("Job-B", cv_data["Vorname"], cv_data["Nachname"], timestamp2)
        
        workspace_1 = RunWorkspace(run_id_1)
        workspace_2 = RunWorkspace(run_id_2)
        
        try:
            # Generate different content for each workspace
            cv_bytes_1, cv_filename_1 = generate_cv_bytes(cv_data, language="de")
            cv_bytes_2, cv_filename_2 = generate_cv_bytes(cv_data, language="en")
            
            # Filenames will be the same (based on candidate name), but workspace paths differ
            workspace_1.save_primary(cv_filename_1, cv_bytes_1)
            workspace_2.save_primary(cv_filename_2, cv_bytes_2)
            
            # Verify isolation - check workspaces have different root paths
            assert workspace_1.root != workspace_2.root
            
            # Verify each workspace has its own files
            files_1 = workspace_1.list_primary_files()
            files_2 = workspace_2.list_primary_files()
            
            assert cv_filename_1 in files_1
            assert cv_filename_2 in files_2
            
            # Verify content is different (DE vs EN)
            content_1 = workspace_1.get_primary(cv_filename_1)
            content_2 = workspace_2.get_primary(cv_filename_2)
            assert content_1 != content_2  # Different languages = different content
            
        finally:
            workspace_1.cleanup()
            workspace_2.cleanup()
