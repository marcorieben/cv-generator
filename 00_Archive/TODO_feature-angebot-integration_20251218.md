# Feature: Angebots-Integration TODO

## 🎯 Ziel
CVs automatisch auf Stellenangebote zuschneiden durch parallele Verarbeitung von CV-PDF und Angebots-PDF.

## Status: In Entwicklung (Branch: `feature/angebot-integration`)

---

## ✅ Phase 1: Ordnerstruktur (ABGESCHLOSSEN)

- [x] **Todo #1:** Ordnerstruktur `input/cv/{pdf,json}` und `input/angebot/{pdf,json}` erstellt
- [x] **Todo #2:** Bestehende 18 JSONs + 3 PDFs nach `input/cv/` migriert, Tests bestehen (37/37)
- [x] **Todo #3:** `.gitignore` aktualisiert, Input-Dateien aus Git entfernt (bleiben lokal)
  - Commit: `6be5113` - "Update .gitignore: exclude input files from git tracking"

---

## 🎨 Phase 2: Dialog-System erweitern

### Todo #4: select_angebot_pdf() Funktion
**Datei:** `scripts/dialogs.py`

**Aufgabe:**
- Neue Funktion `select_angebot_pdf(initial_dir=None, title="Angebot/Stellenbeschreibung auswählen")`
- Analog zu `select_pdf_file()` aber mit Angebot-spezifischem Initialverzeichnis
- Default: `input/angebot/pdf/`

**Code-Snippet:**
```python
def select_angebot_pdf(initial_dir=None, title="Angebot/Stellenbeschreibung auswählen"):
    if not initial_dir:
        initial_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "angebot", "pdf")
    return select_pdf_file(initial_dir=initial_dir, title=title)
```

---

### Todo #5: show_welcome() erweitern
**Datei:** `scripts/dialogs.py`

**Aufgabe:**
- Welcome-Dialog erweitern mit 3 Schritten:
  1. CV-PDF auswählen (Pflicht)
  2. Angebot-PDF auswählen (Optional - "Überspringen" Button)
  3. Zusammenfassung anzeigen
- Rückgabewert ändern: `return (cv_path, angebot_path)` statt nur `cv_path`
- Bei Überspringen: `angebot_path = None`

**UI-Mockup:**
```
┌─────────────────────────────────────────┐
│  🎯 CV Generator - Angebotsspezifisch   │
├─────────────────────────────────────────┤
│  Schritt 1: CV-PDF auswählen            │
│  [Datei auswählen...]  ✅ cv_selected   │
│                                         │
│  Schritt 2: Angebot-PDF (Optional)      │
│  [Datei auswählen...]  [ Überspringen ] │
│                                         │
│  [ Weiter → ]                           │
└─────────────────────────────────────────┘
```

---

### Todo #6: Dialog UI testen
**Aufgabe:**
- Manueller Test mit `demo_dialogs.py` erweitern
- Test-Cases:
  1. Beide PDFs ausgewählt
  2. Nur CV-PDF (Angebot übersprungen)
  3. Abbruch im ersten Schritt

---

## 📄 Phase 3: PDF-Extraktion erweitern

### Todo #7: extract_text_from_pdf() für Angebot
**Datei:** `scripts/pdf_to_json.py`

**Aufgabe:**
- Funktion `extract_angebot_text(angebot_path)` erstellen
- Extrahiert nur reinen Text (keine Strukturierung nötig)
- Fehlerbehandlung: Return `None` bei Fehler

**Code-Snippet:**
```python
def extract_angebot_text(angebot_path):
    """Extrahiert Text aus Angebots-PDF für OpenAI Kontext"""
    try:
        reader = PdfReader(angebot_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"⚠️ Fehler beim Lesen des Angebots: {e}")
        return None
```

---

### Todo #8: OpenAI Prompt erweitern
**Datei:** `scripts/pdf_to_json.py`, Funktion `pdf_to_json()`

**Aufgabe:**
- Parameter erweitern: `pdf_to_json(pdf_path, output_path=None, angebot_text=None)`
- System-Prompt conditional anpassen:

**Ohne Angebot (bisherig):**
```python
system_prompt = """
Du bist ein Experte für CV-Extraktion...
[bestehender Prompt]
"""
```

**Mit Angebot (neu):**
```python
system_prompt = """
Du bist ein Experte für angebotsspezifische CV-Optimierung.

EINGABE:
1. CV-PDF des Kandidaten
2. Stellenangebot/Projektbeschreibung

ANGEBOT-TEXT:
{angebot_text}

AUFGABE:
- Extrahiere CV-Daten gemäß Schema
- PRIORISIERE Skills die im Angebot erwähnt werden
- FOKUSSIERE Kurzprofil auf Angebots-Anforderungen
- MATCHE Projektbeispiele mit Angebots-Kontext
- Bei fehlenden Skills: "! bitte prüfen !" verwenden

[restlicher Schema-Prompt]
"""
```

---

### Todo #9: Test mit Dummy-Angebot
**Aufgabe:**
- Dummy-Angebot erstellen: `input/angebot/pdf/test_projekt_python.pdf`
  - Inhalt: "Python, FastAPI, PostgreSQL, Docker, AWS"
- Test-CV: Arthur Fischer (vorhanden)
- Erwartung: Kurzprofil erwähnt Python/FastAPI prominent

---

## ⚙️ Phase 4: Pipeline-Integration

