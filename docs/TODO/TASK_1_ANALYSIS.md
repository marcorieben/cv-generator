# Task 1: Analyse des aktuellen Naming-Patterns

**Status:** Analyse abgeschlossen  
**Datum:** 2026-01-19  

---

## 1. AKTUELLER STATE (IST-ZUSTAND)

### 1.1 Problematische Muster (SOLLEN GEÄNDERT WERDEN)

#### ❌ **Hardcoded "jobprofile" String**
- **Ort:** `scripts/naming_conventions.py`
- **Zeilen:** 21, 50, 68
- **Beispiel:**
  ```python
  return "jobprofile"  # Fallback statt variabel
  ```
- **Problem:** Fixe Fallback-Werte sind nicht dynamisch steuerbar

#### ❌ **"batch-comparison" Hardcoded**
- **Ort:** `scripts/naming_conventions.py` Line 157
- **Zeile:** `batch_output_dir = get_output_folder_path(base_output, job_profile_name, "batch-comparison", batch_timestamp)`
- **Dateiformat:** `<job_profile>_batch-comparison_<timestamp>`
- **Problem:** Der Modus-String ist nicht aus dem Kontext ableitbar

#### ❌ **"cv" als Modus-Identifier**
- **Ort:** `scripts/naming_conventions.py` Line 157
- **Problem:** Keine Differenzierung zwischen Basic-Modus und Professional Analysis

#### ❌ **Keine Candidate-Subfolder in Single-CV Mode**
- **Ort:** `scripts/batch_comparison.py` Line 188
- **Struktur:** Dateien werden direkt im Stellenprofil-Ordner abgelegt
- **Problem:** Nicht konsistent mit Batch-Struktur

---

## 2. AKTUELL VERWENDETE FUNKTIONEN

### 2.1 `extract_job_profile_name_from_file(job_file_path: str) -> str`
**Ort:** `naming_conventions.py:7-26`

**Input:**  
- Filename: "Senior_Sales_Manager.pdf"

**Output:**  
- "senior_sales_manager"
- Fallback: "jobprofile" ❌

**Logik:**
1. Dateinamen extrahieren
2. Extension entfernen
3. Sanitize: lowercase, replace special chars with underscore

---

### 2.2 `extract_job_profile_name(job_profile_data: Optional[Dict]) -> str`
**Ort:** `naming_conventions.py:30-50`

**Input:**
- JSON-Dict mit `Stelle.Position` oder `Stelle.Titel`

**Output:**  
- "senior_business_analyst" (aus Position)
- Fallback: "jobprofile" ❌

**Logik:**
1. Versuche `Stelle.Position` oder `Stelle.Titel` zu extrahieren
2. Sanitize
3. Fallback auf "jobprofile"

---

### 2.3 `extract_candidate_name_from_file(cv_file_path: str) -> str`
**Ort:** `naming_conventions.py:88-106`

**Input:**  
- Filename: "Max_Mustermann.pdf" oder "Max Mustermann-CV.pdf"

**Output:**
- "max_mustermann"
- Fallback: "candidate"

---

### 2.4 `extract_candidate_name(cv_data: Optional[Dict]) -> str`
**Ort:** `naming_conventions.py:109-130`

**Input:**
- JSON-Dict mit `Vorname` und `Nachname`

**Output:**
- "mustermann_max" (Nachname_Vorname)

---

### 2.5 `get_output_folder_path(...) -> str`
**Ort:** `naming_conventions.py:150-170`

**Parameter:**
- `base_output_dir`: "output/"
- `job_profile_name`: "senior_business_analyst"
- `mode`: "cv" oder "batch-comparison" ← **HARDCODED WERT!**
- `timestamp`: "20260119_114357"

**Output Beispiele (AKTUELL):**
```
senior_business_analyst_cv_20260119_114357/
senior_business_analyst_batch-comparison_20260119_114357/
```

**Problem:**
- Mode ist hardcoded ("cv", "batch-comparison")
- Keine Differenzierung zwischen Basic und Professional Analysis
- Keine Unterscheidung Single vs Batch in der Funktion selbst

---

