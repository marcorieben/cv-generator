import os
import json
import time
import sys
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Callable

# Local imports
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv, validate_json_structure
from scripts.generate_matchmaking import generate_matchmaking_json
from scripts.generate_cv_feedback import generate_cv_feedback_json
from scripts.generate_angebot import generate_angebot_json
from scripts.generate_angebot_word import generate_angebot_word
from scripts.visualize_results import generate_dashboard
from scripts.naming_conventions import (
    extract_job_profile_name,
    extract_job_profile_name_from_file,
    extract_candidate_name_from_file,
    extract_candidate_name,
    get_output_folder_path,
    get_cv_json_filename,
    get_match_json_filename,
    get_feedback_json_filename,
    get_dashboard_html_filename,
    get_angebot_json_filename,
    get_angebot_word_filename,
    get_stellenprofil_json_filename
)

class StreamlitCVGenerator:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
            language: str = "de",
            job_profile_context: Dict[str, Any] = None,
            output_dir: str = None,
            job_profile_name: str = None) -> Dict[str, Any]:
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
            job_profile_context: Pre-extracted Stellenprofil data (from batch mode)
            output_dir: Optional output directory path (when in batch mode, use candidate subfolder)
            job_profile_name: Optional pre-extracted job profile name (from batch mode). If provided, this overrides auto-detection.
        """
        # Load translations
        trans_path = os.path.join(self.base_dir, "scripts", "translations.json")
        translations = {}
        try:
            with open(trans_path, "r", encoding="utf-8") as f:
                translations = json.load(f)
        except:
            pass

        def get_text(section, key, lang="de"):
            try:
                return translations.get(section, {}).get(key, {}).get(lang, key)
            except:
                return key
        
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
            "error": None
        }

        try:
            # --- PHASE 1: PDF Extraction ---
            print(f"\n🔍 [streamlit_pipeline] Starting CV processing", file=sys.stderr)
            print(f"   job_profile_name param: {job_profile_name}", file=sys.stderr)
            print(f"   output_dir param: {output_dir}", file=sys.stderr)
            print(f"   job_profile_context provided: {job_profile_context is not None}", file=sys.stderr)
            
            stellenprofil_data = job_profile_context  # Use pre-extracted context if provided (batch mode)
            
            if job_file and not job_profile_context:
                # Extract Stellenprofil from job_file if not provided as context
                if progress_callback: progress_callback(10, get_text('ui', 'status_extract_job', language), "running")
                job_schema_path = os.path.join(self.base_dir, "scripts", "pdf_to_json_struktur_stellenprofil.json")
                stellenprofil_data = pdf_to_json(job_file, None, job_schema_path, target_language=language)

            if progress_callback: progress_callback(30, get_text('ui', 'status_extract_cv', language), "running")
            cv_data = pdf_to_json(cv_file, output_path=None, job_profile_context=stellenprofil_data, target_language=language)
            
            # Extract job profile name from both data and filename (filename takes priority if meaningful)
            # But if job_profile_name was provided as parameter (from batch mode), use that
            if job_profile_name and job_profile_name != "jobprofile":
                # Use the provided job_profile_name (from batch mode)
                pass  # job_profile_name is already set
            else:
                # Auto-detect job profile name
                job_profile_name_from_data = extract_job_profile_name(stellenprofil_data)
                job_profile_name_from_file = extract_job_profile_name_from_file(job_file.name if hasattr(job_file, 'name') else str(job_file)) if job_file else None
                
                # Use filename extraction if it's not generic, otherwise use data extraction
                if job_profile_name_from_file and job_profile_name_from_file != "jobprofile":
                    job_profile_name = job_profile_name_from_file
                else:
                    job_profile_name = job_profile_name_from_data
            
            # Ensure job_profile_name is set
            if not job_profile_name or job_profile_name == "":
                job_profile_name = "jobprofile"
            
            # Extract candidate name from both data and filename (data takes priority for accuracy)
            vorname = cv_data.get("Vorname", get_text('ui', 'history_unknown', language))
            nachname = cv_data.get("Nachname", "")
            candidate_name_from_data = extract_candidate_name(cv_data) if (vorname or nachname) else None
            candidate_name_from_file = extract_candidate_name_from_file(cv_file.name if hasattr(cv_file, 'name') else str(cv_file)) if cv_file else None
            
            # Use data extraction if available (more accurate), otherwise use filename
            candidate_folder_name = candidate_name_from_data if candidate_name_from_data and candidate_name_from_data != "candidate" else candidate_name_from_file
            
            # Ensure candidate_folder_name is set
            if not candidate_folder_name or candidate_folder_name == "":
                candidate_folder_name = "candidate"
            
            # Use provided output_dir (batch mode) or create new folder (standard mode)
            if output_dir:
                # Batch mode: use provided candidate subfolder
                os.makedirs(output_dir, exist_ok=True)
                final_output_dir = output_dir
            else:
                # Standard mode: create new folder with jobprofileName_candidateName_timestamp
                base_output = os.path.join(self.base_dir, "output")
                # For non-batch mode, include candidate name in folder path for better organization
                folder_name = f"{job_profile_name}_{candidate_folder_name}_{self.timestamp}"
                final_output_dir = os.path.join(base_output, folder_name)
                os.makedirs(final_output_dir, exist_ok=True)
            
            # Save CV JSON with unified naming
            cv_json_filename = get_cv_json_filename(job_profile_name, vorname, nachname, self.timestamp)
            cv_json_path = os.path.join(final_output_dir, cv_json_filename)
            with open(cv_json_path, 'w', encoding='utf-8') as f:
                json.dump(cv_data, f, ensure_ascii=False, indent=2)
            results["cv_json"] = cv_json_path
            results["vorname"] = vorname
            results["nachname"] = nachname
                
            # Save Stellenprofil JSON with unified naming
            stellenprofil_json_path = None
            if stellenprofil_data:
                stellenprofil_filename = get_stellenprofil_json_filename(job_profile_name, self.timestamp)
                stellenprofil_json_path = os.path.join(final_output_dir, stellenprofil_filename)
                with open(stellenprofil_json_path, 'w', encoding='utf-8') as f:
                    json.dump(stellenprofil_data, f, ensure_ascii=False, indent=2)
                results["stellenprofil_json"] = stellenprofil_json_path

            # --- STEP 3: Validation ---
            if progress_callback: progress_callback(50, get_text('ui', 'status_validate', language), "running")
            critical, info = validate_json_structure(cv_data, language=language)
            if critical:
                val_error_prefix = get_text('validation', 'error_prefix', language) if 'validation' in translations else "Validierungsfehler"
                raise ValueError(f"{val_error_prefix}: {'; '.join(critical)}")

            # --- STEP 4: Generation (Word, Match, Feedback) ---
            if progress_callback: progress_callback(70, get_text('ui', 'status_generate', language), "running")
            
            word_path = None
            matchmaking_json_path = None
            feedback_json_path = None
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Word (interactive=False to suppress dialogs)
                future_word = executor.submit(generate_cv, cv_json_path, final_output_dir, interactive=False, language=language)
                
                # Match
                future_match = None
                if stellenprofil_json_path:
                    match_filename = get_match_json_filename(job_profile_name, vorname, nachname, self.timestamp)
                    matchmaking_json_path = os.path.join(final_output_dir, match_filename)
                    schema_path = os.path.join(self.base_dir, "scripts", "matchmaking_json_schema.json")
                    future_match = executor.submit(
                        generate_matchmaking_json,
                        cv_json_path,
                        stellenprofil_json_path,
                        matchmaking_json_path,
                        schema_path,
                        language=language
                    )
                
                # Feedback
                feedback_filename = get_feedback_json_filename(job_profile_name, vorname, nachname, self.timestamp)
                feedback_json_path = os.path.join(final_output_dir, feedback_filename)
                feedback_schema_path = os.path.join(self.base_dir, "scripts", "cv_feedback_json_schema.json")
                future_feedback = executor.submit(
                    generate_cv_feedback_json,
                    cv_json_path,
                    feedback_json_path,
                    feedback_schema_path,
                    stellenprofil_json_path,
                    language=language
                )
                
                word_path = future_word.result()
                if future_match: future_match.result()
                future_feedback.result()

            # --- STEP 4.5: Offer (Background) ---
            angebot_json_path = None
            if pipeline_mode == "Full" and stellenprofil_json_path and matchmaking_json_path:
                if progress_callback: progress_callback(85, get_text('ui', 'status_offer', language), "running")
                try:
                    angebot_json_filename = get_angebot_json_filename(job_profile_name, vorname, nachname, self.timestamp)
                    angebot_json_path = os.path.join(final_output_dir, angebot_json_filename)
                    # Generate JSON
                    generate_angebot_json(cv_json_path, stellenprofil_json_path, matchmaking_json_path, angebot_json_path, language=language)
                    
                    # Generate Word
                    angebot_word_filename = get_angebot_word_filename(job_profile_name, vorname, nachname, self.timestamp)
                    angebot_word_path = os.path.join(final_output_dir, angebot_word_filename)
                    generate_angebot_word(angebot_json_path, angebot_word_path, language=language)
                    
                    results["offer_word_path"] = angebot_word_path
                except Exception as e:
                    print(f"⚠️ Fehler bei Angebotserstellung: {str(e)}")

            results["word_path"] = word_path
            results["match_json"] = matchmaking_json_path

            # --- STEP 5: Dashboard ---
            if progress_callback: progress_callback(90, get_text('ui', 'status_dashboard', language), "running")
            
            dashboard_path = generate_dashboard(
                cv_json_path=cv_json_path,
                match_json_path=matchmaking_json_path if matchmaking_json_path and os.path.exists(matchmaking_json_path) else None,
                feedback_json_path=feedback_json_path,
                output_dir=final_output_dir,
                validation_warnings=info,
                model_name=os.environ.get("MODEL_NAME", "gpt-4o"),
                pipeline_mode=pipeline_mode,
                cv_filename=cv_file.name if hasattr(cv_file, 'name') else os.path.basename(str(cv_file)),
                job_filename=job_file.name if job_file and hasattr(job_file, 'name') else (os.path.basename(str(job_file)) if job_file else None),
                angebot_json_path=angebot_json_path,
                language=language
            )
            results["dashboard_path"] = dashboard_path

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
            
        except Exception as e:
            error_msg = str(e)
            tb_str = traceback.format_exc()
            results["error"] = error_msg
            print(f"❌ [streamlit_pipeline] Exception: {error_msg}", file=sys.stderr)
            print(f"Full traceback:\n{tb_str}", file=sys.stderr)
            if progress_callback: progress_callback(100, f"{get_text('ui', 'error_status', language)}: {error_msg}", "error")
            
        return results
