# Pre-Commit Hook Setup

Der Pre-Commit Hook ist jetzt aktiv und führt **automatisch alle Tests vor jedem Commit** aus.

## ✅ Was passiert bei `git commit`

1. **Database Protection Check** - verhindert Datenverlust
2. **File Header Validation** - prüft Purpose & Lifetime (Warnung)
3. **Translation Duplicates Check** - verhindert doppelte Keys
4. **Test Data Update** - aktualisiert Fixtures automatisch
5. **Requirements Update** - aktualisiert requirements.txt automatisch
6. **CHANGELOG Update** - aktualisiert CHANGELOG.md automatisch
7. **Documentation Check** - warnt bei fehlenden Docs (nicht-blockierend)
8. **Tests ausführen** - 192 Tests (161 Functional + 31 UI)
   - Unit Tests: JSON validation, data models
   - Integration Tests: Pipeline, RunWorkspace, F003 compliance
   - **UI Tests (NEU):** 
     - Syntax validation (4 tests) - verhindert IndentationError
     - AppTest UI interactions (27 tests) - verhindert Runtime-Crashes
     - Alle 5 Streamlit-Seiten getestet
     - Button-Interaktionen, Session State, Workflows
9. **Bei Erfolg** → Commit wird durchgeführt ✅
10. **Bei Fehler** → Commit wird abgebrochen ❌

## 📋 Beispiel

```bash
$ git commit -m "Add new feature"

🛡️ Database Data Protection Check...
✅ No database files in staged changes

🏷️ File Header Validation...
✅ All files have proper headers

🔍 Checking translations.json for duplicate keys...
✅ No duplicate keys found

📄 Updating test data artifacts...
✅ Test data updated

📄 Updating requirements.txt...
✅ Requirements updated

📄 Updating CHANGELOG.md...
✅ CHANGELOG.md updated

📚 Checking documentation updates...
✅ Documentation checks passed

🧪 Running tests...
====================== test session starts ======================
...
========== 192 passed in 8.50s ==========
  - 161 functional tests passed
  - 31 UI tests passed (4 syntax + 27 interactions)

============================================================
✅ All tests passed! Proceeding with commit.
============================================================

[feature/F003-storage-abstraction abc1234] Add new feature
 1 file changed, 10 insertions(+)
```

## ⚠️ Hook umgehen (Notfall)

**Nur in Ausnahmefällen!**

```bash
git commit --no-verify -m "Emergency fix"
```

## 🔧 Hook deaktivieren

```bash
# Umbenennen (deaktiviert)
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Reaktivieren
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

## 📝 Was der Hook macht

Der Hook führt in dieser Reihenfolge aus:

1. **Database Protection** - Verhindert versehentliches Committen von Datenbank-Dateien
2. **File Header Validation** - Prüft ob Purpose & Expected Lifetime vorhanden (Warnung, nicht blockierend)
3. **Translation Duplicates** - Prüft `translations.json` auf doppelte Keys
4. **Test Data Update** - Aktualisiert automatisch Test-Artefakte in `tests/fixtures/`
5. **Requirements Update** - Aktualisiert `requirements.txt` basierend auf Imports
6. **CHANGELOG Update** - Aktualisiert `scripts/CHANGELOG.md` automatisch
7. **Documentation Check** - Warnt wenn Code geändert wurde aber Docs nicht (nicht blockierend)
8. **Test Execution** - Führt alle 192 Tests aus:
   - **Unit Tests:** JSON validation, data models, utilities
   - **Integration Tests:** Pipeline orchestration, RunWorkspace, F003 compliance
   - **UI Tests (NEU):**
     - **Syntax Tests (4):** AST parsing aller Streamlit-Seiten
       - Verhindert: IndentationError, SyntaxError, falsche Einrückungen
       - Testet: app.py + alle pages/*.py
     - **AppTest UI Tests (27):** Simuliert User-Interaktionen ohne Browser
       - Page Loading (9): Alle 5 Seiten laden ohne Crash
       - Button Interactions (10): File upload, downloads, language toggle, reset, tabs, forms
       - Workflows (5): Multi-step processes, state management, error handling
       - Backend Integration (3): Pipeline, RunWorkspace, run_id generation

9. **Auto-Staging** - Fügt automatisch aktualisierte Dateien zum Commit hinzu:
   - requirements.txt
   - tests/fixtures/output (wenn geändert)
   - scripts/CHANGELOG.md

10. **Commit-Entscheidung:**
    - ✅ Alle kritischen Checks bestanden → Commit wird durchgeführt
    - ❌ Kritischer Check fehlgeschlagen → Commit wird abgebrochen
    - ⚠️ Nur Warnungen → Commit wird durchgeführt (mit Warnung in Console)

### Technische Details

- **Findet automatisch Python** - Verwendet `.venv/Scripts/python.exe` wenn verfügbar
- **UTF-8 Encoding** - Stellt sicher dass Windows Console UTF-8 verwendet
- **Zeigt Coverage-Report** - Gibt Test-Coverage aus nach pytest
- **Hilfreiche Fehlermeldungen** - Zeigt genau welcher Check fehlgeschlagen ist
- **Execution Time:** ~8-10 Sekunden für alle Checks + 192 Tests

## 🎯 Best Practice

1. **Vor Commit:** Schau dir die Test-Ausgabe an
2. **Bei Fehler:** Fixe die Tests, dann commit erneut
3. **Nie umgehen:** `--no-verify` nur im absoluten Notfall

---

**Status:** ✅ Aktiv  
**Location:** `.git/hooks/pre-commit`  
**Tests:** 192 Tests (161 Functional + 31 UI Tests)
  - Unit Tests: JSON validation, data models, utilities
  - Integration Tests: Pipeline, RunWorkspace, F003 compliance
  - UI Tests: Streamlit syntax validation + AppTest UI interactions (all pages)
**Hook Scripts:** `tests/hooks/`
