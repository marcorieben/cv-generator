# Managed Talent Service - NEXT STEPS (Konkrete Action Items)

## 🎯 PRIORITÄT: Heute umsetzen (2-3h)

### STEP 1: Database Models erweitern (45 min)
**Datei:** `core/database/models.py`

#### 1.1 JobProfile erweitern
```python
@dataclass
class JobProfile:
    id: int = 0
    name: str = ""
    description: str = ""
    required_skills: List[str] = field(default_factory=list)
    level: str = "intermediate"
    status: str = JobProfileStatus.ACTIVE.value
    workflow_state: str = JobProfileWorkflowState.DRAFT.value
    
    # NEW FIELDS
    budget: Optional[float] = None                    # Salary range
    budget_currency: str = "CHF"                      # Currency
    location: str = ""                                # Job location
    department: str = ""                              # Department
    timeline: Optional[str] = None                    # Start date / timeline
    hiring_manager: str = ""                          # Responsible person
    interview_rounds: int = 1                         # Number of interview rounds
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    updated_at: Optional[datetime] = None
```

#### 1.2 Candidate erweitern
```python
@dataclass
class Candidate:
    id: int = 0
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: Optional[str] = None
    summary: Optional[str] = None
    status: str = CandidateStatus.ACTIVE.value
    workflow_state: str = CandidateWorkflowState.NEW.value
    
    # NEW FIELDS
    skills: List[str] = field(default_factory=list)   # Skills list
    experience_level: str = "intermediate"              # junior/mid/senior
    years_experience: int = 0                           # Total years
    location: str = ""                                  # Current location
    salary_expectation: Optional[float] = None          # Expected salary
    current_company: Optional[str] = None               # Arbeitsort
    highest_degree: Optional[str] = None                # Education level
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    updated_at: Optional[datetime] = None
```

#### 1.3 JobProfileCandidate erweitern
```python
@dataclass
class JobProfileCandidate:
    profile_id: int
    candidate_id: int
    
    # NEW FIELDS
    match_score: float = 0.0                    # 0-100 percentage
    status: str = "new"                         # new/reviewed/shortlisted/rejected
    internal_notes: Optional[str] = None        # Recruiter notes
    rating: Optional[int] = None                # 1-5 star rating
    
    applied_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
```

#### 1.4 Neue Models hinzufügen
```python
@dataclass
class Note:
    id: int = 0
    entity_type: str = ""              # "job_profile" or "candidate"
    entity_id: int = 0                 # Profile ID or Candidate ID
    content: str = ""
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

@dataclass
class Activity:
    id: int = 0
    entity_type: str = ""              # "job_profile" or "candidate"
    entity_id: int = 0
    action: str = ""                   # "created", "updated", "status_changed"
    details: dict = field(default_factory=dict)  # JSON mit was sich geändert hat
    changed_by: str = "system"
    changed_at: datetime = field(default_factory=datetime.now)
```

---

### STEP 2: SQL Migration erstellen (30 min)
**Datei:** `data/migrations/002_add_extended_fields.sql`

