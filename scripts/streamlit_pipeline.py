"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-12
Last Updated: 2026-01-27
"""
import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Callable

# Local imports
from scripts._2_extraction_cv.cv_extractor import extract_cv
from scripts._1_extraction_jobprofile.jobprofile_extractor import extract_jobprofile
from scripts._2_extraction_cv.cv_word import generate_cv_bytes, validate_json_structure  # F003: Use bytes API
from scripts._3_analysis_matchmaking.matchmaking_generator import generate_matchmaking_json
from scripts._4_analysis_feedback.feedback_generator import generate_cv_feedback_json
from scripts._5_generation_offer.offer_generator import generate_angebot_json
from scripts._5_generation_offer.offer_word import generate_offer_bytes  # F003: Use bytes API
from scripts._6_output_dashboard.dashboard_generator import generate_dashboard
from scripts.utils.translations import load_translations, get_text as _get_text
from core.storage.workspace import RunWorkspace  # F003: Storage abstraction
from core.storage.run_id import generate_run_id  # F003: Run ID generation
from core.utils.naming import (  # New naming conventions
    generate_jobprofile_slug,
    generate_candidate_name,
    generate_filename,
    generate_folder_name,
    FileType
)

class StreamlitCVGenerator:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.timestamp_dt = datetime.now()  # F003: Keep datetime object for run_id
        self.timestamp = self.timestamp_dt.strftime("%Y%m%d_%H%M%S")  # String for file names
        self.workspace = None  # F003: Will be initialized with run_id

    def _update_styles(self, custom_styles, custom_logo_path):
        """Updates the styles.json file with custom values."""
        styles_path = os.path.join(self.base_dir, "scripts", "styles.json")
        try:
            with open(styles_path, 'r', encoding='utf-8') as f:
                styles = json.load(f)
            
            if custom_styles:
                # Convert hex to RGB list
                def hex_to_rgb(hex_color):
                    hex_color = hex_color.lstrip('#')
                    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

                if "primary_color" in custom_styles:
                    rgb = hex_to_rgb(custom_styles["primary_color"])
                    styles["heading1"]["color"] = list(rgb)
                    styles["bullet"]["color"] = list(rgb)
                    styles["header"]["text_color"] = list(rgb)
                
                if "secondary_color" in custom_styles:
                    rgb = hex_to_rgb(custom_styles["secondary_color"])
                    styles["heading2"]["color"] = list(rgb)
                
                if "font" in custom_styles:
                    font = custom_styles["font"]
                    styles["heading1"]["font"] = font
                    styles["heading2"]["font"] = font
                    styles["text"]["font"] = font
                    styles["bullet"]["font"] = font
                    styles["header"]["text_font"] = font

            if custom_logo_path:
                # Ensure path is relative or absolute as needed by generate_cv
                # generate_cv uses abs_path relative to scripts dir usually
                # We'll use absolute path here to be safe
                styles["header"]["logo_path"] = os.path.abspath(custom_logo_path)

            with open(styles_path, 'w', encoding='utf-8') as f:
                json.dump(styles, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Warning: Could not update styles: {e}")

    def run(self, 
            cv_file, 
            job_file=None, 
            api_key: str = None, 
            progress_callback: Callable[[int, str, str], None] = None,
            custom_styles: Dict[str, Any] = None,
            custom_logo_path: str = None,
            pipeline_mode: str = None,
            language: str = "de") -> Dict[str, Any]:
        """
        Runs the CV generation pipeline.
        
        Args:
            cv_file: File object or path to CV PDF
            job_file: File object or path to Job Profile PDF (optional)
            api_key: OpenAI API Key
            progress_callback: Function(progress_0_to_100, status_text, state)
            custom_styles: Dict with keys 'primary_color', 'secondary_color', 'font'
            custom_logo_path: Path to custom logo file
            pipeline_mode: The selected pipeline mode (e.g. "Basic", "Full")
            language: Target language (de, en, fr)
        """
        # Load translations
        translations = load_translations()

        def get_text(section, key, lang="de"):
            return _get_text(translations, section, key, lang)
        
        # Set API Key
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            
        # Update styles.json if custom styles are provided
        if custom_styles or custom_logo_path:
            self._update_styles(custom_styles, custom_logo_path)
            
        results = {
            "success": False,
            "cv_json": None,
            "word_path": None,
            "dashboard_path": None,
            "match_score": None,
            "stellenprofil_json": None,
            "match_json": None,
            "model_name": os.environ.get("MODEL_NAME", "gpt-4o-mini"),
            "error": None,
            "performance_metrics": {}  # Performance measurements
        }
        
        # Performance tracking
        perf_start = time.time()
        perf_times = {}

        try:
            # --- PHASE 1: PDF Extraction ---
            phase_1_start = time.time()
            stellenprofil_data = None
            if job_file:
                if progress_callback: progress_callback(10, get_text('ui', 'status_extract_job', language), "running")
                stellenprofil_data = extract_jobprofile(job_file, output_path=None, target_language=language)

            if progress_callback: progress_callback(30, get_text('ui', 'status_extract_cv', language), "running")
            cv_data = extract_cv(cv_file, output_path=None, job_profile_context=stellenprofil_data, target_language=language)
            perf_times["PDF Extraction"] = round(time.time() - phase_1_start, 2)
            
            # Save JSONs
            vorname = cv_data.get("Vorname", get_text('ui', 'history_unknown', language))
            nachname = cv_data.get("Nachname", "")
            
            # Extract jobprofile metadata for naming (new naming convention)
            jobprofile_id = None
            jobprofile_title = "Unbekannte-Stelle"
            if stellenprofil_data:
                # Try to get document_id from metadata
                jobprofile_id = stellenprofil_data.get("metadata", {}).get("document_id")
                jobprofile_title = stellenprofil_data.get("titel", "Unbekannte-Stelle")
                # Clean document_id if it's the missing marker
                if jobprofile_id and ("bitte prüfen" in str(jobprofile_id) or jobprofile_id == ""):
                    jobprofile_id = None
            
            # Generate naming components using new convention
            jobprofile_slug = generate_jobprofile_slug(jobprofile_id, jobprofile_title)
            candidate_name = generate_candidate_name(vorname, nachname)
            folder_name = generate_folder_name(jobprofile_slug, candidate_name, self.timestamp)
            
            # F003: Initialize RunWorkspace early for artifact storage
            run_id = generate_run_id(jobprofile_title, vorname, nachname, self.timestamp_dt)
            self.workspace = RunWorkspace(run_id)
            
            # F003: Use temp directory for intermediate JSON files (needed by legacy functions)
            # These are only used during pipeline execution, not persisted
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="cv_pipeline_")
            
            # Use new naming convention for CV JSON (temp storage for legacy functions)
            cv_json_filename = generate_filename(jobprofile_slug, candidate_name, "cv_extracted", self.timestamp, "json")
            cv_json_path = os.path.join(temp_dir, cv_json_filename)
            with open(cv_json_path, 'w', encoding='utf-8') as f:
                json.dump(cv_data, f, ensure_ascii=False, indent=2)
            
            # Store CV JSON in workspace as artifact (persistent)
            cv_json_bytes = json.dumps(cv_data, ensure_ascii=False, indent=2).encode('utf-8')
            self.workspace.save_artifact(cv_json_filename, cv_json_bytes)
            
            results["cv_json"] = cv_json_path  # Temp path for legacy compatibility
            results["cv_data"] = cv_data  # Store data directly
            results["vorname"] = vorname
            results["nachname"] = nachname
            results["jobprofile_slug"] = jobprofile_slug
            results["candidate_name"] = candidate_name
                
            stellenprofil_json_path = None
            if stellenprofil_data:
                # Use new naming convention for Stellenprofil JSON (temp storage)
                jobprofile_json_filename = generate_filename(jobprofile_slug, candidate_name, FileType.JOBPROFILE, self.timestamp, "json")
                stellenprofil_json_path = os.path.join(temp_dir, jobprofile_json_filename)
                with open(stellenprofil_json_path, 'w', encoding='utf-8') as f:
                    json.dump(stellenprofil_data, f, ensure_ascii=False, indent=2)
                
                # Store in workspace as artifact
                jobprofile_json_bytes = json.dumps(stellenprofil_data, ensure_ascii=False, indent=2).encode('utf-8')
                self.workspace.save_artifact(jobprofile_json_filename, jobprofile_json_bytes)
                
                results["stellenprofil_json"] = stellenprofil_json_path  # Temp path
                results["stellenprofil_data"] = stellenprofil_data  # Store data directly

            # --- STEP 3: Validation ---
            validation_start = time.time()
            if progress_callback: progress_callback(50, get_text('ui', 'status_validate', language), "running")
            critical, info = validate_json_structure(cv_data, language=language)
            if critical:
                val_error_prefix = get_text('validation', 'error_prefix', language) if 'validation' in translations else "Validierungsfehler"
                raise ValueError(f"{val_error_prefix}: {'; '.join(critical)}")
            perf_times["Validation"] = round(time.time() - validation_start, 2)

            # --- STEP 4: Generation (Match, Feedback, CV Word) ---
            generation_start = time.time()
            if progress_callback: progress_callback(70, get_text('ui', 'status_generate', language), "running")
            
            # Generate CV Word document using bytes API with naming conventions
            cv_bytes, cv_filename = generate_cv_bytes(
                cv_data, 
                language=language,
                jobprofile_slug=jobprofile_slug,
                timestamp=self.timestamp
            )
            self.workspace.save_primary(cv_filename, cv_bytes)
            results["cv_word_bytes"] = cv_bytes
            results["cv_word_filename"] = cv_filename
            
            matchmaking_json_path = None
            feedback_json_path = None
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Match
                future_match = None
                if stellenprofil_json_path:
                    # Use new naming convention for Match JSON (temp storage)
                    match_json_filename = generate_filename(jobprofile_slug, candidate_name, FileType.MATCH, self.timestamp, "json")
                    matchmaking_json_path = os.path.join(temp_dir, match_json_filename)
                    schema_path = os.path.join(self.base_dir, "scripts", "_3_analysis_matchmaking", "matchmaking_schema.json")
                    future_match = executor.submit(
                        generate_matchmaking_json,
                        cv_json_path,
                        stellenprofil_json_path,
                        matchmaking_json_path,
                        schema_path,
                        language=language
                    )
                
                # Feedback - use new naming convention (temp storage)
                feedback_json_filename = generate_filename(jobprofile_slug, candidate_name, FileType.FEEDBACK, self.timestamp, "json")
                feedback_json_path = os.path.join(temp_dir, feedback_json_filename)
                feedback_schema_path = os.path.join(self.base_dir, "scripts", "_4_analysis_feedback", "feedback_schema.json")
                future_feedback = executor.submit(
                    generate_cv_feedback_json,
                    cv_json_path,
                    feedback_json_path,
                    feedback_schema_path,
                    stellenprofil_json_path,
                    language=language
                )
                
                if future_match: 
                    future_match.result()
                    # Save Match JSON to workspace as artifact
                    if os.path.exists(matchmaking_json_path):
                        with open(matchmaking_json_path, 'rb') as f:
                            self.workspace.save_artifact(match_json_filename, f.read())
                        results["match_json"] = matchmaking_json_path
                
                future_feedback.result()
                # Save Feedback JSON to workspace as artifact
                if os.path.exists(feedback_json_path):
                    with open(feedback_json_path, 'rb') as f:
                        self.workspace.save_artifact(feedback_json_filename, f.read())
            
            perf_times["Match & Feedback Generation"] = round(time.time() - generation_start, 2)

            # --- STEP 4.5: Offer (Background) ---
            offer_start = time.time()
            angebot_json_path = None
            if pipeline_mode == "Full" and stellenprofil_json_path and matchmaking_json_path:
                if progress_callback: progress_callback(85, get_text('ui', 'status_offer', language), "running")
                try:
                    # Use new naming convention for Angebot JSON (temp storage)
                    angebot_json_filename = generate_filename(jobprofile_slug, candidate_name, "angebot", self.timestamp, "json")
                    angebot_json_path = os.path.join(temp_dir, angebot_json_filename)
                    # Generate JSON
                    generate_angebot_json(cv_json_path, stellenprofil_json_path, matchmaking_json_path, angebot_json_path, language=language)
                    
                    # F003: Save Angebot JSON to workspace and load for Word generation
                    with open(angebot_json_path, 'rb') as f:
                        angebot_json_bytes = f.read()
                        self.workspace.save_artifact(angebot_json_filename, angebot_json_bytes)
                    
                    with open(angebot_json_path, 'r', encoding='utf-8') as f:
                        offer_data = json.load(f)
                    offer_bytes, offer_filename = generate_offer_bytes(
                        offer_data, 
                        language=language,
                        jobprofile_slug=jobprofile_slug,
                        timestamp=self.timestamp
                    )
                    self.workspace.save_primary(offer_filename, offer_bytes)
                    results["offer_word_bytes"] = offer_bytes
                    results["offer_word_filename"] = offer_filename
                except Exception as e:
                    print(f"⚠️ Fehler bei Angebotserstellung: {str(e)}")
            
            perf_times["Offer Generation"] = round(time.time() - offer_start, 2)

            results["workspace"] = self.workspace  # F003: Provide workspace for ZIP download
            results["run_id"] = run_id  # F003: Business-meaningful run identifier
            
            # F003: Cleanup temp directory after pipeline completion
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Best effort cleanup

            # --- STEP 5: Dashboard ---
            dashboard_start = time.time()
            if progress_callback: progress_callback(90, get_text('ui', 'status_dashboard', language), "running")
            
            # F003: Generate Dashboard using bytes API (with temp paths)
            dashboard_bytes, dashboard_filename = generate_dashboard(
                cv_json_path=cv_json_path,
                match_json_path=matchmaking_json_path if matchmaking_json_path and os.path.exists(matchmaking_json_path) else None,
                feedback_json_path=feedback_json_path,
                output_dir=temp_dir,  # Use temp_dir instead of persistent output_dir
                validation_warnings=info,
                model_name=os.environ.get("MODEL_NAME", "gpt-4o"),
                pipeline_mode=pipeline_mode,
                cv_filename=cv_file.name if hasattr(cv_file, 'name') else os.path.basename(str(cv_file)),
                job_filename=job_file.name if job_file and hasattr(job_file, 'name') else (os.path.basename(str(job_file)) if job_file else None),
                angebot_json_path=angebot_json_path,
                language=language,
                jobprofile_slug=jobprofile_slug,
                timestamp=self.timestamp
            )
            self.workspace.save_primary(dashboard_filename, dashboard_bytes)
            results["dashboard_bytes"] = dashboard_bytes
            results["dashboard_filename"] = dashboard_filename
            perf_times["Dashboard Generation"] = round(time.time() - dashboard_start, 2)
            
            # Calculate total pipeline duration
            perf_times["Total Pipeline"] = round(time.time() - perf_start, 2)
            results["performance_metrics"] = perf_times
            
            # Display performance metrics
            print("\n" + "="*60)
            print("⏱️  PERFORMANCE METRICS")
            print("="*60)
            for phase, duration in perf_times.items():
                bar_length = int(duration * 2)
                bar = "█" * bar_length
                print(f"{phase:.<35} {duration:>6.2f}s {bar}")
            print("="*60 + "\n")

            # Final success
            if progress_callback: progress_callback(100, get_text('ui', 'status_complete', language), "complete")
            
            # Get Match Score
            if matchmaking_json_path and os.path.exists(matchmaking_json_path):
                try:
                    with open(matchmaking_json_path, 'r', encoding='utf-8') as f:
                        match_data = json.load(f)
                        score_val = match_data.get("match_score", {}).get("score_gesamt")
                        if score_val:
                            if isinstance(score_val, str):
                                score_val = score_val.replace('%', '').strip()
                                if score_val.isdigit():
                                    results["match_score"] = int(score_val)
                            elif isinstance(score_val, (int, float)):
                                results["match_score"] = int(score_val)
                except Exception:
                    pass

            results["success"] = True
            results["timestamp"] = self.timestamp  # Store for ZIP filename generation
            
        except Exception as e:
            results["error"] = str(e)
            if progress_callback: progress_callback(100, f"{get_text('ui', 'error_status', language)}: {str(e)}", "error")
            
        return results
