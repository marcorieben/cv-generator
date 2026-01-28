# Naming Conventions - Output Files & Folders

**Purpose:** Zentrale Definition aller Namenskonventionen für Output-Dateien, Ordner und ZIP-Archive  
**Expected Lifetime:** Permanent (Core Documentation)  
**Category:** DOCUMENTATION  
**Created:** 2026-01-28  
**Last Updated:** 2026-01-28

---

## 📋 Übersicht

Alle Output-Dateien folgen einem **konsistenten, vorhersagbaren** Namensschema basierend auf 4 Kernvariablen:

| Variable | Quelle | Format | Beispiel |
|----------|--------|--------|----------|
| `jobprofile_slug` | JobProfile.id + JobProfile.name | `gdjob_{id}_{truncated_title}` | `gdjob_12881_senior_business_analyst_bizdevops_engi` |
| `candidate_name` | CV JSON: Vorname + Nachname | `{Vorname}_{Nachname}` | `Marco_Rieben` |
| `timestamp` | Pipeline: `datetime.now()` | `YYYYMMdd_HHMMSS` | `20260119_170806` |
| `filetype` | Document Type | `cv`, `offer`, `dashboard`, `match`, `feedback` | `cv` |

---

## 🎯 Namensschema-Patterns

### 1. ZIP-Datei / Hauptordner
**Format:**  
```
{jobprofile_slug}_{candidate_name}_{timestamp}.zip
```

**Beispiel:**  
```
gdjob_12881_senior_business_analyst_bizdevops_engi_Marco_Rieben_20260119_170806.zip
```

**Verwendung:**
- ZIP-Download mit allen Dokumenten
- Workspace-Ordner bei RunWorkspace (F003)

---

### 2. Primäre Output-Dateien
**Format:**  
```
{jobprofile_slug}_{candidate_name}_{filetype}_{timestamp}.{extension}
```

**Beispiele:**  
```
gdjob_12881_senior_business_analyst_bizdevops_engi_Marco_Rieben_cv_20260119_170806.docx
gdjob_12881_senior_business_analyst_bizdevops_engi_Marco_Rieben_offer_20260119_170806.docx
gdjob_12881_senior_business_analyst_bizdevops_engi_Marco_Rieben_dashboard_20260119_170806.html
```

**Gültige Filetypes:**
| Filetype | Beschreibung | Extension |
|----------|--------------|-----------|
| `cv` | Lebenslauf Word-Dokument | `.docx` |
| `offer` | Angebotsschreiben Word-Dokument | `.docx` |
| `dashboard` | Dashboard HTML-Report | `.html` |
| `match` | Matchmaking Analyse JSON | `.json` |
| `feedback` | CV Feedback JSON | `.json` |
| `jobprofile` | Stellenprofil JSON | `.json` |

**Verwendung:**
- Download-Buttons in Streamlit UI
- Primary outputs in RunWorkspace
- User-facing Dateien

---

### 3. Intermediate/Hilfsdateien (Artefakte)
**Format:**  
```
{jobprofile_slug}_{candidate_name}_{timestamp}/{filename}
```

**Beispiel-Ordnerstruktur:**  
```
gdjob_12881_senior_business_analyst_bizdevops_engi_Marco_Rieben_20260119_170806/
├── primary_outputs/
│   ├── gdjob_12881_..._Marco_Rieben_cv_20260119_170806.docx
│   ├── gdjob_12881_..._Marco_Rieben_offer_20260119_170806.docx
│   └── gdjob_12881_..._Marco_Rieben_dashboard_20260119_170806.html
└── artifacts/
    ├── cv_extracted.json
    ├── jobprofile_extracted.json
    ├── match_analysis.json
    └── feedback_analysis.json
```

**Verwendung:**
- Intermediate JSON files (vor Word-Generierung)
- Debug-Artefakte
- Logs und temporäre Dateien

---

## 🔧 Variable-Generierung (Code Reference)

### 1. `jobprofile_slug` - Job Profile Identifikation

**Quelle:**  
- Database: `core/database/models.py::JobProfile`  
- Felder: `id` (int), `name` (str)

**Generierung:**
```python
def generate_jobprofile_slug(job_profile_id: int, job_profile_name: str, max_length: int = 50) -> str:
    """
    Generiert Job Profile Slug für Dateinamen.
    
    Format: gdjob_{id}_{truncated_slugified_name}
    
    Args:
        job_profile_id: Database ID des Job Profiles
        job_profile_name: Titel des Job Profiles (z.B. "Senior Business Analyst - BizDevOps Engineer")
        max_length: Maximale Länge des Name-Anteils (default: 50)
    
    Returns:
        str: Job Profile Slug (z.B. "gdjob_12881_senior_business_analyst_bizdevops_engi")
    
    Examples:
        >>> generate_jobprofile_slug(12881, "Senior Business Analyst - BizDevOps Engineer")
        'gdjob_12881_senior_business_analyst_bizdevops_engi'
        
        >>> generate_jobprofile_slug(99, "C++ & Python Expert!!!")
        'gdjob_99_c_python_expert'
    """
    import re
    
    # Normalize name: remove special characters, lowercase
    name_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', job_profile_name.lower())
    name_slug = re.sub(r'\s+', '_', name_slug.strip())
    name_slug = re.sub(r'_+', '_', name_slug)
    
    # Truncate to max_length
    name_slug = name_slug[:max_length].strip('_')
    
    return f"gdjob_{job_profile_id}_{name_slug}"
```