```sql
-- Erweitere job_profiles table
ALTER TABLE job_profiles ADD COLUMN budget REAL DEFAULT NULL;
ALTER TABLE job_profiles ADD COLUMN budget_currency TEXT DEFAULT 'CHF';
ALTER TABLE job_profiles ADD COLUMN location TEXT DEFAULT '';
ALTER TABLE job_profiles ADD COLUMN department TEXT DEFAULT '';
ALTER TABLE job_profiles ADD COLUMN timeline TEXT DEFAULT NULL;
ALTER TABLE job_profiles ADD COLUMN hiring_manager TEXT DEFAULT '';
ALTER TABLE job_profiles ADD COLUMN interview_rounds INTEGER DEFAULT 1;

-- Erweitere candidates table
ALTER TABLE candidates ADD COLUMN skills JSON DEFAULT '[]';
ALTER TABLE candidates ADD COLUMN experience_level TEXT DEFAULT 'intermediate';
ALTER TABLE candidates ADD COLUMN years_experience INTEGER DEFAULT 0;
ALTER TABLE candidates ADD COLUMN location TEXT DEFAULT '';
ALTER TABLE candidates ADD COLUMN salary_expectation REAL DEFAULT NULL;
ALTER TABLE candidates ADD COLUMN current_company TEXT DEFAULT NULL;
ALTER TABLE candidates ADD COLUMN highest_degree TEXT DEFAULT NULL;

-- Erweitere job_profile_candidates
ALTER TABLE job_profile_candidates ADD COLUMN match_score REAL DEFAULT 0.0;
ALTER TABLE job_profile_candidates ADD COLUMN status TEXT DEFAULT 'new';
ALTER TABLE job_profile_candidates ADD COLUMN internal_notes TEXT DEFAULT NULL;
ALTER TABLE job_profile_candidates ADD COLUMN rating INTEGER DEFAULT NULL;
ALTER TABLE job_profile_candidates ADD COLUMN reviewed_at TIMESTAMP DEFAULT NULL;
ALTER TABLE job_profile_candidates ADD COLUMN reviewed_by TEXT DEFAULT NULL;

-- Neue Tabellen
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details JSON DEFAULT '{}',
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_notes_entity ON notes(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activities_entity ON activities(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_job_profile_candidates_score ON job_profile_candidates(match_score);
```

---

### STEP 3: Database Operationen erweitern (30 min)
**Datei:** `core/database/db.py`

#### 3.1 CRUD für Notes
```python
def add_note(self, entity_type: str, entity_id: int, content: str, created_by: str) -> Tuple[bool, int, str]:
    """Add a note"""
    try:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notes (entity_type, entity_id, content, created_by)
            VALUES (?, ?, ?, ?)
        """, (entity_type, entity_id, content, created_by))
        self.conn.commit()
        return True, cursor.lastrowid, "Note erstellt"
    except Exception as e:
        return False, 0, f"Fehler: {str(e)}"

def get_notes(self, entity_type: str, entity_id: int) -> List[Note]:
    """Get all notes for entity"""
    try:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM notes
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
        """, (entity_type, entity_id))
        return [Note(*row) for row in cursor.fetchall()]
    except:
        return []

def delete_note(self, note_id: int) -> Tuple[bool, str]:
    """Delete a note"""
    # Implementation...
```

#### 3.2 Logging für Activities
```python
def log_activity(self, entity_type: str, entity_id: int, action: str, 
                details: dict = None, changed_by: str = "system") -> bool:
    """Log activity/change"""
    try:
        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO activities (entity_type, entity_id, action, details, changed_by)
            VALUES (?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, json.dumps(details or {}), changed_by))
        self.conn.commit()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

def get_activities(self, entity_type: str, entity_id: int, limit: int = 50) -> List[Activity]:
    """Get activity log for entity"""
    # Implementation...
```

---

### STEP 4: Matching Algorithm erstellen (45 min)
**Datei:** `scripts/matching_algorithm.py` (NEU)

