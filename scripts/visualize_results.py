import os
import json
from datetime import datetime

def generate_dashboard(cv_json_path, match_json_path, feedback_json_path, output_dir):
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

    # Extract Key Info
    vorname = cv_data.get("Vorname", "")
    nachname = cv_data.get("Nachname", "")
    candidate_name = f"{vorname} {nachname}".strip()
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

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
                --primary-color: #2c3e50;
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
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
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
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>CV Analyse Dashboard</h1>
                    <div class="meta">Kandidat: <strong>{candidate_name}</strong> | Generiert: {timestamp}</div>
                </div>
                <div>
                    <a href="#" onclick="window.print()" style="text-decoration: none; color: var(--secondary-color); font-weight: bold;">🖨️ Drucken / PDF</a>
                </div>
            </header>
    """

    # --- MATCHING SECTION ---
    if match_data:
        score = match_data.get("match_score", {}).get("score_gesamt", 0)
        fazit = match_data.get("gesamt_fazit", {})
        empfehlung = fazit.get("empfehlung", "N/A")
        
        score_color = "var(--danger-color)"
        if score >= 80: score_color = "var(--success-color)"
        elif score >= 60: score_color = "var(--warning-color)"
        
        html_content += f"""
            <div class="grid">
                <div class="card">
                    <div class="card-header">Match Score</div>
                    <div class="score-display">
                        <div class="score-value" style="color: {score_color}">{score}%</div>
                        <div class="score-label">Gesamtübereinstimmung</div>
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
        
        for k in match_data.get("muss_kriterien_abgleich", []):
            status = k.get("bewertung", "").lower()
            icon = "✅" if "erfüllt" in status and "nicht" not in status else "❌"
            html_content += f"""
                <tr>
                    <td><strong>[MUSS]</strong> {k.get("kriterium", "")}</td>
                    <td>{icon} {k.get("bewertung", "")}</td>
                    <td>{k.get("cv_evidenz", "")}</td>
                </tr>
            """
            
        for k in match_data.get("soll_kriterien_abgleich", []):
            status = k.get("bewertung", "").lower()
            icon = "✅" if "erfüllt" in status and "nicht" not in status else "⚠️"
            html_content += f"""
                <tr>
                    <td><strong>[SOLL]</strong> {k.get("kriterium", "")}</td>
                    <td>{icon} {k.get("bewertung", "")}</td>
                    <td>{k.get("cv_evidenz", "")}</td>
                </tr>
            """
            
        html_content += """
                    </tbody>
                </table>
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
                
                <div class="card" style="grid-column: span 2;">
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
        muss_total = len(match_data.get("muss_kriterien_abgleich", []))
        muss_ok = sum(1 for k in match_data.get("muss_kriterien_abgleich", []) if "erfüllt" in k.get("bewertung", "").lower() and "nicht" not in k.get("bewertung", "").lower())
        
        soll_total = len(match_data.get("soll_kriterien_abgleich", []))
        soll_ok = sum(1 for k in match_data.get("soll_kriterien_abgleich", []) if "erfüllt" in k.get("bewertung", "").lower() and "nicht" not in k.get("bewertung", "").lower())

        html_content += f"""
        <script>
            const ctx = document.getElementById('criteriaChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: ['Muss-Kriterien', 'Soll-Kriterien'],
                    datasets: [
                        {{
                            label: 'Erfüllt',
                            data: [{muss_ok}, {soll_ok}],
                            backgroundColor: '#27ae60'
                        }},
                        {{
                            label: 'Nicht Erfüllt',
                            data: [{muss_total - muss_ok}, {soll_total - soll_ok}],
                            backgroundColor: '#e74c3c'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
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
