# DEVELOPER GUIDELINES – AGENTIC CODING STANDARDS
VERSION 1.1
==============================================

## Zweck
Dieses Dokument definiert verbindliche Standards für Entwicklung,
Projektstruktur, Tests, Cleanup, Dokumentation und Entscheidungsfindung
in diesem Repository.

Ziel ist:
- konsistente Qualität
- wartbare Struktur
- kontrolliertes agentic coding
- Vermeidung von technischem Wildwuchs
- langfristige Nachvollziehbarkeit von Entscheidungen

Diese Guidelines gelten für:
- alle neuen Features
- alle Bugfixes
- alle agentisch generierten Änderungen

--------------------------------------------------
## 1. GRUNDPRINZIPIEN
--------------------------------------------------

### 1.1 Requirement before Code
Kein Code ohne:
- klar formulierte Anforderung
- expliziten Scope (In / Out)
- definierte Akzeptanzkriterien

Unklare Punkte sind aktiv zu challengen.
Annahmen dürfen nicht stillschweigend implementiert werden.

### 1.2 Determinismus vor Kreativität
- explizite Logik > implizite Annahmen
- lesbarer Code > cleverer Code
- vorhersehbares Verhalten > „magische“ Lösungen

### 1.3 Incremental & Reversible
Jede Änderung muss:
- isolierbar
- testbar
- im Notfall rückbaubar sein

Refactorings dürfen nur erfolgen, wenn sie:
- Bestandteil der Anforderung sind oder
- zur Umsetzung zwingend notwendig sind

--------------------------------------------------
## 2. VERBINDLICHE PROJEKTSTRUKTUR
--------------------------------------------------

```
project_root/

core/                  stabile, wiederverwendbare Kernlogik
  database/            Datenbank-Layer
  llm/                 LLM Integration
  storage/             File Storage
  ui/                  UI Components & Utilities
  utils/               Shared Utilities

pages/                 Streamlit UI Pages (numbered for menu order)
  01_Stellenprofile.py
  02_Kandidaten.py
  03_Stellenprofil-Status.py
  04_CV_Generator.py
  ...

scripts/               Pipeline & Tooling
  _shared/             Shared utilities (PDF, dates, prompts)
  _1_extraction_jobprofile/   Pipeline Phase 1
  _2_extraction_cv/           Pipeline Phase 2
  _3_analysis_matchmaking/    Pipeline Phase 3
  _4_analysis_feedback/       Pipeline Phase 4
  _5_generation_offer/        Pipeline Phase 5
  _6_output_dashboard/        Pipeline Phase 6
  cleanup/             Cleanup automation tools
  pipeline.py          Pipeline orchestration
  streamlit_pipeline.py
  ...

templates/             Templates (HTML, Word, Images)

data/
  input/               Rohdaten / Uploads
  output/              generierte Artefakte
  migrations/          Database migrations
  schema.sql           Database schema

docs/                  Projekt-Dokumentation
  developer/           Development guidelines
  features/            Feature-spezifische Artefakte (KEIN Production Code!)
    FEATURE_INDEX.md   Index aller Features (Single Source of Truth)
    FXXX-feature_name/ Feature ID + Name
      README.md        Feature Overview & Status
      docs/            Requirements, Specs, Design Decisions
      tests/           Feature-spezifische Tests (vor Integration)
      prototypes/      Experimenteller Code
  ARCHITECTURE.md      System architecture
  SETUP.md             Setup instructions
  TODO.md              Global todos
  ...

tests/                 Dauerhafte Integrationstests (mirrors scripts/)
  _shared/             Shared test utilities
  1_extraction_jobprofile/
  2_extraction_cv/
  fixtures/            Test data
  hooks/               Pre-commit hooks
  ...

input/                 Input files (PDFs, JSONs)
output/                Output files (Word, HTML)

tmp/                   temporäre Dateien
archive/               deprecated Inhalte
```

--------------------------------------------------
## 3. ORDNERREGELN
--------------------------------------------------

