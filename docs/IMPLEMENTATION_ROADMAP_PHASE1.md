# Managed Talent Service - Implementation Roadmap

## PHASE 1: MVP - Database Erweiterung & Core Features (Diese Woche)

### Sprint 1a: Database Layer Enhancement
**Zeitaufwand:** ~3h
**Priorität:** CRITICAL

#### Tasks:
1. **Erweiterte Datenmodelle** (models.py)
   - JobProfile: Neue Felder hinzufügen
     - `budget: Optional[float] = None`
     - `location: str = ""`
     - `department: str = ""`
     - `timeline: Optional[str] = None`
     - `hiring_manager: str = ""`
   
   - Candidate: Neue Felder erweitern
     - `skills: List[str] = []` (Skill-Liste)
     - `experience_level: str = "intermediate"`
     - `years_experience: int = 0`
     - `location: str = ""`
   
   - JobProfileCandidate (aktuell): `match_score: float = 0.0` hinzufügen

2. **Notes Model** (models.py)
   ```python
   @dataclass
   class Note:
       id: int
       entity_type: str  # "job_profile" or "candidate"
       entity_id: int
       content: str
       created_by: str
       created_at: datetime
       updated_at: Optional[datetime] = None
   ```

3. **Activity/Audit Log Model** (models.py)
   ```python
   @dataclass
   class Activity:
       id: int
       entity_type: str  # "job_profile" or "candidate"
       entity_id: int
       action: str  # "created", "updated", "status_changed", "note_added"
       details: dict  # Was hat sich geändert?
       changed_by: str
       changed_at: datetime
   ```

4. **SQL Migration** (001_initial_schema.sql)
   - Neue Tabellen: `notes`, `activities`
   - Neue Spalten zu `job_profiles`, `candidates`, `job_profile_candidates`
   - Indizes für Performance

5. **CRUD Operationen** (db.py)
   - `add_note()`, `get_notes()`, `delete_note()`
   - `log_activity()`, `get_activity_log()`
   - `update_job_profile()` mit Activity-Logging
   - `update_candidate()` mit Activity-Logging

**Acceptance Criteria:**
- [ ] Alle neuen Models sind in models.py definiert
- [ ] SQL Migration läuft erfolgreich
- [ ] CRUD für Notes & Activities funktioniert
- [ ] Activity wird automatisch geloggt bei Änderungen
- [ ] Tests für neue Funktionen grün

---

### Sprint 1b: Matching Algorithm
**Zeitaufwand:** ~2h
**Priorität:** HIGH

#### Tasks:
1. **Matching Score Berechnung** (scripts/matching_algorithm.py - NEW)
   ```python
   def calculate_match_score(profile: JobProfile, candidate: Candidate) -> float:
       """
       Berechnet Match-Score basierend auf:
       - Skill-Overlap (60% Gewicht)
       - Experience Level (30% Gewicht)
       - Location Match (10% Gewicht)
       
       Returns: Float 0.0 - 100.0
       """
   
   def get_skill_overlap(profile_skills, candidate_skills) -> float:
       """Prozentsatz gemeinsamer Skills"""
       
   def get_matching_candidates(profile_id: int, db: Database) -> List[tuple]:
       """Alle Kandidaten für Profile sortiert nach Match Score"""
   ```

2. **Integration in DB** (db.py)
   - `get_candidates_for_profile(profile_id)` - Returns sorted by match
   - `get_profiles_for_candidate(candidate_id)` - Returns sorted by match

3. **Update Workflow** (workflows.py)
   - Beim Erstellen von Job Profile: Auto-Match mit Kandidaten
   - Beim Erstellen von Kandidaten: Auto-Match mit Profiles

**Acceptance Criteria:**
- [ ] Matching Score-Algorithmus ist implementiert
- [ ] Score wird bei Creation auto-calculated
- [ ] Score wird gespeichert in DB
- [ ] Tests für Matching-Logik grün

---

### Sprint 1c: Streamlit UI Enhancements
**Zeitaufwand:** ~4h
**Priorität:** HIGH

#### Tasks:
1. **Input Validation auf Stellenprofile.py** (pages/01_Stellenprofile.py)
   ```python
   def validate_job_profile_form(name, description, skills, budget, location):
       """Validiert alle Eingaben, returnt errors"""
       errors = []
       if len(name) < 3:
           errors.append("Name muss mindestens 3 Zeichen sein")
       # ... weitere Validationen
       return errors
   ```

   - Name: Min 3, Max 255 chars
   - Description: Min 10 chars
   - Skills: Min 1, Max 20
   - Budget: Nur wenn angegeben, muss > 0 sein
   - Location: Max 255 chars

