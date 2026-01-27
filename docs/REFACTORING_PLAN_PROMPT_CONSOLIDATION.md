# Refactoring Plan: Prompt & Schema Konsolidierung

> **Ziel:** Redundanz zwischen Python-Prompts und JSON-Schemas eliminieren, einheitliche Struktur für alle drei Cases (Jobprofile, CV, Offer) schaffen.

## Übersicht

| Phase | Beschreibung | Geschätzter Aufwand |
|-------|--------------|---------------------|
| 0 | Struktur-Reorganisation | 45 min |
| 1 | Vorbereitung & Baseline | 30 min |
| 2 | Schema-Bereinigung | 45 min |
| 3 | Prompt-Konsolidierung | 60 min |
| 4 | Testing | 45 min |
| 5 | Cleanup & Dokumentation | 30 min |

**Total: ~4 Stunden**

---

## Namenskonvention & Ordnerstruktur

### Prinzipien

1. **Feature-basierte Ordner** - Alle Dateien eines Features zusammen
2. **Konsistente Präfixe** - Alphabetische Sortierung innerhalb Ordner
3. **Klare Suffixe** - Sofort erkennbar was die Datei macht

### Suffix-Konvention

| Suffix | Bedeutung | Beispiel |
|--------|-----------|----------|
| `_prompt.py` | LLM Prompt-Logik | `cv_prompt.py` |
| `_schema.json` | JSON-Schema Definition | `cv_schema.json` |
| `_generator.py` | Hauptlogik/Orchestration | `cv_generator.py` |
| `_word.py` | Word-Dokument-Generierung | `cv_word.py` |
| `_extractor.py` | PDF-Extraktion | `cv_extractor.py` |

### Neue Ordnerstruktur (Prozess-orientiert)

> **Hinweis `_` Prefix:** Nummerierte Ordner erhalten einen `_` Prefix (z.B. `_1_extraction_jobprofile/`),
> weil Python-Module nicht mit einer Ziffer beginnen dürfen. Der Prefix signalisiert zudem:
> "internes Package — nicht direkt importieren, sondern über den Alias-Layer in `scripts/__init__.py`."

```
scripts/
├── __init__.py                                  # 🔑 ALIAS-LAYER: Zentrale Import-API
│
├── _shared/                                     # 📁 STEP 0: Gemeinsame Utilities
│   ├── __init__.py                              #    (Underscore = sortiert vor Nummern)
│   ├── pdf_utils.py                             #    PDF-Extraktion Utilities
│   ├── date_utils.py                            #    Datums-Normalisierung
│   └── prompt_rules.py                          #    Gemeinsame LLM Prompt-Regeln (NEU)
│
├── _1_extraction_jobprofile/                    # 📁 STEP 1: Stellenprofil extrahieren
│   ├── __init__.py                              #    Exportiert: extract_jobprofile, SCHEMA_PATH
│   ├── jobprofile_extractor.py                  #    Input: PDF → Output: JSON
│   ├── jobprofile_prompt.py                     #    LLM Prompt-Regeln (NEU)
│   └── jobprofile_schema.json                   #    (vorher: pdf_to_json_struktur_stellenprofil.json)
│
├── _2_extraction_cv/                            # 📁 STEP 2: CV extrahieren
│   ├── __init__.py                              #    Exportiert: extract_cv, validate_cv, SCHEMA_PATH
│   ├── cv_extractor.py                          #    Input: PDF + optional Jobprofile-JSON → Output: JSON
│   ├── cv_prompt.py                             #    LLM Prompt-Regeln (NEU)
│   ├── cv_schema.json                           #    (vorher: pdf_to_json_struktur_cv.json)
│   ├── cv_validator.py                          #    Validierung
│   └── cv_word.py                               #    Word-Export (kein LLM)
│
├── _3_analysis_matchmaking/                     # 📁 STEP 3: Matching CV ↔ Jobprofile
│   ├── __init__.py                              #    Exportiert: generate_matchmaking_json, SCHEMA_PATH
│   ├── matchmaking_generator.py                 #    Input: CV-JSON + Jobprofile-JSON → Output: Match-JSON
│   ├── matchmaking_prompt.py                    #    LLM Prompt-Regeln (NEU)
│   └── matchmaking_schema.json                  #    (vorher: matchmaking_json_schema.json)
│
├── _4_analysis_feedback/                        # 📁 STEP 4: CV Feedback generieren
│   ├── __init__.py                              #    Exportiert: generate_feedback_json, SCHEMA_PATH
│   ├── feedback_generator.py                    #    Input: CV-JSON + optional Jobprofile-JSON → Output: JSON
│   ├── feedback_prompt.py                       #    LLM Prompt-Regeln (NEU)
│   └── feedback_schema.json                     #    (vorher: cv_feedback_json_schema.json)
│
├── _5_generation_offer/                         # 📁 STEP 5: Offer erstellen
│   ├── __init__.py                              #    Exportiert: generate_offer_json, SCHEMA_PATH
│   ├── offer_generator.py                       #    Input: CV + Jobprofile + Match → Output: Offer-JSON
│   ├── offer_prompt.py                          #    LLM Prompt-Regeln (NEU)
│   ├── offer_schema.json                        #    (vorher: angebot_json_schema.json)
│   └── offer_word.py                            #    Word-Export (kein LLM)
│
├── _6_output_dashboard/                         # 📁 STEP 6: Visualisierung
│   ├── __init__.py                              #    Exportiert: generate_dashboard
│   └── dashboard_generator.py                   #    Input: Alle JSONs → Output: HTML Dashboard
│
├── pipeline.py                                  # Pipeline-Orchestration (bleibt)
└── streamlit_pipeline.py                        # Streamlit-Integration (bleibt)
```

### Import-Alias Layer

Ordnerstruktur (`_1_`, `_2_`, ...) darf **nicht** Teil der Import-API sein.
Consumer importieren ausschliesslich über `scripts/__init__.py` — nie direkt aus Feature-Ordnern.

**Vorteile:**
- Ordner-Umbenennungen brechen keine Imports
- Stabile API unabhängig von interner Struktur
- Nur `scripts/__init__.py` muss bei Reorganisationen angepasst werden

#### Feature-Ordner `__init__.py` (exportieren ihre Public API)

**`scripts/_1_extraction_jobprofile/__init__.py`**
```python
from scripts._1_extraction_jobprofile.jobprofile_extractor import extract_jobprofile
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "jobprofile_schema.json")
```

**`scripts/_2_extraction_cv/__init__.py`**
```python
from scripts._2_extraction_cv.cv_extractor import extract_cv
from scripts._2_extraction_cv.cv_validator import validate_cv
from scripts._2_extraction_cv.cv_word import generate_cv_word
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "cv_schema.json")
```

**`scripts/_3_analysis_matchmaking/__init__.py`**
```python
from scripts._3_analysis_matchmaking.matchmaking_generator import generate_matchmaking_json
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "matchmaking_schema.json")
```

**`scripts/_4_analysis_feedback/__init__.py`**
```python
from scripts._4_analysis_feedback.feedback_generator import generate_feedback_json
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "feedback_schema.json")
```

**`scripts/_5_generation_offer/__init__.py`**
```python
from scripts._5_generation_offer.offer_generator import generate_offer_json
from scripts._5_generation_offer.offer_word import generate_offer_word
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "offer_schema.json")
```

**`scripts/_6_output_dashboard/__init__.py`**
```python
from scripts._6_output_dashboard.dashboard_generator import generate_dashboard
```

#### Zentraler Alias-Layer: `scripts/__init__.py`