### 3.1 core/
- stabile, wiederverwendbare Logik
- keine Feature-Abhängigkeiten
- darf von allen Features genutzt werden

### 3.2 scripts/ - Pipeline Phases & Tooling

**Pipeline-Phasen (nummeriert mit `_` Präfix):**
- `_N_phase_name/` Ordner für sequentielle Pipeline-Schritte
- Jeder Ordner enthält: `*_generator.py`, `*_prompt.py`, `*_schema.json`, `__init__.py`
- `__init__.py` exportiert Public API (Funktionen + SCHEMA_PATH)
- `_shared/` für gemeinsame Utilities (sortiert vor Nummern)

**Import-Regel (ALIAS-LAYER):**
```python
# ❌ NIEMALS direkt importieren
from scripts._2_extraction_cv.cv_extractor import extract_cv

# ✅ IMMER via Alias-Layer (scripts/__init__.py)
from scripts import extract_cv
```

**Warum nummerierte Ordner?**
- Repräsentiert klare Prozess-Reihenfolge
- Underscore-Präfix: Python-kompatibel + signalisiert "internes Package"
- Alias-Layer entkoppelt Consumer von interner Struktur

**Manuelle Skripte:**
- `cleanup/`, `pipeline.py`, `database_protection_check.py`
- Migrations- & Wartungsskripte
- Keine automatische Ausführung

### 3.3 pages/ (Root-Level Streamlit Pages)
- ausschliesslich UI-Logik
- keine Business-Logik
- nummeriert für Menu-Reihenfolge: `01_*.py`, `02_*.py`
- ruft Services aus `core/` oder `scripts/` auf

