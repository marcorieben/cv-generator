import os
import json
from datetime import datetime

def generate_dashboard(cv_json_path, match_json_path, feedback_json_path, output_dir, validation_warnings=None, model_name=None, pipeline_mode=None, cv_filename=None, job_filename=None):
    """
    Generates a professional HTML dashboard visualizing the results of the CV processing,
    matchmaking, and quality feedback.
    """
    
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
    meta_cols.append(("Generiert", timestamp))
    if model_name:
        meta_cols.append(("KI-Modell", f"<b>{model_name}</b>"))
    if pipeline_mode:
        meta_cols.append(("Modus", pipeline_mode))
    
    input_files = []
    if cv_filename: input_files.append(f"CV: {cv_filename}")
    if job_filename: input_files.append(f"SP: {job_filename}")
    if input_files:
        meta_cols.append(("Input Dateien", "<br>".join(input_files)))

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
    html_content = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV Analyse Dashboard - {candidate_name}</title>
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
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h1>Dashboard - CV Analyse - {candidate_name}</h1>
                    <a href="#" onclick="window.print()" style="text-decoration: none; color: var(--secondary-color); font-weight: bold;">🖨️ Drucken / PDF</a>
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
                    <div class="card-header">Match Score</div>
                    <div style="position: relative; height: 160px; width: 100%; display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                        <canvas id="scoreGauge"></canvas>
                        <div style="position: absolute; bottom: 20px; width: 100%; text-align: center;">
                            <div style="font-size: 36px; font-weight: bold; color: {score_color}; line-height: 1;">{score}%</div>
                            <div style="font-size: 12px; color: #7f8c8d; text-transform: uppercase;">Gesamt</div>
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
                    <div class="card-header">Kriterien Abdeckung</div>
                    <canvas id="criteriaChart"></canvas>
                </div>
                
                <div class="card">
                    <div class="card-header">Risiken & Lücken</div>
                    <div style="max-height: 200px; overflow-y: auto;">
        """
        
        risiken = match_data.get("risiken_und_luecken", [])
        if not risiken:
            html_content += "<p style='color: #999; text-align: center;'>Keine Risiken identifiziert.</p>"
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
            
            <div class="card" style="margin-bottom: 20px;">
                <div class="card-header">Detaillierter Kriterien-Abgleich</div>
                <table>
                    <thead>
                        <tr>
                            <th>Kriterium</th>
                            <th>Status</th>
                            <th>Evidenz im CV</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Helper to render a section
        def render_criteria_section(title, items, bg_color="#f8f9fa"):
            if not items: return ""
            
            section_html = f"""
                <tr style="background-color: {bg_color}; border-bottom: 2px solid #ddd;">
                    <td colspan="3" style="font-weight: bold; padding-top: 15px; padding-bottom: 10px; color: #2c3e50;">{title}</td>
                </tr>
            """
            
            for k in items:
                status = k.get("bewertung", "").lower()
                
                # Determine Icon
                if "nicht explizit" in status:
                    icon = "⚪" # Neutral
                elif "nicht" in status:
                    icon = "❌"
                elif "potenziell" in status or "implizit" in status:
                    icon = "🤔" # Potential / Review needed
                elif "teilweise" in status or "unklar" in status:
                    icon = "⚠️"
                elif "erfüllt" in status:
                    icon = "✅"
                else:
                    icon = "❓"

                # Format Evidence
                evidenz_raw = k.get("cv_evidenz", "")
                if evidenz_raw:
                    parts = [p.strip() for p in evidenz_raw.replace(";", "\n").split("\n") if p.strip()]
                    if len(parts) > 1:
                        evidenz_html = "<ol style='margin: 0; padding-left: 20px;'>" + "".join([f"<li>{p}</li>" for p in parts]) + "</ol>"
                    else:
                        evidenz_html = parts[0]
                else:
                    if "nicht explizit" in status:
                        evidenz_html = "<span style='color: #999; font-style: italic;'>Keine explizite Evidenz</span>"
                    else:
                        evidenz_html = "<span style='color: #999; font-style: italic;'>Keine Evidenz gefunden</span>"

                section_html += f"""
                    <tr>
                        <td style="padding-left: 20px;">{k.get("kriterium", "")}</td>
                        <td>{icon} {k.get("bewertung", "")}</td>
                        <td>{evidenz_html}</td>
                    </tr>
                """
            return section_html

        html_content += render_criteria_section("Muss-Kriterien (Pflicht)", match_data.get("muss_kriterien_abgleich", []), "#e8f6f3")
        html_content += render_criteria_section("Soll-Kriterien (Wunsch)", match_data.get("soll_kriterien_abgleich", []), "#fef9e7")
        html_content += render_criteria_section("Soft Skills & Persönlichkeit", match_data.get("soft_skills_abgleich", []), "#f4f6f7")
        html_content += render_criteria_section("Weitere Kriterien", match_data.get("weitere_kriterien_abgleich", []), "#f4f6f7")
            
        html_content += """
                    </tbody>
                </table>
            </div>
        """

    # --- VALIDATION SECTION ---
    # Always show validation section, even if empty
    html_content += f"""
        <h2 style="color: var(--primary-color); margin-top: 30px;">Technische Validierung</h2>
        <div class="grid">
            <div class="card" style="grid-column: 1 / -1;">
                <div class="card-header">
                    <span>{'⚠️ Validierungshinweise' if validation_warnings else '✅ Validierung erfolgreich'}</span>
                </div>
                <div style="margin-bottom: 10px; color: #666; font-size: 14px;">
                    Ergebnis der technischen Prüfung der CV-Struktur (Pflichtfelder, Datentypen, Längen).
                </div>
                <div style="max-height: 300px; overflow-y: auto;">
    """
    
    if validation_warnings:
        for warning in validation_warnings:
             html_content += f"""
                <div class="feedback-item warning">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>Struktur-Check</strong>
                        <span style="font-size: 11px; text-transform: uppercase; opacity: 0.7;">Info</span>
                    </div>
                    <div>{warning}</div>
                </div>
            """
    else:
        html_content += """
            <div style="text-align: center; padding: 20px; color: #27ae60;">
                <div style="font-size: 24px; margin-bottom: 10px;">✨</div>
                <div>Keine strukturellen Fehler oder Warnungen gefunden.</div>
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
            <h2 style="color: var(--primary-color); margin-top: 30px;">CV Qualitäts-Check</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-header">Qualitätseinschätzung</div>
                    <div class="score-display">
                        <div class="score-value" style="font-size: 32px; color: var(--primary-color)">{quality_rating}</div>
                        <div class="score-label">Datenqualität & Struktur</div>
                    </div>
                    <div style="padding: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>Kritische Punkte:</span>
                            <span style="font-weight: bold; color: var(--danger-color)">{summary.get("kritische_punkte", 0)}</span>
                        </div>
                        <div style="font-size: 13px; margin-top: 10px;">
                            <strong>Empfehlung:</strong> {summary.get("empfehlung", "")}
                        </div>
                    </div>
                </div>
                
                <div class="card" style="grid-column: 2 / -1;">
                    <div class="card-header">Handlungsbedarf & Feedback</div>
                    <div style="max-height: 250px; overflow-y: auto;">
        """
        
        # Combine different feedback sections
        all_feedback = []
        for item in feedback_data.get("feldbezogenes_feedback", []):
            item['source'] = f"Feld: {item.get('cv_feld', '')}"
            all_feedback.append(item)
        
        for item in feedback_data.get("struktur_und_regelchecks", []):
            if item.get("status") != "erfüllt":
                item['source'] = "Struktur-Check"
                item['beschreibung'] = item.get('beobachtung', '')
                item['feedback_typ'] = "Regelverstoß"
                all_feedback.append(item)

        if not all_feedback:
             html_content += "<p style='color: #999; text-align: center;'>Keine nennenswerten Qualitätsprobleme gefunden.</p>"
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
                    labels: ['Muss', 'Soll', 'Soft Skills', 'Weitere'],
                    datasets: [
                        {{
                            label: 'Erfüllt',
                            data: [{muss_ok}, {soll_ok}, {soft_ok}, {weitere_ok}],
                            backgroundColor: '#27ae60'
                        }},
                        {{
                            label: 'Potenziell / Teilweise',
                            data: [{muss_pot}, {soll_pot}, {soft_pot}, {weitere_pot}],
                            backgroundColor: '#f1c40f'
                        }},
                        {{
                            label: 'Neutral / Nicht explizit',
                            data: [{muss_neu}, {soll_neu}, {soft_neu}, {weitere_neu}],
                            backgroundColor: '#95a5a6'
                        }},
                        {{
                            label: 'Nicht Erfüllt',
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
