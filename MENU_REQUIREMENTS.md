# Menu System - Anforderungen & Design

## 1. ANFORDERUNGEN (Was muss das Menü können?)

### 1.1 Navigation
- [ ] Benutzer kann zwischen 4 Pages navigieren:
  - Home (app.py)
  - Stellenprofile (pages/01_Stellenprofile.py)
  - Kandidaten (pages/02_Kandidaten.py)
  - CV Generator (pages/04_CV_Generator.py)

### 1.2 Sprache
- [ ] Benutzer kann zwischen 3 Sprachen wechseln: DE, EN, FR
- [ ] Sprache wird in Session State gespeichert
- [ ] Beim Wechsel wird Seite neu gerendert

### 1.3 Farben & Styling
- [ ] Primary Color: Orange (#FF7900) - für aktive/wichtige Elemente
- [ ] Secondary Color: Grau (#444444) - für inaktive Elemente
- [ ] Design Settings erlauben Farbänderung

### 1.4 Komponenten
- [ ] Language Selection: 3 Buttons (DE, EN, FR) in einer Row
- [ ] Navigation: 4 Buttons (Home, Stellenprofile, Kandidaten, CV Generator)
- [ ] Settings Expander: Model Settings, Design Settings, Personal Settings
- [ ] History Expander
- [ ] App Info Expander
- [ ] User Info & Logout

### 1.5 Verhalten
- [ ] Sidebar ist auf **allen Seiten** sichtbar
- [ ] Sidebar wird aus YAML konfiguriert
- [ ] Nur 2 Item-Types: `button` und `expander`
- [ ] Max 2 Levels (keine tiefen Verschachtelungen)

---

## 2. AKTUELLE PROBLEME

### Problem 1: Navigation Button Coloring
- **Issue**: Versuche, aktive/inaktive Buttons durch `type="primary"/"secondary"` zu färben funktioniert nicht
- **Root Cause**: Streamlit rendert den type Parameter nicht konsistent bei Wiederrenderings
- **Impact**: Alle Buttons werden manchmal orange, manchmal grau - unkonsistent

### Problem 2: State Management
- **Issue**: `st.session_state.current_page` wird nicht zuverlässig zwischen Seiten weitergegeben
- **Root Cause**: Wenn Page wechselt, wird Sidebar komplett neu gerendert, bevor current_page aktualisiert wird
- **Impact**: Race Condition zwischen State-Update und Rendering

### Problem 3: Zu viele Render-Aufrufe
- **Issue**: Sidebar wird mehrfach pro Seite gerendert
- **Root Cause**: Jeder Button-Klick triggert re-run, jeder st.rerun() triggert neu Render
- **Impact**: Performance-Problem und visuelle Flackern

---

## 3. LÖSUNGSANSÄTZE

### Option A: Keine aktive Farb-Unterscheidung
- Navigation Buttons sind alle sekundär (grau)
- Nur Language Buttons zeigen aktiv (orange) vs inaktiv (grau)
- ✅ Einfach
- ✅ Zuverlässig
- ❌ Weniger visuelles Feedback

### Option B: Icons statt Farben für aktiven Button
- Aktiver Button hat Icon/Symbol (z.B. ✓)
- Farbe bleibt konsistent
- ✅ Eindeutig erkennbar
- ✅ Keine State-Komplexität

### Option C: Custom HTML/CSS Components (GEWÄHLT) ✅
- HTML/CSS Buttons statt Streamlit buttons
- Volle Kontrolle über Styling
- Active-State durch CSS-Klassen, nicht Parameter
- ✅ Zuverlässiges Active/Inactive Coloring
- ✅ Beliebig erweiterbar
- ✅ Konsistent über alle Renders

---

## 4. EMPFOHLENES DESIGN

**Option C: Custom HTML/CSS Components für volle Styling-Kontrolle**

```
LAYOUT:
┌─────────────────────────────┐
│ [DE] [EN] [FR]              │ ← Language Buttons (HTML/CSS)
├─────────────────────────────┤
│ [🏠 Home]                   │ ← Navigation Buttons (HTML/CSS)
│ [📋 Stellenprofile]         │   Active = Orange, Inactive = Grau
│ [👥 Kandidaten]             │
│ [📄 CV Generator]           │
├─────────────────────────────┤
│ ⚙️ Settings                  │ ← Streamlit Expanders
│   ├─ Model Settings (Form)  │   (Komponenten in Expander)
│   ├─ Design Settings (Form) │
│   └─ Personal Settings      │
│ 📜 History                  │
│ ℹ️ App Info                 │
├─────────────────────────────┤
│ Welcome, User!              │ ← User Info & Logout
│ [Logout]                    │
└─────────────────────────────┘
```

**DEFAULTS:**
- Language: `DE` (gespeichert in `st.session_state.language`)
- Current Page: `app.py` (Home - gespeichert in `st.session_state.current_page`)

**CSS-Styling:**
```css
.nav-button {
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  display: block;
  width: 100%;
  text-align: left;
  transition: background-color 0.2s;
}

.nav-button.active {
  background-color: #FF7900;  /* Primary: Orange */
  color: white;
}

.nav-button.inactive {
  background-color: #444444;  /* Secondary: Grau */
  color: white;
}

.nav-button:hover {
  opacity: 0.9;
}

.lang-button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  flex: 1;
  transition: background-color 0.2s;
}

.lang-button.active {
  background-color: #FF7900;  /* Primary: Orange */
  color: white;
}

.lang-button.inactive {
  background-color: #444444;  /* Secondary: Grau */
  color: white;
}
```

**HTML Button Template:**
```html
<button class="nav-button {active|inactive}" 
        onclick="navigateTo('{page}')"
        title="{label}">
  {icon} {label}
</button>
```

---

## 5. TECHNISCHE ARCHITEKTUR

**Custom HTML/CSS Buttons für Navigation & Language**

```
Renderer Logik:
render_sidebar()
├── Language Selection (HTML/CSS, 3 custom buttons)
│   └── Check st.session_state.language for active state
├── Loop through YAML items:
│   ├── if type == "button" → HTML/CSS custom button
│   │   └── Check st.session_state.current_page for active state
│   ├── if type == "expander" → st.expander()
│   │   └── Render children (components)
│   ├── if type == "divider" → st.divider()
│   └── if type == "component" → _render_component()
```

**Daten-Flow:**
1. Page lädt (z.B. pages/01_Stellenprofile.py)
2. Setzt `st.session_state.current_page = "pages/01_Stellenprofile.py"`
3. Setzt `st.session_state.language` (default: "de")
4. Ruft `render_sidebar_in_page()` auf
5. Sidebar rendert HTML/CSS Buttons
   - Navigation: Vergleicht `current_page` mit Button `page`
   - Language: Vergleicht `language` mit Button `lang_code`
6. Active Buttons werden orange, Inactive grau

---

## 6. IMPLEMENTIERUNGS-PLAN

### Phase 0: Cleanup (ALTE ALTLASTEN ENTFERNEN) ✅ DONE
- [x] `st.session_state.current_page` aus allen Pages entfernt (außer neu: app.py)
- [x] `current_page` in Pages 01-05 korrekt positioniert (nach imports)
- [x] App.py mit neuen Defaults aktualisiert
- [x] Neue sidebar_renderer.py geschrieben (sidebar_renderer_new.py)
- [x] Syntax-Check erfolgreich

**Status: Phase 0 abgeschlossen ✅**

### Phase 1: File Swap - Alte durch Neue ersetzen ⏳ NÄCHST
- [ ] `sidebar_renderer.py` → `sidebar_renderer_old.py` (Backup)
- [ ] `sidebar_renderer_new.py` → `sidebar_renderer.py` (Neue Version aktiv)
- [ ] Test: App startet ohne Fehler
- [ ] Test: Sidebar rendert

### Phase 2: YAML für Navigation Buttons
- [ ] Neue Struktur in `sidebar_config.yaml` hinzufügen
- [ ] `navigation_buttons` Section mit 4 Buttons
- [ ] Test: YAML loads

### Phase 3: Language Selection Testing
- [ ] Language Buttons funktionieren (DE/EN/FR)
- [ ] Active Language zeigt Orange
- [ ] Inactive Languages zeigen Grau
- [ ] Sprachwechsel funktioniert

### Phase 4: Navigation Buttons Testing
- [ ] Navigation Buttons funktionieren
- [ ] Active Button zeigt Orange
- [ ] Inactive Buttons zeigen Grau
- [ ] Navigation funktioniert (st.switch_page)

### Phase 5: Expander & Components
- [ ] Settings Expander funktioniert
- [ ] Model Settings Komponente
- [ ] Design Settings Komponente
- [ ] History Expander
- [ ] App Info Expander

### Phase 6: Integration & Final Test
- [ ] Alle Pages laden Sidebar korrekt
- [ ] Keine Fehler in der Console
- [ ] Kein Flackern
- [ ] Farben korrekt
- [ ] Language Switching funktioniert

---

## 7. AKZEPTANZKRITERIEN

✅ **Navigation:**
- Navigation zwischen 4 Pages funktioniert zuverlässig
- Active Button wird Orange (#FF7900)
- Inactive Buttons werden Grau (#444444)
- Kein Flackern beim Navigation
- st.switch_page() wird verwendet

✅ **Language:**
- Language-Wechsel funktioniert (DE/EN/FR)
- Active Language Button wird Orange
- Inactive Language Buttons werden Grau
- Sprache wechselt sofort
- st.rerun() bei Language Change

✅ **Quality:**
- Sidebar ist auf allen Pages sichtbar
- Keine visuellen Fehler
- Code ist wartbar (~200 Zeilen sidebar_renderer.py)
- Keine Debug-Ausgaben
- Neue Features: Expander mit Components

## DURCHGEFÜHRTE ARBEITEN (Phase 0)

✅ **Cleanup erfolgreich abgeschlossen:**

1. **Pages aktualisiert:**
   - Entfernt: Alte `current_page` Setting oben
   - Hinzugefügt: Neue `current_page` Setting nach imports
   - Betroffen: pages/01_Stellenprofile.py, 02_Kandidaten.py, 03_Stellenprofil-Status.py, 04_CV_Generator.py, 05_Admin_Sidebar_Manager.py

2. **app.py aktualisiert:**
   - Defaults gesetzt: `language="de"`, `current_page="app.py"`
   - Neue Custom Styles Initialisierung

3. **Neue sidebar_renderer.py geschrieben:**
   - File: `core/ui/sidebar_renderer_new.py`
   - Funktionen: `_render_language_selection()`, `_render_navigation_buttons()`, `_render_settings_section()`
   - ~290 Zeilen, clean und dokumentiert
   - Verwendet `st.button()` mit type parameter für Farbgebung
   - Fallback auf hardcoded buttons wenn YAML nicht vorhanden

4. **Syntax-Validierung:**
   - Alle 6 Python-Files erfolgreich kompiliert
   - Keine Fehler

## NÄCHSTE SCHRITTE (Phase 1+)

1. Alte sidebar_renderer.py durch neue ersetzen
2. App neu starten und testen
3. YAML aktualisieren mit navigation_buttons
4. Iterativ Features testen

---

## 8. NICHT IM SCOPE (für später)

- [ ] Status Page (pages/03_Stellenprofil-Status.py) - entfernt
- [ ] Admin Sidebar Manager (pages/05_Admin_Sidebar_Manager.py) - entfernt
- [ ] Active Navigation Button Coloring (nicht nötig)
- [ ] Advanced Animations
- [ ] Mobile-Responsive Design

