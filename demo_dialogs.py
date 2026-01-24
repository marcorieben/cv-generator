"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-14
Last Updated: 2026-01-24
"""
from scripts.dialogs import (
    show_success, show_error, show_warning, ask_yes_no,
    select_pdf_file, select_json_file, ModernDialog
)
import time


def demo_dialogs():
    """Show all dialog types in sequence"""
    
    print("\n" + "="*60)
    print("MODERN DIALOGS DEMO")
    print("Showcasing corporate-styled dialogs")
    print("="*60 + "\n")
    
    # 1. Success Dialog
    print("1️⃣ Showing Success Dialog...")
    show_success(
        "Der Lebenslauf wurde erfolgreich generiert und ist bereit zur Verwendung.",
        title="CV erfolgreich generiert",
        details=(
            f"{ModernDialog.ICON_FILE} PDF Input:\n"
            f"  Marco_Rieben_CV.pdf\n\n"
            f"{ModernDialog.ICON_JSON} JSON gespeichert:\n"
            f"  input/json/Marco_Rieben_20251217_143022.json\n\n"
            f"{ModernDialog.ICON_WORD} Word Dokument:\n"
            f"  output/word/Marco_Rieben_CV_20251217_143022.docx"
        )
    )
    
    print("✅ Success Dialog completed\n")
    time.sleep(0.5)
    
    # 2. Error Dialog
    print("2️⃣ Showing Error Dialog...")
    show_error(
        "Die JSON-Struktur weist kritische Fehler auf, die eine Word-Generierung verhindern.",
        title="JSON-Validierungsfehler",
        details=(
            "Kritische Fehler:\n\n"
            "• Feld 'Vorname' fehlt oder ist leer\n"
            "• Feld 'Nachname' fehlt oder ist leer\n"
            "• 'Hauptrolle' muss ein Objekt mit 'Titel' und 'Beschreibung' sein\n"
            "• 'Fachwissen_und_Schwerpunkte' muss genau 3 Einträge haben\n\n"
            "📋 JSON gespeichert:\n"
            "input/json/Test_User_20251217.json\n\n"
            "Bitte korrigieren Sie die Fehler manuell und führen Sie die Generierung erneut aus."
        )
    )
    
    print("✅ Error Dialog completed\n")
    time.sleep(0.5)
    
    # 3. Warning Dialog
    print("3️⃣ Showing Warning Dialog...")
    result = show_warning(
        "Die JSON-Datei weist folgende Strukturprobleme auf:",
        title="JSON-Validierung",
        details=(
            "⚠️ Kritische Fehler:\n"
            "  • 'Hauptrolle.Beschreibung' sollte 5-10 Wörter haben, ist aber 2 Wörter\n"
            "  • 'Kurzprofil' sollte 50-100 Wörter haben, ist aber 35 Wörter\n\n"
            "ℹ️ Hinweise (nicht kritisch):\n"
            "  • Projekt 1 hat 7 Tätigkeiten (empfohlen: max 5)\n"
            "  • Sprache 'Italienisch' hat ungültiges Level: 'Gut'\n\n"
            "Möchten Sie trotzdem fortfahren?"
        )
    )
    
    print(f"✅ Warning Dialog completed - User chose: {'Ja' if result else 'Nein'}\n")
    time.sleep(0.5)
    
    # 4. Confirmation Dialog
    print("4️⃣ Showing Confirmation Dialog...")
    result = ask_yes_no(
        "Möchten Sie das generierte Word-Dokument jetzt öffnen?",
        title="Dokument öffnen",
        icon_type="success"
    )
    
    print(f"✅ Confirmation Dialog completed - User chose: {'Ja' if result else 'Nein'}\n")
    time.sleep(0.5)
    
    # 5. File Picker (optional - will open but user can cancel)
    print("5️⃣ Showing File Picker Dialog (optional - you can cancel)...")
    print("   Opening PDF picker...")
    pdf_file = select_pdf_file()
    
    if pdf_file:
        print(f"✅ PDF selected: {pdf_file}\n")
    else:
        print("✅ PDF picker cancelled\n")
    
    # Done
    print("="*60)
    print("DEMO COMPLETED")
    print("All modern dialogs use corporate styling:")
    print("  • Orange (#FF7900) for primary actions")
    print("  • Gray (#444444) for secondary elements")
    print("  • Professional icons for visual clarity")
    print("  • Segoe UI font for modern appearance")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo_dialogs()
