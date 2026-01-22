# Anforderung: Managed Talent Service (Phase 1)

## Ziel
Ermögliche das Management von Stellenprofilen und Kandidaten über eine Web-Oberfläche mit einfachen Workflows.

---

## 1. Datenschema

### Job Profile
- **Name**: Stellenbezeichnung (z.B. "Senior Python Developer")
- **Description**: Kurzbeschreibung der Position
- **Required Skills**: Liste von erforderlichen Fähigkeiten
- **Level**: junior, intermediate, senior, lead
- **Status**: active, inactive
- **Workflow State**: draft, published, closed

**Aktionen:**
- Erstellen (neues Profil → draft)
- Bearbeiten (Name, Description, Skills, Level)
- Löschen
- Veröffentlichen (draft → published)
- Schließen (published → closed)

### Candidate
- **First Name**: Vorname
- **Last Name**: Nachname
- **Email**: E-Mail-Adresse
- **Phone**: Telefonnummer (optional)
- **Summary**: Kurzbeschreibung (optional)
- **Status**: active, inactive
- **Workflow State**: new, profile_completed, archived

**Aktionen:**
- Erstellen
- Bearbeiten (Name, Email, Phone, Summary)
- Löschen
- Archivieren (inactive → archived)

---

## 2. Benutzeroberfläche

### Sidebar Navigation (Hauptseite app.py)
```
🎯 Managed Talent Service
├─ 📄 CV Generator      (aktuelle Sicht - bleibt gleich)
├─ 📋 Stellenprofile    (neue Seite: pages/01_Stellenprofile.py)
└─ 👥 Kandidaten        (neue Seite: pages/02_Kandidaten.py)
```

### Seite: Stellenprofile (pages/01_Stellenprofile.py)
**Tab 1: Übersicht**
- Liste aller Profile mit Filtern (Status, Workflow State)
- Jedes Profil zeigt: Name, Description (gekürzt), Skills, Status, Workflow State
- Pro Profil Buttons: Bearbeiten, Löschen, Veröffentlichen/Schließen

**Tab 2: Neues Profil / Bearbeiten**
- Formular mit Feldern: Name, Description, Skills (Textarea), Level
- Buttons: Speichern, Abbrechen
- Status/Workflow State nur lesbar

### Seite: Kandidaten (pages/02_Kandidaten.py)
**Tab 1: Übersicht**
- Liste aller Kandidaten mit Filtern (Status, Workflow State)
- Jeder Kandidat zeigt: Name, Email, Phone, Summary (gekürzt)
- Pro Kandidat Buttons: Bearbeiten, Löschen, Archivieren

**Tab 2: Neuer Kandidat / Bearbeiten**
- Formular mit Feldern: Vorname, Nachname, Email, Phone, Summary
- Buttons: Speichern, Abbrechen
- Status/Workflow State nur lesbar

---

## 3. Datenbank

**Tabellen:**
- `job_profiles`: Alle Stellenprofile
- `candidates`: Alle Kandidaten
- `schema_migrations`: Schema-Versionierung (bereits vorhanden)

**Verwaltung:**
- SQLite lokal (data/cv_generator.db)
- Nicht in Git (data/*.db in .gitignore)
- Migration system (nur Schema, keine Daten)

---

## 4. Implementierungs-Steps

### Step 1: Database Layer (✅ DONE)
- [x] Models (JobProfile, Candidate)
- [x] CRUD Operations (db.py)
- [x] Workflows (JobProfileWorkflow, CandidateWorkflow)
- [x] Data Protection (.gitignore, pre-commit hooks)

### Step 2: Streamlit Pages (TODO)
- [ ] Sidebar Navigation anpassen (app.py)
- [ ] Seite: pages/01_Stellenprofile.py
- [ ] Seite: pages/02_Kandidaten.py

### Step 3: Testing & Validation
- [ ] Manual testing der UI
- [ ] Datensätze erfolgreich speichern/laden/löschen
- [ ] Workflows korrekt funktionieren

---

## 5. Phase 2 (Später)

Diese Phase startet NACH erfolgreichem Phase 1:
- Integration Job Profile + Candidates mit CV Generator
- Matching-Logik
- Reporting/Dashboard

**NICHT in Phase 1 enthalten!**

---

## Notizen

- Keep it simple - keine fancy Features jetzt
- Fokus: Datenverwaltung über UI
- Validierungen: minimal (nur erforderliche Felder)
- Workflow Transitions: einfache Zustandsübergänge
