"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2025-12-24
Last Updated: 2026-01-24
"""
import os
import json
from datetime import datetime

def load_translations():
    """Lädt die Übersetzungen aus der translations.json Datei."""
    try:
        paths = [
            os.path.join(os.path.dirname(__file__), "translations.json"),
            os.path.join("scripts", "translations.json"),
            "translations.json"
        ]
        for path in paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return {}
    except:
        return {}

def get_text(translations, section, key, lang="de"):
    """Holt einen übersetzten Text."""
    try:
        return translations.get(section, {}).get(key, {}).get(lang, f"[{key}]")
    except:
        return f"[{key}]"


def generate_cv_word_on_demand(cv_json_path, output_dir, language="de"):
    """
    Generiert das Word CV on-demand basierend auf den gleichen JSON-Daten.
    Diese Funktion wird aufgerufen wenn der Nutzer den "Generiere Word CV" Button klickt.
    
    Args:
        cv_json_path: Path to the CV JSON file
        output_dir: Output directory for the Word document
        language: Language for generation
        
    Returns:
        Path to generated Word file or None if failed
    """
    try:
        # Validierung: cv_json_path darf nicht None sein
        if not cv_json_path:
            raise ValueError("CV JSON Pfad ist leer oder None. Bitte versuchen Sie später erneut.")
        
        # Validierung: Datei muss existieren
        if not os.path.exists(cv_json_path):
            raise ValueError(f"CV JSON Datei nicht gefunden: {cv_json_path}")
        
        # Import here to avoid circular imports
        from scripts.generate_cv import generate_cv, validate_json_structure
        
        print(f"📄 Starte Word-Generierung für: {os.path.basename(cv_json_path)}")
        
        # Validate first
        with open(cv_json_path, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
        
        critical, info = validate_json_structure(cv_data, language=language)
        if critical:
            print(f"❌ Validierungsfehler: {'; '.join(critical)}")
            return None
        
        # Generate Word
        word_path = generate_cv(cv_json_path, output_dir, interactive=False, language=language)
        
        if word_path and os.path.exists(word_path):
            print(f"✅ Word erfolgreich generiert: {word_path}")
            return word_path
        else:
            print(f"❌ Word-Generierung fehlgeschlagen")
            return None
            
    except Exception as e:
        print(f"❌ Fehler bei Word-Generierung: {str(e)}")
        return None


def generate_dashboard(cv_json_path, match_json_path, feedback_json_path, output_dir, 
                       validation_warnings=None, model_name=None, pipeline_mode=None, 
                       cv_filename=None, job_filename=None, angebot_json_path=None,
                       language="de"):
    """
    Generates a professional HTML dashboard visualizing the results of the CV processing,
    matchmaking, and quality feedback.
    """
    translations = load_translations()
    
    # Load Data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    match_data = None
    if match_json_path and os.path.exists(match_json_path):
        with open(match_json_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
            
    feedback_data = None
    if feedback_json_path and os.path.exists(feedback_json_path):
        with open(feedback_json_path, 'r', encoding='utf-8') as f:
            feedback_data = json.load(f)

    angebot_data = None
    if angebot_json_path and os.path.exists(angebot_json_path):
        try:
            with open(angebot_json_path, 'r', encoding='utf-8') as f:
                angebot_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load offer data: {e}")

    # Load Styles for CI/CD Color
    primary_color_rgb = "44, 62, 80" # Default dark blue
    try:
        styles_path = os.path.join(os.path.dirname(__file__), "styles.json")
        if os.path.exists(styles_path):
            with open(styles_path, 'r', encoding='utf-8') as f:
                styles = json.load(f)
                rgb = styles.get("heading1", {}).get("color", [44, 62, 80])
                primary_color_rgb = f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
    except Exception as e:
        print(f"Warning: Could not load styles: {e}")

    # Extract Key Info
    vorname = cv_data.get("Vorname", "")
    nachname = cv_data.get("Nachname", "")
    candidate_name = f"{vorname} {nachname}".strip()
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Build metadata matrix (table)
    meta_cols = []
    meta_cols.append((get_text(translations, 'dashboard', 'generated_at', language), timestamp))
    if model_name:
        meta_cols.append((get_text(translations, 'dashboard', 'ai_model', language), f"<b>{model_name}</b>"))
    
    # Add target language with flag
    lang_flags = {"de": "🇩🇪", "en": "🇺🇸", "fr": "🇫🇷"}
    meta_cols.append((get_text(translations, 'ui', 'language_label', language), lang_flags.get(language, language.upper())))

    if pipeline_mode:
        meta_cols.append((get_text(translations, 'dashboard', 'mode', language), pipeline_mode))
    
    input_files = []
    if cv_filename: input_files.append(f"{get_text(translations, 'dashboard', 'cv_prefix', language)} {cv_filename}")
    if job_filename: input_files.append(f"{get_text(translations, 'dashboard', 'job_prefix', language)} {job_filename}")
    if input_files:
        meta_cols.append((get_text(translations, 'dashboard', 'input_files', language), "<br>".join(input_files)))

    # Construct HTML table for metadata
    table_html = '<table class="meta-table"><thead><tr>'
    for header_text, _ in meta_cols:
        table_html += f'<th>{header_text}</th>'
    table_html += '</tr></thead><tbody><tr>'
    for _, content in meta_cols:
        table_html += f'<td>{content}</td>'
    table_html += '</tr></tbody></table>'
    
    subtitle_text = table_html

    # Prepare HTML Content
    dashboard_title = get_text(translations, 'dashboard', 'title', language)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{dashboard_title} - {candidate_name}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --primary-color: rgb({primary_color_rgb});
                --secondary-color: #3498db;
                --success-color: #27ae60;
                --warning-color: #f39c12;
                --danger-color: #c0392b;
                --light-bg: #ecf0f1;
                --card-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f7f6;
                color: #333;
            }}
            .container {{
                max-width: 100%;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
            }}
            header {{
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: var(--card-shadow);
                margin-bottom: 20px;
            }}
            h1 {{ margin: 0; color: var(--primary-color); font-size: 24px; }}
            .meta {{ color: #7f8c8d; font-size: 14px; width: 100%; }}
            
            .meta-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                background-color: #fcfcfc;
                border: 1px solid #eee;
                border-radius: 4px;
            }}
            .meta-table th {{
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px 15px;
                border-bottom: 1px solid #eee;
                border-right: 1px solid #eee;
                text-align: left;
            }}
            .meta-table th:last-child {{ border-right: none; }}
            .meta-table td {{
                padding: 10px 15px;
                font-size: 13px;
                color: #2c3e50;
                vertical-align: top;
                border-right: 1px solid #eee;
                text-align: left;
            }}
            .meta-table td:last-child {{ border-right: none; }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            
            .card {{
                background: #fff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: var(--card-shadow);
            }}
            
            .card-header {{
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 15px;
                font-weight: bold;
                color: var(--primary-color);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .score-display {{
                text-align: center;
                padding: 20px 0;
            }}
            .score-value {{
                font-size: 48px;
                font-weight: bold;
                color: var(--secondary-color);
            }}
            .score-label {{
                font-size: 14px;
                color: #7f8c8d;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .status-badge {{
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
                color: #fff;
            }}
            .status-success {{ background-color: var(--success-color); }}
            .status-warning {{ background-color: var(--warning-color); }}
            .status-danger {{ background-color: var(--danger-color); }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }}
            th {{ color: #7f8c8d; font-weight: 600; }}
            
            .progress-bar {{
                background-color: #eee;
                border-radius: 4px;
                height: 8px;
                width: 100%;
                overflow: hidden;
            }}
            .progress-fill {{
                height: 100%;
                border-radius: 4px;
                transition: width 0.5s ease;
            }}
            
            .feedback-item {{
                margin-bottom: 10px;
                padding: 10px;
                background-color: #f9f9f9;
                border-left: 3px solid var(--secondary-color);
                border-radius: 0 4px 4px 0;
            }}
            .feedback-item.critical {{ border-left-color: var(--danger-color); background-color: #fff5f5; }}
            .feedback-item.warning {{ border-left-color: var(--warning-color); background-color: #fdfbf0; }}

            /* Modal Styles */
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }}
            .modal-content {{
                background-color: #fefefe;
                margin: 10% auto;
                padding: 25px;
                border-radius: 8px;
                width: 50%;
                max-width: 600px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            .close {{
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }}
            .close:hover {{ color: black; }}
            .status-info-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .info-btn {{
                background: none;
                border: 1px solid var(--primary-color);
                color: var(--primary-color);
                border-radius: 50%;
                width: 20px;
                height: 20px;
                font-size: 12px;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h1>{get_text(translations, 'dashboard', 'title', language)} - {candidate_name}</h1>
                    <a href="#" onclick="window.print()" style="text-decoration: none; color: var(--secondary-color); font-weight: bold;">{get_text(translations, 'dashboard', 'print_pdf', language)}</a>
                </div>
                <div class="meta">{subtitle_text}</div>
            </header>
    """

    # --- MATCHING SECTION ---
    if match_data:
        score = match_data.get("match_score", {}).get("score_gesamt", 0)
        # Ensure score is a number
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 0
            
        fazit = match_data.get("gesamt_fazit", {})
        empfehlung = fazit.get("empfehlung", "N/A")
        
        score_color = "var(--danger-color)"
        gauge_hex = "#c0392b" # danger
        if score >= 80: 
            score_color = "var(--success-color)"
            gauge_hex = "#27ae60"
        elif score >= 60: 
            score_color = "var(--warning-color)"
            gauge_hex = "#f39c12"
        
        html_content += f"""
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <span>{get_text(translations, 'dashboard', 'matching_score', language)}</span>
                        <button class="info-btn" onclick="document.getElementById('scoreModal').style.display='block'" title="Erklärung der Score-Berechnung">i</button>
                    </div>
                    <div style="position: relative; height: 160px; width: 100%; display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                        <canvas id="scoreGauge"></canvas>
                        <div style="position: absolute; bottom: 20px; width: 100%; text-align: center;">
                            <div style="font-size: 36px; font-weight: bold; color: {score_color}; line-height: 1;">{score}%</div>
                            <div style="font-size: 12px; color: #7f8c8d; text-transform: uppercase;">{get_text(translations, 'dashboard', 'overall', language)}</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 0px;">
                        <span class="status-badge" style="background-color: {score_color}">{empfehlung}</span>
                    </div>
                    <p style="margin-top: 15px; font-size: 13px; color: #666; text-align: center;">
                        {fazit.get("kurzbegruendung", "")}
                    </p>
                </div>
                
                <div class="card">
                    <div class="card-header">{get_text(translations, 'dashboard', 'criteria_matching', language)}</div>
                    <canvas id="criteriaChart"></canvas>
                </div>
                
                <div class="card">
                    <div class="card-header">{get_text(translations, 'dashboard', 'risks_gaps', language)}</div>
                    <div style="max-height: 200px; overflow-y: auto;">
        """
        
        risiken = match_data.get("risiken_und_luecken", [])
        if not risiken:
            html_content += f"<p style='color: #999; text-align: center;'>{get_text(translations, 'dashboard', 'no_risks_found', language)}</p>"
        else:
            for risiko in risiken:
                krit = risiko.get("kritikalitaet", "niedrig").lower()
                color_class = "critical" if krit == "hoch" else "warning" if krit == "mittel" else ""
                html_content += f"""
                    <div class="feedback-item {color_class}">
                        <strong>{risiko.get("typ", "Risiko")}:</strong> {risiko.get("beschreibung", "")}<br>
                        <small>{risiko.get("begruendung", "")}</small>
                    </div>
                """
        
        html_content += """
                    </div>
                </div>
            </div>
        """

        # --- QUALITATIVE ANGEBOTS-DETAILS (New) ---
        if angebot_data:
            beurteilung = angebot_data.get("gesamtbeurteilung", {})
            kompetenzen = angebot_data.get("profil_und_kompetenzen", {})
            
            mehrwert_raw = beurteilung.get("mehrwert_fuer_kunden", [])
            
            # Helper to safely get list
            def get_as_list(val):
                if isinstance(val, list): return val
                if isinstance(val, str): return [p.strip() for p in val.split("\n") if p.strip()]
                return []

            mehrwert_list = get_as_list(mehrwert_raw)
            methoden_list = get_as_list(kompetenzen.get("methoden_und_technologien", []))
            erfahrung_list = get_as_list(kompetenzen.get("operative_und_fuehrungserfahrung", []))

            html_content += f"""
            <h2 style="color: var(--primary-color); margin-top: 30px;">{get_text(translations, 'dashboard', 'offer_argumentation', language)}</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-header">{get_text(translations, 'dashboard', 'suitability_summary', language)}</div>
                    <p style="font-size: 14px; line-height: 1.6;">
                        {beurteilung.get("zusammenfassung", get_text(translations, 'dashboard', 'no_summary', language))}
                    </p>
                </div>
                
                <div class="card">
                    <div class="card-header">{get_text(translations, 'dashboard', 'methods_tech', language)}</div>
                    <ul style="font-size: 13px; line-height: 1.5; padding-left: 20px;">
                        {"".join([f"<li style='margin-bottom: 4px;'>{item.replace('**', '<b>').replace('**', '</b>')}</li>" for item in methoden_list])}
                    </ul>
                </div>

                <div class="card">
                    <div class="card-header">{get_text(translations, 'dashboard', 'suitability_focus', language)}</div>
                    <ul style="font-size: 13px; line-height: 1.5; padding-left: 20px;">
                        {"".join([f"<li style='margin-bottom: 4px;'>{item.replace('**', '<b>').replace('**', '</b>')}</li>" for item in erfahrung_list])}
                    </ul>
                </div>
            </div>

            <div class="card" style="margin-top: 20px;">
                <div class="card-header">{get_text(translations, 'offer', 'added_value', language)}</div>
                <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            """
            
            for item in mehrwert_list:
                display_item = item.replace("**", "<b>").replace("**", "</b>")
                html_content += f"""
                    <div style="padding: 10px; background: #fffcf5; border: 1px solid #fef5d4; border-radius: 6px; font-size: 13px;">
                        ✨ {display_item}
                    </div>
                """
            
            html_content += """
                </div>
            </div>
            """

        # --- CRITERIA TABLES (Split into Muss/Soll) ---
        html_content += f"""
            <h2 style="color: var(--primary-color); margin-top: 30px;">{get_text(translations, 'dashboard', 'criteria_matching', language)}</h2>
        """

        # Helper to render a specific section as separate table
        def render_criteria_card(title, items, bg_color="#f8f9fa"):
            if not items: 
                return f"""
                <div class="card" style="margin-bottom: 20px; opacity: 0.6;">
                    <div class="card-header" style="background-color: {bg_color}; border-radius: 4px 4px 0 0; margin-bottom: 0; padding: 10px;">
                        <span>{title} (0)</span>
                    </div>
                    <p style="text-align: center; padding: 20px; color: #999;">{get_text(translations, 'dashboard', 'no_criteria', language)}</p>
                </div>
                """
            
            card_html = f"""
            <div class="card" style="margin-bottom: 20px; padding: 0; overflow: hidden;">
                <div class="card-header" style="background-color: {bg_color}; border-radius: 4px 4px 0 0; margin-bottom: 0; padding: 15px; border-bottom: 2px solid #ddd;">
                    <span>{title} ({len(items)})</span>
                </div>
                <table style="margin: 0;">
                    <thead>
                        <tr style="background-color: #fafafa;">
                            <th style="width: 35%; padding-left: 20px;">{get_text(translations, 'dashboard', 'criterion', language)}</th>
                            <th style="width: 15%;">{get_text(translations, 'dashboard', 'status', language)}</th>
                            <th style="width: 50%;">{get_text(translations, 'dashboard', 'evidence', language)}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Map canonical statuses to translations
            s_fulfilled = get_text(translations, 'status', 'fulfilled', language)
            s_partial = get_text(translations, 'status', 'partial', language)
            s_not_fulfilled = get_text(translations, 'status', 'not_fulfilled', language)
            s_not_mentioned = get_text(translations, 'status', 'not_mentioned', language)
            s_potential = get_text(translations, 'status', 'potential', language)

            for k in items:
                status_raw = k.get("bewertung", "").lower().strip()
                
                # Consistent mapping with Word output and multi-language support
                status_display = status_raw
                icon = "❓"
                
                # Fulfilled
                if any(x in status_raw for x in ["erfüllt", "fulfilled", "rempli"]) and "nicht" not in status_raw and "teilweise" not in status_raw and "pas" not in status_raw:
                    icon = "✅"
                    status_display = s_fulfilled
                # Partial / Potential
                elif any(x in status_raw for x in ["teilweise", "partial", "partiellement", "potenziell", "potential", "potentiellement"]):
                    icon = "⚠️"
                    status_display = s_partial if "teilweise" in status_raw else s_potential
                # Not fulfilled
                elif any(x in status_raw for x in ["nicht erfüllt", "not fulfilled", "non rempli", "pas rempli"]):
                    icon = "❌"
                    status_display = s_not_fulfilled
                # Not mentioned
                elif any(x in status_raw for x in ["nicht explizit", "explicitly", "mention"]):
                    icon = "➖"
                    status_display = s_not_mentioned
                elif "! bitte prüfen !" in status_raw or "! please check !" in status_raw or "! à vérifier !" in status_raw:
                    icon = "❓"
                    status_display = get_text(translations, 'system', 'missing_data_marker', language)

                evidenz_raw = k.get("cv_evidenz", "")
                kommentar_raw = k.get("kommentar", "")
                
                # Combine evidence and comment for the dashboard if they differ
                display_evidenz = evidenz_raw
                if kommentar_raw and kommentar_raw != evidenz_raw:
                    if display_evidenz:
                        display_evidenz += f" ({kommentar_raw})"
                    else:
                        display_evidenz = kommentar_raw

                if display_evidenz:
                    parts = [p.strip() for p in display_evidenz.replace(";", "\n").split("\n") if p.strip()]
                    if len(parts) > 1:
                        evidenz_html = "<ul style='margin: 0; padding-left: 20px;'>" + "".join([f"<li>{p}</li>" for p in parts]) + "</ul>"
                    else:
                        evidenz_html = parts[0]
                else:
                    evidenz_html = f"<span style='color: #999; font-style: italic;'>{get_text(translations, 'dashboard', 'no_evidence', language)}</span>"

                card_html += f"""
                    <tr>
                        <td style="padding-left: 20px; font-weight: 500;">{k.get("kriterium", "")}</td>
                        <td style="white-space: nowrap;">{icon} {status_display}</td>
                        <td style="font-size: 13px;">{evidenz_html}</td>
                    </tr>
                """
            
            card_html += """
                    </tbody>
                </table>
            </div>
            """
            return card_html

        # Now render them as separate blocks
        html_content += render_criteria_card(get_text(translations, 'offer', 'muss_criteria', language), match_data.get("muss_kriterien_abgleich", []), "#e8f6f3")
        html_content += render_criteria_card(get_text(translations, 'offer', 'soll_criteria', language), match_data.get("soll_kriterien_abgleich", []), "#fef9e7")
        
        # Soft Skills and others in a 2-column grid to save space
        html_content += """<div class="grid">"""
        html_content += render_criteria_card(get_text(translations, 'offer', 'soft_skills', language), match_data.get("soft_skills_abgleich", []), "#f4f6f7")
        html_content += render_criteria_card(get_text(translations, 'offer', 'other_criteria', language), match_data.get("weitere_kriterien_abgleich", []), "#f4f6f7")
        html_content += """</div>"""

    # --- VALIDATION SECTION ---
    # Always show validation section, even if empty
    html_content += f"""
        <h2 style="color: var(--primary-color); margin-top: 30px;">{get_text(translations, 'dashboard', 'validation_title', language)}</h2>
        <div class="grid">
            <div class="card" style="grid-column: 1 / -1;">
                <div class="card-header">
                    <span>{get_text(translations, 'dashboard', 'validation_warnings', language) if validation_warnings else get_text(translations, 'dashboard', 'validation_success', language)}</span>
                </div>
                <div style="margin-bottom: 10px; color: #666; font-size: 14px;">
                    {get_text(translations, 'dashboard', 'validation_desc', language)}
                </div>
                <div style="max-height: 300px; overflow-y: auto;">
    """
    
    if validation_warnings:
        for warning in validation_warnings:
             html_content += f"""
                <div class="feedback-item warning">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>{get_text(translations, 'dashboard', 'structure_check', language)}</strong>
                        <span style="font-size: 11px; text-transform: uppercase; opacity: 0.7;">Info</span>
                    </div>
                    <div>{warning}</div>
                </div>
            """
    else:
        html_content += f"""
            <div style="text-align: center; padding: 20px; color: #27ae60;">
                <div style="font-size: 24px; margin-bottom: 10px;">✨</div>
                <div>{get_text(translations, 'dashboard', 'no_errors_found', language)}</div>
            </div>
        """
        
    html_content += """
                </div>
            </div>
        </div>
    """

    # --- FEEDBACK SECTION ---
    if feedback_data:
        summary = feedback_data.get("zusammenfassung", {})
        quality_rating = summary.get("gesamt_einschaetzung", "Unbekannt")
        
        html_content += f"""
            <h2 style="color: var(--primary-color); margin-top: 30px;">{get_text(translations, 'dashboard', 'cv_quality_check', language)}</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-header">{get_text(translations, 'dashboard', 'quality_assessment', language)}</div>
                    <div class="score-display">
                        <div class="score-value" style="font-size: 32px; color: var(--primary-color)">{quality_rating}</div>
                        <div class="score-label">{get_text(translations, 'dashboard', 'quality_data_structure', language)}</div>
                    </div>
                    <div style="padding: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>{get_text(translations, 'dashboard', 'critical_points', language)}</span>
                            <span style="font-weight: bold; color: var(--danger-color)">{summary.get("kritische_punkte", 0)}</span>
                        </div>
                        <div style="font-size: 13px; margin-top: 10px;">
                            <strong>{get_text(translations, 'dashboard', 'recommendation', language)}</strong> {summary.get("empfehlung", "")}
                        </div>
                    </div>
                </div>
                
                <div class="card" style="grid-column: 2 / -1;">
                    <div class="card-header">{get_text(translations, 'dashboard', 'action_needed_feedback', language)}</div>
                    <div style="max-height: 250px; overflow-y: auto;">
        """
        
        # Combine different feedback sections
        all_feedback = []
        for item in feedback_data.get("feldbezogenes_feedback", []):
            item['source'] = f"{get_text(translations, 'dashboard', 'field_prefix', language)} {item.get('cv_feld', '')}"
            all_feedback.append(item)
        
        for item in feedback_data.get("struktur_und_regelchecks", []):
            if item.get("status") != "erfüllt":
                item['source'] = get_text(translations, 'dashboard', 'structure_check', language)
                item['beschreibung'] = item.get('beobachtung', '')
                item['feedback_typ'] = "Regelverstoss"
                all_feedback.append(item)

        if not all_feedback:
             html_content += f"<p style='color: #999; text-align: center;'>{get_text(translations, 'dashboard', 'no_quality_issues', language)}</p>"
        else:
            for item in all_feedback:
                typ = item.get("feedback_typ", "").lower()
                is_critical = "fehlend" in typ or "regelverstoss" in typ or "kritisch" in typ
                css_class = "critical" if is_critical else "warning"
                
                html_content += f"""
                    <div class="feedback-item {css_class}">
                        <div style="display:flex; justify-content:space-between;">
                            <strong>{item.get('source', '')}</strong>
                            <span style="font-size: 11px; text-transform: uppercase; opacity: 0.7;">{item.get('feedback_typ', '')}</span>
                        </div>
                        <div>{item.get('beschreibung', '')}</div>
                        {f"<div style='margin-top:5px; font-size:12px; color:#666;'>💡 {item.get('empfohlene_klaerung', '')}</div>" if item.get('empfohlene_klaerung') else ""}
                    </div>
                """

        html_content += """
                    </div>
                </div>
            </div>
        """

    # --- JAVASCRIPT FOR CHARTS ---
    if match_data:
        def count_status(items):
            ok = 0
            potential = 0
            neutral = 0
            for k in items:
                s = k.get("bewertung", "").lower()
                if "nicht explizit" in s:
                    neutral += 1
                elif "nicht" in s: # "nicht erfüllt"
                    continue
                elif "potenziell" in s or "implizit" in s or "teilweise" in s:
                    potential += 1
                elif "erfüllt" in s:
                    ok += 1
            return ok, potential, neutral

        muss_total = len(match_data.get("muss_kriterien_abgleich", []))
        muss_ok, muss_pot, muss_neu = count_status(match_data.get("muss_kriterien_abgleich", []))
        
        soll_total = len(match_data.get("soll_kriterien_abgleich", []))
        soll_ok, soll_pot, soll_neu = count_status(match_data.get("soll_kriterien_abgleich", []))

        soft_total = len(match_data.get("soft_skills_abgleich", []))
        soft_ok, soft_pot, soft_neu = count_status(match_data.get("soft_skills_abgleich", []))

        weitere_total = len(match_data.get("weitere_kriterien_abgleich", []))
        weitere_ok, weitere_pot, weitere_neu = count_status(match_data.get("weitere_kriterien_abgleich", []))

        html_content += f"""
        <script>
            // Score Gauge
            const ctxScore = document.getElementById('scoreGauge').getContext('2d');
            new Chart(ctxScore, {{
                type: 'doughnut',
                data: {{
                    labels: ['Score', 'Gap'],
                    datasets: [{{
                        data: [{score}, {100 - score}],
                        backgroundColor: [
                            '{gauge_hex}', 
                            '#e0e0e0'
                        ],
                        borderWidth: 0,
                        borderRadius: 5
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    circumference: 180,
                    rotation: 270,
                    cutout: '75%',
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{ enabled: false }}
                    }}
                }}
            }});

            // Criteria Chart
            const ctx = document.getElementById('criteriaChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: [
                        '{get_text(translations, "dashboard", "muss", language)}', 
                        '{get_text(translations, "dashboard", "soll", language)}', 
                        '{get_text(translations, "dashboard", "soft_skills", language)}', 
                        '{get_text(translations, "dashboard", "weitere", language)}'
                    ],
                    datasets: [
                        {{
                            label: '{get_text(translations, "dashboard", "chart_ok", language)}',
                            data: [{muss_ok}, {soll_ok}, {soft_ok}, {weitere_ok}],
                            backgroundColor: '#27ae60'
                        }},
                        {{
                            label: '{get_text(translations, "dashboard", "chart_potential", language)}',
                            data: [{muss_pot}, {soll_pot}, {soft_pot}, {weitere_pot}],
                            backgroundColor: '#f1c40f'
                        }},
                        {{
                            label: '{get_text(translations, "dashboard", "chart_neutral", language)}',
                            data: [{muss_neu}, {soll_neu}, {soft_neu}, {weitere_neu}],
                            backgroundColor: '#95a5a6'
                        }},
                        {{
                            label: '{get_text(translations, "dashboard", "chart_not_ok", language)}',
                            data: [
                                {muss_total - muss_ok - muss_pot - muss_neu}, 
                                {soll_total - soll_ok - soll_pot - soll_neu},
                                {soft_total - soft_ok - soft_pot - soft_neu},
                                {weitere_total - weitere_ok - weitere_pot - weitere_neu}
                            ],
                            backgroundColor: '#e74c3c'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    layout: {{
                        padding: {{
                            bottom: 10
                        }}
                    }},
                    plugins: {{
                        legend: {{ 
                            position: 'bottom',
                            labels: {{
                                padding: 20,
                                boxWidth: 12
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ stacked: true }},
                        y: {{ stacked: true, beginAtZero: true }}
                    }}
                }}
            }});
        </script>
        """

    html_content += """
        <!-- Score Legend Modal -->
        <div id="scoreModal" class="modal">
            <div class="modal-content" style="max-width: 700px;">
                <span class="close" onclick="document.getElementById('scoreModal').style.display='none'">&times;</span>
                <h3>{get_text("dashboard_modals", "score_title", language)}</h3>
                <p>{get_text("dashboard_modals", "score_desc", language)}</p>
                
                <table class="status-info-table" style="margin-bottom: 20px;">
                    <tr style="background-color: #e8f6f3;">
                        <td style="width: 150px;"><strong>{get_text("dashboard_modals", "score_must", language)}</strong></td>
                        <td><strong>{get_text("dashboard_modals", "score_basis_90", language)}</strong></td>
                        <td>{get_text("dashboard_modals", "score_must_desc", language)}</td>
                    </tr>
                    <tr style="background-color: #fef9e7;">
                        <td><strong>{get_text("dashboard_modals", "score_should", language)}</strong></td>
                        <td><strong>{get_text("dashboard_modals", "score_basis_10", language)}</strong></td>
                        <td>{get_text("dashboard_modals", "score_should_desc", language)}</td>
                    </tr>
                    <tr style="background-color: #f4f6f7;">
                        <td><strong>{get_text("dashboard_modals", "score_soft_skills", language)}</strong></td>
                        <td><strong>{get_text("dashboard_modals", "score_basis_0", language)}</strong></td>
                        <td>{get_text("dashboard_modals", "score_soft_skills_desc", language)}</td>
                    </tr>
                </table>

                <h4 style="margin-top: 20px; font-size: 14px;">{get_text("dashboard_modals", "score_weighting_title", language)}</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px; margin-bottom: 15px;">
                    <div style="padding: 8px; background-color: #e8f5e9; border: 1px solid #2e7d32; border-radius: 4px; color: #1b5e20;"><strong>✅ {get_text("dashboard_modals", "score_fulfilled", language)}</strong></div>
                    <div style="padding: 8px; background-color: #fff3e0; border: 1px solid #ef6c00; border-radius: 4px; color: #e65100;"><strong>⚠️ {get_text("dashboard_modals", "score_partial", language)}</strong></div>
                    <div style="padding: 8px; background-color: #fffde7; border: 1px solid #fbc02d; border-radius: 4px; color: #f57f17;"><strong>🤔 {get_text("dashboard_modals", "score_potential", language)}</strong></div>
                    <div style="padding: 8px; background-color: #ffebee; border: 1px solid #c62828; border-radius: 4px; color: #b71c1c;"><strong>❌ {get_text("dashboard_modals", "score_not_fulfilled_val", language)}</strong></div>
                </div>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px; font-size: 13px; border-left: 4px solid var(--secondary-color);">
                    <strong>{get_text("dashboard_modals", "score_example_title", language)}</strong><br>
                    {get_text("dashboard_modals", "score_example_scenario", language)}<br>
                    • {get_text("dashboard_modals", "score_example_1", language)} (<span style="color: #27ae60;">✅</span>) & {get_text("dashboard_modals", "score_example_1_soll", language)} (<span style="color: #f39c12;">⚠️</span>) → <strong>ca. 95%</strong><br>
                    • {get_text("dashboard_modals", "score_example_2", language)} (<span style="color: #c0392b;">❌</span>) → <strong>{get_text("dashboard_modals", "score_example_2_desc", language)}</strong>
                </div>

                <div style="background-color: #eee; padding: 15px; border-radius: 8px; margin-top: 10px; font-size: 13px;">
                    <strong>{get_text("dashboard_modals", "score_dynamic_title", language)}</strong>
                    {get_text("dashboard_modals", "score_dynamic_desc", language)}
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <div style="flex: 1; padding: 10px; background: #e8f5e9; border-radius: 4px; text-align: center; border-bottom: 3px solid #2e7d32;">
                        <strong>> 80%</strong><br><span style="font-size: 12px;">{get_text("dashboard_modals", "score_excellent", language)}</span>
                    </div>
                    <div style="flex: 1; padding: 10px; background: #fff3e0; border-radius: 4px; text-align: center; border-bottom: 3px solid #ef6c00;">
                        <strong>60-80%</strong><br><span style="font-size: 12px;">{get_text("dashboard_modals", "score_good", language)}</span>
                    </div>
                    <div style="flex: 1; padding: 10px; background: #ffebee; border-radius: 4px; text-align: center; border-bottom: 3px solid #c62828;">
                        <strong>< 60%</strong><br><span style="font-size: 12px;">{get_text("dashboard_modals", "score_critical", language)}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Status Legend Modal -->
        <div id="statusModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="document.getElementById('statusModal').style.display='none'">&times;</span>
                <h3>{get_text("dashboard_modals", "status_title", language)}</h3>
                <p>{get_text("dashboard_modals", "status_desc", language)}</p>
                <table class="status-info-table">
                    <tr>
                        <td style="width: 40px; font-size: 20px;">✅</td>
                        <td><strong>{get_text("dashboard_modals", "status_fulfilled", language)}</strong>: {get_text("dashboard_modals", "status_fulfilled_desc", language)}</td>
                    </tr>
                    <tr>
                        <td style="font-size: 20px;">⚠️</td>
                        <td><strong>{get_text("dashboard_modals", "status_partial", language)}</strong>: {get_text("dashboard_modals", "status_partial_desc", language)}</td>
                    </tr>
                    <tr>
                        <td style="font-size: 20px;">❌</td>
                        <td><strong>{get_text("dashboard_modals", "status_not_fulfilled", language)}</strong>: {get_text("dashboard_modals", "status_not_fulfilled_desc", language)}</td>
                    </tr>
                    <tr>
                        <td style="font-size: 20px;">⚪</td>
                        <td><strong>{get_text("dashboard_modals", "status_not_mentioned", language)}</strong>: {get_text("dashboard_modals", "status_not_mentioned_desc", language)}</td>
                    </tr>
                    <tr>
                        <td style="font-size: 20px;">❓</td>
                        <td><strong>{get_text("dashboard_modals", "status_check", language)}</strong>: {get_text("dashboard_modals", "status_check_desc", language)}</td>
                    </tr>
                </table>
                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    <em>{get_text("dashboard_modals", "ai_note", language)}</em>
                </p>
            </div>
        </div>

        <script>
            // Close modals when clicking outside
            window.onclick = function(event) {
                var scoreModal = document.getElementById('scoreModal');
                var statusModal = document.getElementById('statusModal');
                if (event.target == scoreModal) {
                    scoreModal.style.display = "none";
                }
                if (event.target == statusModal) {
                    statusModal.style.display = "none";
                }
            }
        </script>
        </div>
    </body>
    </html>
    """

    # Save File
    filename = f"Dashboard_{vorname}_{nachname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ Dashboard generiert: {output_path}")
    return output_path
