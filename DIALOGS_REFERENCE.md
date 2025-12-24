# Dialog System - Komplette Referenz

## 📁 Dateistruktur

```
cv_generator/
├── scripts/
│   └── dialogs.py              # Alle Dialog-Klassen und Helper-Funktionen
├── tests/
│   └── test_dialogs.py         # Unit-Tests für Dialogs
├── demo_dialogs.py             # Demo aller Dialogs
├── test_processing_dialog.py   # Spezieller Test für ProcessingDialog
└── DIALOGS_REFERENCE.md        # Diese Dokumentation
```

---

## 🎨 Design System

### Corporate Colors
```python
ORANGE = "#FF7900"      # Primary brand color (Buttons, Highlights)
DARK_GRAY = "#444444"   # Secondary text/elements
WHITE = "#FFFFFF"
SUCCESS_GREEN = "#28A745"
ERROR_RED = "#DC3545"
WARNING_YELLOW = "#FFC107"
LIGHT_GRAY = "#F8F9FA"
```

### Typography
- **Font**: Segoe UI (Windows) / System Standard
- **Header**: 14pt, Bold
- **Content**: 11pt, Regular
- **Buttons**: 10pt, Bold

### Icons
```python
ICON_SUCCESS = "✅"
ICON_ERROR = "❌"
ICON_WARNING = "⚠️"
ICON_INFO = "ℹ️"
ICON_QUESTION = "❓"
ICON_FILE = "📄"
ICON_JSON = "📋"
ICON_WORD = "📝"
```

---

## 📦 Verfügbare Dialogs

### 1. WelcomeDialog 🚪
**Zweck**: Erster Dialog beim Pipeline-Start - Auswahl von CV und optional Angebot

**Verwendung**:
```python
from scripts.dialogs import show_welcome

result = show_welcome()
if result:
    cv_path, angebot_path = result
    # cv_path ist immer gesetzt (Pflicht)
    # angebot_path kann None sein (Optional)
```

**Features**:
- DSGVO-Einwilligung (Checkbox muss aktiviert werden)
- 2-Schritt Upload: CV (Pflicht) + Angebot (Optional)
- Pipeline-Visualisierung (5 Schritte)
- Grüne Bestätigung nach Upload
- Breite: 750px, Höhe: 850px

**Wann verwenden?**:
- Beim Start von `run_pipeline.py`
- Immer wenn User Dateien auswählen soll

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 424-747
- DSGVO-Text anpassen: Zeile 537-548
- Pipeline-Schritte: Zeile 487-521

---

### 2. ProcessingDialog ⚙️
**Zweck**: Warte-Animation während LLM-Verarbeitung (PDF → JSON)

**Verwendung**:
```python
from scripts.dialogs import show_processing

# Nur CV
dialog = show_processing("Max_Mustermann.pdf")

# CV + Angebot
dialog = show_processing("Max_Mustermann.pdf", "Stellenangebot.pdf")

# In Thread starten (für Pipeline)
import threading
def show_dialog():
    dialog.show()  # Blockiert bis close()
thread = threading.Thread(target=show_dialog, daemon=True)
thread.start()

# Nach Verarbeitung schließen
dialog.close()
```

**Features**:
- Rotierende Spinner (◐ ◓ ◑ ◒) über Dokumenten
- Dynamisches Layout:
  - 1 Dokument → Zentriert
  - 2 Dokumente → Nebeneinander
- Animierte Fortschritts-Punkte ("Verarbeitung läuft...")
- Dateinamen werden angezeigt (gekürzt bei >25 Zeichen)
- Breite: 550px, Höhe: 500px

**Wann verwenden?**:
- Während `pdf_to_json()` läuft
- Bei längeren API-Aufrufen (>5 Sekunden)

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 749-928
- Spinner-Zeichen: Zeile 766 (`self.spinner_frames`)
- Animation-Geschwindigkeit: Zeile 925 (100ms)
- Dialog-Größe: Zeile 758

**Testen**:
```bash
python test_processing_dialog.py
# Wähle: 1 (nur CV), 2 (CV+Angebot), 3 (beide)
```

---

### 3. SuccessDialog ✅
**Zweck**: Erfolgsmeldung nach abgeschlossener Generierung

**Verwendung**:
```python
from scripts.dialogs import show_success, ModernDialog

result = show_success(
    message="Der Lebenslauf wurde erfolgreich generiert.",
    title="Erfolg",
    details=(
        f"{ModernDialog.ICON_FILE} PDF Input: example.pdf\n"
        f"{ModernDialog.ICON_JSON} JSON: output.json\n"
        f"{ModernDialog.ICON_WORD} Word: output.docx"
    ),
    file_path="C:/path/to/output.docx"  # Optional: Zeigt "Öffnen" Button
)

if result == 'open':
    # User hat "Öffnen" geklickt
```

