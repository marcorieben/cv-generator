# Pre-Commit Hook Setup

Der Pre-Commit Hook ist jetzt aktiv und führt **automatisch alle Tests vor jedem Commit** aus.

## ✅ Was passiert bei `git commit`

1. **Tests werden ausgeführt** (alle 15 Tests)
2. **Bei Erfolg** → Commit wird durchgeführt ✅
3. **Bei Fehler** → Commit wird abgebrochen ❌

## 📋 Beispiel

```bash
$ git commit -m "Add new feature"

🧪 Running tests before commit...
============================================================
========== test session starts ==========
...
========== 15 passed in 1.04s ==========

============================================================
✅ All tests passed! Proceeding with commit.
============================================================

[feature/unified-pipeline abc1234] Add new feature
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

Der Hook:
- Findet automatisch das richtige Python (.venv)
- Führt `pytest -v` aus
- Zeigt Coverage-Report
- Blockiert Commit bei fehlgeschlagenen Tests
- Gibt hilfreiche Fehlermeldungen

## 🎯 Best Practice

1. **Vor Commit:** Schau dir die Test-Ausgabe an
2. **Bei Fehler:** Fixe die Tests, dann commit erneut
3. **Nie umgehen:** `--no-verify` nur im absoluten Notfall

---

**Status:** ✅ Aktiv  
**Location:** `.git/hooks/pre-commit`  
**Tests:** 15 Unit Tests (JSON Validation)