**core/ui/**
- Wiederverwendbare UI-Components
- Dialog-Utilities
- UI-Helper-Funktionen

### 3.4 templates/
- nur Templates
- keine Logik
- erwartete Variablen sind dokumentiert

### 3.5 data/
- enthält ausschliesslich Daten
- kein produktiver Code
- keine Imports aus data/ erlaubt

### 3.6 docs/ - Projekt-Dokumentation & Feature-Management

**Struktur:**
- Flat structure für globale Dokumentation
- `developer/` für Development Guidelines
- `features/` für Feature-spezifische Artefakte
- Root-level: `ARCHITECTURE.md`, `TODO.md`, `SETUP.md`, etc.

**docs/features/ - Feature-Entwicklung:**

**Namenskonvention:**
```
docs/features/
  FXXX-feature_name/          # Feature ID (F001, F002, ...) + sprechender Name
    README.md                 # Feature Overview & Status
    docs/
      requirements.md         # Anforderungen & Akzeptanzkriterien
      architecture.md         # Architektur-Entscheidungen
      implementation_plan.md  # Umsetzungsplan
    tests/
      test_prototype.py       # Temporäre Feature-Tests (vor Integration)
    prototypes/
      experiment_v1.py        # Experimenteller Code
```

**Lifecycle:**
1. Feature-Entwicklung startet → Ordner in `docs/features/FXXX-name/` anlegen
2. Code reift → Production Code wandert nach `core/`, `scripts/`, `pages/`
3. Tests reifen → Dauerhafte Tests wandern nach `tests/`
4. Feature abgeschlossen → Dokumentation bleibt in `docs/features/`, Code ist integriert
5. Optional: Nach Stabilisierung → Feature-Ordner nach `archive/features/` verschieben

**Verboten in docs/features/:**
- Imports aus `docs/features/` in Production Code
- Production Code, der nicht in `core/`, `scripts/`, `pages/` gehört

**FEATURE_INDEX.md (Pflicht):**
Zentrale Übersicht in `docs/FEATURE_INDEX.md` mit:
- Feature ID & Name
- Status (Planning, In Development, Integrated, Archived)
- Owner / Verantwortlicher
- Links zu `docs/features/FXXX-name/README.md`
- Kurzbeschreibung

Beispiel:
```markdown
# Feature Index

| ID | Feature | Status | Owner | Links |
|----|---------|--------|-------|-------|
| F001 | Multilanguage Support | Integrated | MR | [docs/features/F001-multilanguage/](features/F001-multilanguage/) |
| F002 | Prompt Consolidation | Integrated | MR | [docs/features/F002-prompt-consolidation/](features/F002-prompt-consolidation/) |
| F003 | Storage Abstraction | Planning | MR | [docs/features/F003-storage-abstraction/](features/F003-storage-abstraction/) |
```

**Architektur-Entscheidungen:**
- Wichtige Entscheidungen in `docs/features/FXXX-*/docs/architecture.md` oder root-level Docs
- Minimalinhalt: Kontext, Entscheidung, Alternativen, Konsequenzen

**Feature Index Management:**

Die Datei `docs/features/FEATURE_INDEX.md` ist der **Single Source of Truth** für alle Features.

**Pflicht-Updates:**
- Neues Feature → Zeile mit Status "Planning" hinzufügen
- Development Start → Status auf "In Development" ändern
- Integration abgeschlossen → Status auf "Integrated" ändern, Details ergänzen
- Archivierung → Status auf "Archived" ändern, Pfad zu archive/ eintragen

**Format:**
```markdown
| ID | Feature | Status | Owner | Pfad | Beschreibung |
|----|---------|--------|-------|------|--------------|
| FXXX | Name | Planning/In Development/Integrated/Archived | Initialen | Link | Kurzbeschreibung (max 100 Zeichen) |
```

**Wann aktualisieren:**
- Bei Feature-Anlage (Planning)
- Bei jedem Status-Wechsel
- Bei Feature-Abschluss (Integrated) mit vollständigen Details
- Bei Archivierung

**Verantwortlichkeit:**
- Feature-Owner ist für Updates verantwortlich
- Bei Feature-Abschluss: Teil der Definition of Done (siehe 5.3)

--------------------------------------------------
### 3.7 tests/ - Dauerhafte Integrationstests

**Zweck:**
- Langfristige, stabile Tests die im Pre-Commit Hook laufen
- Integration Tests für Production Code
- Spiegelt `scripts/`-Struktur

**Struktur:**
- `tests/_shared/` für gemeinsame Test-Utilities
- `tests/N_extraction_*/` für Pipeline-Phase-Tests
- `tests/fixtures/` für Test-Daten
- `tests/hooks/` für Pre-Commit-Hooks

**Abgrenzung zu docs/features/*/tests/:**
- `docs/features/FXXX-*/tests/` → temporäre, feature-spezifische Tests während Entwicklung
- `tests/` → stabile Tests, die dauerhaft laufen
- **Migration:** Wenn Feature integriert ist, relevante Tests von `docs/features/FXXX-*/tests/` nach `tests/` verschieben

### 3.8 tmp/
- temporäre Dateien
- Debug- & Agenten-Artefakte (.claude/)
- darf jederzeit gelöscht werden
- kein produktiver Code
- keine Imports erlaubt
- via .gitignore ausgeschlossen

### 3.9 archive/
- deprecated Features (aus `docs/features/` nach Stabilisierung)
- ersetzte Implementierungen
- alte Anforderungsstände

Jeder Archivordner enthält eine README.txt mit:
- Grund der Archivierung
- Ersatz / Nachfolge
- Datum

--------------------------------------------------
## 4. VERBOTENE MUSTER (HARD RULES)
--------------------------------------------------

**NIEMALS erlaubt:**
- `*_old.py`, `*_backup.py`, `*_final_v2.py` (Versionskontrolle nutzen!)
- produktiver Code in `tmp/` oder `archive/`
- Imports aus `data/`, `tmp/`, `archive/`, `docs/features/` in Production Code
- Silent Failures (Fehler ohne sichtbare Reaktion)
- direkte Imports aus `scripts/_N_*/` (Alias-Layer nutzen!)

**Nummerierte Ordner - ERLAUBT für:**
- Pipeline-Phasen in `scripts/` mit `_` Präfix: `_1_`, `_2_`, etc.
- UI-Pages in `pages/` mit Ziffern-Präfix: `01_`, `02_`, etc.
- GRUND: Repräsentiert klare Sequenz/Reihenfolge
- BEDINGUNG: Alias-Layer (scripts) oder Framework-Convention (Streamlit pages)

**Nummerierte Ordner - VERBOTEN für:**
- Alle anderen Kontexte (core/, docs/, tests/, etc.)
- Ad-hoc Versionierung (`v1/`, `v2/`)

--------------------------------------------------
## 5. ENTWICKLUNGSPROZESS (MINIMALSTANDARD)
--------------------------------------------------

### 5.1 Pflichtartefakte vor Coding
- Requirement-Spezifikation
- Lösungs-Skizze
- Impact-Analyse

### 5.2 Testing (nicht verhandelbar)
- Unit Tests für neue **Core-Logik** und **Pipeline-Phasen**
- Integration Tests bei Feature-Änderungen
- bestehende Tests bleiben grün

**Pragmatische Ausnahmen:**
- Prototypen in `tmp/` (vor Production-Integration)
- Einmalige Migrations-Skripte (manuell getestet)
- UI-Only-Changes (manuelle Smoke-Tests)

**Pre-Commit:**
- Tests müssen grün sein vor jedem Commit
- Automatisiert via `.github/` Hooks

### 5.3 Definition of Done
Ein Feature gilt nur dann als abgeschlossen, wenn:
- alle Tests grün sind
- keine temporären Dateien im produktiven Code-Pfad existieren
- `tmp/` und `.claude/` sind via `.gitignore` ausgeschlossen
- die Struktur guideline-konform ist
- die Dokumentation aktualisiert wurde (inkl. `docs/features/FEATURE_INDEX.md`)
- relevante Entscheidungen dokumentiert sind (in `docs/features/FXXX-*/docs/` oder root-level)
- Production Code aus `docs/features/FXXX-*/prototypes/` nach `core/`, `scripts/`, `pages/` migriert
- stabile Tests aus `docs/features/FXXX-*/tests/` nach `tests/` migriert

--------------------------------------------------
## 6. BRANCH-STRATEGIE & GIT-WORKFLOW
--------------------------------------------------

### 6.1 Branch-Struktur

```
main (production)
  └── development (integration branch)
        ├── feature/FXXX-feature-name   # Feature-Implementation
        ├── bugfix/issue-description    # Bugfixes
        └── hotfix/critical-issue       # Production Hotfixes
