# Managed Talent Service - Feature Requirements & Roadmap

## 1. AKTUELLE SITUATION (Status Quo)

### Was ist bereits implementiert:
- ✅ Database Layer (SQLite mit Models, CRUD, Workflows)
- ✅ Streamlit Hauptapp mit CV Generator
- ✅ Sidebar Navigation (Managed Talent Service)
- ✅ Stellenprofile Seite (Basic CRUD)
- ✅ Kandidaten Seite (Basic CRUD)
- ✅ Pre-Commit Data Protection System
- ✅ Database Migrations System
- ✅ Tests für Database-Layer

### Was fehlt oder ist unvollständig:

#### A. DATABASE & DATENMODELLE
- ❌ Job Profile Status Management (nur Draft/Published/Closed, keine Details wie Budget, Timeline)
- ❌ Attachment/File Support (für CVs, Dokumente, etc.)
- ❌ Workflow History Tracking (Audit-Log, wer hat was geändert)
- ❌ Matching Score / Rating System (Kandidat ↔ Job Profile)
- ❌ Note/Comment System (intern bei Profiles/Kandidaten)
- ❌ Activity Timeline / Events

#### B. STREAMLIT UI/UX
- ❌ Dashboard / Overview Page (KPIs, Recent Activity)
- ❌ Detailseiten für Job Profiles (vollständige Ansicht + Kandidaten)
- ❌ Detailseiten für Kandidaten (vollständige Ansicht + Bewerbungen)
- ❌ Matching/Comparison View (Kandidat vs Job Profile)
- ❌ Advanced Search & Filtering
- ❌ Bulk Operations (mehrere Items gleichzeitig ändern)
- ❌ Export Funktionen (Excel, PDF, etc.)
- ❌ Drag-and-Drop für Status-Änderungen (Kanban-Board)

#### C. DATEI-HANDLING
- ❌ CV Upload & Storage
- ❌ Dokument Management
- ❌ File Versioning
- ❌ Attachments verlinken mit Kandidaten/Profilen

#### D. WORKFLOWS & PROZESSE
- ❌ Candidate Application Workflow (New → Reviewed → Shortlisted → Rejected)
- ❌ Interview Management (Termine, Feedback, Ergebnisse)
- ❌ Offer Management (Angebot erstellen, versenden, unterschreiben)
- ❌ State Machine mit gültigen Übergängen
- ❌ Workflow Permissions (wer kann was ändern)

#### E. SEARCH & MATCHING
- ❌ Skill-basiertes Matching (Skills-Vergleich)
- ❌ Full-Text Search
- ❌ Advanced Filtering (mehrere Kriterien kombinieren)
- ❌ Saved Searches / Favorites
- ❌ Matching Score Berechnung & Visualization

#### F. REPORTING & ANALYTICS
- ❌ Dashboard mit KPIs (offene Positionen, Top Kandidaten, etc.)
- ❌ Pipeline Reports (wieviele in welchem Stage)
- ❌ Time-to-Hire Metrics
- ❌ Export Reports
- ❌ Graphische Darstellungen (Charts, Graphs)

#### G. AUTHENTIFIZIERUNG & AUTORISIERUNG
- ❌ Role-based Access Control (Admin, Recruiter, Manager, etc.)
- ❌ Permission Management pro User
- ❌ Audit Logging (wer hat was wann gemacht)
- ❌ User Activity Tracking

#### H. VALIDIERUNG & ERROR HANDLING
- ❌ Input Validation auf Streamlit-Seiten
- ❌ Duplicate Detection (gleiche Kandidaten mehrfach?)
- ❌ Data Consistency Checks
- ❌ Error Messages & User Feedback Verbesserungen

#### I. INTEGRATION
- ❌ Email Notifications (neue Bewerbungen, Status Updates)
- ❌ Email Template System
- ❌ Integration mit OpenAI für CV-Parsing
- ❌ Integration mit Calendar/Scheduling Tools
- ❌ REST API für externe Systeme

#### J. TESTING
- ❌ Streamlit Page Tests
- ❌ Integration Tests (Database + Streamlit)
- ❌ E2E Tests für komplette Workflows
- ❌ Performance Tests

---

## 2. FEATURE BREAKDOWN BY PRIORITY

### PHASE 1: FOUNDATION (MVP) - Woche 1-2
**Ziel:** Funktionierende Kandidaten- und Stellenprofilverwaltung

#### 1.1 Database Enhancements
- [ ] Erweiterte Job Profile Fields (Budget, Timeline, Department, Location)
- [ ] Candidate Details erweitern (Skills, Experience, Availability)
- [ ] Notes/Comments Model hinzufügen
- [ ] Activity Log Model für Audit Trail

