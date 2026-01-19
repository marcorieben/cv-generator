# Feature: Konsistente Naming-Konvention für alle Artefakte

**Status:** Geplant (nicht gestartet)  
**Priorität:** Hoch  
**Datum:** 2026-01-19

---

## 1. ZIEL

Ziel dieser Anforderung ist die Einführung einer konsistenten, dynamischen und skalierbaren Naming-Konvention
für alle durch die Applikation erzeugten Ordner und Dateien.

Fixe, hart codierte Begriffe wie 'jobprofile' oder 'stellenprofil' dürfen nicht mehr direkt verwendet werden.
Alle Namen müssen ausschliesslich über Variablen generiert werden.

---

## 2. GRUNDPRINZIPIEN (VERBINDLICH)

- ❌ Keine fixen Strings in Datei- oder Ordnernamen
- ✅ Naming erfolgt ausschliesslich über Variablen
- ✅ Naming ist modus-abhängig
- ✅ Naming ist deterministisch und reproduzierbar
- ✅ Jeder Name enthält einen Zeitstempel

---

## 3. VERWENDETE VARIABLEN

| Variable | Beispiel | Beschreibung |
|----------|----------|-------------|
| `v_KandidatName` | fischer_arthur | Normalisierter Kandidatenname |
| `v_Stellenprofil` | senior_business_analyst | Normalisierte Designationdes Stellenprofils |
| `v_Timestamp` | 20260119_114357 | Zeitpunkt der Generierung (YYYYMMDD_HHMMSS) |
| `v_Mode` | basic \| professional_analysis | Betriebsmodus |
| `v_IsBatch` | true \| false | Flag für Batch-Verarbeitung |

**WICHTIG:** Begriffe wie 'jobprofile' oder 'stellenprofil' dürfen ausschliesslich als Wert von `v_Stellenprofil` auftreten.

---

## 4. GLOBALE NAMING-REGELN

```
✓ lowercase
✓ snake_case
✓ keine Leerzeichen
✓ keine Umlaute
✓ keine fixen Präfixe
```

---

## 5. ORDNER- & FILE-STRUKTUR NACH MODUS

### 5.1 MODUS: BASIC (NUR CV)

**Ziel:** Einzelne CV-Verarbeitung ohne Stellenprofil-Kontext.

**Ordnerstruktur:**
```
output/
└── v_KandidatName_v_Timestamp/
    ├── v_KandidatName_cv_v_Timestamp.docx
    ├── v_KandidatName_cv_v_Timestamp.json
    └── v_KandidatName_dashboard_v_Timestamp.html
```

---

### 5.2 MODUS: PROFESSIONELLE ANALYSE

#### 5.2.1 FALL: 1 CV (SINGLE ANALYSIS)

**Ordnerstruktur:**
```
output/
└── v_Stellenprofil_v_KandidatName_v_Timestamp/
    ├── v_Stellenprofil_v_KandidatName_cv_v_Timestamp.docx
    ├── v_Stellenprofil_v_KandidatName_match_v_Timestamp.json
    ├── v_Stellenprofil_v_KandidatName_feedback_v_Timestamp.json
    └── v_Stellenprofil_v_KandidatName_dashboard_v_Timestamp.html
```

**Dateibeispiele:**
```
senior_business_analyst_fischer_arthur_cv_20260119_114357.docx
senior_business_analyst_fischer_arthur_match_20260119_114357.json
senior_business_analyst_fischer_arthur_feedback_20260119_114357.json
senior_business_analyst_fischer_arthur_dashboard_20260119_114357.html
```

#### 5.2.2 FALL: MEHRERE CVs (BATCH)