### 2.6 `get_candidate_subfolder_path(...) -> str`
**Ort:** `naming_conventions.py:172-210`

**Parameter:**
- `batch_folder_path`: Pfad zum Batch-Ordner
- `candidate_name`: "fischer_arthur"
- `timestamp`: "20260119_114357"

**Output Format:**
```
{batch_folder}/{candidate_name}_{timestamp}
```

**Beispiel:**
```
senior_business_analyst_batch-comparison_20260119_114357/fischer_arthur_20260119_114357
```

---

### 2.7 `get_stellenprofil_json_filename(...) -> str`
**Ort:** `naming_conventions.py:212-220`

**Format:**
```
{job_profile_name}_stellenprofil_{timestamp}.json
```

**Beispiel:**
```
senior_business_analyst_stellenprofil_20260119_114357.json
```

**Problem:** Der String "stellenprofil" ist hardcoded!

---

## 3. VERWENDUNG IN BATCH-VERARBEITUNG

### 3.1 `batch_comparison.py:139-149`

**Aktueller Code:**
```python
# Format: jobprofileName_batch-comparison_timestamp
job_profile_name_from_file = extract_job_profile_name_from_file(job_file.name if hasattr(job_file, 'name') else "")
job_profile_name = extract_job_profile_name(stellenprofil_data)
if job_profile_name == "jobprofile" and job_profile_name_from_file != "jobprofile":
    job_profile_name = job_profile_name_from_file

batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_output = os.path.join(base_dir, "output")
batch_output_dir = get_output_folder_path(base_output, job_profile_name, "batch-comparison", batch_timestamp)
```

**Problem:**
- "batch-comparison" ist Magic String
- Kein Kontext über Mode (Basic vs Professional)

---

### 3.2 Ordner-Struktur aktuell (BATCH):
```
output/
└── senior_business_analyst_batch-comparison_20260119_114357/
    ├── senior_business_analyst_stellenprofil_20260119_114357.json
    ├── fischer_arthur_20260119_114357/
    │   ├── (CV/Match/Feedback Dateien generiert)
    │   └── ...
    └── mueller_hans_20260119_114357/
        └── ...
```

**Erkannt Struktur:** ✓ Die Candidate-Subfolder werden bereits korrekt erstellt!

---

## 4. VERWENDUNG IN SINGLE-CV VERARBEITUNG

### 4.1 `streamlit_pipeline.py` (Single CV)

**Problem:** Keine klare Naming-Konvention für Single-CV Modus erkannt.

Die Dokumentation sagt:
```
5.2.1 FALL: 1 CV (SINGLE ANALYSIS)
v_Stellenprofil_v_KandidatName_v_Timestamp/
```

Aber aktuell wird möglicherweise in den Batch-Ordner geschrieben?

---

## 5. DATEI-GENERIERUNG

### 5.1 In `generate_cv.py`

**Zu prüfen:** Wie werden Dateinamen generiert?
- Word-Datei: `cv_*.docx`
- JSON: `*_cv.json`
- Dashboard: `jobprofile_*_dashboard_*.html` ← **HARDCODED!**

---

### 5.2 In `generate_matchmaking.py`

**Zu prüfen:** Wie werden Match-Dateien benannt?
- Format: `jobprofile_*_match_*.json` ← **HARDCODED!**

---

### 5.3 In `generate_cv_feedback.py`

**Zu prüfen:** Wie werden Feedback-Dateien benannt?
- Format: `jobprofile_*_feedback_*.json` ← **HARDCODED!**

---

## 6. IDENTIFIZIERTE HARDCODED STRINGS

| String | Ort | Zeilen | Kontext |
|--------|-----|--------|---------|
| `"jobprofile"` | naming_conventions.py | 21, 50, 68 | Fallback-Werte |
| `"batch-comparison"` | batch_comparison.py | 139 | Mode-Identifier |
| `"jobprofile_"` | generate_cv.py | ? | Dateiname-Präfix |
| `"jobprofile_"` | generate_matchmaking.py | ? | Dateiname-Präfix |
| `"jobprofile_"` | generate_cv_feedback.py | ? | Dateiname-Präfix |
| `"stellenprofil"` | naming_conventions.py | 216 | Dateiname-Infix |
| `"_dashboard_"` | generate_cv.py | ? | Dateiname-Infix |
| `"_match_"` | generate_matchmaking.py | ? | Dateiname-Infix |
| `"_feedback_"` | generate_cv_feedback.py | ? | Dateiname-Infix |