```python
# scripts/__init__.py
# ============================================================
# Public API — Import-Aliase
# ============================================================
# Consumer importieren von hier. Ordnerstruktur ist intern.
#
# Verwendung:
#   from scripts import extract_jobprofile, extract_cv
#   from scripts import generate_matchmaking_json
#   from scripts import JOBPROFILE_SCHEMA_PATH
# ============================================================

# Step 1: Jobprofile Extraction
from scripts._1_extraction_jobprofile import extract_jobprofile
from scripts._1_extraction_jobprofile import SCHEMA_PATH as JOBPROFILE_SCHEMA_PATH

# Step 2: CV Extraction
from scripts._2_extraction_cv import extract_cv, validate_cv, generate_cv_word
from scripts._2_extraction_cv import SCHEMA_PATH as CV_SCHEMA_PATH

# Step 3: Matchmaking
from scripts._3_analysis_matchmaking import generate_matchmaking_json
from scripts._3_analysis_matchmaking import SCHEMA_PATH as MATCHMAKING_SCHEMA_PATH

# Step 4: Feedback
from scripts._4_analysis_feedback import generate_feedback_json
from scripts._4_analysis_feedback import SCHEMA_PATH as FEEDBACK_SCHEMA_PATH

# Step 5: Offer
from scripts._5_generation_offer import generate_offer_json, generate_offer_word
from scripts._5_generation_offer import SCHEMA_PATH as OFFER_SCHEMA_PATH

# Step 6: Dashboard
from scripts._6_output_dashboard import generate_dashboard
```

#### Import-Vergleich: Vorher → Nachher

**`pipeline.py` — Vorher (aktuell):**
```python
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv, validate_json_structure
from scripts.generate_matchmaking import generate_matchmaking_json
from scripts.generate_cv_feedback import generate_cv_feedback_json
from scripts.generate_angebot import generate_angebot_json
from scripts.visualize_results import generate_dashboard

# Schema-Pfade hardcodiert:
schema_path = os.path.join(self.base_dir, "scripts", "matchmaking_json_schema.json")
```

**`pipeline.py` — Nachher (mit Alias):**
```python
from scripts import (
    extract_jobprofile, extract_cv, validate_cv, generate_cv_word,
    generate_matchmaking_json, generate_feedback_json,
    generate_offer_json, generate_dashboard,
    JOBPROFILE_SCHEMA_PATH, CV_SCHEMA_PATH,
    MATCHMAKING_SCHEMA_PATH, FEEDBACK_SCHEMA_PATH,
    OFFER_SCHEMA_PATH,
)

# Keine hardcodierten Pfade mehr nötig
```

**`app.py` — Vorher → Nachher:**
```python
# Vorher:
from scripts.generate_angebot import generate_angebot_json
from scripts.generate_angebot_word import generate_angebot_word

# Nachher:
from scripts import generate_offer_json, generate_offer_word
```

#### Schutz bei Ordner-Umbenennung

Szenario: `_5_generation_offer/` → `_5_output_offer/`

**Ohne Alias:** Jede Datei die `from scripts._5_generation_offer...` importiert, bricht.
**Mit Alias:** Nur eine Stelle ändern — `scripts/__init__.py`.
Alle Consumer (`pipeline.py`, `app.py`, `streamlit_pipeline.py`) bleiben unverändert.

### Prozess-Flow Visualisierung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CV GENERATOR PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐      ┌──────────────────┐                                │
│  │ 1_extraction_    │      │ 2_extraction_    │                                │
│  │   jobprofile     │─────▶│      cv          │                                │
│  │                  │      │                  │                                │
│  │ PDF → JSON       │      │ PDF → JSON       │                                │
│  │ (Anforderungen)  │      │ (mit JP-Kontext) │                                │
│  └────────┬─────────┘      └────────┬─────────┘                                │
│           │                         │                                          │
│           │    ┌────────────────────┼────────────────────┐                     │
│           │    │                    │                    │                     │
│           ▼    ▼                    ▼                    ▼                     │
│  ┌──────────────────┐      ┌──────────────────┐  ┌──────────────────┐         │
│  │ 3_analysis_      │      │ 4_analysis_      │  │    cv_word.py    │         │
│  │   matchmaking    │      │   feedback       │  │                  │         │
│  │                  │      │                  │  │  JSON → DOCX     │         │
│  │ CV + JP → Match  │      │ CV → Feedback    │  │  (CV Dokument)   │         │
│  └────────┬─────────┘      └──────────────────┘  └──────────────────┘         │
│           │                                                                    │
│           ▼                                                                    │
│  ┌──────────────────┐      ┌──────────────────┐                                │
│  │ 5_generation_    │      │ 6_output_        │                                │
│  │   offer          │─────▶│   dashboard      │                                │
│  │                  │      │                  │                                │
│  │ All → Offer      │      │ All → HTML       │                                │
│  │ JSON + DOCX      │      │ (Visualisierung) │                                │
│  └──────────────────┘      └──────────────────┘                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Test-Ordnerstruktur (Prozess-orientiert)

```
tests/
├── __init__.py
├── conftest.py                                 # Gemeinsame Fixtures & Pytest Config
│
├── _shared/                                    # 📁 Tests für Shared-Module
│   ├── __init__.py
│   ├── test_pdf_utils.py
│   ├── test_date_utils.py
│   └── test_prompt_rules.py
│
├── 1_extraction_jobprofile/                    # 📁 Tests für Jobprofile-Extraktion
│   ├── __init__.py
│   ├── test_jobprofile_extractor.py
│   ├── test_jobprofile_prompt.py
│   └── fixtures/
│       ├── sample_jobprofile.pdf
│       ├── valid_jobprofile.json
│       └── invalid_jobprofile.json
│
├── 2_extraction_cv/                            # 📁 Tests für CV-Extraktion
│   ├── __init__.py
│   ├── test_cv_extractor.py
│   ├── test_cv_prompt.py
│   ├── test_cv_validator.py
│   ├── test_cv_word.py
│   └── fixtures/
│       ├── sample_cv.pdf
│       ├── valid_cv.json
│       └── invalid_cv.json
│
├── 3_analysis_matchmaking/                     # 📁 Tests für Matchmaking
│   ├── __init__.py
│   ├── test_matchmaking_generator.py
│   ├── test_matchmaking_prompt.py
│   └── fixtures/
│       ├── sample_cv_for_match.json
│       ├── sample_jobprofile_for_match.json
│       └── expected_match_output.json
│
├── 4_analysis_feedback/                        # 📁 Tests für Feedback
│   ├── __init__.py
│   ├── test_feedback_generator.py
│   ├── test_feedback_prompt.py
│   └── fixtures/
│       └── expected_feedback_output.json
│
├── 5_generation_offer/                       # 📁 Tests für Offer
│   ├── __init__.py
│   ├── test_offer_generator.py
│   ├── test_offer_prompt.py
│   ├── test_offer_word.py
│   └── fixtures/
│       ├── sample_offer_input.json
│       └── expected_offer_output.json
│
├── 6_output_dashboard/                         # 📁 Tests für Dashboard
│   ├── __init__.py
│   ├── test_dashboard_generator.py
│   └── fixtures/
│       └── expected_dashboard.html
│
└── integration/                                # 📁 End-to-End Pipeline Tests
    ├── __init__.py
    ├── test_full_pipeline.py
    ├── test_pipeline_modes.py
    └── fixtures/
        ├── e2e_sample_cv.pdf
        └── e2e_sample_jobprofile.pdf
```