2. **Input Validation auf Kandidaten.py** (pages/02_Kandidaten.py)
   - Email: Valid format & No duplicates
   - Phone: Valid format (optional)
   - Names: Min 2 chars each

3. **Error Handling Verbesserung**
   - Try-catch Blöcke um alle DB-Operationen
   - User-friendly Error Messages in Deutsch
   - Stack Traces nur im Console, nicht im UI

4. **Matching Score Display** (pages/01_Stellenprofile.py - new section)
   - Nach "Neues Profil" Tab einen neuen Tab: "Matching Kandidaten"
   - Zeigt:
     - Kandidaten-Name
     - Match Score (%)
     - Top 3 Matching Skills
     - Top 3 Missing Skills
     - Button "View Profile"

5. **Better Confirmations**
   - Ersetze simple `st.button` für Delete mit Dialog
   - Show what will be deleted

**Acceptance Criteria:**
- [ ] Alle Input-Felder werden validiert
- [ ] Fehler werden klar angezeigt
- [ ] Matching-Tab funktioniert in Stellenprofile
- [ ] UI ist responsive & gut zu lesen

---

### Sprint 1d: Testing & Bug Fixes
**Zeitaufwand:** ~2h
**Priorität:** MEDIUM

#### Tasks:
1. **Fix in pages/01_Stellenprofile.py**
   - Fehler bei `add_basic_info_table()` Methode (falls vorhanden)
   - Database Update Funktionen prüfen
   - Session State Management debuggen

2. **Fix in pages/02_Kandidaten.py**
   - Gleiche Fehler wie oben
   - Duplicate Email Check

3. **Test Updates** (tests/test_streamlit_pages.py)
   - Matching Score Berechnung testen
   - Input Validation testen
   - Neue Database Fields testen

4. **Integration Tests**
   - Kompletter Flow: Profile → Matching → Kandidaten
   - Workflow State Transitions

**Acceptance Criteria:**
- [ ] Alle Tests grün
- [ ] Keine unerwarteten Exceptions
- [ ] Performance ist akzeptabel (< 1s für Queries)

---

## PHASE 2: Detailseiten & File Handling (Nächste Woche)

### Sprint 2a: Detail Pages
- Job Profile Detail mit Tabs (Info, Kandidaten, Activity, Notes)
- Candidate Detail mit Tabs (Info, Skills, Applications, Activity, Notes)
- Matching Comparison View

### Sprint 2b: File Handling
- CV Upload für Kandidaten
- Document Storage
- File Preview
- Version History

### Sprint 2c: Workflow Improvements
- Interview Scheduling
- Application Status Workflow
- Feedback & Rating System

---

## PHASE 3: Search, Analytics & Polish

### Sprint 3a: Search & Filter
- Full-Text Search
- Advanced Filters
- Saved Searches

### Sprint 3b: Analytics
- Dashboard mit KPIs
- Pipeline Visualization
- Reports

### Sprint 3c: Performance & UX Polish
- Caching
- Loading States
- Better Error Messages

---

## IMMEDIATE ACTION ITEMS (Nächste 30 Min)

### 1. Update models.py
```
Neue Felder in JobProfile:
- budget: Optional[float] = None
- location: str = ""
- department: str = ""
- timeline: Optional[str] = None

Neue Felder in Candidate:
- skills: List[str] = []
- experience_level: str = "intermediate"
- location: str = ""

Neue Models:
- Note (dataclass)
- Activity (dataclass)
```

### 2. Erstelle matching_algorithm.py
- calculate_match_score() Funktion
- get_matching_candidates() Funktion

### 3. Update Database Schema
- data/migrations/002_add_notes_activities.sql
- data/migrations/003_extend_profiles_candidates.sql

### 4. Update Stellenprofile.py
- Validierung hinzufügen
- Matching Tab hinzufügen
- Error Handling verbessern

### 5. Commit & Test
- Alle neuen Features testen
- Pre-Commit Hook läuft erfolgreich

---

## DELIVERABLES PHASE 1

### Am Ende dieser Phase:
- ✅ Database mit erweiterten Models
- ✅ Matching Algorithm funktioniert
- ✅ Stellenprofile zeigt Matching Kandidaten
- ✅ Input Validation auf alle Forms
- ✅ Besseres Error Handling
- ✅ Alle Tests grün
- ✅ Dokumentation updated

### Code Quality:
- Keine Pylance/Linter Fehler
- > 70% Test Coverage
- Clean Git History

---

## SUCCESS METRICS

Nach Phase 1 sollte:
- [ ] Job Profile können erstellt, bearbeitet, gelöscht werden
- [ ] Kandidaten können verwaltung werden
- [ ] Automatisches Matching zeigt beste Kandidaten
- [ ] Alle Eingaben validiert
- [ ] System ist stabil & performant
- [ ] User kann produktiv arbeiten