```

### 6.2 Branch-Typen & Verwendung

| Branch-Typ | Wann nutzen | Merge Target | Lebensdauer |
|------------|-------------|--------------|-------------|
| `main` | Production-Releases | - | ∞ (permanent) |
| `development` | Integration, Planning-Docs | `main` | ∞ (permanent) |
| `feature/FXXX-*` | Code-Implementation ab Phase 1 | `development` | Kurz (1-2 Wochen) |
| `bugfix/*` | Bug-Fixes | `development` | Sehr kurz (1-3 Tage) |
| `hotfix/*` | Kritische Production-Fixes | `main` + `development` | Sofort |

### 6.3 Feature-Branch-Lifecycle

**Phase 1: Planning (Branch: `development`)**
```bash
# In development committen
git checkout development
git add docs/features/FXXX-*/
git commit -m "docs: Add FXXX feature planning"
git push origin development
```

**Warum development?**
- Nur Dokumentation, kein Code-Risiko
- Team sieht Planning sofort
- Feedback-Möglichkeit vor Implementation

---

**Phase 2: Implementation (Branch: `feature/FXXX-name`)**
```bash
# Feature Branch erstellen
git checkout development
git pull origin development
git checkout -b feature/FXXX-feature-name

# Implementation
git add core/ scripts/ tests/
git commit -m "feat: Implement FXXX core logic"
git push origin feature/FXXX-feature-name
```

**Warum Feature Branch?**
- Code-Änderungen isoliert
- Development bleibt stabil
- Einfaches Rollback
- Code Review via Pull Request

---

**Phase 3: Integration (Merge → `development`)**
```bash
# Pull Request erstellen: feature/FXXX → development
# Nach Review & grünen Tests:
git checkout development
git merge feature/FXXX-feature-name
git push origin development

