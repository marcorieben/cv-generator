"""
Unified CV Generation Pipeline
PDF → JSON → Word in einem einzigen Flow

Usage:
    python run_pipeline.py                     # Mit Dialog
    python run_pipeline.py path/to/file.pdf    # Direkt mit PDF
"""

import os
import sys
from datetime import datetime
from tkinter import Tk, filedialog, messagebox

# Import unserer Module
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv, validate_json_structure


def select_pdf_file():
    """
    Zeigt einen Datei-Auswahl-Dialog für PDF
    
    Returns:
        Pfad zur ausgewählten PDF oder None
    """
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    pdf_path = filedialog.askopenfilename(
        title="PDF-Datei auswählen",
        initialdir=os.path.join(os.path.dirname(__file__), "input", "pdf"),
        filetypes=[("PDF Dateien", "*.pdf"), ("Alle Dateien", "*.*")]
    )
    
    root.destroy()
    return pdf_path if pdf_path else None


def show_error(title, message):
    """Zeigt Fehlermeldung"""
    root = Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()


def show_success(message):
    """Zeigt Erfolgsmeldung"""
    root = Tk()
    root.withdraw()
    messagebox.showinfo("Erfolg", message)
    root.destroy()


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
            
            error_msg = "JSON-Validierung fehlgeschlagen:\n\n" + "\n".join(critical)
            error_msg += f"\n\nJSON wurde gespeichert in:\n{json_path}"
            error_msg += "\n\nBitte Datei manuell korrigieren und erneut versuchen."
            
            show_error("Validierungsfehler", error_msg)
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
            show_error("Fehler", "Word-Generierung fehlgeschlagen")
            return None
        
        # Erfolg!
        print("\n" + "="*60)
        print("✅ PIPELINE ERFOLGREICH ABGESCHLOSSEN")
        print("="*60)
        print(f"\n📄 PDF Input:  {os.path.basename(pdf_path)}")
        print(f"📋 JSON:       {json_path}")
        print(f"📝 Word Output: {word_path}")
        print("="*60 + "\n")
        
        success_msg = (
            f"✅ CV erfolgreich generiert!\n\n"
            f"Input: {os.path.basename(pdf_path)}\n\n"
            f"JSON gespeichert:\n{json_path}\n\n"
            f"Word gespeichert:\n{word_path}"
        )
        
        # Frage, ob Word-Datei geöffnet werden soll
        root = Tk()
        root.withdraw()
        open_file = messagebox.askyesno(
            "Erfolg", 
            success_msg + "\n\nWord-Datei jetzt öffnen?"
        )
        root.destroy()
        
        if open_file:
            os.startfile(word_path)
        
        return word_path
    
    except Exception as e:
        error_msg = f"Fehler in Pipeline:\n\n{str(e)}"
        print(f"\n❌ {error_msg}")
        show_error("Pipeline Fehler", error_msg)
        return None


def main():
    """Hauptfunktion"""
    print("="*60)
    print("CV GENERATOR - Unified Pipeline")
    print("PDF → JSON → Word")
    print("="*60)
    
    # PDF-Datei aus Argument oder Dialog
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if not os.path.exists(pdf_path):
            print(f"❌ Datei nicht gefunden: {pdf_path}")
            return 1
    else:
        pdf_path = select_pdf_file()
        if not pdf_path:
            print("❌ Keine Datei ausgewählt. Programm abgebrochen.")
            return 1
    
    # Pipeline ausführen
    result = run_pipeline(pdf_path)
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