**Existierende Variable in Pipeline:**  
❌ **NICHT VORHANDEN** - muss erstellt werden  
✅ **Verfügbare Daten:** `JobProfile.id`, `JobProfile.name` aus Database

**Empfehlung:** Funktion zu `core/utils/naming.py` hinzufügen

---

### 2. `candidate_name` - Kandidaten-Name

**Quelle:**  
- CV JSON: `Vorname` (str), `Nachname` (str)  
- Pipeline: `scripts/streamlit_pipeline.py::run()` - Variablen `vorname`, `nachname`

**Generierung:**
```python
def generate_candidate_name(vorname: str, nachname: str) -> str:
    """
    Generiert Kandidaten-Name für Dateinamen.
    
    Format: {Vorname}_{Nachname}
    
    Args:
        vorname: Vorname des Kandidaten
        nachname: Nachname des Kandidaten
    
    Returns:
        str: Kandidaten-Name mit Underscore (z.B. "Marco_Rieben")
    
    Examples:
        >>> generate_candidate_name("Marco", "Rieben")
        'Marco_Rieben'
        
        >>> generate_candidate_name("Max", "Müller")
        'Max_Muller'  # Special chars removed
    """
    import re
    
    # Remove special characters, keep only alphanumeric
    vorname_clean = re.sub(r'[^a-zA-Z0-9]', '', vorname)
    nachname_clean = re.sub(r'[^a-zA-Z0-9]', '', nachname)
    
    return f"{vorname_clean}_{nachname_clean}"
```

**Existierende Variable in Pipeline:**  
✅ **VORHANDEN:** `vorname`, `nachname` in `streamlit_pipeline.py::run()`  
📍 **Location:** Zeile 148, 151, 196, 208, 234

**Status:** Kann direkt verwendet werden (eventuell Sonderzeichen-Cleaning hinzufügen)

---

### 3. `timestamp` - Zeitstempel

**Quelle:**  
- Pipeline: `scripts/streamlit_pipeline.py::__init__()`  
- Variable: `self.timestamp`

**Generierung:**
```python
# In streamlit_pipeline.py (Zeile 34)
self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
```

**Format:** `YYYYMMdd_HHMMSS`  
**Beispiel:** `20260119_170806`

**Existierende Variable in Pipeline:**  
✅ **VORHANDEN:** `self.timestamp` in `StreamlitCVGenerator`  
📍 **Location:** `streamlit_pipeline.py::__init__()` Zeile 34

**Status:** Bereits korrekt formatiert, kann direkt verwendet werden

---

### 4. `filetype` - Dokumenttyp

**Definition:**  
Fest definierte Strings für jeden Dokumenttyp.

```python
# In core/utils/naming.py oder constants.py
class FileType:
    """Definierte Dokumenttypen für Output-Dateien."""
    CV = "cv"
    OFFER = "offer"
    DASHBOARD = "dashboard"
    MATCH = "match"
    FEEDBACK = "feedback"
    JOBPROFILE = "jobprofile"
```

**Existierende Variable in Pipeline:**  
❌ **NICHT VORHANDEN** - wird aktuell implizit durch Funktion bestimmt  
✅ **Verwendung:** Sollte als Parameter übergeben werden

---

## 📝 Best Practices

### ✅ DO's

1. **Immer alle 4 Variablen verwenden** für primäre Output-Dateien
2. **Lowercase für filetype** (`cv` nicht `CV`, `offer` nicht `Offer`)
3. **Underscore als Separator** (`_`) - keine Bindestriche in Dateinamen
4. **Timestamp immer am Ende** - für chronologische Sortierung
5. **JobProfile ID einbinden** - für eindeutige Zuordnung bei mehreren Stellen
6. **Slugify alle User-Inputs** - keine Sonderzeichen, keine Umlaute

### ❌ DON'Ts

1. **Keine gemischte Sprache** - nicht `Angebot` und `cv` mischen
2. **Keine Leerzeichen** in Dateinamen
3. **Keine Sonderzeichen** außer `_` und `-`
4. **Keine inkonsistenten Formate** - immer alle 4 Variablen
5. **Keine deutschen Umlaute** in Dateinamen (ä → a, ö → o, ü → u)
6. **Keine Uppercase/Lowercase Mischung** - entweder alles lowercase oder PascalCase