```python
"""
Matching algorithm for candidates and job profiles
Calculates compatibility scores based on skills, experience, etc.
"""

from typing import List, Tuple
from core.database.db import Database
from core.database.models import JobProfile, Candidate

def calculate_skill_overlap(profile_skills: List[str], candidate_skills: List[str]) -> float:
    """
    Calculate skill match percentage
    Returns: 0.0 - 100.0
    """
    if not profile_skills:
        return 100.0
    
    profile_set = set(s.lower().strip() for s in profile_skills)
    candidate_set = set(s.lower().strip() for s in candidate_skills)
    
    if not profile_set:
        return 100.0
    
    matching_skills = len(profile_set & candidate_set)
    total_required = len(profile_set)
    
    return (matching_skills / total_required) * 100

def calculate_experience_match(profile_level: str, candidate_level: str) -> float:
    """
    Calculate experience level match
    Returns: 0.0 - 100.0
    """
    level_hierarchy = {"junior": 1, "intermediate": 2, "senior": 3, "lead": 4}
    
    profile_score = level_hierarchy.get(profile_level.lower(), 2)
    candidate_score = level_hierarchy.get(candidate_level.lower(), 2)
    
    # Perfect match = 100, -1 level = 70%, -2 levels = 40%
    diff = abs(profile_score - candidate_score)
    
    if diff == 0:
        return 100.0
    elif diff == 1:
        return 70.0 if candidate_score >= profile_score else 80.0
    else:
        return 40.0 if candidate_score >= profile_score else 50.0

def calculate_location_match(profile_location: str, candidate_location: str) -> float:
    """
    Calculate location match
    Returns: 0.0 (no match) or 100.0 (match) or 50.0 (flexible)
    """
    if not profile_location or not candidate_location:
        return 50.0  # Unknown = flexible
    
    profile = profile_location.lower().strip()
    candidate = candidate_location.lower().strip()
    
    if profile == candidate:
        return 100.0
    elif "remote" in profile or "anywhere" in profile:
        return 100.0
    else:
        return 40.0

def calculate_match_score(profile: JobProfile, candidate: Candidate) -> float:
    """
    Calculate overall match score (0-100)
    
    Weighting:
    - Skills: 60%
    - Experience: 30%
    - Location: 10%
    """
    skill_score = calculate_skill_overlap(
        profile.required_skills,
        candidate.skills
    )
    
    experience_score = calculate_experience_match(
        profile.level,
        candidate.experience_level
    )
    
    location_score = calculate_location_match(
        profile.location,
        candidate.location
    )
    
    # Weighted average
    overall_score = (
        skill_score * 0.60 +
        experience_score * 0.30 +
        location_score * 0.10
    )
    
    return min(100.0, max(0.0, overall_score))

def get_matching_candidates(db: Database, profile_id: int, limit: int = 10) -> List[Tuple[Candidate, float]]:
    """
    Get best matching candidates for a job profile
    Returns: List of (Candidate, MatchScore) tuples
    """
    profile = db.get_job_profile(profile_id)
    if not profile:
        return []
    
    all_candidates = db.get_all_candidates()
    
    # Calculate scores
    matches = []
    for candidate in all_candidates:
        score = calculate_match_score(profile, candidate)
        matches.append((candidate, score))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N
    return matches[:limit]

def get_matching_profiles(db: Database, candidate_id: int, limit: int = 10) -> List[Tuple[JobProfile, float]]:
    """
    Get best matching profiles for a candidate
    Returns: List of (JobProfile, MatchScore) tuples
    """
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        return []
    
    all_profiles = db.get_all_job_profiles()
    
    # Calculate scores
    matches = []
    for profile in all_profiles:
        score = calculate_match_score(profile, candidate)
        matches.append((profile, score))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N
    return matches[:limit]
```

---

### STEP 5: Streamlit Validierung hinzufügen (30 min)
**Dateien:** `pages/01_Stellenprofile.py` und `pages/02_Kandidaten.py`

#### 5.1 Validation Helper
```python
def validate_job_profile_form(name, description, skills, budget=None, location=""):
    """Validate job profile input"""
    errors = []
    
    if not name or len(name.strip()) < 3:
        errors.append("Stellenbezeichnung: Mindestens 3 Zeichen erforderlich")
    
    if not description or len(description.strip()) < 10:
        errors.append("Beschreibung: Mindestens 10 Zeichen erforderlich")
    
    if not skills or len(skills) == 0:
        errors.append("Skills: Mindestens ein Skill erforderlich")
    
    if len(skills) > 20:
        errors.append("Skills: Max. 20 Skills erlaubt")
    
    if budget is not None and budget <= 0:
        errors.append("Budget: Muss positiv sein")
    
    if location and len(location) > 255:
        errors.append("Location: Max. 255 Zeichen")
    
    return errors

def validate_candidate_form(first_name, last_name, email):
    """Validate candidate input"""
    errors = []
    
    if not first_name or len(first_name.strip()) < 2:
        errors.append("Vorname: Mindestens 2 Zeichen erforderlich")
    
    if not last_name or len(last_name.strip()) < 2:
        errors.append("Nachname: Mindestens 2 Zeichen erforderlich")
    
    if not email or "@" not in email:
        errors.append("E-Mail: Gültige Email erforderlich")
    
    # Duplicate check
    db = get_database()
    existing = [c for c in db.get_all_candidates() if c.email.lower() == email.lower()]
    if existing:
        errors.append("E-Mail: Kandidat mit dieser Email existiert bereits")
    
    return errors
```