**Features**:
- Grüner Header mit ✅
- Optional: "Öffnen" Button (wenn `file_path` gesetzt)
- Expandable Details-Sektion
- Return: `'open'` oder `None`

**Wann verwenden?**:
- Nach erfolgreicher Word-Generierung
- Nach erfolgreichem Speichern

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 133-199
- Button-Text: Zeile 188-189

---

### 4. ErrorDialog ❌
**Zweck**: Fehlerbehandlung mit Details

**Verwendung**:
```python
from scripts.dialogs import show_error

show_error(
    message="Die Word-Generierung ist fehlgeschlagen.",
    title="Pipeline-Fehler",
    details=traceback.format_exc()  # Stack-Trace
)
```

**Features**:
- Roter Header mit ❌
- Expandable Details (Scrollbar bei viel Text)
- Automatische Höhen-Anpassung

**Wann verwenden?**:
- Bei Exceptions
- Bei kritischen Validierungsfehlern
- Bei API-Fehlern

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 201-257

---

### 5. WarningDialog ⚠️
**Zweck**: Warnung mit Ja/Nein Optionen

**Verwendung**:
```python
from scripts.dialogs import show_warning

result = show_warning(
    message="JSON enthält fehlende Daten. Trotzdem fortfahren?",
    title="Validierungs-Warnung",
    details="Fehlende Felder:\n• Kurzprofil\n• Sprachen"
)

if result:  # True = Ja, False/None = Nein/Abbrechen
    # User hat "Ja" geklickt
```

**Features**:
- Gelber Header mit ⚠️
- Ja/Nein Buttons
- Optional: Details-Sektion
- Return: `True` (Ja) oder `False/None` (Nein)

**Wann verwenden?**:
- Bei Info-Level Validierungs-Warnungen
- Wenn User Entscheidung treffen muss

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 259-371

---

### 6. ConfirmDialog ❓
**Zweck**: Ja/Nein Bestätigung (einfacher als Warning)

**Verwendung**:
```python
from scripts.dialogs import ask_yes_no

result = ask_yes_no(
    message="Möchten Sie die Datei überschreiben?",
    title="Bestätigung",
    icon_type="question"  # oder "info"
)

if result:
    # User hat "Ja" geklickt
```

**Features**:
- Blauer Header mit ❓ oder ℹ️
- Einfaches Ja/Nein
- Kompakt (keine Details)

**Wann verwenden?**:
- Einfache Ja/Nein Fragen
- Datei überschreiben?
- Aktion bestätigen?

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 373-422

---

### 7. FilePickerDialog 📂
**Zweck**: Dateiauswahl (PDF oder JSON)

**Verwendung**:
```python
from scripts.dialogs import select_pdf_file, select_json_file, FilePickerDialog

# Convenience Funktionen
pdf_path = select_pdf_file(title="CV auswählen")
json_path = select_json_file(title="JSON auswählen")

# Oder direkt
pdf_path = FilePickerDialog.open_pdf(
    title="PDF auswählen",
    initial_dir="C:/custom/path"
)
```

**Features**:
- Native OS-Dateiauswahl
- Automatischer Initial-Pfad:
  - PDF: `input/cv/pdf/`
  - JSON: `input/cv/json/`
- File-Type Filter

**Wann verwenden?**:
- Wird von WelcomeDialog intern verwendet
- Standalone: Bei Skripten die nur eine Datei brauchen

**Wo anpassen?**:
- `scripts/dialogs.py` → Zeile 936-983

---

## 🔄 Dialog-Flow in Pipeline

```
1. run_pipeline.py startet
   ↓
2. WelcomeDialog (Dateiauswahl)
   → User wählt CV + optional Angebot
   ↓
3. ProcessingDialog (Animation)
   → pdf_to_json() läuft (10-15 Sek)
   → Dialog schließt automatisch
   ↓
4a. Bei Fehler: ErrorDialog
4b. Bei Warnung: WarningDialog (Ja/Nein)
4c. Bei Erfolg: JSON Validierung läuft
   ↓
5. Word-Generierung
   ↓
6. SuccessDialog (mit "Öffnen" Button)
```

---

## 🛠️ Anpassungs-Guide

### Dialog-Größe ändern
```python
# In __init__ der Dialog-Klasse:
super().__init__("Titel", width=600, height=400)  # Default: 550x300
```