### Datei-Umbenennung (Migration)

| Alt | Neu | Step |
|-----|-----|------|
| `scripts/pdf_to_json_struktur_stellenprofil.json` | `scripts/_1_extraction_jobprofile/jobprofile_schema.json` | 1 |
| `scripts/pdf_to_json.py` (Stellenprofil-Teil) | `scripts/_1_extraction_jobprofile/jobprofile_extractor.py` | 1 |
| `scripts/pdf_to_json_struktur_cv.json` | `scripts/_2_extraction_cv/cv_schema.json` | 2 |
| `scripts/pdf_to_json.py` (CV-Teil) | `scripts/_2_extraction_cv/cv_extractor.py` | 2 |
| `scripts/generate_cv.py` | `scripts/_2_extraction_cv/cv_word.py` + `cv_validator.py` | 2 |
| `scripts/generate_matchmaking.py` | `scripts/_3_analysis_matchmaking/matchmaking_generator.py` | 3 |
| `scripts/matchmaking_json_schema.json` | `scripts/_3_analysis_matchmaking/matchmaking_schema.json` | 3 |
| `scripts/generate_cv_feedback.py` | `scripts/_4_analysis_feedback/feedback_generator.py` | 4 |
| `scripts/cv_feedback_json_schema.json` | `scripts/_4_analysis_feedback/feedback_schema.json` | 4 |
| `scripts/generate_angebot.py` | `scripts/_5_generation_offer/offer_generator.py` | 5 |
| `scripts/generate_angebot_word.py` | `scripts/_5_generation_offer/offer_word.py` | 5 |
| `scripts/angebot_json_schema.json` | `scripts/_5_generation_offer/offer_schema.json` | 5 |
| `scripts/visualize_results.py` | `scripts/_6_output_dashboard/dashboard_generator.py` | 6 |
| `tests/fixtures/*` | Verteilt in Step-Ordner | - |

---

## Phase 0: Struktur-Reorganisation

### 0.1 Prozess-Ordner erstellen

```bash
# Scripts: Prozess-orientierte Ordnerstruktur (mit _ Prefix für gültige Python-Module)
mkdir -p scripts/_shared
mkdir -p scripts/_1_extraction_jobprofile
mkdir -p scripts/_2_extraction_cv
mkdir -p scripts/_3_analysis_matchmaking
mkdir -p scripts/_4_analysis_feedback
mkdir -p scripts/_5_generation_offer
mkdir -p scripts/_6_output_dashboard

# Tests: Gleiche Nummerierung, OHNE _ Prefix (nicht als Python-Package importiert)
mkdir -p tests/_shared
mkdir -p tests/1_extraction_jobprofile/fixtures
mkdir -p tests/2_extraction_cv/fixtures
mkdir -p tests/3_analysis_matchmaking/fixtures
mkdir -p tests/4_analysis_feedback/fixtures
mkdir -p tests/5_generation_offer/fixtures
mkdir -p tests/6_output_dashboard/fixtures
mkdir -p tests/integration/fixtures
```

### 0.2 `__init__.py` Dateien erstellen (Alias-Layer)

