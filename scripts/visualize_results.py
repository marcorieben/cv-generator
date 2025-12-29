import os
import json
from datetime import datetime

def generate_dashboard(cv_json_path, match_json_path, feedback_json_path, output_dir, validation_warnings=None, model_name=None, pipeline_mode=None):
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
    
    subtitle_parts = [f"Generiert: {timestamp}"]
    if model_name:
        subtitle_parts.append(f"KI-Modell: {model_name}")
    if pipeline_mode:
        subtitle_parts.append(f"Modus: {pipeline_mode}")
    subtitle_text = " &bull; ".join(subtitle_parts)

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
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            h1 {{ margin: 0; color: var(--primary-color); font-size: 24px; }}
            .meta {{ color: #7f8c8d; font-size: 14px; }}
            
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
                overflow: auto; 
                background-color: rgba(0,0,0,0.4); 
                backdrop-filter: blur(4px);
            }}
            .modal-content {{
                background-color: #fefefe;
                margin: 10% auto; 
                padding: 25px;
                border: 1px solid #888;
                width: 90%; 
                max-width: 600px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                animation: slideIn 0.3s ease-out;
            }}
            @keyframes slideIn {{
                from {{ transform: translateY(-50px); opacity: 0; }}
                to {{ transform: translateY(0); opacity: 1; }}
            }}
            .close {{
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                transition: color 0.2s;
            }}
            .close:hover,
            .close:focus {{
                color: var(--primary-color);
                text-decoration: none;
                cursor: pointer;
            }}
            .info-icon {{
                cursor: pointer;
                font-size: 16px;
                color: #95a5a6;
                margin-left: 8px;
                transition: color 0.2s;
            }}
            .info-icon:hover {{
                color: var(--secondary-color);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>Dashboard - CV Analyse - {candidate_name}</h1>
                    <div class="meta">{subtitle_text}</div>
                </div>
                <div>
                    <a href="#" onclick="window.print()" style="text-decoration: none; color: var(--secondary-color); font-weight: bold;">🖨️ Drucken / PDF</a>
                </div>
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
            
        # Extract weights for modal
        weights = match_data.get("match_score", {}).get("gewichtung", {})
        w_muss = weights.get("muss_kriterien", 60)
        w_soll = weights.get("soll_kriterien", 30)
        w_skill = weights.get("skill_abdeckung", 10)
            
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
                        Match Score
                        <span class="info-icon" onclick="document.getElementById('scoreInfoModal').style.display='block'" title="Wie wird der Score berechnet?">ℹ️</span>
                    </div>
                    
                    <div style="height: 150px; width: 100%; margin-bottom: 10px;">
                        <canvas id="scoreBarChart"></canvas>
                    </div>
                    <div style="text-align: center; margin-top: 5px;">
                         <span style="font-size: 14px; color: #7f8c8d;">Manuell Gesamt:</span>
                         <span id="manualScoreValue" style="font-size: 24px; font-weight: bold; color: {score_color}; margin-left: 5px;">{score}%</span> 
                    </div>

                    <div style="text-align: center; margin-top: 10px;">
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
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Detaillierter Kriterien-Abgleich</span>
                    <button onclick="downloadJSON()" style="background-color: #2ecc71; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px;">💾 Änderungen speichern (JSON)</button>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 26.666%;">Kriterium</th>
                            <th style="width: 10%;">KI Status</th>
                            <th style="width: 10%;">Manuell</th>
                            <th style="width: 26.666%;">Kommentar</th>
                            <th style="width: 26.666%;">Evidenz im CV</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Helper to render a section
        def render_criteria_section(title, items, category_key, bg_color="#f8f9fa"):
            if not items: return ""
            
            section_html = f"""
                <tr style="background-color: {bg_color}; border-bottom: 2px solid #ddd;">
                    <td colspan="5" style="font-weight: bold; padding-top: 15px; padding-bottom: 10px; color: #2c3e50;">{title}</td>
                </tr>
            """
            
            for idx, k in enumerate(items):
                status = k.get("bewertung", "").lower()
                
                # Determine Icon & Standardized Status
                std_status = "neutral"
                if "nicht" in status and "explizit" not in status:
                    icon = "❌"
                    std_status = "nicht erfüllt"
                elif "potenziell" in status or "implizit" in status:
                    icon = "🤔"
                    std_status = "potenziell"
                elif "teilweise" in status or "unklar" in status:
                    icon = "⚠️"
                    std_status = "potenziell"
                elif "erfüllt" in status:
                    icon = "✅"
                    std_status = "erfüllt"
                else:
                    icon = "⚪"
                    std_status = "neutral"

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

                # Check for Manual Overrides
                manual_data = k.get("manuell", {})
                current_status = manual_data.get("status", std_status)
                current_comment = manual_data.get("kommentar", "")

                # Dropdown Selection
                sel_erfuellt = "selected" if current_status == "erfüllt" else ""
                sel_potenziell = "selected" if current_status == "potenziell" else ""
                sel_nicht = "selected" if current_status == "nicht erfüllt" else ""
                sel_neutral = "selected" if current_status == "neutral" else ""

                section_html += f"""
                    <tr>
                        <td style="padding-left: 20px;">{k.get("kriterium", "")}</td>
                        <td>{icon} {k.get("bewertung", "")}</td>
                        <td>
                            <select class="manual-status" data-category="{category_key}" data-index="{idx}" onchange="updateManualScore()" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="erfüllt" {sel_erfuellt}>✅ Erfüllt</option>
                                <option value="potenziell" {sel_potenziell}>🤔 Potenziell</option>
                                <option value="nicht erfüllt" {sel_nicht}>❌ Nicht Erfüllt</option>
                                <option value="neutral" {sel_neutral}>⚪ Neutral</option>
                            </select>
                        </td>
                        <td>
                            <input type="text" class="manual-comment" data-category="{category_key}" data-index="{idx}" value="{current_comment}" placeholder="Kommentar..." style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 4px;">
                        </td>
                        <td>{evidenz_html}</td>
                    </tr>
                """
            return section_html

        html_content += render_criteria_section("Muss-Kriterien (Pflicht)", match_data.get("muss_kriterien_abgleich", []), "muss", "#e8f6f3")
        html_content += render_criteria_section("Soll-Kriterien (Wunsch)", match_data.get("soll_kriterien_abgleich", []), "soll", "#fef9e7")
        html_content += render_criteria_section("Soft Skills & Persönlichkeit", match_data.get("soft_skills_abgleich", []), "soft", "#f4f6f7")
        html_content += render_criteria_section("Weitere Kriterien", match_data.get("weitere_kriterien_abgleich", []), "weitere", "#f4f6f7")
            
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

        # Serialize match_data for JS
        match_data_json = json.dumps(match_data, ensure_ascii=False)

        html_content += f"""
        <script>
            // --- Global Data ---
            const matchData = {match_data_json};

            // --- Data & Weights ---
            const weights = {{ 
                muss: {w_muss}, 
                soll: {w_soll}, 
                skill: {w_skill} 
            }};
            
            // Initial AI Counts (passed from Python)
            const aiData = {{
                muss: {{ ok: {muss_ok}, pot: {muss_pot}, neu: {muss_neu}, total: {muss_total} }},
                soll: {{ ok: {soll_ok}, pot: {soll_pot}, neu: {soll_neu}, total: {soll_total} }},
                soft: {{ ok: {soft_ok}, pot: {soft_pot}, neu: {soft_neu}, total: {soft_total} }},
                weitere: {{ ok: {weitere_ok}, pot: {weitere_pot}, neu: {weitere_neu}, total: {weitere_total} }}
            }};

            // Helper: Calculate Score % for a category
            function calcCatScore(ok, pot, total) {{
                if (total === 0) return 0;
                return ((ok * 1.0 + pot * 0.5) / total) * 100;
            }}

            // Calculate Initial AI Category Scores
            const aiScores = {{
                muss: calcCatScore(aiData.muss.ok, aiData.muss.pot, aiData.muss.total),
                soll: calcCatScore(aiData.soll.ok, aiData.soll.pot, aiData.soll.total),
                soft: calcCatScore(aiData.soft.ok, aiData.soft.pot, aiData.soft.total),
                weitere: calcCatScore(aiData.weitere.ok, aiData.weitere.pot, aiData.weitere.total)
            }};

            // --- Charts ---
            
            // 1. Score Stacked Bar Chart (Horizontal)
            const ctxScore = document.getElementById('scoreBarChart').getContext('2d');
            
            // Calculate initial contributions
            const aiContrib = {{
                muss: aiScores.muss * weights.muss / 100,
                soll: aiScores.soll * weights.soll / 100,
                skill: ((aiScores.soft + aiScores.weitere) / 2) * weights.skill / 100
            }};

            // Initial Manual is same as AI
            const manContrib = {{ ...aiContrib }};

            const scoreBarChart = new Chart(ctxScore, {{
                type: 'bar',
                data: {{
                    labels: ['KI', 'Manuell'],
                    datasets: [
                        {{ 
                            label: 'Muss-Kriterien (' + weights.muss + '%)', 
                            data: [aiContrib.muss, manContrib.muss], 
                            backgroundColor: '#2ecc71', 
                            barPercentage: 0.6,
                            stack: 'Stack 0'
                        }},
                        {{ 
                            label: 'Soll-Kriterien (' + weights.soll + '%)', 
                            data: [aiContrib.soll, manContrib.soll], 
                            backgroundColor: '#3498db', 
                            barPercentage: 0.6,
                            stack: 'Stack 0'
                        }},
                        {{ 
                            label: 'Skills & Weitere (' + weights.skill + '%)', 
                            data: [aiContrib.skill, manContrib.skill], 
                            backgroundColor: '#9b59b6', 
                            barPercentage: 0.6,
                            stack: 'Stack 0'
                        }}
                    ]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ stacked: true, max: 100, title: {{ display: true, text: 'Score Beitrag' }} }},
                        y: {{ stacked: true }}
                    }},
                    plugins: {{
                        legend: {{ position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + Math.round(context.raw) + ' Punkte';
                                }}
                            }}
                        }}
                    }}
                }}
            }});

            // 2. Criteria Comparison Chart (Bar)
            const ctxCriteria = document.getElementById('criteriaChart').getContext('2d');
            const criteriaChart = new Chart(ctxCriteria, {{
                type: 'bar',
                data: {{
                    labels: ['Muss-Kriterien', 'Soll-Kriterien', 'Soft Skills', 'Weitere'],
                    datasets: [
                        {{
                            label: 'KI Bewertung',
                            data: [aiScores.muss, aiScores.soll, aiScores.soft, aiScores.weitere],
                            backgroundColor: 'rgba(52, 152, 219, 0.7)',
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Manuelle Bewertung',
                            data: [aiScores.muss, aiScores.soll, aiScores.soft, aiScores.weitere], // Start same as AI
                            backgroundColor: 'rgba(46, 204, 113, 0.7)',
                            borderColor: 'rgba(46, 204, 113, 1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Erfüllungsgrad (%)' }} }}
                    }},
                    plugins: {{
                        legend: {{ position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + Math.round(context.raw) + '%';
                                }}
                            }}
                        }}
                    }}
                }}
            }});

            // --- Logic ---

            function updateManualScore() {{
                // 1. Gather data from DOM
                const selects = document.querySelectorAll('.manual-status');
                const counts = {{
                    muss: {{ ok: 0, pot: 0, total: 0 }},
                    soll: {{ ok: 0, pot: 0, total: 0 }},
                    soft: {{ ok: 0, pot: 0, total: 0 }},
                    weitere: {{ ok: 0, pot: 0, total: 0 }}
                }};

                selects.forEach(sel => {{
                    const cat = sel.getAttribute('data-category');
                    const val = sel.value;
                    
                    if (counts[cat]) {{
                        counts[cat].total++;
                        if (val === 'erfüllt') counts[cat].ok++;
                        else if (val === 'potenziell') counts[cat].pot++;
                    }}
                }});

                // 2. Calculate Category Scores
                const scores = {{
                    muss: calcCatScore(counts.muss.ok, counts.muss.pot, counts.muss.total),
                    soll: calcCatScore(counts.soll.ok, counts.soll.pot, counts.soll.total),
                    soft: calcCatScore(counts.soft.ok, counts.soft.pot, counts.soft.total),
                    weitere: calcCatScore(counts.weitere.ok, counts.weitere.pot, counts.weitere.total)
                }};

                // 3. Calculate Total Weighted Score
                // Formula: (Muss * w_muss + Soll * w_soll + (Soft+Weitere)/2 * w_skill) / 100
                
                const skillAvg = (scores.soft + scores.weitere) / 2 || 0;
                
                let totalScore = (scores.muss * weights.muss + scores.soll * weights.soll + skillAvg * weights.skill) / 100;
                totalScore = Math.round(totalScore);

                // 4. Update UI
                
                // Update Label
                document.getElementById('manualScoreValue').innerText = totalScore + '%';
                
                // Update Gauge Color
                let color = '#c0392b'; // red
                if (totalScore >= 80) color = '#27ae60'; // green
                else if (totalScore >= 60) color = '#f39c12'; // orange
                
                document.getElementById('manualScoreValue').style.color = color;
                
                // Calculate Contributions for Manual
                const manContrib = {{
                    muss: scores.muss * weights.muss / 100,
                    soll: scores.soll * weights.soll / 100,
                    skill: skillAvg * weights.skill / 100
                }};

                // Update Bar Chart (Index 1 is 'Manuell')
                scoreBarChart.data.datasets[0].data[1] = manContrib.muss;
                scoreBarChart.data.datasets[1].data[1] = manContrib.soll;
                scoreBarChart.data.datasets[2].data[1] = manContrib.skill;
                scoreBarChart.update();

                // Update Bar Chart
                criteriaChart.data.datasets[1].data = [scores.muss, scores.soll, scores.soft, scores.weitere];
                criteriaChart.update();
            }}

            function downloadJSON() {{
                const data = JSON.parse(JSON.stringify(matchData)); // Deep copy
                
                const categories = {{
                    'muss': 'muss_kriterien_abgleich',
                    'soll': 'soll_kriterien_abgleich',
                    'soft': 'soft_skills_abgleich',
                    'weitere': 'weitere_kriterien_abgleich'
                }};

                for (const [shortKey, jsonKey] of Object.entries(categories)) {{
                    const selects = document.querySelectorAll(`.manual-status[data-category="${{shortKey}}"]`);
                    selects.forEach(select => {{
                        const idx = select.getAttribute('data-index');
                        const status = select.value;
                        const commentInput = document.querySelector(`.manual-comment[data-category="${{shortKey}}"][data-index="${{idx}}"]`);
                        const comment = commentInput ? commentInput.value : "";

                        if (data[jsonKey] && data[jsonKey][idx]) {{
                            if (!data[jsonKey][idx].manuell) data[jsonKey][idx].manuell = {{}};
                            data[jsonKey][idx].manuell.status = status;
                            data[jsonKey][idx].manuell.kommentar = comment;
                        }}
                    }});
                }}
                
                // Trigger download
                const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
                const downloadAnchorNode = document.createElement('a');
                downloadAnchorNode.setAttribute("href", dataStr);
                downloadAnchorNode.setAttribute("download", "matchmaking.json");
                document.body.appendChild(downloadAnchorNode);
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
            }}
        </script>
        
        <!-- Modal for Score Explanation -->
        <div id="scoreInfoModal" class="modal">
          <div class="modal-content">
            <span class="close" onclick="document.getElementById('scoreInfoModal').style.display='none'">&times;</span>
            <h2 style="color: var(--primary-color); margin-top: 0;">Berechnung des Match Scores</h2>
            <p>Der Gesamt-Score (0-100%) basiert auf einer gewichteten Analyse der Anforderungen:</p>
            <ul>
                <li><strong>Muss-Kriterien ({w_muss}%):</strong> Essenzielle Anforderungen. Werden diese nicht erfüllt, sinkt der Score drastisch.</li>
                <li><strong>Soll-Kriterien ({w_soll}%):</strong> Wünschenswerte Qualifikationen, die den Kandidaten hervorheben.</li>
                <li><strong>Skill-Abdeckung ({w_skill}%):</strong> Übereinstimmung der technischen und fachlichen Fähigkeiten.</li>
            </ul>
            <p style="font-size: 13px; color: #666; border-top: 1px solid #eee; padding-top: 10px; margin-top: 15px;">
                <strong>Hinweis:</strong> Der Score wird durch ein KI-Modell ermittelt, das nicht nur Stichworte zählt, sondern auch den Kontext (z.B. Projekterfahrung, Seniorität) bewertet.
            </p>
          </div>
        </div>
        <script>
        // Close modal when clicking outside
        window.onclick = function(event) {{
          var modal = document.getElementById('scoreInfoModal');
          if (event.target == modal) {{
            modal.style.display = "none";
          }}
        }}
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
