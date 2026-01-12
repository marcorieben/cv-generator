import os
import sys
import json
import socket
import threading
import time
import subprocess
import platform
import traceback
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to sys.path to allow imports from scripts module
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_dependencies():
    """Check if all required packages are installed."""
    required_packages = {
        'openai': 'openai',
        'pypdf': 'pypdf',
        'python-dotenv': 'dotenv',
        'python-docx': 'docx'
    }
    
    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("\nError: Missing required dependencies!")
        print("The following packages are missing:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install them using the following command:")
        print(f"  pip install -r {os.path.join(current_dir, 'requirements.txt')}")
        print("\nOr install them individually:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)

# Check dependencies before importing local modules that might use them
check_dependencies()

# Local imports
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv, validate_json_structure
from scripts.generate_matchmaking import generate_matchmaking_json
from scripts.generate_cv_feedback import generate_cv_feedback_json
from scripts.generate_angebot import generate_angebot_json
from scripts.visualize_results import generate_dashboard
from scripts.dialogs import (
    show_success, show_error, show_warning, ask_yes_no,
    select_pdf_file, show_welcome, show_processing, ModernDialog
)

class CVPipeline:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.processing_dialog = None
        self.dialog_thread = None
        self.dialog_closed_event = threading.Event()

    def check_internet_connection(self) -> bool:
        try:
            socket.create_connection(("api.openai.com", 443), timeout=5)
            return True
        except OSError:
            return False

    def _show_processing_dialog(self, cv_filename: str, stellenprofil_filename: Optional[str], mode: str = "full"):
        self.processing_dialog = show_processing(cv_filename, stellenprofil_filename, mode=mode)
        self.processing_dialog.show()
        self.dialog_closed_event.set()

    def start_processing_dialog(self, cv_filename: str, stellenprofil_filename: Optional[str], mode: str = "full"):
        self.dialog_thread = threading.Thread(
            target=self._show_processing_dialog,
            args=(cv_filename, stellenprofil_filename, mode),
            daemon=True
        )
        self.dialog_thread.start()
        # Wait until dialog is created
        start_time = time.time()
        while self.processing_dialog is None and time.time() - start_time < 5.0:
            time.sleep(0.1)

    def update_progress(self, step_index: int, status: str):
        """
        Update progress step in the dialog.
        status: 'pending', 'running', 'completed', 'error', 'skipped'
        """
        if self.processing_dialog:
            try:
                self.processing_dialog.update_step(step_index, status)
                
                # Add delay for demo purposes if in mock mode
                if os.environ.get("MODEL_NAME") == "mock" and status == "completed":
                    time.sleep(1.5)  # 1.5 seconds delay per completed step to make it visible
                    
            except Exception as e:
                print(f"Error updating progress dialog: {e}")

    def stop_processing_dialog(self):
        if self.processing_dialog:
            try:
                self.processing_dialog.close()
            except Exception:
                pass
        
        if self.dialog_thread and self.dialog_thread.is_alive():
            self.dialog_thread.join(timeout=5.0)

    def process_cv_pdf(self, pdf_path: str, job_profile_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        print("\n" + "="*60)
        print("SCHRITT 1: PDF -> JSON Konvertierung (CV)")
        if job_profile_context:
            print("ℹ️  Mit Stellenprofil-Kontext für massgeschneiderte Extraktion")
        print("="*60)
        return pdf_to_json(pdf_path, output_path=None, job_profile_context=job_profile_context)

    def process_job_profile_pdf(self, pdf_path: str, output_path: str) -> Dict[str, Any]:
        print("\n" + "="*60)
        print("SCHRITT 1b: PDF -> JSON Konvertierung (Stellenprofil)")
        print("="*60)
        schema_path = os.path.join(self.base_dir, "scripts", "pdf_to_json_struktur_stellenprofil.json")
        return pdf_to_json(
            pdf_path,
            output_path=output_path,
            schema_path=schema_path
        )

    def save_json(self, data: Dict[str, Any], path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def validate_data(self, json_data: Dict[str, Any], json_path: str) -> bool:
        print("\n" + "="*60)
        print("SCHRITT 2: JSON Validierung")
        print("="*60)
        critical, info = validate_json_structure(json_data)
        
        if critical:
            print("❌ KRITISCHE FEHLER gefunden:")
            for err in critical:
                print(f"   • {err}")
            
            error_msg = "Die JSON-Struktur weist kritische Fehler auf, die eine Word-Generierung verhindern."
            details = "Kritische Fehler:\n\n" + "\n".join([f"• {err}" for err in critical])
            details += f"\n\n📋 JSON gespeichert:\n{json_path}\n\nBitte korrigieren Sie die Fehler manuell und führen Sie die Generierung erneut aus."
            
            # Stop dialog before showing error
            self.stop_processing_dialog()
            show_error(error_msg, title="JSON-Validierungsfehler", details=details)
            return False
            
        if info:
            print("⚠️  Warnungen:")
            for warning in info:
                print(f"   • {warning}")
        
        print("✅ JSON-Struktur ist valid")
        return True

    def generate_word(self, json_path: str, output_dir: str) -> Optional[str]:
        print("\n" + "="*60)
        print("SCHRITT 3: Word-Dokument Generierung")
        print("="*60)
        word_path = generate_cv(json_path, output_dir=output_dir)
        if not word_path:
            # Don't stop dialog here, let the caller handle it or just log error
            print("❌ Word-Dokument-Generierung fehlgeschlagen.")
            return None
        return word_path

    def open_file(self, file_path: str):
        print("📂 Öffne Word-Dokument...")
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
            print("✅ Dokument geöffnet")
        except Exception as e:
            print(f"⚠️  Konnte Dokument nicht öffnen: {e}")

    def run(self, cv_path: str, stellenprofil_path: Optional[str] = None) -> Optional[str]:
        cv_filename = os.path.basename(cv_path)
        stellenprofil_filename = os.path.basename(stellenprofil_path) if stellenprofil_path else None
        
        mode = os.environ.get("CV_GENERATOR_MODE", "full")
        self.start_processing_dialog(cv_filename, stellenprofil_filename, mode=mode)

        try:
            # --- STEP 1: PDF Extraction ---
            cv_data = None
            stellenprofil_data = None
            stellenprofil_json_path = None
            
            # If offer exists, process it FIRST to get context
            if stellenprofil_path:
                self.update_progress(0, "running") # Stellenprofil analysieren
                print("\n" + "="*60)
                print("SCHRITT 0: Stellenprofil extrahieren (für Kontext)")
                print("="*60)
                schema_path = os.path.join(self.base_dir, "scripts", "pdf_to_json_struktur_stellenprofil.json")
                # Run synchronously to ensure we have data for CV extraction
                stellenprofil_data = pdf_to_json(stellenprofil_path, None, schema_path)
                self.update_progress(0, "completed")
            else:
                self.update_progress(0, "skipped")
            
            # Process CV (with offer context if available)
            self.update_progress(1, "running") # CV analysieren
            cv_data = self.process_cv_pdf(cv_path, job_profile_context=stellenprofil_data)
            self.update_progress(1, "completed")
            
            # Determine paths and save
            vorname = cv_data.get("Vorname", "Unbekannt")
            nachname = cv_data.get("Nachname", "Unbekannt")
            
            output_dir = os.path.join(self.base_dir, "output", f"{vorname}_{nachname}_{self.timestamp}")
            os.makedirs(output_dir, exist_ok=True)
            
            cv_json_filename = f"cv_{vorname}_{nachname}_{self.timestamp}.json"
            cv_json_path = os.path.join(output_dir, cv_json_filename)
            self.save_json(cv_data, cv_json_path)

            # Save Offer Data if it exists
            if stellenprofil_data:
                # Use original filename of the job profile for the JSON file
                sp_basename = os.path.splitext(stellenprofil_filename)[0]
                stellenprofil_json_filename = f"stellenprofil_{sp_basename}_{self.timestamp}.json"
                stellenprofil_json_path = os.path.join(output_dir, stellenprofil_json_filename)
                self.save_json(stellenprofil_data, stellenprofil_json_path)

            # --- STEP 2: Validation ---
            self.update_progress(2, "running") # Qualitätsprüfung
            if not self.validate_data(cv_data, cv_json_path):
                self.update_progress(2, "error")
                return None
            self.update_progress(2, "completed")

            # --- PARALLEL STEP 3: Generation (Word, Matchmaking, Feedback) ---
            word_path = None
            matchmaking_json_path = None
            feedback_json_path = None
            
            # Mark steps as running/skipped
            self.update_progress(3, "running") # Word
            
            if stellenprofil_path:
                self.update_progress(4, "running") # Match
            else:
                self.update_progress(4, "skipped")
                
            self.update_progress(5, "running") # Feedback
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 1. Word Generation
                future_word = executor.submit(self.generate_word, cv_json_path, output_dir)
                
                # 2. Matchmaking (if offer exists)
                future_match = None
                if stellenprofil_json_path and os.path.exists(stellenprofil_json_path):
                    matchmaking_json_path = os.path.join(output_dir, f"Match_{vorname}_{nachname}_{self.timestamp}.json")
                    schema_path = os.path.join(self.base_dir, "scripts", "matchmaking_json_schema.json")
                    future_match = executor.submit(
                        generate_matchmaking_json,
                        cv_json_path,
                        stellenprofil_json_path,
                        matchmaking_json_path,
                        schema_path
                    )

                # 3. Feedback
                feedback_json_path = os.path.join(output_dir, f"CV_Feedback_{vorname}_{nachname}_{self.timestamp}.json")
                feedback_schema_path = os.path.join(self.base_dir, "scripts", "cv_feedback_json_schema.json")
                future_feedback = executor.submit(
                    generate_cv_feedback_json,
                    cv_json_path,
                    feedback_json_path,
                    feedback_schema_path,
                    stellenprofil_json_path
                )

                # Collect results
                word_path = future_word.result()
                self.update_progress(3, "completed" if word_path else "error")
                
                if future_match:
                    try:
                        future_match.result() # Wait for completion
                        self.update_progress(4, "completed")
                    except Exception:
                        self.update_progress(4, "error")
                        
                try:
                    future_feedback.result() # Wait for completion
                    self.update_progress(5, "completed")
                except Exception:
                    self.update_progress(5, "error")

            # --- STEP 3b: Angebot Generation (Sequential, depends on Match) ---
            angebot_json_path = None
            mode = os.environ.get("CV_GENERATOR_MODE", "full")
            
            if mode == "full" and stellenprofil_json_path and matchmaking_json_path and os.path.exists(matchmaking_json_path):
                self.update_progress(6, "running") # Angebot
                try:
                    angebot_json_path = os.path.join(output_dir, f"Angebot_{vorname}_{nachname}_{self.timestamp}.json")
                    schema_path = os.path.join(self.base_dir, "scripts", "angebot_json_schema.json")
                    generate_angebot_json(
                        cv_json_path,
                        stellenprofil_json_path,
                        matchmaking_json_path,
                        angebot_json_path,
                        schema_path
                    )
                    self.update_progress(6, "completed")
                except Exception as e:
                    print(f"❌ Fehler bei Angebots-Generierung: {e}")
                    self.update_progress(6, "error")
            else:
                self.update_progress(6, "skipped")

            if not word_path:
                self.stop_processing_dialog()
                show_error(
                    "Die Word-Dokument-Generierung konnte nicht abgeschlossen werden.",
                    title="Word-Generierungsfehler",
                    details="Bitte überprüfen Sie die Konsole für weitere Details."
                )
                return None

            # --- STEP 4: Dashboard ---
            self.update_progress(7, "running") # Dashboard
            dashboard_path = generate_dashboard(
                cv_json_path=cv_json_path,
                match_json_path=matchmaking_json_path if stellenprofil_json_path and os.path.exists(stellenprofil_json_path) else None,
                feedback_json_path=feedback_json_path,
                output_dir=output_dir,
                model_name=os.environ.get("MODEL_NAME", "gpt-4o"),
                pipeline_mode="CLI Pipeline",
                cv_filename=cv_filename,
                job_filename=stellenprofil_filename,
                angebot_json_path=angebot_json_path
            )
            self.update_progress(7, "completed")

            self.stop_processing_dialog()
            
            # Success Message
            print("\n" + "="*60)
            print("✅ PIPELINE ERFOLGREICH ABGESCHLOSSEN")
            print("="*60)
            print(f"\n📄 PDF Input:  {cv_filename}")
            print(f"📋 JSON:       {cv_json_path}")
            print(f"📝 Word Output: {word_path}")
            if dashboard_path:
                print(f"📊 Dashboard:  {dashboard_path}")
            print("="*60 + "\n")
            
            success_msg = "Der Lebenslauf wurde erfolgreich generiert und ist bereit zur Verwendung."
            
            # Construct structured details
            details = "📂 INPUT DATEIEN:\n"
            details += f"• CV PDF: {cv_filename}\n"
            if stellenprofil_filename:
                details += f"• Stellenprofil PDF: {stellenprofil_filename}\n"
            
            details += "\n📤 OUTPUT DATEIEN:\n"
            details += f"• Word CV: {os.path.basename(word_path)}\n"
            details += f"• CV JSON: {os.path.basename(cv_json_path)}\n"
            
            if stellenprofil_json_path:
                details += f"• Stellenprofil JSON: {os.path.basename(stellenprofil_json_path)}\n"
                
            if matchmaking_json_path:
                 details += f"• Matchmaking JSON: {os.path.basename(matchmaking_json_path)}\n"
            
            if angebot_json_path:
                 details += f"• Angebot JSON: {os.path.basename(angebot_json_path)}\n"
                 
            if feedback_json_path:
                details += f"• Feedback JSON: {os.path.basename(feedback_json_path)}\n"

            if dashboard_path:
                details += f"• Dashboard HTML: {os.path.basename(dashboard_path)}\n"
                
            details += f"\n📍 Speicherort: {os.path.dirname(word_path)}"
            
            # Stop processing dialog before showing success dialog
            self.stop_processing_dialog()
            
            # Wait a moment for Tkinter cleanup to ensure main thread is ready for new dialog
            time.sleep(1.0)

            # Extract match score if available
            match_score = None
            if matchmaking_json_path and os.path.exists(matchmaking_json_path):
                try:
                    with open(matchmaking_json_path, 'r', encoding='utf-8') as f:
                        match_data = json.load(f)
                        # Try to get score from match_score.score_gesamt
                        score_val = match_data.get("match_score", {}).get("score_gesamt")
                        if score_val is not None:
                            # Handle string or int
                            if isinstance(score_val, str):
                                # Remove % if present
                                score_val = score_val.replace('%', '').strip()
                                if score_val.isdigit():
                                    match_score = int(score_val)
                            elif isinstance(score_val, (int, float)):
                                match_score = int(score_val)
                except Exception as e:
                    print(f"⚠️  Konnte Match-Score nicht lesen: {e}")

            # Dialog handles opening files now
            show_success(success_msg, details=details, file_path=word_path, dashboard_path=dashboard_path, match_score=match_score, angebot_json_path=angebot_json_path)
                
            return word_path

        except Exception as e:
            self.stop_processing_dialog()
            print(f"\n❌ Fehler in Pipeline: {str(e)}")
            details = traceback.format_exc()
            show_error(
                "Ein unerwarteter Fehler ist während der Pipeline-Ausführung aufgetreten.",
                title="Pipeline-Fehler",
                details=details
            )
            return None

def main():
    print("[DEBUG] main() wurde gestartet", flush=True)
    print("="*60)
    print("CV GENERATOR - Unified Pipeline")
    print("PDF -> JSON -> Word")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pipeline = CVPipeline(base_dir)

    print("\n🌐 Prüfe Internetverbindung...")
    if not pipeline.check_internet_connection():
        show_error(
            "Für die CV-Generierung ist eine Internetverbindung erforderlich.",
            title="Keine Internetverbindung",
            details=(
                "Die Applikation benötigt Zugriff auf die OpenAI API zur "
                "Extraktion und Strukturierung der CV-Daten aus PDF-Dateien.\n\n"
                "Bitte stellen Sie sicher, dass:\n"
                "• Sie mit dem Internet verbunden sind\n"
                "• Ihre Firewall den Zugriff auf api.openai.com erlaubt\n"
                "• Keine Proxy-Einstellungen die Verbindung blockieren"
            )
        )
        print("❌ Keine Internetverbindung. Programm abgebrochen.")
        return 1
    print("✅ Internetverbindung verfügbar")

    cv_path = None
    stellenprofil_path = None

    if len(sys.argv) > 1:
        cv_path = sys.argv[1]
        if not os.path.exists(cv_path):
            print(f"❌ Datei nicht gefunden: {cv_path}")
            return 1
        
        if len(sys.argv) > 2:
            stellenprofil_path = sys.argv[2]
            if not os.path.exists(stellenprofil_path):
                print(f"⚠️  Stellenprofil-Datei nicht gefunden: {stellenprofil_path}")
                stellenprofil_path = None
    else:
        result = show_welcome()
        if not result:
            print("❌ Keine Datei ausgewählt. Programm abgebrochen.")
            return 1
        cv_path, stellenprofil_path = result
        if stellenprofil_path:
            print(f"📋 Stellenprofil ausgewählt: {os.path.basename(stellenprofil_path)}")

    result_path = pipeline.run(cv_path, stellenprofil_path)
    return 0 if result_path else 1

if __name__ == "__main__":
    sys.exit(main())