Die `__init__.py` Dateien sind **nicht leer** — sie bilden den Import-Alias-Layer.
Inhalt siehe Abschnitt [Import-Alias Layer](#import-alias-layer) oben.

```bash
# Scripts: Feature-Ordner __init__.py (mit Re-Exports)
# → Inhalt gemäss Import-Alias Layer Abschnitt
touch scripts/_shared/__init__.py
# scripts/_1_extraction_jobprofile/__init__.py  → exportiert extract_jobprofile, SCHEMA_PATH
# scripts/_2_extraction_cv/__init__.py          → exportiert extract_cv, validate_cv, SCHEMA_PATH
# scripts/_3_analysis_matchmaking/__init__.py   → exportiert generate_matchmaking_json, SCHEMA_PATH
# scripts/_4_analysis_feedback/__init__.py      → exportiert generate_feedback_json, SCHEMA_PATH
# scripts/_5_generation_offer/__init__.py       → exportiert generate_offer_json, SCHEMA_PATH
# scripts/_6_output_dashboard/__init__.py       → exportiert generate_dashboard

# Scripts: Zentraler Alias-Layer
# scripts/__init__.py → Re-exportiert alles (siehe Import-Alias Layer Abschnitt)

# Tests: Leere __init__.py (nur für pytest Discovery)
touch tests/_shared/__init__.py
touch tests/1_extraction_jobprofile/__init__.py
touch tests/2_extraction_cv/__init__.py
touch tests/3_analysis_matchmaking/__init__.py
touch tests/4_analysis_feedback/__init__.py
touch tests/5_generation_offer/__init__.py
touch tests/6_output_dashboard/__init__.py
touch tests/integration/__init__.py
```

### 0.3 Dateien verschieben und umbenennen

```bash
# Step 1: Jobprofile Extraction
git mv scripts/pdf_to_json_struktur_stellenprofil.json scripts/_1_extraction_jobprofile/jobprofile_schema.json

# Step 2: CV Extraction
git mv scripts/pdf_to_json_struktur_cv.json scripts/_2_extraction_cv/cv_schema.json
git mv scripts/generate_cv.py scripts/_2_extraction_cv/cv_word.py

# Step 3: Matchmaking
git mv scripts/generate_matchmaking.py scripts/_3_analysis_matchmaking/matchmaking_generator.py
git mv scripts/matchmaking_json_schema.json scripts/_3_analysis_matchmaking/matchmaking_schema.json

# Step 4: Feedback
git mv scripts/generate_cv_feedback.py scripts/_4_analysis_feedback/feedback_generator.py
git mv scripts/cv_feedback_json_schema.json scripts/_4_analysis_feedback/feedback_schema.json

# Step 5: Offer
git mv scripts/generate_angebot.py scripts/_5_generation_offer/offer_generator.py
git mv scripts/generate_angebot_word.py scripts/_5_generation_offer/offer_word.py
git mv scripts/angebot_json_schema.json scripts/_5_generation_offer/offer_schema.json

# Step 6: Dashboard
git mv scripts/visualize_results.py scripts/_6_output_dashboard/dashboard_generator.py

# Test-Fixtures verschieben
git mv tests/fixtures/valid_cv.json tests/2_extraction_cv/fixtures/ 2>/dev/null || true
git mv tests/fixtures/sample_cv.pdf tests/2_extraction_cv/fixtures/ 2>/dev/null || true
```

### 0.4 pdf_to_json.py aufteilen

Die Datei `scripts/pdf_to_json.py` wird aufgeteilt in:

| Neue Datei | Inhalt |
|------------|--------|
| `scripts/_shared/pdf_utils.py` | `extract_text_from_pdf()` |
| `scripts/_shared/date_utils.py` | `normalize_date_format()` |
| `scripts/_shared/prompt_rules.py` | Gemeinsame LLM-Regeln |
| `scripts/_1_extraction_jobprofile/jobprofile_extractor.py` | Jobprofile-Extraktion |
| `scripts/_2_extraction_cv/cv_extractor.py` | CV-Extraktion + `normalize_json_structure()` |

### 0.5 Import-Alias-Layer einrichten

> **Kernprinzip:** Consumer importieren **nur** über `from scripts import ...`.
> Kein Code ausserhalb der Feature-Ordner importiert direkt aus `scripts._1_...`, `scripts._2_...` etc.

**Schritt 1:** Feature-`__init__.py` mit Re-Exports befüllen (siehe [Import-Alias Layer](#import-alias-layer)).

**Schritt 2:** Zentralen `scripts/__init__.py` Alias-Layer erstellen (siehe [Import-Alias Layer](#import-alias-layer)).

**Schritt 3:** Alle Consumer-Imports umstellen:

| Datei | Vorher | Nachher |
|-------|--------|---------|
| `pipeline.py` | `from scripts.pdf_to_json import pdf_to_json` | `from scripts import extract_jobprofile, extract_cv` |
| `pipeline.py` | `from scripts.generate_matchmaking import ...` | `from scripts import generate_matchmaking_json` |
| `pipeline.py` | `from scripts.generate_angebot import ...` | `from scripts import generate_offer_json` |
| `pipeline.py` | `os.path.join(..., "matchmaking_json_schema.json")` | `from scripts import MATCHMAKING_SCHEMA_PATH` |
| `app.py` | `from scripts.generate_angebot import ...` | `from scripts import generate_offer_json` |
| `app.py` | `from scripts.generate_angebot_word import ...` | `from scripts import generate_offer_word` |
| `streamlit_pipeline.py` | Alle `scripts.*` Imports | `from scripts import ...` |
| `pages/*.py` | Direkte Modul-Imports | `from scripts import ...` |

**Schritt 4:** Verifizieren, dass keine Imports direkt auf `scripts._1_...` etc. zugreifen:

```bash
# Prüfen: Keine direkten Imports auf interne Ordner (ausser in __init__.py)
grep -rn "from scripts\._[0-9]" --include="*.py" | grep -v "__init__.py"
# Erwartetes Ergebnis: Keine Treffer
```

---

## Phase 1: Vorbereitung & Baseline

### 1.1 Backup erstellen
```bash
# Git Branch erstellen
git checkout -b refactor/prompt-consolidation

# Aktuellen Stand committen falls uncommitted changes
git add -A && git commit -m "chore: Backup before prompt consolidation refactoring"
```

### 1.2 Baseline-Metriken erfassen

**Token-Zählung vor Refactoring:**

| Case | Input-Tokens (geschätzt) |
|------|--------------------------|
| Stellenprofil-Extraktion | ~2500 |
| CV-Extraktion | ~3000 |
| Offer-Generierung | ~1500 |

**Performance-Baseline:**
```bash
# Einen vollständigen Pipeline-Run durchführen und Zeit messen
# Notieren: Total Zeit, Zeit pro LLM-Call
python scripts/pipeline.py --cv "test_cv.pdf" --job "test_job.pdf"
```

### 1.3 Test-Fixtures vorbereiten

Sicherstellen, dass vorhanden (in neuer Struktur):
- [ ] `tests/2_extraction_cv/fixtures/valid_cv.json` - Referenz-CV
- [ ] `tests/1_extraction_jobprofile/fixtures/valid_jobprofile.json` - Referenz-Jobprofile
- [ ] `tests/3_analysis_matchmaking/fixtures/valid_match.json` - Referenz-Matching
- [ ] `tests/2_extraction_cv/fixtures/sample_cv.pdf` - Test-PDF CV
- [ ] `tests/1_extraction_jobprofile/fixtures/sample_jobprofile.pdf` - Test-PDF Jobprofile

---

## Phase 2: Schema-Bereinigung

### 2.1 Jobprofile-Schema bereinigen

**Datei:** `scripts/_1_extraction_jobprofile/jobprofile_schema.json`

**Änderungen:**
1. `_extraction_control` Block komplett entfernen (Zeilen 2-40)
2. `_hint_` Felder behalten
3. Validieren, dass JSON weiterhin valide ist

**Vorher:**
```json
{
  "_extraction_control": {
    "purpose": "...",
    "missing_value_marker": "...",
    "hard_rules": [...],
    ...
  },
  "metadata": { ... }
}
```

**Nachher:**
```json
{
  "_schema_info": {
    "version": "2.0",
    "type": "jobprofile",
    "description": "Schema for jobprofile extraction. Rules defined in jobprofile_prompt.py"
  },
  "metadata": { ... }
}
```

### 2.2 CV-Schema bereinigen

**Datei:** `scripts/_2_extraction_cv/cv_schema.json`

**Änderungen:**
1. `_extraction_control` Block komplett entfernen (Zeilen 2-43)
2. `_hint_` Felder behalten

### 2.3 Matchmaking-Schema prüfen

**Datei:** `scripts/_3_analysis_matchmaking/matchmaking_schema.json`

Falls `_extraction_control` vorhanden → entfernen.

### 2.4 Feedback-Schema prüfen

**Datei:** `scripts/_4_analysis_feedback/feedback_schema.json`

Falls `_extraction_control` vorhanden → entfernen.

### 2.5 Offer-Schema bereinigen

**Datei:** `scripts/_5_generation_offer/offer_schema.json`

**Änderungen:**
1. `_extraction_control` Block entfernen (Zeilen 2-27)
2. `_hint_` Felder behalten (werden von `extract_hints()` genutzt)

### 2.6 Schema-Validierung

```bash
# JSON-Syntax prüfen (neue Pfade)
python -c "import json; json.load(open('scripts/_1_extraction_jobprofile/jobprofile_schema.json'))"
python -c "import json; json.load(open('scripts/_2_extraction_cv/cv_schema.json'))"
python -c "import json; json.load(open('scripts/_3_analysis_matchmaking/matchmaking_schema.json'))"
python -c "import json; json.load(open('scripts/_4_analysis_feedback/feedback_schema.json'))"
python -c "import json; json.load(open('scripts/_5_generation_offer/offer_schema.json'))"
```

---

## Phase 3: Prompt-Konsolidierung

### 3.1 Übersicht Prompt-Dateien

| Step | Datei | Inhalt |
|------|-------|--------|
| 0 | `scripts/_shared/prompt_rules.py` | Gemeinsame Regeln & Utilities |
| 1 | `scripts/_1_extraction_jobprofile/jobprofile_prompt.py` | Jobprofile-Extraktion Regeln |
| 2 | `scripts/_2_extraction_cv/cv_prompt.py` | CV-Extraktion Regeln |
| 3 | `scripts/_3_analysis_matchmaking/matchmaking_prompt.py` | Matching-Analyse Regeln |
| 4 | `scripts/_4_analysis_feedback/feedback_prompt.py` | Feedback-Generierung Regeln |
| 5 | `scripts/_5_generation_offer/offer_prompt.py` | Offer-Generierung Regeln |

### 3.2 Shared Prompt Rules erstellen

**Datei:** `scripts/_shared/prompt_rules.py`

```python
"""
Shared prompt rules and utilities for all LLM generation modules.

This module contains:
- Common rules applied to all LLM calls (Swiss spelling, no invention, etc.)
- Helper functions for building prompts
- Schema hint extraction utilities
"""

# Common rules applied to all LLM calls
COMMON_RULES = {
    "swiss_spelling": (
        "SWISS SPELLING: Use Swiss German spelling exclusively. "
        "Replace every 'ß' with 'ss' (e.g., 'gross' not 'groß')."
    ),
    "no_invention": (
        "NO INVENTION: Never invent or guess information. "
        "Only use information explicitly present in the document."
    ),
    "missing_marker": (
        "MISSING DATA: Mark missing information with '{marker}'"
    ),
    "strict_schema": (
        "STRICT SCHEMA: Follow field names and structure exactly. "
        "No additional fields allowed."
    ),
}


def get_missing_marker(language: str = "de") -> str:
    """Return the language-specific marker for missing data."""
    markers = {
        "de": "! bitte prüfen !",
        "en": "! please check !",
        "fr": "! à vérifier !"
    }
    return markers.get(language, markers["de"])


def get_language_name(language_code: str) -> str:
    """Return the full language name for a language code."""
    names = {"de": "Deutsch", "en": "English", "fr": "Français"}
    return names.get(language_code, "Deutsch")


def build_language_instruction(target_language: str) -> str:
    """Build the language instruction for the prompt."""
    lang_name = get_language_name(target_language)
    return (
        f"TARGET LANGUAGE: Extract and translate all content consistently to {lang_name}. "
        "Keep technical terms (Scrum, Python, etc.) in their original form."
    )


def extract_hints_from_schema(schema: dict, prefix: str = "_hint_") -> dict:
    """
    Extract all _hint_ fields from a schema.

    Based on the approach in offer_generator.py.
    Recursively processes nested structures.

    Args:
        schema: The JSON schema dictionary
        prefix: The prefix identifying hint fields (default: "_hint_")

    Returns:
        Dictionary with extracted hints
    """
    hints = {}
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key.startswith(prefix):
                field_name = key[len(prefix):]
                hints[field_name] = value
            elif isinstance(value, (dict, list)):
                nested = extract_hints_from_schema(value, prefix)
                if nested:
                    hints[key] = nested
    elif isinstance(schema, list):
        for item in schema:
            nested = extract_hints_from_schema(item, prefix)
            hints.update(nested)
    return hints


def build_numbered_rules(rules: list[str], start_number: int = 1) -> str:
    """Build a numbered list of rules for the prompt."""
    lines = []
    for i, rule in enumerate(rules, start=start_number):
        lines.append(f"{i}. {rule}")
    return "\n".join(lines)
```

### 3.3 CV Prompt erstellen

**Datei:** `scripts/_2_extraction_cv/cv_prompt.py`

```python
"""
CV extraction prompt rules.

Consolidates all rules previously in pdf_to_json.py and cv_schema.json.
"""
import json
from scripts._shared.prompt_rules import (
    COMMON_RULES,
    get_missing_marker,
    build_language_instruction,
    build_numbered_rules
)

# CV-specific extraction rules
CV_EXTRACTION_RULES = [
    # Sprachen
    """SPRACHEN: Level 1-5 numerisch. Normalisiere unterschiedliche Skalen:
   - Grafische Elemente (Sterne, Punkte) haben VORRANG vor Textbeschreibungen
   - 5er-Skala: 1=1, ..., 5=5
   - 3er-Skala: 1=1, 2=3, 3=5
   - Text: A1/A2=1, B1=2, B2=3, C1=4, C2/Muttersprache=5
   Sortiere absteigend nach Level.""",

    # Referenzprojekte
    """REFERENZPROJEKTE: Erfasse VOLLSTÄNDIG ALLE beruflichen Stationen aus dem gesamten Lebenslauf.
   - 'Ausgewählte_Referenzprojekte' muss ALLE Stationen enthalten (nicht nur eine Auswahl)
   - Jede Station als eigenes Objekt
   - TÄTIGKEITEN: Erfasse WÖRTLICH und VOLLSTÄNDIG, keine Kürzungen""",

    # Fachwissen
    """FACHWISSEN: Immer genau 3 Kategorien in dieser Reihenfolge:
   1. "Projektmethodik" (Scrum, SAFe, HERMES, Kanban, etc.)
   2. "Tech Stack" (Technologien, Tools, Sprachen)
   3. "Weitere Skills" (Soft Skills, Domain-Wissen)
   Verwende "Inhalt" (nicht "BulletList"), direkt auf oberster Ebene (nicht in "Expertise").""",

    # Zertifikate
    "ZERTIFIKATE: Erfasse ausnahmslos JEDES Zertifikat und Training. Keine Auslassungen.",

    # Kurzprofil
    "KURZPROFIL: 50-100 Wörter, 3. Person mit Vornamen. Nur belegbare Stärken, keine Übertreibungen.",

    # Rolle
    "ROLLE in Referenzprojekten: Maximal 8 Wörter, kurz und prägnant.",

    # Zeitformate
    """ZEITFORMATE:
   - Referenzprojekte: MM/YYYY - MM/YYYY
   - Aus_und_Weiterbildung & Trainings: Nur YYYY""",
]

def build_cv_extraction_prompt(schema: dict, target_language: str = "de", job_profile_context: dict = None) -> tuple[str, str]:
    """
    Baut den System- und User-Prompt für CV-Extraktion.

    Returns:
        tuple: (system_prompt, user_prompt_template)
    """
    missing_marker = get_missing_marker(target_language)

    # System Prompt aufbauen
    system_parts = [
        "Du bist ein Experte für CV-Extraktion und arbeitest für eine IT-Beratungsfirma.",
        "",
        "Deine Aufgabe: Extrahiere alle Informationen aus dem bereitgestellten CV-Text und erstelle ein strukturiertes JSON gemäss dem Schema.",
        "",
        "WICHTIGE REGELN:",
    ]

    # Gemeinsame Regeln
    rule_num = 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['no_invention']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['missing_marker'].format(marker=missing_marker)}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['strict_schema']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['swiss_spelling']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {build_language_instruction(target_language)}")

    # CV-specific rules
    for rule in CV_EXTRACTION_RULES:
        rule_num += 1
        system_parts.append(f"{rule_num}. {rule}")

    # Schema anhängen (ohne _extraction_control, nur Struktur + Hints)
    system_parts.append("")
    system_parts.append("SCHEMA:")
    system_parts.append(json.dumps(schema, ensure_ascii=False, indent=2))
    system_parts.append("")
    system_parts.append("Antworte ausschliesslich mit dem validen JSON-Objekt gemäss diesem Schema.")

    system_prompt = "\n".join(system_parts)

    # User Prompt Template
    user_template = f"Extrahiere die CV-Daten (Zielsprache: {target_language.upper()}) aus folgendem Text:\n\n{{cv_text}}"

    if job_profile_context:
        user_template = (
            f"KONTEXT (Ziel-Stellenprofil):\n{json.dumps(job_profile_context, ensure_ascii=False)}\n\n"
            "Nutze diesen Kontext, um im CV besonders auf relevante Erfahrungen zu achten. "
            "Die Extraktion bleibt faktenbasiert auf dem CV-Text.\n\n"
            + user_template
        )

    return system_prompt, user_template
```

### 3.4 Jobprofile Prompt erstellen

**Datei:** `scripts/_1_extraction_jobprofile/jobprofile_prompt.py`

```python
"""
Job profile extraction prompt rules.
"""
import json
from scripts._shared.prompt_rules import (
    COMMON_RULES,
    get_missing_marker,
    build_language_instruction
)

# Jobprofile-specific extraction rules
JOBPROFILE_EXTRACTION_RULES = [
    "REQUIREMENTS: Each criterion as SEPARATE entry. No summaries.",
    "PRIORITIZATION: Role descriptions and tasks over marketing text.",
    "LISTS: Maintain document granularity, no consolidation.",
]


def build_jobprofile_prompt(
    schema: dict,
    target_language: str = "de"
) -> tuple[str, str]:
    """Build system and user prompt for jobprofile extraction."""
    missing_marker = get_missing_marker(target_language)

    system_parts = [
        "You are an expert for analyzing IT project offers and job profiles.",
        "",
        "Your task: Extract all requirements and conditions from the job profile.",
        "",
        "IMPORTANT RULES:",
    ]

    rule_num = 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['no_invention']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['missing_marker'].format(marker=missing_marker)}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['strict_schema']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['swiss_spelling']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {build_language_instruction(target_language)}")

    for rule in JOBPROFILE_EXTRACTION_RULES:
        rule_num += 1
        system_parts.append(f"{rule_num}. {rule}")

    system_parts.append("")
    system_parts.append("SCHEMA:")
    system_parts.append(json.dumps(schema, ensure_ascii=False, indent=2))
    system_parts.append("")
    system_parts.append("Respond only with the valid JSON object.")

    return "\n".join(system_parts), "Extract job profile data from:\n\n{text}"
```

### 3.5 Offer Prompt erstellen

**Datei:** `scripts/_5_generation_offer/offer_prompt.py`

```python
"""
Offer generation prompt rules.

Based on existing approach in offer_generator.py.
Uses hint extraction from schema.
"""
from scripts._shared.prompt_rules import (
    extract_hints_from_schema,
    get_language_name
)

# Offer-specific generation rules
OFFER_GENERATION_RULES = [
    "LANGUAGE: Generate all text consistently in target language.",
    "TONE: Professional, empathetic, convincing. Swiss spelling (ss not ß).",
    "WE-FORM: Always use 'We as Orange Business', never 'I'.",
    "STRICTLY POSITIVE: Never mention gaps or deficits. Only strengths.",
    "BOLD: Use **bold** for keywords, technologies, customer name.",
]


def build_offer_prompt(schema: dict, language: str = "de") -> str:
    """
    Build system prompt for offer generation.

    Uses hint extraction approach for relevant fields.
    """
    lang_name = get_language_name(language)

    system_parts = [
        f"You are an expert for professional IT service offers in **{lang_name}**.",
        "",
        "IMPORTANT RULES:",
    ]

    for i, rule in enumerate(OFFER_GENERATION_RULES, 1):
        system_parts.append(f"{i}. {rule}")

    # Extract hints from schema
    hints = extract_hints_from_schema(schema)
    system_parts.append("")
    system_parts.append("FIELDS (with hints):")

    # Relevant hints for qualitative fields
    relevant_fields = [
        ("kurzkontext", "stellenbezug"),
        ("eignungs_summary", "kandidatenvorschlag"),
        ("zusammenfassung", "gesamtbeurteilung"),
        ("mehrwert_fuer_kunden", "gesamtbeurteilung"),
        ("empfehlung", "gesamtbeurteilung"),
    ]

    for field, section in relevant_fields:
        hint = hints.get(section, {}).get(field, "")
        if hint:
            system_parts.append(f"- '{field}': {hint}")

    return "\n".join(system_parts)
```

### 3.6 CV Extractor aktualisieren

**Datei:** `scripts/_2_extraction_cv/cv_extractor.py`

**Änderungen:**
1. Import des neuen Prompt-Moduls
2. System-Prompt-Generierung durch Modul-Aufruf ersetzen
3. Alte Inline-Regeln entfernen

```python
# NEW: Import from prompt module
from scripts._2_extraction_cv.cv_prompt import build_cv_extraction_prompt
from scripts._shared.pdf_utils import extract_text_from_pdf
from scripts._shared.date_utils import normalize_date_format

def extract_cv(pdf_path, schema_path, target_language="de", job_profile_context=None):
    """Extract CV data from PDF."""
    # Load schema
    schema = load_schema(schema_path)

    # Build prompt using dedicated module
    system_prompt, user_template = build_cv_extraction_prompt(
        schema, target_language, job_profile_context
    )

    # Extract text and call LLM...
```

### 3.7 Jobprofile Extractor aktualisieren

**Datei:** `scripts/_1_extraction_jobprofile/jobprofile_extractor.py`

```python
# NEW: Import from prompt module
from scripts._1_extraction_jobprofile.jobprofile_prompt import build_jobprofile_prompt
from scripts._shared.pdf_utils import extract_text_from_pdf

def extract_jobprofile(pdf_path, schema_path, target_language="de"):
    """Extract job profile data from PDF."""
    schema = load_schema(schema_path)
    system_prompt, user_template = build_jobprofile_prompt(schema, target_language)
    # ...
```

### 3.8 Offer Generator aktualisieren

**Datei:** `scripts/_5_generation_offer/offer_generator.py`

```python
# NEW: Import from prompt module (interner Import innerhalb Feature-Ordner)
from scripts._5_generation_offer.offer_prompt import build_offer_prompt

def generate_offer_json(cv_json_path, jobprofile_json_path, match_json_path, ...):
    """Generate offer JSON."""
    schema = load_schema(schema_path)
    system_prompt = build_offer_prompt(schema, language)
    # ...
```

---

## Phase 4: Testing

### 4.1 Unit Tests für Shared Prompt Rules

**Datei:** `tests/_shared/test_prompt_rules.py`

```python
"""Tests for shared prompt rules module."""
import pytest
from scripts._shared.prompt_rules import (
    get_missing_marker,
    extract_hints_from_schema,
    get_language_name,
    build_numbered_rules,
    COMMON_RULES
)


class TestMissingMarker:
    """Tests for get_missing_marker()"""

    def test_german(self):
        assert get_missing_marker("de") == "! bitte prüfen !"

    def test_english(self):
        assert get_missing_marker("en") == "! please check !"

    def test_french(self):
        assert get_missing_marker("fr") == "! à vérifier !"

    def test_fallback(self):
        assert get_missing_marker("xx") == "! bitte prüfen !"


class TestHintExtraction:
    """Tests for extract_hints_from_schema()"""

    def test_simple_hint(self):
        schema = {
            "field1": "value",
            "_hint_field1": "This is a hint"
        }
        hints = extract_hints_from_schema(schema)
        assert hints == {"field1": "This is a hint"}

    def test_nested_hint(self):
        schema = {
            "section": {
                "field1": "",
                "_hint_field1": "Nested hint"
            }
        }
        hints = extract_hints_from_schema(schema)
        assert hints["section"]["field1"] == "Nested hint"

    def test_empty_schema(self):
        assert extract_hints_from_schema({}) == {}
```

### 4.2 Unit Tests für CV Prompt

**Datei:** `tests/2_extraction_cv/test_cv_prompt.py`

```python
"""Tests for CV extraction prompt module."""
import pytest
from scripts._2_extraction_cv.cv_prompt import (
    build_cv_extraction_prompt,
    CV_EXTRACTION_RULES
)


class TestCVPrompt:
    """Tests for CV prompt building"""

    @pytest.fixture
    def sample_schema(self):
        return {
            "Vorname": "",
            "_hint_Vorname": "First name",
            "Nachname": ""
        }

    def test_returns_tuple(self, sample_schema):
        result = build_cv_extraction_prompt(sample_schema)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_contains_swiss_spelling_rule(self, sample_schema):
        system_prompt, _ = build_cv_extraction_prompt(sample_schema)
        assert "ss" in system_prompt.lower() or "swiss" in system_prompt.lower()

    def test_contains_schema(self, sample_schema):
        system_prompt, _ = build_cv_extraction_prompt(sample_schema)
        assert "Vorname" in system_prompt

    def test_language_german(self, sample_schema):
        system_prompt, _ = build_cv_extraction_prompt(sample_schema, "de")
        assert "Deutsch" in system_prompt

    def test_language_english(self, sample_schema):
        system_prompt, _ = build_cv_extraction_prompt(sample_schema, "en")
        assert "English" in system_prompt
```

### 4.3 Unit Tests für Offer Prompt

**Datei:** `tests/5_generation_offer/test_offer_prompt.py`

```python
"""Tests for Offer generation prompt module."""
import pytest
from scripts._5_generation_offer.offer_prompt import (
    build_offer_prompt,
    OFFER_GENERATION_RULES
)


class TestOfferPrompt:
    """Tests for Offer prompt building"""

    @pytest.fixture
    def sample_schema(self):
        return {
            "stellenbezug": {
                "kurzkontext": "",
                "_hint_kurzkontext": "Personal introduction"
            }
        }

    def test_contains_we_form_rule(self, sample_schema):
        prompt = build_offer_prompt(sample_schema)
        assert "We" in prompt or "we" in prompt

    def test_extracts_hints(self, sample_schema):
        prompt = build_offer_prompt(sample_schema)
        assert "kurzkontext" in prompt.lower()
```

### 4.4 Integration Tests

**Datei:** `tests/integration/test_full_pipeline.py`

```python
"""Integration tests for full pipeline after refactoring."""
import pytest
import json
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key required"
)


class TestCVExtractionIntegration:
    """End-to-end tests for CV extraction."""

    def test_cv_extraction_produces_valid_json(self, tmp_path):
        """Verify CV extraction produces valid JSON."""
        from scripts._2_extraction_cv.cv_extractor import extract_cv

        fixture_pdf = "tests/2_extraction_cv/fixtures/sample_cv.pdf"
        if not os.path.exists(fixture_pdf):
            pytest.skip("Fixture PDF not found")

        output_path = tmp_path / "cv_output.json"
        result = extract_cv(fixture_pdf, str(output_path))

        assert result is not None
        assert "Vorname" in result
        assert "Nachname" in result
        assert "Fachwissen_und_Schwerpunkte" in result

    def test_cv_has_three_skill_categories(self, tmp_path):
        """Verify exactly 3 skill categories exist."""
        from scripts._2_extraction_cv.cv_extractor import extract_cv

        fixture_pdf = "tests/2_extraction_cv/fixtures/sample_cv.pdf"
        if not os.path.exists(fixture_pdf):
            pytest.skip("Fixture PDF not found")

        result = extract_cv(fixture_pdf, None)

        fachwissen = result.get("Fachwissen_und_Schwerpunkte", [])
        assert len(fachwissen) == 3


class TestOutputComparison:
    """Compare output before/after refactoring."""

    def test_output_structure_unchanged(self):
        """Verify output structure is identical."""
        baseline_path = "tests/2_extraction_cv/fixtures/valid_cv.json"
        if not os.path.exists(baseline_path):
            pytest.skip("Baseline fixture not found")

        with open(baseline_path) as f:
            baseline = json.load(f)

        required_fields = [
            "Vorname", "Nachname", "Hauptrolle", "Nationalität",
            "Ausbildung", "Kurzprofil", "Fachwissen_und_Schwerpunkte",
            "Aus_und_Weiterbildung", "Trainings_und_Zertifizierungen",
            "Sprachen", "Ausgewählte_Referenzprojekte"
        ]

        for field in required_fields:
            assert field in baseline, f"Missing field: {field}"
```

### 4.5 Test-Befehle

```bash
# Run all tests
pytest tests/ -v

# Run tests by step
pytest tests/_shared/ -v                      # Step 0: Shared
pytest tests/1_extraction_jobprofile/ -v      # Step 1
pytest tests/2_extraction_cv/ -v              # Step 2
pytest tests/3_analysis_matchmaking/ -v       # Step 3
pytest tests/4_analysis_feedback/ -v          # Step 4
pytest tests/5_generation_offer/ -v         # Step 5
pytest tests/6_output_dashboard/ -v           # Step 6
pytest tests/integration/ -v                  # E2E

# Coverage report
pytest tests/ --cov=scripts --cov-report=html
```

### 4.6 Manual End-to-End Test

```bash
# Test pipeline with real data
python scripts/pipeline.py \
    --cv "tests/2_extraction_cv/fixtures/sample_cv.pdf" \
    --job "tests/1_extraction_jobprofile/fixtures/sample_jobprofile.pdf" \
    --output "output/refactor_test"

# Compare output with baseline
diff output/refactor_test/cv.json tests/2_extraction_cv/fixtures/valid_cv.json
```

---

## Phase 5: Cleanup & Dokumentation

### 5.1 Alte Dateien aufräumen

**Zu löschende Dateien (nach Migration):**
```bash
# Old files in scripts/ root (now moved to step folders)
git rm scripts/pdf_to_json.py                           # → Split into step 1 & 2
git rm scripts/pdf_to_json_struktur_cv.json             # → 2_extraction_cv/
git rm scripts/pdf_to_json_struktur_stellenprofil.json  # → 1_extraction_jobprofile/
git rm scripts/generate_cv.py                           # → 2_extraction_cv/
git rm scripts/generate_matchmaking.py                  # → 3_analysis_matchmaking/
git rm scripts/matchmaking_json_schema.json             # → 3_analysis_matchmaking/
git rm scripts/generate_cv_feedback.py                  # → 4_analysis_feedback/
git rm scripts/cv_feedback_json_schema.json             # → 4_analysis_feedback/
git rm scripts/generate_angebot.py                     # → 5_generation_offer/
git rm scripts/generate_angebot_word.py                # → 5_generation_offer/
git rm scripts/angebot_json_schema.json               # → 5_generation_offer/
git rm scripts/visualize_results.py                     # → 6_output_dashboard/

# Old test fixtures
git rm -r tests/fixtures/                               # → Moved to step folders
```

**Schema-Bereinigung prüfen:**
- [ ] `scripts/_1_extraction_jobprofile/jobprofile_schema.json` - `_extraction_control` entfernt?
- [ ] `scripts/_2_extraction_cv/cv_schema.json` - `_extraction_control` entfernt?
- [ ] `scripts/_3_analysis_matchmaking/matchmaking_schema.json` - `_extraction_control` entfernt?
- [ ] `scripts/_4_analysis_feedback/feedback_schema.json` - `_extraction_control` entfernt?
- [ ] `scripts/_5_generation_offer/offer_schema.json` - `_extraction_control` entfernt?

### 5.2 Code-Kommentare aktualisieren

In allen bearbeiteten Dateien:
- Docstrings aktualisieren
- Verweise auf alte Struktur entfernen
- Hinweise auf neue Prompt-Module hinzufügen

### 5.3 Dokumentation aktualisieren

**Datei:** `docs/GENERATION_RULES.md` (neu erstellen)

```markdown
# Generation Rules Overview

## Architecture

The codebase follows a process-oriented folder structure:

```
scripts/
├── __init__.py                      # Alias-Layer (zentrale Import-API)
├── _shared/                         # Shared utilities & prompt rules
├── _1_extraction_jobprofile/        # Step 1: Extract job profile
├── _2_extraction_cv/                # Step 2: Extract CV
├── _3_analysis_matchmaking/         # Step 3: Match CV ↔ Jobprofile
├── _4_analysis_feedback/            # Step 4: Generate feedback
├── _5_generation_offer/             # Step 5: Generate offer
└── _6_output_dashboard/             # Step 6: Create dashboard
```

## Prompt Rules per Step

### Step 1: Jobprofile Extraction
- Prompt: `scripts/_1_extraction_jobprofile/jobprofile_prompt.py`
- Schema: `scripts/_1_extraction_jobprofile/jobprofile_schema.json`
- Rules: `JOBPROFILE_EXTRACTION_RULES`

### Step 2: CV Extraction
- Prompt: `scripts/_2_extraction_cv/cv_prompt.py`
- Schema: `scripts/_2_extraction_cv/cv_schema.json`
- Rules: `CV_EXTRACTION_RULES`

### Step 3: Matchmaking Analysis
- Prompt: `scripts/_3_analysis_matchmaking/matchmaking_prompt.py`
- Schema: `scripts/_3_analysis_matchmaking/matchmaking_schema.json`

### Step 4: Feedback Analysis
- Prompt: `scripts/_4_analysis_feedback/feedback_prompt.py`
- Schema: `scripts/_4_analysis_feedback/feedback_schema.json`

### Step 5: Offer Generation
- Prompt: `scripts/_5_generation_offer/offer_prompt.py`
- Schema: `scripts/_5_generation_offer/offer_schema.json`
- Rules: `OFFER_GENERATION_RULES`

## Modifying Rules

1. ALWAYS change rules in Python `*_prompt.py` files (not in JSON)
2. `_hint_` fields in JSON are for field-specific hints only
3. After changes: Run tests `pytest tests/<step_folder>/`
```

### 5.4 CHANGELOG aktualisieren

**Datei:** `CHANGELOG.md`

```markdown
## [Unreleased]

### Changed
- Refactored: Prompt-Logik in separate Module konsolidiert
- Removed: `_extraction_control` Blöcke aus allen JSON-Schemas
- Optimized: ~1600 Tokens pro Pipeline-Run eingespart

### Added
- `scripts/__init__.py` - Import-Alias-Layer (stabile API)
- `scripts/_*/__init__.py` - Feature-Exports pro Step
- `scripts/_shared/prompt_rules.py` - Gemeinsame Prompt-Regeln
- `docs/GENERATION_RULES.md` - Dokumentation der Regeln
- Step-spezifische `*_prompt.py` Module und Tests
```

### 5.5 Git Commit & PR

```bash
# Commit all changes
git add -A
git commit -m "refactor: Reorganize codebase with process-oriented structure

BREAKING CHANGE: File paths have changed. Update imports accordingly.

## Structure Changes
- Reorganize scripts/ into numbered process steps (1-6)
- Move schemas into respective step folders
- Split pdf_to_json.py into step-specific extractors
- Create dedicated prompt modules per step

## New Folder Structure
scripts/
├── __init__.py                 # Import-Alias-Layer
├── _shared/                    # Shared utilities
├── _1_extraction_jobprofile/   # Step 1
├── _2_extraction_cv/           # Step 2
├── _3_analysis_matchmaking/    # Step 3
├── _4_analysis_feedback/       # Step 4
├── _5_generation_offer/        # Step 5
└── _6_output_dashboard/        # Step 6

## Import-Alias Layer
- Central scripts/__init__.py re-exports all public APIs
- Consumer imports via 'from scripts import ...' only
- No direct imports from _1_, _2_, etc. outside __init__.py

## Prompt Consolidation
- Remove _extraction_control blocks from all JSON schemas
- Consolidate rules in *_prompt.py modules
- Single source of truth for LLM rules

## Benefits
- ~1600 tokens saved per pipeline run
- Clear process flow visible in folder structure
- Stable import API decoupled from folder structure
- Feature-based test organization

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push branch
git push -u origin refactor/prompt-consolidation

# Create PR
gh pr create --title "Refactor: Process-oriented folder structure & prompt consolidation" --body "..."
```

---

## Checkliste

### Phase 0: Struktur-Reorganisation
- [x] Prozess-Ordner erstellt (`scripts/_1_extraction_jobprofile/`, etc.)
- [x] Test-Ordner erstellt (`tests/1_extraction_jobprofile/`, etc.)
- [x] Feature-`__init__.py` mit Re-Exports erstellt (pro Step-Ordner)
- [x] Zentraler Alias-Layer `scripts/__init__.py` erstellt
- [x] Dateien verschoben und umbenannt
- [x] `pdf_to_json.py` aufgeteilt in Extraktoren
- [x] Consumer-Imports umgestellt auf `from scripts import ...`
- [x] Keine direkten Imports auf `scripts._1_...` ausserhalb `__init__.py`
- [x] Verifikation: `grep -rn "from scripts\._[0-9]" | grep -v __init__` = leer

### Phase 1: Vorbereitung
- [x] Git Branch erstellt (`feature/prompt-consolidation`)
- [x] Baseline-Commit: `6be8e51` (75 Tests bestanden)
- [x] Test-Fixtures in neue Ordner verschoben

### Phase 2: Schema-Bereinigung
- [x] `_1_extraction_jobprofile/jobprofile_schema.json` bereinigt (`_extraction_control` -> `_schema_info`)
- [x] `_2_extraction_cv/cv_schema.json` bereinigt
- [x] `_3_analysis_matchmaking/matchmaking_schema.json` bereinigt
- [x] `_4_analysis_feedback/feedback_schema.json` bereinigt
- [x] `_5_generation_offer/offer_schema.json` bereinigt
- [x] Alle JSON-Dateien valide (python -c "json.load()" bestanden)

### Phase 3: Prompt-Konsolidierung
- [x] `scripts/_shared/prompt_rules.py` erstellt (COMMON_RULES, extract_hints, get_missing_marker)
- [x] `scripts/_1_extraction_jobprofile/jobprofile_prompt.py` erstellt
- [x] `scripts/_2_extraction_cv/cv_prompt.py` erstellt
- [x] `scripts/_3_analysis_matchmaking/matchmaking_prompt.py` erstellt (Wrapper fuer translations.json)
- [x] `scripts/_4_analysis_feedback/feedback_prompt.py` erstellt (Wrapper fuer translations.json)
- [x] `scripts/_5_generation_offer/offer_prompt.py` erstellt (mit Hint-Extraktion)
- [x] Extraktoren/Generatoren aktualisiert (Inline-Prompts durch Module ersetzt)

### Phase 4: Testing
- [x] `tests/_shared/test_prompt_rules.py` geschrieben (16 Tests)
- [x] `tests/2_extraction_cv/test_cv_prompt.py` geschrieben (13 Tests)
- [x] `tests/5_generation_offer/test_offer_prompt.py` geschrieben (11 Tests)
- [x] Alle 119 Unit Tests bestanden
- [x] Integration Tests bestanden (existierende 75 + 44 neue)
- [ ] Manueller E2E-Test erfolgreich (erfordert API-Key)

### Phase 5: Cleanup & Dokumentation
- [x] Alte Dateien in `scripts/` Root geloescht (`pdf_to_json.py`)
- [x] Alte `tests/fixtures/output/` geloescht (generierte .docx/.html Artefakte)
- [x] `.gitignore` aktualisiert (`tests/fixtures/output/` hinzugefuegt)
- [ ] `docs/GENERATION_RULES.md` erstellt
- [ ] CHANGELOG aktualisiert
- [x] Checkliste aktualisiert
- [ ] Git Commit erstellt
- [ ] PR erstellt

---

## Rollback-Plan

Falls Probleme auftreten:

```bash
# Zum vorherigen Stand zurückkehren
git checkout main
git branch -D refactor/prompt-consolidation

# Oder spezifischen Commit rückgängig machen
git revert <commit-hash>
```

---

## Erfolgskriterien

| Metrik | Vorher | Nachher | Ziel |
|--------|--------|---------|------|
| Token pro Run | ~7000 | ~5400 | -20% |
| Regelquellen | 2 (JSON + Python) | 1 (Python) | Single Source |
| Direkte Ordner-Imports | ~18 Stellen | 0 | Nur via Alias |
| Unit Test Coverage | - | >80% | >80% |
| E2E Tests | Bestanden | Bestanden | Keine Regression |