# Feature Branch löschen
git branch -d feature/FXXX-feature-name
git push origin --delete feature/FXXX-feature-name
```

### 6.4 Naming-Conventions

**Feature Branches:**
```
feature/F003-storage-abstraction
feature/F004-user-authentication
feature/F010-export-templates
```
- Format: `feature/FXXX-descriptive-name`
- Feature ID aus FEATURE_INDEX.md verwenden
- Lowercase, Bindestriche statt Spaces

**Bugfix Branches:**
```
bugfix/cv-generation-encoding-error
bugfix/dashboard-date-format
```

**Hotfix Branches:**
```
hotfix/database-migration-failure
hotfix/openai-api-timeout
```

### 6.5 Commit-Message-Konventionen

**Format:** `<type>: <subject>` (max 72 Zeichen)

**Types:**
- `feat:` Neue Features
- `fix:` Bugfixes
- `docs:` Nur Dokumentation
- `refactor:` Code-Refactoring (keine Funktionsänderung)
- `test:` Tests hinzufügen/ändern
- `chore:` Build, Dependencies, Tooling
- `style:` Formatierung (keine Code-Änderung)
- `perf:` Performance-Verbesserungen

**Beispiele:**
```
feat: Add StorageProvider interface with LocalTempStorage
fix: Correct date format validation in CV extractor
docs: Update F003 requirements with architecture decisions
refactor: Extract PDF parsing logic to shared utility
test: Add integration tests for pipeline with storage
chore: Update python-docx dependency to 1.1.0
```

**Multi-Line Commits:**
```
feat: Implement StorageProvider abstraction layer

- Add StorageProvider interface with 7 methods
- Implement LocalTempStorage using tempfile
- Add path traversal protection
- Include unit tests with 95% coverage