---

## 🔄 Migration Plan

### Aktuelle Inkonsistenzen

| Datei | Aktuelles Format | Neues Format |
|-------|------------------|--------------|
| **CV Word** | `cv_Marco_Rieben.docx` | `gdjob_12881_..._Marco_Rieben_cv_20260119_170806.docx` |
| **Offer Word** | `offer_Marco_Rieben.docx` | `gdjob_12881_..._Marco_Rieben_offer_20260119_170806.docx` |
| **Dashboard** | `Dashboard_Marco_Rieben_20260119_170806.html` | `gdjob_12881_..._Marco_Rieben_dashboard_20260119_170806.html` |
| **Match JSON** | `Match_Marco_Rieben_20260119_170806.json` | `gdjob_12881_..._Marco_Rieben_match_20260119_170806.json` |
| **Feedback JSON** | `CV_Feedback_Marco_Rieben_20260119_170806.json` | `gdjob_12881_..._Marco_Rieben_feedback_20260119_170806.json` |

### Betroffene Dateien (Code Changes)

1. ✅ `core/storage/run_id.py` - Run ID Format (bereits korrekt)
2. 🔄 `scripts/_2_extraction_cv/cv_word.py` - CV Filename (Zeile 1161)
3. 🔄 `scripts/_5_generation_offer/offer_word.py` - Offer Filename (Zeile 646)
4. 🔄 `scripts/_6_output_dashboard/dashboard_generator.py` - Dashboard Filename (Zeile 977)
5. 🔄 `scripts/streamlit_pipeline.py` - Alle JSON Intermediate Files (Zeilen 151, 160, 196, 208, 234)

### Migrations-Schritte

1. **Phase 1: Utility Functions** (1h)
   - Erstelle `core/utils/naming.py` mit allen Helper-Funktionen
   - `generate_jobprofile_slug()`
   - `generate_candidate_name()`
   - `generate_filename()` - Master-Funktion
   - Unit Tests in `tests/core/test_naming.py`

2. **Phase 2: Integration** (2-3h)
   - Update `streamlit_pipeline.py` - JobProfile Slug aus Database holen
   - Update alle Generator-Funktionen (cv_word.py, offer_word.py, dashboard_generator.py)
   - Übergabe von `jobprofile_slug` durch gesamte Pipeline

3. **Phase 3: Testing** (1h)
   - Integration Tests mit echten Dateinamen
   - Validation: Keine Sonderzeichen, korrekte Länge
   - Download-Buttons testen

4. **Phase 4: Documentation Update** (30min)
   - README.md aktualisieren
   - ARCHITECTURE.md aktualisieren
   - Beispiele in docs/ anpassen

**Geschätzte Zeit:** 4-5 Stunden

---

## 📚 Code Examples

### Vollständiges Beispiel: Filename Generation

```python
# core/utils/naming.py
from datetime import datetime
import re
from typing import Optional

class FileType:
    """Definierte Dokumenttypen."""
    CV = "cv"
    OFFER = "offer"
    DASHBOARD = "dashboard"
    MATCH = "match"
    FEEDBACK = "feedback"
    JOBPROFILE = "jobprofile"

def generate_jobprofile_slug(job_profile_id: int, job_profile_name: str, max_length: int = 50) -> str:
    """Generiert Job Profile Slug."""
    name_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', job_profile_name.lower())
    name_slug = re.sub(r'\s+', '_', name_slug.strip())
    name_slug = re.sub(r'_+', '_', name_slug)
    name_slug = name_slug[:max_length].strip('_')
    return f"gdjob_{job_profile_id}_{name_slug}"

def generate_candidate_name(vorname: str, nachname: str) -> str:
    """Generiert Kandidaten-Name."""
    vorname_clean = re.sub(r'[^a-zA-Z0-9]', '', vorname)
    nachname_clean = re.sub(r'[^a-zA-Z0-9]', '', nachname)
    return f"{vorname_clean}_{nachname_clean}"

def generate_filename(
    jobprofile_slug: str,
    candidate_name: str,
    filetype: str,
    timestamp: str,
    extension: str
) -> str:
    """
    Master-Funktion: Generiert konsistenten Dateinamen.
    
    Args:
        jobprofile_slug: Job Profile Slug (z.B. "gdjob_12881_senior_business_analyst...")
        candidate_name: Kandidaten-Name (z.B. "Marco_Rieben")
        filetype: Dokumenttyp (z.B. "cv", "offer", "dashboard")
        timestamp: Zeitstempel (z.B. "20260119_170806")
        extension: Dateiendung ohne Punkt (z.B. "docx", "html", "json")
    
    Returns:
        str: Vollständiger Dateiname
    
    Examples:
        >>> generate_filename("gdjob_12881_senior_ba", "Marco_Rieben", "cv", "20260119_170806", "docx")
        'gdjob_12881_senior_ba_Marco_Rieben_cv_20260119_170806.docx'
    """
    return f"{jobprofile_slug}_{candidate_name}_{filetype}_{timestamp}.{extension}"

def generate_folder_name(
    jobprofile_slug: str,
    candidate_name: str,
    timestamp: str
) -> str:
    """
    Generiert Ordnername für ZIP/Workspace.
    
    Args:
        jobprofile_slug: Job Profile Slug
        candidate_name: Kandidaten-Name
        timestamp: Zeitstempel
    
    Returns:
        str: Ordnername
    
    Examples:
        >>> generate_folder_name("gdjob_12881_senior_ba", "Marco_Rieben", "20260119_170806")
        'gdjob_12881_senior_ba_Marco_Rieben_20260119_170806'
    """
    return f"{jobprofile_slug}_{candidate_name}_{timestamp}"
```