### Header-Farbe ändern
```python
# Beim create_header() Aufruf:
self.create_header("Text", "🤖", self.ORANGE)  # Orange
self.create_header("Text", "❌", self.ERROR_RED)  # Rot
```

### Button-Text ändern
```python
# In der jeweiligen Dialog-Klasse, z.B. SuccessDialog:
self.create_button(btn_container, "OK", close, is_primary=True)
# Ändere zu:
self.create_button(btn_container, "Schließen", close, is_primary=True)
```

### Animation-Geschwindigkeit (ProcessingDialog)
```python
# scripts/dialogs.py, Zeile ~925
self.root.after(100, self._animate_spinners)  # 100ms = 10 FPS
# Schneller: 50ms = 20 FPS
# Langsamer: 200ms = 5 FPS
```

### Spinner-Zeichen ändern
```python
# scripts/dialogs.py, Zeile 766
self.spinner_frames = ["◐", "◓", "◑", "◒"]  # Rotating circle
# Alternativen:
# ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]  # Braille
# ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]  # Dots
# ["|", "/", "-", "\\"]  # Simple ASCII
```

---

## 📊 Dialog-Dimensionen Übersicht

| Dialog | Breite | Höhe | Dynamisch |
|--------|--------|------|-----------|
| WelcomeDialog | 750px | 850px | Nein |
| ProcessingDialog | 550px | 500px | Nein |
| SuccessDialog | 550px | 260-450px | Ja (Details) |
| ErrorDialog | 550px | 260-450px | Ja (Details) |
| WarningDialog | 550px | 260-450px | Ja (Details) |
| ConfirmDialog | 550px | 200px | Nein |
| FilePickerDialog | OS-Standard | OS-Standard | OS |

**Dynamisch**: Höhe passt sich automatisch an Inhalt an (bei Details-Sektion)

---

## 🧪 Testing

### Alle Dialogs testen
```bash
python demo_dialogs.py
```

### Nur ProcessingDialog
```bash
python test_processing_dialog.py
# Wähle: 1, 2 oder 3
```

### Unit-Tests
```bash
pytest tests/test_dialogs.py -v
```

---

## 🐛 Troubleshooting

### Dialog erscheint nicht
- **Ursache**: Threading-Problem oder tkinter-Fehler
- **Lösung**: Prüfe ob `dialog.show()` im richtigen Thread aufgerufen wird
- **Check**: Ist `.venv` aktiviert? Ist tkinter installiert?

### Dialog schließt nicht automatisch
- **Ursache**: `mainloop()` blockiert
- **Lösung**: Verwende `dialog.root.after(ms, dialog.close)` für Timer
- **Beispiel**: `dialog.root.after(5000, dialog.close)  # 5 Sekunden`

### Text wird abgeschnitten
- **Ursache**: Dialog zu klein oder `wraplength` falsch
- **Lösung 1**: Erhöhe Dialog-Höhe in `__init__`
- **Lösung 2**: Setze `wraplength` Parameter in Label

### Spinner dreht nicht
- **Ursache**: Animation wurde nicht gestartet oder `animation_running = False`
- **Lösung**: Prüfe `_animate_spinners()` wird in `__init__` aufgerufen
- **Debug**: Füge `print()` in Animation-Loop ein

---

## 📝 Best Practices

### ✅ DO
- Verwende immer die Helper-Funktionen (`show_success()`, nicht `SuccessDialog().show()`)
- Zeige Details bei Fehlern (Stack-Trace, Logs)
- Verwende Icons aus `ModernDialog.ICON_*`
- Teste Dialogs mit `demo_dialogs.py` nach Änderungen
- Halte Titel kurz (max. 30 Zeichen)
- Verwende Corporate Colors

### ❌ DON'T
- Keine tkinter `messagebox` mehr verwenden (veraltet)
- Keine Dialogs im Main-Thread blockieren (Threading verwenden)
- Keine Hard-Coded Farben (verwende Class-Variablen)
- Keine zu langen Texte ohne `wraplength`
- Keine Custom-Fonts (Segoe UI verwenden)

---

## 🔗 Verwandte Dateien

- **Styles**: `scripts/styles.json` - Farben und Schriften für Word-Dokumente
- **Pipeline**: `run_pipeline.py` - Verwendet WelcomeDialog + ProcessingDialog
- **Tests**: `tests/test_dialogs.py` - Unit-Tests für alle Dialogs
- **Demo**: `demo_dialogs.py` - Interaktive Demo aller Dialogs

---

**Zuletzt aktualisiert**: 18. Dezember 2025  
**Version**: 2.0 (mit ProcessingDialog)
