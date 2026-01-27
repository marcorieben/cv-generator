# Feature Index

**Purpose:** Zentrale Übersicht aller Features im CV Generator Projekt  
**Location:** `docs/features/FEATURE_INDEX.md`  
**Maintained by:** Development Team

---

## Status-Definitionen

| Status | Beschreibung | Nächster Schritt |
|--------|--------------|------------------|
| **Planning** | Initiale Konzeption, Requirements-Gathering | Architecture Review |
| **In Development** | Aktive Implementierung | Testing & Integration |
| **Integrated** | Code in Production, Dokumentation vollständig | Monitoring |
| **Archived** | Ersetzt oder deprecated, in archive/ verschoben | - |

---

## Feature-Übersicht

| ID | Feature | Status | Owner | Pfad | Beschreibung |
|----|---------|--------|-------|------|--------------|
| F001 | Multilanguage Support | Integrated | MR | [docs/features/F001-multilanguage/](features/F001-multilanguage/) | Database-backed translations for UI (German, English, French) |
| F002 | Prompt Consolidation | Integrated | MR | [docs/features/F002-prompt-consolidation/](features/F002-prompt-consolidation/) | Unified prompt architecture across all pipeline phases |
| F003 | Storage Abstraction | Planning | MR | [docs/features/F003-storage-abstraction/](features/F003-storage-abstraction/) | Deploy-ready I/O with StorageProvider pattern |

---

## Feature erstellen - Quick Guide

1. **Feature ID vergeben:** Nächste freie FXX Nummer (F004, F005, ...)
2. **Ordner anlegen:** `docs/features/FXXX-feature_name/`
3. **README.md erstellen:** Feature Overview mit Status
4. **In Index eintragen:** Diese Datei aktualisieren
5. **Development starten:** Requirements, Architecture, Implementation Plan

---

## Archivierte Features

Siehe: `archive/features/`

- Keine archivierten Features bisher