#### 1.2 Streamlit UI Verbesserungen
- [ ] Input Validation auf allen Forms
- [ ] Error Messages & Success Feedback
- [ ] Modal Dialogs für Delete Confirmations (aktuell nur einfach)
- [ ] Better Layout & Responsive Design
- [ ] Loading States & Spinners

#### 1.3 Matching Basics
- [ ] Simple Skill-Matching Algorithm
- [ ] Matching Score Display
- [ ] "Show matching candidates for profile" Feature

#### 1.4 Testing
- [ ] Streamlit Page Integration Tests
- [ ] Workflow Tests für alle CRUD Operations

---

### PHASE 2: WORKFLOWS & DETAILS - Woche 3
**Ziel:** State-Management und detaillierte Views

#### 2.1 Candidate Application Workflow
- [ ] Application States definieren
- [ ] Status-Transition Logic
- [ ] Interview Scheduling
- [ ] Feedback/Rating System

#### 2.2 Detailseiten
- [ ] Job Profile Detail View (mit Candidate List)
- [ ] Candidate Detail View (mit Application History)
- [ ] Activity Timeline für beide
- [ ] Related Items anzeigen

#### 2.3 File Handling
- [ ] CV Upload für Kandidaten
- [ ] Document Storage
- [ ] File Preview/Download
- [ ] Versioning

---

### PHASE 3: SEARCH & ANALYTICS - Woche 4
**Ziel:** Produktive Nutzung & Insights

#### 3.1 Search & Filter
- [ ] Full-Text Search
- [ ] Advanced Multi-Filters
- [ ] Saved Searches
- [ ] Quick Filters (Buttons für häufige Searches)

#### 3.2 Analytics & Reporting
- [ ] Dashboard mit KPIs
- [ ] Pipeline Visualization
- [ ] Export zu Excel/PDF
- [ ] Time-to-Hire Metrics

---

### PHASE 4: ADVANCED - Woche 5+
**Ziel:** Enterprise Features

#### 4.1 Autorisierung & Access Control
- [ ] Role-based Permissions
- [ ] User Management
- [ ] Audit Logging

#### 4.2 Integrations
- [ ] Email Notifications
- [ ] Calendar Integration
- [ ] AI-powered Candidate Screening (nutze OpenAI)
- [ ] REST API

#### 4.3 Performance & Skalierung
- [ ] Caching Strategy
- [ ] Database Optimization
- [ ] Async Operations für lange Tasks

---

## 3. DETAILED USER FLOWS

### USER FLOW 1: Job Profile erstellen und Kandidaten finden
```
1. Recruiter erstellt Job Profile:
   - Grunddaten eingeben (Name, Description, Skills)
   - Extended Info (Budget, Timeline, Location, Department)
   - Publish (Status wechselt zu Published)

2. System zeigt "Matching Candidates":
   - Basierend auf Required Skills
   - Mit Matching Score
   - Sortiert nach Match %

3. Recruiter kann Kandidaten anschauen:
   - CV/Dokumente anschauen
   - Notes hinzufügen
   - Status ändern (Interested, Not Interested, Shortlist)
```

### USER FLOW 2: Kandidat verwalten
```
1. Recruiter fügt Kandidaten manuell hinzu:
   - Name, Email, Phone
   - Optional: CV uploaden
   - Kurzbeschreibung

2. System indexiert CV:
   - Nutze OpenAI um Skills zu extrahieren
   - Auto-populate Skills, Experience
   - Vorschlag für Kandidaten-Profil

3. Recruiter kann anpassen:
   - Skills korrigieren/ergänzen
   - Experience Level setzen
   - Availability eingeben

4. Kandidat kann sich zu Positions bewerben:
   - Application erstellen
   - Status tracking
   - Interview scheduling
```

### USER FLOW 3: Matching & Evaluierung
```
1. Automatisches Matching:
   - Für jedes neue Job Profile
   - Für jeden neuen Kandidaten
   - Basierend auf Skill-Overlap

2. Matching Anzeige:
   - Match % pro Kandidat
   - Fehlende/Überschuss Skills highlighten
   - Visuelle Comparison

3. Interview & Feedback:
   - Interview planen
   - Feedback geben (Rating 1-5)
   - Notes hinzufügen
   - Accept/Reject Decision
```

---

## 4. DATA MODEL ADDITIONS