**Ordnerstruktur:**
```
output/
└── batch_comparison_v_Stellenprofil_v_Timestamp/
    │
    ├── v_Stellenprofil_v_Timestamp.json
    │   (Stellenprofil-Daten für alle Kandidaten)
    │
    ├── v_Stellenprofil_v_KandidatName_1_v_Timestamp/
    │   ├── v_Stellenprofil_v_KandidatName_1_cv_v_Timestamp.docx
    │   ├── v_Stellenprofil_v_KandidatName_1_match_v_Timestamp.json
    │   ├── v_Stellenprofil_v_KandidatName_1_feedback_v_Timestamp.json
    │   └── v_Stellenprofil_v_KandidatName_1_dashboard_v_Timestamp.html
    │
    ├── v_Stellenprofil_v_KandidatName_2_v_Timestamp/
    │   ├── ...
    │
    └── v_Stellenprofil_v_KandidatName_N_v_Timestamp/
        └── ...
```

**Batch-Beispiel:**
```
batch_comparison_senior_business_analyst_20260119_114357/
├── senior_business_analyst_20260119_114357.json
├── senior_business_analyst_fischer_arthur_20260119_114357/
│   ├── senior_business_analyst_fischer_arthur_cv_20260119_114357.docx
│   ├── senior_business_analyst_fischer_arthur_match_20260119_114357.json
│   ├── senior_business_analyst_fischer_arthur_feedback_20260119_114357.json
│   └── senior_business_analyst_fischer_arthur_dashboard_20260119_114357.html
│
└── senior_business_analyst_mueller_hans_20260119_114357/
    ├── senior_business_analyst_mueller_hans_cv_20260119_114357.docx
    ├── senior_business_analyst_mueller_hans_match_20260119_114357.json
    ├── senior_business_analyst_mueller_hans_feedback_20260119_114357.json
    └── senior_business_analyst_mueller_hans_dashboard_20260119_114357.html
```

---

## 6. DATEI-NAMING (VERBINDLICH)

**Format:**
```
<v_Stellenprofil>_<v_KandidatName>_<artefakt_typ>_<v_Timestamp>.<ext>
```

**Artefakt-Typen:**
- `cv` → CV Word-Dokument
- `cv` → CV JSON-Struktur
- `match` → Matchmaking-Analyse JSON
- `feedback` → Feedback JSON
- `dashboard` → HTML-Dashboard

**Beispiele (mit Wert-Substitution):**
```
senior_business_analyst_fischer_arthur_cv_20260119_065205.docx
senior_business_analyst_fischer_arthur_match_20260119_065136.json
senior_business_analyst_fischer_arthur_feedback_20260119_065136.json
senior_business_analyst_fischer_arthur_dashboard_20260119_065241.html
```

---

## 7. VERBOTENE MUSTER (MÜSSEN ENTFERNT WERDEN)

### ❌ **Nicht erlaubt:**

```
jobprofile_fischer_arthur_dashboard_20260119_065241.html
jobprofile_fischer_arthur_match_20260119_065136.json
jobprofile_fischer_arthur_feedback_20260119_065136.json
jobprofile_stellenprofil_20260119_065136.json
jobprofile_fischer_arthur_cv_20260119_065136.json
jobprofile_batch-comparison_20260119_065136 (Ordner)
```

### **Begründung:**
- ❌ Verwendung fixer Strings ('jobprofile', 'stellenprofil')
- ❌ Nicht variabel steuerbar
- ❌ Nicht batch-fähig
- ❌ Semantisch uneindeutig
- ❌ Keine Beziehung zu aktuellem Stellenprofil

---

## 8. TECHNISCHE UMSETZUNGSANFORDERUNGEN

### 8.1 Zentrale Naming-Funktion

**Ort:** `scripts/naming_conventions.py`

**Funktion:** `build_output_path(mode, candidate_name, stellenprofil, artifact_type, is_batch=False, timestamp=None)`

**Parameter:**
- `mode` (str): 'basic' oder 'professional_analysis'
- `candidate_name` (str): Rohname → wird normalisiert
- `stellenprofil` (str): Jobprofil-Bezeichnung → wird normalisiert
- `artifact_type` (str): 'cv', 'match', 'feedback', 'dashboard'
- `is_batch` (bool): Batch-Modus aktiviert?
- `timestamp` (str, optional): Format YYYYMMDD_HHMMSS

**Rückgabe:** `dict` mit:
- `folder_name` (str): Name des Ordners
- `file_name` (str): Name der Datei (ohne Extension)
- `full_path` (str): Kompletter Pfad
- `folder_path` (str): Nur der Ordner-Pfad