---

## 7. ZUSAMMENFASSUNG: WAS MUSS GEÄNDERT WERDEN

### 7.1 **Zentrale Naming-Funktion erweitern**

**Neue Funktion:** `build_output_path(mode, candidate_name, stellenprofil, artifact_type, is_batch=False, timestamp=None)`

**Muss entfernen:**
- Magic Strings ("jobprofile", "batch-comparison", "stellenprofil")
- Fallbacks auf "jobprofile"

**Muss hinzufügen:**
- Mode-Kontext (basic, professional_analysis)
- Batch-Flag (true/false)
- Artefakt-Typ (cv, match, feedback, dashboard)

---

### 7.2 **Alle Datei-Generierung zentralisieren**

**Aktuell:** Jede Funktion baut ihren eigenen Dateinamen
- `generate_cv.py` → Namen mit hardcoded "jobprofile"
- `generate_matchmaking.py` → Namen mit hardcoded "jobprofile"
- `generate_cv_feedback.py` → Namen mit hardcoded "jobprofile"

**Ziel:**
```python
# Zentral in naming_conventions.py
naming = build_output_path(
    mode='professional_analysis',
    candidate_name='fischer_arthur',
    stellenprofil='senior_business_analyst',
    artifact_type='cv',
    is_batch=True,
    timestamp='20260119_114357'
)

# Rückgabe:
{
    'folder_name': 'senior_business_analyst_fischer_arthur_20260119_114357',
    'file_name': 'senior_business_analyst_fischer_arthur_cv_20260119_114357',
    'full_path': '...',
    'folder_path': '...'
}
```

---

### 7.3 **Pipeline-Integration**

| Funktion | Änderung |
|----------|----------|
| `batch_comparison.py` | Nutze `build_output_path` statt `get_output_folder_path` |
| `streamlit_pipeline.py` | Übergebe `is_batch`, `mode` an Naming-Funktion |
| `generate_cv.py` | Nutze `build_output_path` für Dateinamen |
| `generate_matchmaking.py` | Nutze `build_output_path` für Dateinamen |
| `generate_cv_feedback.py` | Nutze `build_output_path` für Dateinamen |

---

## 8. NÄCHSTE SCHRITTE (TASKS 2-3)

✅ **Task 1:** Analyse abgeschlossen  
⏳ **Task 2:** `naming_conventions.py` mit Modus-Logik erweitern  
⏳ **Task 3:** `build_output_path()` zentral implementieren  

---

## 9. REFERENZ: AKTUELLE ORDNERSTRUKTUR

```
output/
├── senior_business_analyst_batch-comparison_20260119_074950/
│   ├── senior_business_analyst_stellenprofil_20260119_074950.json
│   ├── fischer_arthur_20260119_074950/
│   │   ├── cv_fischer_arthur_20260119_074950.docx
│   │   ├── cv_fischer_arthur_20260119_074950.json
│   │   ├── jobprofile_fischer_arthur_match_20260119_074950.json
│   │   ├── jobprofile_fischer_arthur_feedback_20260119_074950.json
│   │   └── jobprofile_fischer_arthur_dashboard_20260119_074950.html
│   └── mueller_hans_20260119_074950/
│       └── ...
│
└── (andere Modi hier)
```

**Zu ändernde Dateien:**
- ❌ `jobprofile_fischer_arthur_*.json` → ✅ `senior_business_analyst_fischer_arthur_*.json`
- ❌ `jobprofile_fischer_arthur_dashboard_*.html` → ✅ `senior_business_analyst_fischer_arthur_dashboard_*.html`
- ❌ `senior_business_analyst_stellenprofil_*.json` → ✅ `senior_business_analyst_20260119_074950.json`
- ❌ `senior_business_analyst_batch-comparison_*` → ✅ `batch_comparison_senior_business_analyst_*`