### Job Profile - Neue Fields
```python
- budget: Optional[float]          # Salary range
- budget_currency: str = "CHF"     # Currency
- location: str                    # Job location
- department: str                  # Which department
- timeline: str                    # When to start
- hiring_manager: str              # Who is responsible
- interview_rounds: int = 1        # Number of rounds
- notes: List[Note]               # Internal notes
- activities: List[Activity]      # Change log
```

### Candidate - Neue Fields
```python
- skills: List[str]               # Extracted from CV
- experience_level: str           # junior/mid/senior
- years_experience: int           # Total years
- availability: str               # When available
- location: str                   # Current location
- salary_expectation: float       # Optional
- cv_file: Optional[Attachment]   # Uploaded CV
- notes: List[Note]              # Internal notes
- activities: List[Activity]     # Change log
```

### New Models
```python
class Note:
    id: int
    content: str
    created_by: str
    created_at: datetime
    entity_type: str  # job_profile, candidate
    entity_id: int

class Activity:
    id: int
    action: str  # "created", "updated", "status_changed"
    details: dict
    created_by: str
    created_at: datetime
    entity_type: str
    entity_id: int

class JobProfileCandidate:
    profile_id: int
    candidate_id: int
    status: str  # new, reviewed, shortlisted, rejected, offered, hired
    match_score: float
    applied_at: datetime
    notes: str
```

---

## 5. VALIDATION RULES

### Job Profile Validation
- [ ] Name: Required, min 3 chars, max 255
- [ ] Description: Required, min 10 chars
- [ ] Required Skills: Min 1, max 20
- [ ] Level: Required, must be valid enum
- [ ] Budget (if provided): Must be > 0
- [ ] Timeline (if provided): Must be valid date
- [ ] Location (if provided): Max 255 chars

### Candidate Validation
- [ ] First Name: Required, min 2 chars
- [ ] Last Name: Required, min 2 chars
- [ ] Email: Required, must be valid email format
- [ ] Phone (optional): Must be valid phone format
- [ ] Skills: Max 50 items

### Application Validation
- [ ] Candidate must exist
- [ ] Job Profile must exist
- [ ] Cannot apply to same profile twice
- [ ] Can only apply to published profiles

---

## 6. UI COMPONENTS TO BUILD

### New Streamlit Components
- [ ] `JobProfileDetailPanel` - Detailansicht mit Tabs
- [ ] `CandidateDetailPanel` - Detailansicht mit Tabs
- [ ] `MatchingScore` - Visual representation (%)
- [ ] `SkillMatch` - Show matching/missing skills
- [ ] `ActivityTimeline` - Changes over time
- [ ] `NotesSection` - Comments/Notes
- [ ] `FileUploader` - CV und Dokumente
- [ ] `StatusBadge` - Colored status indicators
- [ ] `ConfirmDialog` - Bessere Delete Confirmations
- [ ] `Dashboard` - KPI Cards, Charts

---

## 7. NEXT IMMEDIATE STEPS

### MUST HAVE (für MVP):
1. [ ] Database Model für Notes & Activities
2. [ ] Extended Job Profile Fields (in DB)
3. [ ] Extended Candidate Fields (in DB)
4. [ ] Better Input Validation in Streamlit
5. [ ] Error Handling & User Feedback
6. [ ] Matching Algorithm (einfach: Skill-Overlap %)
7. [ ] "View Matches" Feature für Profiles

### SHOULD HAVE (für Beta):
8. [ ] Detail Pages mit Tabs
9. [ ] Activity Timeline
10. [ ] File Upload für CVs
11. [ ] Application Status Tracking
12. [ ] Better UI/UX Polish

### NICE TO HAVE (später):
13. [ ] Advanced Search
14. [ ] Dashboard
15. [ ] Export Features
16. [ ] Email Notifications

---

## 8. TECHNICAL DEBT & CONSIDERATIONS

- [ ] Add unique constraints (Email für Candidate)
- [ ] Add indexes (für Performance)
- [ ] Connection pooling (später, bei vielen Users)
- [ ] Caching für häufige Queries
- [ ] Error Handling im Workflow-Layer konsistent
- [ ] Logging System für Debugging
- [ ] Better Session Management in Streamlit

---

## 9. SUCCESS CRITERIA

- MVP ist bereit wenn:
  - [ ] Alle CRUD Operationen funktionieren stabil
  - [ ] Input Validation arbeitet
  - [ ] Matching Score angezeigt wird
  - [ ] Job Profile ↔ Candidate Zuordnung möglich
  - [ ] Alle Tests grün sind
  - [ ] Kein kritische Bugs
