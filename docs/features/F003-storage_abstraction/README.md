# Feature: Storage Abstraction & Deploy-Ready I/O

**Feature ID:** F003  
**Status:** In Planning  
**Owner:** MR  
**Created:** 2026-01-27  
**Target:** Phase 1 - Foundation

---

## Übersicht

Entkopplung aller 5 Generator-Pipelines (CV, Offer, Dashboard, Matchmaking, Feedback) von lokalen Dateisystem-Pfaden. Einführung eines **RunWorkspace-Patterns** für Railway-Deployment mit klarem Migrationspfad zu Supabase Storage.

**Kernprinzip:** Generatoren arbeiten mit Bytes, nicht mit Pfaden. Die Storage-Schicht (RunWorkspace) ist austauschbar ohne Business-Logik-Änderungen.

---

## Ziele

1. **Pipeline-Entkopplung:** Business-Logik (alle 5 Generatoren) kennt keine physischen Pfade mehr
2. **Railway-Ready:** Funktioniert auf ephemeren Container-Filesystems (tempfile-basiert)
3. **Multi-User:** Isolierte Workspaces pro Pipeline-Run (keine shared folders)
4. **Structured Downloads:** ZIP mit `primary_outputs/` (User-Dokumente) und `artifacts/` (JSONs)
5. **Supabase-Ready:** RunWorkspace ist austauschbar gegen Supabase Storage ohne Generator-Änderungen

---

## Nicht-Ziele (Phase 1)

- ❌ **Phase 1:** Langzeit-Speicherung (kommt in Phase 2 mit Supabase)
- ❌ Gemeinsame Input-Ordner zwischen Users
- ❌ Background-Jobs oder Batch-Processing
- ❌ User-Rechteverwaltung auf Storage-Ebene (außer Run-Isolation)
- ❌ Versionierung von Dateien

## Zukünftige Erweiterungen (Post-Railway)

- 🔜 **Supabase Storage Integration:** RunWorkspace austauschen gegen Supabase-backed Implementierung
- 🔜 **Persistent Storage:** User kann Dokumente langfristig speichern (Datenbank-Referenz)
- 🔜 **Document History:** Versionierung früherer Generierungen in Supabase
- 🔜 **Shared Workspaces:** Team-Kollaboration mit geteilten Dokumenten

---

## Dokumente

- [**Feature Requirement**](docs/feature_requirement.md) - **Komplette Anforderung & Implementation Plan** ⭐

---

## Status

- [x] Initial Spec erstellt
- [x] Architecture Review (Simplified Approach gewählt)
- [x] Developer Guidelines Compliance Check
- [x] Railway Deployment Plan erstellt
- [ ] **Day 1-2:** Implement RunWorkspace + migrate all 5 generators (10h)
- [ ] **Day 3:** Testing & Railway Deployment (3h)
- [ ] **Day 4:** Cleanup & Documentation (2h)
- [ ] **Post-Railway:** Supabase Migration Planning