Closes #42
```

### 6.6 Wann Feature Branch vs. Development?

| Änderung | Branch | Begründung |
|----------|--------|------------|
| Feature-Doku erstellen | `development` | Nur Docs, kein Risiko |
| Requirements schreiben | `development` | Team-Sichtbarkeit wichtig |
| Architecture Decisions | `development` | Frühe Feedback-Möglichkeit |
| Prototype Code | `feature/*` | Code kann unstable sein |
| Core Implementation | `feature/*` | Isolierung & Review nötig |
| Tests schreiben | `feature/*` | Zusammen mit Code |
| Bugfix (<10 Lines) | `development` | Direkter Fix OK wenn Tests grün |
| Bugfix (>10 Lines) | `bugfix/*` | Review empfohlen |
| Production Hotfix | `hotfix/*` | Direkt auf `main` |

### 6.7 Anti-Patterns (Vermeide)

❌ **Lange lebende Feature Branches** (>2 Wochen)
- Merge-Konflikte wachsen exponentiell
- Divergenz von `development`
- **Lösung:** Kleinere Features, häufiger mergen

❌ **Direkt in `main` committen**
- Keine Review-Möglichkeit
- Kein Rollback ohne Revert
- **Lösung:** Immer über `development` gehen

❌ **Feature-Dokumentation im Branch verstecken**
- Team sieht Planning nicht
- Keine Feedback-Möglichkeit
- **Lösung:** Docs in `development`, Code in `feature/*`

❌ **Ungetestete Commits in `development`**
- Pre-Commit Hook verhindert das bereits
- **Lösung:** Tests grün vor Push

❌ **Feature-Branch ohne Pull Request mergen**
- Kein Code Review
- Keine Diskussion
- **Lösung:** Immer PR erstellen (auch wenn Self-Merge)

### 6.8 Pull Request Checkliste

Vor Merge `feature/FXXX-*` → `development`:
- [ ] Alle Tests grün (Pre-Commit Hook erfolgreich)
- [ ] Code entspricht Developer Guidelines
- [ ] Dokumentation aktualisiert (`docs/features/FXXX-*/`)
- [ ] FEATURE_INDEX.md Status aktualisiert
- [ ] Keine Merge-Konflikte mit `development`
- [ ] Code Review durchgeführt (oder Self-Review dokumentiert)
- [ ] Breaking Changes dokumentiert (falls vorhanden)

--------------------------------------------------
## 7. CLEANUP-REGELN
--------------------------------------------------

Cleanup ist Teil jedes Features:
- ungenutzte Dateien entfernen
- ersetzte Logik löschen oder archivieren
- Imports prüfen
- Projektstruktur validieren

**Automatisierte Cleanup-Tools:**
- `scripts/cleanup/` - Automatische File-Klassifikation & Cleanup
- `scripts/database_protection_check.py` - Pre-Commit Database-Protection
- Pre-Commit Hooks validieren Structure & Tests

--------------------------------------------------
## 8. ERROR-, LOGGING- & FEHLERPHILOSOPHIE
--------------------------------------------------

- Fehler sind explizit zu behandeln
- Silent Failures sind verboten
- Exceptions werden geworfen, wenn:
  - der Zustand nicht sinnvoll weiterverarbeitet werden kann
- Logs sind:
  - verständlich für Menschen
  - kontextreich
  - frei von sensiblen Daten

--------------------------------------------------
## 9. DEPENDENCY-REGELN
--------------------------------------------------

- neue Abhängigkeiten sind zu begründen
- keine unnötigen Libraries
- bestehende Dependencies sind bevorzugt zu nutzen
- globale Abhängigkeiten sind minimal zu halten

--------------------------------------------------
## 10. SECURITY & DATENHANDLING (MINIMALSTANDARD)
--------------------------------------------------

- keine Secrets im Code oder Repository
- keine produktiven oder personenbezogenen Daten im Repo
- Testdaten müssen anonymisiert oder synthetisch sein
- sensible Konfigurationen gehören in Environment-Variablen

--------------------------------------------------
## 11. AGENTIC CODING REGELN
--------------------------------------------------

- Agenten dürfen Code erzeugen
- Agenten dürfen keine Projektstruktur erfinden
- Agenten folgen strikt diesen Guidelines
- Commits erfolgen nur nach lokal erfolgreichem Testlauf
- Agenten haben keinen Interpretationsspielraum bei Hard Rules

--------------------------------------------------
## 12. CHECKLISTE BEI FEATURE-ABSCHLUSS
--------------------------------------------------

- Requirement erfüllt
- Tests implementiert und nach `tests/` migriert
- **Pre-Commit Integration geprüft:** Relevante Tests in Pre-Commit Hook eingebaut?
- Production Code nach `core/`, `scripts/`, `pages/` migriert
- Cleanup durchgeführt (`docs/features/FXXX-*` kann bleiben oder nach `archive/features/`)
- Struktur eingehalten
- **`docs/features/FEATURE_INDEX.md` aktualisiert:**
  - Status auf "Integrated" geändert
  - Beschreibung vollständig ausgefüllt
  - Pfad korrekt verlinkt
- Dokumentation in `docs/features/FXXX-*/README.md` aktualisiert (Status, Completion Date)
- Entscheidungen dokumentiert (`docs/features/FXXX-*/docs/architecture.md`)

--------------------------------------------------
## SCHLUSSWORT
--------------------------------------------------

Ordnung ist kein Selbstzweck.
Ordnung ist eine Voraussetzung für Geschwindigkeit,
Qualität und Skalierung – insbesondere beim agentic coding.

Diese Guidelines ersetzen Diskussionen,
nicht Verantwortung.