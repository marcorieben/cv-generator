import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Callable

# Local imports
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv, validate_json_structure
from scripts.generate_matchmaking import generate_matchmaking_json
from scripts.generate_cv_feedback import generate_cv_feedback_json
from scripts.generate_angebot import generate_angebot_json
from scripts.visualize_results import generate_dashboard

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
            custom_logo_path: str = None) -> Dict[str, Any]:
        """
        Runs the CV generation pipeline.
        
        Args:
            cv_file: File object or path to CV PDF
            job_file: File object or path to Job Profile PDF (optional)
            api_key: OpenAI API Key
            progress_callback: Function(progress_0_to_100, status_text, state)
            custom_styles: Dict with keys 'primary_color', 'secondary_color', 'font'
            custom_logo_path: Path to custom logo file
        """
        
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
            "error": None
        }

        try:
            # --- STEP 1: Extract Job Profile (if present) ---
            if progress_callback: progress_callback(10, "Analysiere Stellenprofil...", "running")
            
            stellenprofil_data = None
            stellenprofil_json_path = None
            
            if job_file:
                schema_path = os.path.join(self.base_dir, "scripts", "pdf_to_json_struktur_stellenprofil.json")
                stellenprofil_data = pdf_to_json(job_file, None, schema_path)
            
            # --- STEP 2: Extract CV ---
            if progress_callback: progress_callback(30, "Analysiere Lebenslauf...", "running")
            
            # WICHTIG: job_profile_context=None, um Halluzinationen zu vermeiden!
            cv_data = pdf_to_json(cv_file, output_path=None, job_profile_context=None)
            
            # Save JSONs
            vorname = cv_data.get("Vorname", "Unbekannt")
            nachname = cv_data.get("Nachname", "Unbekannt")
            output_dir = os.path.join(self.base_dir, "output", f"{vorname}_{nachname}_{self.timestamp}")
            os.makedirs(output_dir, exist_ok=True)
            
            cv_json_path = os.path.join(output_dir, f"cv_{vorname}_{nachname}_{self.timestamp}.json")
            with open(cv_json_path, 'w', encoding='utf-8') as f:
                json.dump(cv_data, f, ensure_ascii=False, indent=2)
            results["cv_json"] = cv_json_path
                
            if stellenprofil_data:
                stellenprofil_json_path = os.path.join(output_dir, f"stellenprofil_{self.timestamp}.json")
                with open(stellenprofil_json_path, 'w', encoding='utf-8') as f:
                    json.dump(stellenprofil_data, f, ensure_ascii=False, indent=2)
                results["stellenprofil_json"] = stellenprofil_json_path

            # --- STEP 3: Validation ---
            if progress_callback: progress_callback(50, "Validiere Daten...", "running")
            critical, info = validate_json_structure(cv_data)
            if critical:
                raise ValueError(f"Validierungsfehler: {'; '.join(critical)}")

            # --- STEP 4: Generation (Word, Match, Feedback) ---
            if progress_callback: progress_callback(70, "Generiere Dokumente...", "running")
            
            word_path = None
            matchmaking_json_path = None
            feedback_json_path = None
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Word (interactive=False to suppress dialogs)
                future_word = executor.submit(generate_cv, cv_json_path, output_dir, interactive=False)
                
                # Match
                future_match = None
                if stellenprofil_json_path:
                    matchmaking_json_path = os.path.join(output_dir, f"Match_{vorname}_{nachname}_{self.timestamp}.json")
                    schema_path = os.path.join(self.base_dir, "scripts", "matchmaking_json_schema.json")
                    future_match = executor.submit(
                        generate_matchmaking_json,
                        cv_json_path,
                        stellenprofil_json_path,
                        matchmaking_json_path,
                        schema_path
                    )
                
                # Feedback
                feedback_json_path = os.path.join(output_dir, f"CV_Feedback_{vorname}_{nachname}_{self.timestamp}.json")
                feedback_schema_path = os.path.join(self.base_dir, "scripts", "cv_feedback_json_schema.json")
                future_feedback = executor.submit(
                    generate_cv_feedback_json,
                    cv_json_path,
                    feedback_json_path,
                    feedback_schema_path,
                    stellenprofil_json_path
                )
                
                word_path = future_word.result()
                if future_match: future_match.result()
                future_feedback.result()

            results["word_path"] = word_path
            results["match_json"] = matchmaking_json_path

            # --- STEP 5: Dashboard ---
            if progress_callback: progress_callback(90, "Erstelle Dashboard...", "running")
            
            dashboard_path = generate_dashboard(
                cv_json_path=cv_json_path,
                match_json_path=matchmaking_json_path if matchmaking_json_path and os.path.exists(matchmaking_json_path) else None,
                feedback_json_path=feedback_json_path,
                output_dir=output_dir,
                validation_warnings=info
            )
            results["dashboard_path"] = dashboard_path
            
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
            if progress_callback: progress_callback(100, "Fertig!", "completed")
            
        except Exception as e:
            results["error"] = str(e)
            if progress_callback: progress_callback(100, f"Fehler: {str(e)}", "error")
            
        return results