### Integration in Pipeline

```python
# scripts/streamlit_pipeline.py
from core.utils.naming import (
    generate_jobprofile_slug,
    generate_candidate_name,
    generate_filename,
    generate_folder_name,
    FileType
)

class StreamlitCVGenerator:
    def run(self, cv_file, job_file=None, job_profile_id: int = None, ...):
        # ... CV extraction ...
        vorname = cv_data.get("Vorname", "Unknown")
        nachname = cv_data.get("Nachname", "")
        
        # Generate naming components
        jobprofile_slug = generate_jobprofile_slug(job_profile_id, stellenprofil_data.get("titel"))
        candidate_name = generate_candidate_name(vorname, nachname)
        
        # Generate filenames
        cv_filename = generate_filename(jobprofile_slug, candidate_name, FileType.CV, self.timestamp, "docx")
        offer_filename = generate_filename(jobprofile_slug, candidate_name, FileType.OFFER, self.timestamp, "docx")
        dashboard_filename = generate_filename(jobprofile_slug, candidate_name, FileType.DASHBOARD, self.timestamp, "html")
        
        # Generate workspace folder name
        workspace_folder = generate_folder_name(jobprofile_slug, candidate_name, self.timestamp)
        
        # ... rest of pipeline ...
```

---

## 🔍 Validation Rules

### Filename Validation

```python
# core/utils/naming.py
import re

def validate_filename(filename: str) -> tuple[bool, str]:
    """
    Validiert Dateinamen gegen Namenskonventionen.
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Check for invalid characters
    if re.search(r'[^a-zA-Z0-9_\-.]', filename):
        return False, "Filename contains invalid characters (only alphanumeric, _, -, . allowed)"
    
    # Check for spaces
    if ' ' in filename:
        return False, "Filename contains spaces"
    
    # Check for double underscores
    if '__' in filename:
        return False, "Filename contains double underscores"
    
    # Check minimum length
    if len(filename) < 10:
        return False, "Filename too short (min 10 characters)"
    
    # Check maximum length (Windows limit: 260 chars, safe limit: 200)
    if len(filename) > 200:
        return False, "Filename too long (max 200 characters)"
    
    return True, ""

def validate_naming_pattern(filename: str, expected_pattern: str = "primary") -> tuple[bool, str]:
    """
    Validiert ob Filename dem erwarteten Pattern entspricht.
    
    Args:
        filename: Zu validierender Dateiname
        expected_pattern: "primary" oder "folder"
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if expected_pattern == "primary":
        # Expected: {jobprofile}_{candidate}_{filetype}_{timestamp}.{ext}
        pattern = r'^gdjob_\d+_[a-z0-9_]+_[A-Za-z0-9_]+_(cv|offer|dashboard|match|feedback|jobprofile)_\d{8}_\d{6}\.\w+$'
        if not re.match(pattern, filename):
            return False, f"Filename doesn't match primary output pattern: {filename}"
    
    elif expected_pattern == "folder":
        # Expected: {jobprofile}_{candidate}_{timestamp}
        pattern = r'^gdjob_\d+_[a-z0-9_]+_[A-Za-z0-9_]+_\d{8}_\d{6}$'
        if not re.match(pattern, filename):
            return False, f"Foldername doesn't match pattern: {filename}"
    
    return True, ""
```

---

## 📖 Related Documentation

- **F003 Storage Abstraction:** `docs/features/F003-storage-abstraction/README.md`
- **Run ID Generation:** `core/storage/run_id.py`
- **Development Guidelines:** `docs/developer/development_guidelines.md`
- **Architecture:** `docs/ARCHITECTURE.md`

---

**Maintainer:** Development Team  
**Review Cycle:** Bei jedem neuen Dokumenttyp oder Format-Änderung  
**Status:** ✅ Aktiv (ab 2026-01-28)
