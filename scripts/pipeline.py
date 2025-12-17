"""
Unified CV Generation Pipeline
PDF → JSON → Word in einem einzigen Flow

Usage:
    python scripts/pipeline.py                 # Mit Dialog
    python scripts/pipeline.py path/to/file.pdf    # Direkt mit PDF
"""

import os
import sys

# Add parent directory to path for imports - always, not just in __main__
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import socket
from datetime import datetime

# Import unserer Module
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv, validate_json_structure
from scripts.dialogs import (
    show_success, show_error, show_warning, ask_yes_no,
    select_pdf_file, show_welcome, ModernDialog
)


def check_internet_connection():
    """
    Prüft, ob eine Internetverbindung verfügbar ist
    
    Returns:
        True wenn Internet verfügbar, sonst False
    """
    try:
        # Versuche DNS-Lookup für openai.com
        socket.create_connection(("api.openai.com", 443), timeout=5)
        return True
    except OSError:
        return False


# Dialog functions are now imported from modern_dialogs.py


def run_pipeline(pdf_path):
    """
    Führt die komplette Pipeline aus: PDF → JSON → Word
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        
    Returns:
        Pfad zur generierten Word-Datei oder None bei Fehler
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Schritt 1: PDF → JSON
        print("\n" + "="*60)
        print("SCHRITT 1: PDF → JSON Konvertierung")
        print("="*60)
        
        # OpenAI API Konvertierung (JSON wird dort gespeichert)
        json_data = pdf_to_json(pdf_path, output_path=None)
        
        # Erstelle JSON-Dateinamen mit Vorname_Nachname_Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        vorname = json_data.get("Vorname", "Unbekannt")
        nachname = json_data.get("Nachname", "Unbekannt")
        json_filename = f"{vorname}_{nachname}_{timestamp}.json"
        json_path = os.path.join(base_dir, "input", "json", json_filename)
        
        # Speichere JSON mit neuem Namen
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Schritt 2: JSON Validierung
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
            
            show_error(error_msg, title="JSON-Validierungsfehler", details=details)
            return None
        
        if info:
            print("⚠️  Warnungen:")
            for warning in info:
                print(f"   • {warning}")
        
        print("✅ JSON-Struktur ist valid")
        
        # Schritt 3: JSON → Word
        print("\n" + "="*60)
        print("SCHRITT 3: Word-Dokument Generierung")
        print("="*60)
        
        word_path = generate_cv(json_path)
        
        if not word_path:
            show_error(
                "Die Word-Dokument-Generierung konnte nicht abgeschlossen werden.",
                title="Word-Generierungsfehler",
                details="Bitte überprüfen Sie die Konsole für weitere Details."
            )
            return None
        
        # Erfolg!
        print("\n" + "="*60)
        print("✅ PIPELINE ERFOLGREICH ABGESCHLOSSEN")
        print("="*60)
        print(f"\n📄 PDF Input:  {os.path.basename(pdf_path)}")
        print(f"📋 JSON:       {json_path}")
        print(f"📝 Word Output: {word_path}")
        print("="*60 + "\n")
        
        # Build success message with details
        success_msg = "Der Lebenslauf wurde erfolgreich generiert und ist bereit zur Verwendung."
        
        details = (
            f"{ModernDialog.ICON_FILE} PDF Input:\n"
            f"  {os.path.basename(pdf_path)}\n\n"
            f"{ModernDialog.ICON_JSON} JSON gespeichert:\n"
            f"  {json_path}\n\n"
            f"{ModernDialog.ICON_WORD} Word Dokument:\n"
            f"  {word_path}"
        )
        
        # Show success with open button
        result = show_success(success_msg, details=details, file_path=word_path)
        
        # Open document if user clicked "Open"
        if result == 'open':
            print("📂 Öffne Word-Dokument...")
            import subprocess
            import platform
            
            try:
                if platform.system() == 'Windows':
                    os.startfile(word_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', word_path])
                else:  # Linux
                    subprocess.run(['xdg-open', word_path])
                print("✅ Dokument geöffnet")
            except Exception as e:
                print(f"⚠️  Konnte Dokument nicht öffnen: {e}")
        
        return word_path
    
    except Exception as e:
        print(f"\n❌ Fehler in Pipeline: {str(e)}")
        import traceback
        details = traceback.format_exc()
        
        show_error(
            "Ein unerwarteter Fehler ist während der Pipeline-Ausführung aufgetreten.",
            title="Pipeline-Fehler",
            details=details
        )
        return None


def main():
    """Hauptfunktion"""
    print("="*60)
    print("CV GENERATOR - Unified Pipeline")
    print("PDF → JSON → Word")
    print("="*60)
    
    # Internetverbindung prüfen
    print("\n🌐 Prüfe Internetverbindung...")
    if not check_internet_connection():
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
    
    # PDF-Datei aus Argument oder Dialog
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if not os.path.exists(pdf_path):
            print(f"❌ Datei nicht gefunden: {pdf_path}")
            return 1
    else:
        # Show welcome dialog which includes PDF selection
        pdf_path = show_welcome()
        if not pdf_path:
            print("❌ Keine Datei ausgewählt. Programm abgebrochen.")
            return 1
    
    # Pipeline ausführen
    result = run_pipeline(pdf_path)
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