#### 5.2 In den Forms verwenden
```python
# In Stellenprofile.py save section:
if st.button("💾 Speichern", use_container_width=True, type="primary"):
    # Validate first
    errors = validate_job_profile_form(profile_name, description, skills, budget, location)
    
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Save if valid
        # ... existing save code ...
```

---

### STEP 6: Matching Tab hinzufügen (30 min)
**Datei:** `pages/01_Stellenprofile.py`

```python
# Nach der bestehenden Form, neuer Tab oder neue Section:

st.subheader("🎯 Passende Kandidaten")

if is_edit and profile_id:
    from scripts.matching_algorithm import get_matching_candidates
    
    db = get_database()
    matches = get_matching_candidates(db, profile_id, limit=10)
    
    if not matches:
        st.info("Keine Kandidaten gefunden")
    else:
        for candidate, score in matches:
            with st.container(border=True):
                col_cand, col_score, col_skills = st.columns([2, 1, 1])
                
                with col_cand:
                    st.markdown(f"**{candidate.first_name} {candidate.last_name}**")
                    st.caption(f"📧 {candidate.email}")
                    st.caption(f"📍 {candidate.location or 'Ort unbekannt'}")
                
                with col_score:
                    # Color based on score
                    if score >= 80:
                        color = "green"
                    elif score >= 60:
                        color = "orange"
                    else:
                        color = "red"
                    
                    st.metric("Match Score", f"{score:.0f}%", help="Basierend auf Skills, Experience, Location")
                
                with col_skills:
                    st.caption(f"🔧 Skills: {len(candidate.skills)} / {len(profile.required_skills)}")
```

---

## ✅ CHECKLIST FÜR HEUTE

- [ ] models.py erweitert (neue Felder in JobProfile, Candidate, JobProfileCandidate)
- [ ] Neue Models erstellt (Note, Activity)
- [ ] Migration 002_add_extended_fields.sql erstellt
- [ ] DB CRUD für Notes erweitert
- [ ] Activity Logging hinzugefügt
- [ ] matching_algorithm.py erstellt
- [ ] Validierungsfunktionen in Streamlit hinzugefügt
- [ ] Matching Tab in Stellenprofile funktioniert
- [ ] Alle Tests updated & grün
- [ ] Git Commit: "feat(talent-service): Add extended database schema and matching algorithm"

---

## 📊 NACH HEUTE (MORGEN)

**Wenn alles oben done ist:**
1. Detail Pages (Job Profile Detail View)
2. Activity Timeline anzeigen
3. Notes/Comments System
4. Improved Error Handling
5. File Upload (CVs)

---

## ⏱️ ZEITSCHÄTZUNG

```
STEP 1 (Models):        45 min ✓
STEP 2 (Migration):     30 min ✓
STEP 3 (DB Ops):        30 min ✓
STEP 4 (Matching):      45 min ✓
STEP 5 (Validation):    30 min ✓
STEP 6 (UI):            30 min ✓
─────────────────────────────
TOTAL:                  3h 30 min
```

**Plus:**
- Testing & Bug Fixes: 1h
- Git Commit & Cleanup: 15 min

**Grand Total: ~4.5h** ← Realistisch für heute

---

## 🚀 START POINT

**Begin hier:**
1. Öffne `core/database/models.py`
2. Scroll zu JobProfile Dataclass
3. Füge die NEW FIELDS ein (wie oben)
4. Mache STEP 1-6 in dieser Reihenfolge

Alles klar? Ready to go? 💪