### 8.2 Keine String-Konkatenation in Fachlogik

- ❌ `folder = f"jobprofile_{candidate}_{timestamp}"`
- ✅ `naming = build_output_path(...)`
- ✅ `folder = naming['folder_path']`

### 8.3 Modus- und Batch-Logik ausschliesslich in der Naming-Funktion

- Single CV → `professional_analysis` Mode + `is_batch=False`
- Batch CVs → `professional_analysis` Mode + `is_batch=True`
- Basic CV → `basic` Mode

### 8.4 Unit-Tests für alle Modi und Fälle

**Test-Szenarien:**
```python
# BASIC Mode
build_output_path('basic', 'fischer_arthur', '', 'cv')
→ fischer_arthur_cv_20260119_114357.docx

# SINGLE ANALYSIS
build_output_path('professional_analysis', 'fischer_arthur', 'senior_business_analyst', 'cv', is_batch=False)
→ senior_business_analyst_fischer_arthur_cv_20260119_114357.docx
  (im Ordner: senior_business_analyst_fischer_arthur_20260119_114357/)

# BATCH
build_output_path('professional_analysis', 'fischer_arthur', 'senior_business_analyst', 'cv', is_batch=True)
→ senior_business_analyst_fischer_arthur_cv_20260119_114357.docx
  (im Ordner: batch_comparison_senior_business_analyst_20260119_114357/
              senior_business_analyst_fischer_arthur_20260119_114357/)
```

---

## 9. AKZEPTANZKRITERIEN

- [ ] Kein Dateiname enthält fixe Begriffe wie 'jobprofile'
- [ ] Änderung von `v_Stellenprofil` wirkt sich korrekt auf alle Namen aus
- [ ] Batch-Vergleiche erzeugen saubere, getrennte Ordner
- [ ] Struktur ist deterministisch und reproduzierbar
- [ ] Naming ist Cloud- und Filesystem-tauglich
- [ ] Alle 77 Tests bestehen
- [ ] Manuelle Tests zeigen korrekte Ordner/Datei-Struktur

---

## 10. IMPLEMENTATION PLAN

### Phase 1: Analyse & Design
- [ ] **Task 1:** Aktuelles Naming-Pattern dokumentieren
- [ ] **Task 2:** naming_conventions.py mit Modus-Logik erweitern
- [ ] **Task 3:** `build_output_path()` Funktion zentral implementieren

### Phase 2: Implementierung (Core)
- [ ] **Task 4:** Batch-Ordnerstruktur in batch_comparison.py umstellen
- [ ] **Task 5:** Single CV Naming in streamlit_pipeline.py anpassen
- [ ] **Task 6:** generate_cv.py Datei-Naming aktualisieren
- [ ] **Task 7:** generate_matchmaking.py & generate_cv_feedback.py anpassen

### Phase 3: Migration
- [ ] **Task 8:** Alle hardcodierten 'jobprofile' Strings suchen/ersetzen

### Phase 4: Validierung & Tests
- [ ] **Task 9:** Unit-Tests für alle Modi schreiben
- [ ] **Task 10:** Integration-Tests validieren

### Phase 5: Dokumentation & Abschluss
- [ ] **Task 11:** NAMING_CONVENTION.md erstellen
- [ ] **Task 12:** Akzeptanztest: Manuelle Validierung aller Modi

---

## 11. WIRKUNG

Diese Anforderung verhindert Naming-Schulden, ermöglicht sauberes Batch-Processing
und bildet die Grundlage für Skalierung, Cloud-Storage und Automatisierung.

---

## 12. NOTIZEN

- Zeitstempel-Format: `YYYYMMDD_HHMMSS` (deterministisch)
- Normalisierung: Alle Namen werden durch `normalize_name()` in `naming_conventions.py` verarbeitet
- Batch-Folder: `batch_comparison_<stellenprofil>_<timestamp>`
- Candidate-Subfolder: `<stellenprofil>_<candidate>_<timestamp>`