### Todo #10: run_pipeline() mit angebot_path
**Datei:** `run_pipeline.py`

**Aufgabe:**
- Signatur ändern: `run_pipeline(pdf_path, angebot_path=None)`
- Angebot-Text extrahieren falls `angebot_path` gegeben
- An `pdf_to_json()` weitergeben

**Code-Änderung:**
```python
def run_pipeline(pdf_path, angebot_path=None):
    # ...
    
    # Angebot-Text extrahieren (falls vorhanden)
    angebot_text = None
    if angebot_path:
        print(f"\n📋 Extrahiere Angebots-Informationen...")
        angebot_text = extract_angebot_text(angebot_path)
        if angebot_text:
            print(f"✅ {len(angebot_text)} Zeichen extrahiert")
    
    # PDF → JSON mit Angebots-Kontext
    json_data = pdf_to_json(pdf_path, output_path=None, angebot_text=angebot_text)
```

---

### Todo #11: Angebot-Text in JSON speichern (Optional)
**Datei:** `run_pipeline.py`

**Aufgabe:**
- Überlegen: Soll Angebot-Text im Output-JSON gespeichert werden?
- Vorteil: Nachvollziehbarkeit welches Angebot verwendet wurde
- Nachteil: JSON-Größe steigt

**Vorschlag:** Nur Metadaten speichern:
```json
{
  "Vorname": "Marco",
  ...
  "_metadata": {
    "angebot_referenz": "Projekt_Python_Backend.pdf",
    "generiert_am": "2025-12-17T17:30:00",
    "mit_angebot": true
  }
}
```

---

### Todo #12: Output-Dateiname mit Referenz
**Datei:** `run_pipeline.py`

**Aufgabe:**
- Dateinamen erweitern falls Angebot verwendet
- Bisherig: `Marco_Rieben_20251217_173000.json`
- Neu: `Marco_Rieben_ProjektX_20251217_173000.json`

**Code:**
```python
if angebot_path:
    angebot_name = os.path.splitext(os.path.basename(angebot_path))[0]
    # Sanitize: Nur erste 20 Zeichen, keine Sonderzeichen
    angebot_name = re.sub(r'[^a-zA-Z0-9]', '', angebot_name)[:20]
    json_filename = f"{vorname}_{nachname}_{angebot_name}_{timestamp}.json"
else:
    json_filename = f"{vorname}_{nachname}_{timestamp}.json"
```

---

## 🧪 Phase 5: Testing & Validation

### Todo #13: 2-PDF Workflow Unit Tests
**Datei:** `tests/test_angebot_integration.py` (neu)

**Test-Cases:**
```python
class TestAngebotIntegration:
    def test_extract_angebot_text_valid_pdf(self):
        """Test Angebots-Text-Extraktion"""
        
    def test_pdf_to_json_with_angebot_context(self):
        """Test OpenAI mit Angebots-Kontext"""
        
    def test_pipeline_with_angebot_generates_tailored_cv(self):
        """Test kompletter Workflow mit Angebot"""
```

---

### Todo #14: CV-only Workflow (Rückwärtskompatibilität)
**Datei:** `tests/test_angebot_integration.py`

**Test-Cases:**
```python
def test_pipeline_without_angebot_still_works(self):
    """Sicherstellen dass bisheriger Workflow funktioniert"""
    result = run_pipeline(cv_path, angebot_path=None)
    assert result is not None
```

---

### Todo #15: Dokumentation aktualisieren
**Dateien:**
- `README.md`: Neues Feature dokumentieren
- `ARCHITECTURE.md`: Datenfluss mit Angebot ergänzen
- `.github/copilot-instructions.md`: Neue Patterns hinzufügen

**Dokumentation:**
```markdown
## Angebotsspezifische CV-Generierung

### Workflow
1. CV-PDF hochladen (Pflicht)
2. Angebot-PDF hochladen (Optional)
3. OpenAI matched CV mit Angebots-Anforderungen
4. Generiertes CV ist auf Stelle zugeschnitten

### Beispiel
```bash
python run_pipeline.py cv.pdf angebot.pdf
```
```

---

## 📊 Definition of Done

- [ ] Alle 15 Todos abgeschlossen
- [ ] Alle bestehenden Tests bestehen (37/37)
- [ ] Mindestens 5 neue Tests für Angebots-Feature
- [ ] Dokumentation aktualisiert
- [ ] Manueller End-to-End Test erfolgreich
- [ ] Pull Request erstellt: `feature/angebot-integration` → `development`

---

## 🚀 Optionale Erweiterungen (Backlog)

- [ ] **Multi-Angebot Support:** Batch-Generierung für mehrere Angebote
- [ ] **Angebot-JSON Schema:** Strukturierte Extraktion statt nur Text
- [ ] **Skill-Matching Score:** Bewertung wie gut CV zum Angebot passt
- [ ] **Template-Varianten:** Unterschiedliche Word-Designs pro Angebots-Typ
- [ ] **Web-UI:** Drag & Drop für beide PDFs

---

## 📝 Notizen & Entscheidungen

**2025-12-17:**
- Entscheidung: Angebot-Text wird nicht im JSON gespeichert (nur Metadaten)
- Ordnerstruktur: Separation in `input/cv/` und `input/angebot/`
- Dateinamen-Konvention: `{Vorname}_{Nachname}_{AngebotKurz}_{Timestamp}`
