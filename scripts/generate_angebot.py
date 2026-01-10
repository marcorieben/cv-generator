import os
import json
from openai import OpenAI
from datetime import datetime

def abs_path(relative_path):
    """Gibt den absoluten Pfad relativ zum Skript-Verzeichnis zurück"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, relative_path)

def load_translations():
    """Lädt die Übersetzungen aus der translations.json Datei."""
    translations_path = abs_path("translations.json")
    if os.path.exists(translations_path):
        try:
            with open(translations_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def get_text(translations, section, key, lang="de"):
    """Holt einen übersetzten Text."""
    try:
        return translations.get(section, {}).get(key, {}).get(lang, f"[{key}]")
    except:
        return f"[{key}]"

def generate_angebot_json(cv_json_path, stellenprofil_json_path, match_json_path, output_path, schema_path=None, language='de'):
    """
    Generate an Offer (Angebot) JSON using the provided CV, Stellenprofil, and Match JSONs.
    """
    translations = load_translations()
    # Load schema
    if not schema_path:
        schema_path = abs_path("angebot_json_schema.json")
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Load input data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    with open(stellenprofil_json_path, 'r', encoding='utf-8') as f:
        stellenprofil_data = json.load(f)
        
    match_data = None
    if match_json_path and os.path.exists(match_json_path):
        with open(match_json_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)

    # 1. Initialize result from schema
    angebot_json = {}
    
    # 2. Programmatically fill criteria to save tokens and time
    # This prevents the LLM from having to repeat large amounts of data
    abgleich = {
        "muss_kriterien": [],
        "soll_kriterien": [],
        "weitere_kriterien": [],
        "soft_skills": []
    }
    
    if match_data:
        # Muss-Kriterien
        for item in match_data.get("muss_kriterien_abgleich", []):
            # Combine evidence and comment for the Word document
            raw_evidenz = item.get("cv_evidenz", "")
            raw_kommentar = item.get("kommentar", "")
            combined_begruendung = raw_evidenz
            if raw_kommentar and raw_kommentar != raw_evidenz:
                combined_begruendung += f" ({raw_kommentar})"
            
            abgleich["muss_kriterien"].append({
                "kriterium": item.get("kriterium", ""),
                "erfuellt": item.get("bewertung", ""),
                "begruendung": combined_begruendung.strip()
            })
        # Soll-Kriterien
        for item in match_data.get("soll_kriterien_abgleich", []):
            raw_evidenz = item.get("cv_evidenz", "")
            raw_kommentar = item.get("kommentar", "")
            combined_begruendung = raw_evidenz
            if raw_kommentar and raw_kommentar != raw_evidenz:
                combined_begruendung += f" ({raw_kommentar})"
                
            abgleich["soll_kriterien"].append({
                "kriterium": item.get("kriterium", ""),
                "erfuellt": item.get("bewertung", ""),
                "begruendung": combined_begruendung.strip()
            })
        # Weitere Kriterien
        for item in match_data.get("weitere_kriterien_abgleich", []):
            raw_evidenz = item.get("cv_evidenz", "")
            raw_kommentar = item.get("kommentar", "")
            combined_begruendung = raw_evidenz
            if raw_kommentar and raw_kommentar != raw_evidenz:
                combined_begruendung += f" ({raw_kommentar})"

            abgleich["weitere_kriterien"].append({
                "kriterium": item.get("kriterium", ""),
                "erfuellt": item.get("bewertung", ""),
                "begruendung": combined_begruendung.strip()
            })
        # Soft Skills
        for item in match_data.get("soft_skills_abgleich", []):
            raw_evidenz = item.get("cv_evidenz", "")
            raw_kommentar = item.get("kommentar", "")
            combined_begruendung = raw_evidenz
            if raw_kommentar and raw_kommentar != raw_evidenz:
                combined_begruendung += f" ({raw_kommentar})"

            abgleich["soft_skills"].append({
                "kriterium": item.get("kriterium", ""),
                "erfuellt": item.get("bewertung", ""),
                "begruendung": combined_begruendung.strip()
            })

    # Prepare reduced context for LLM
    # We only send what's needed for the qualitative sections
    # Include explicit matches for deep qualitative analysis
    top_matches = []
    if match_data:
        # Get top Muss-Kriterien that are fulfilled
        for m in match_data.get("muss_kriterien_abgleich", []):
            if "erfüllt" in m.get("bewertung", "").lower():
                top_matches.append(f"Muss: {m.get('kriterium')} -> {m.get('kommentar') or m.get('cv_evidenz')}")
        # Get top Soll-Kriterien that are fulfilled
        for s in match_data.get("soll_kriterien_abgleich", []):
            if "erfüllt" in s.get("bewertung", "").lower():
                top_matches.append(f"Soll: {s.get('kriterium')} -> {s.get('kommentar') or s.get('cv_evidenz')}")

    # Extract hints from schema for prompt injection
    def get_hints(obj, prefix="_hint_"):
        hints = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.startswith(prefix):
                    hints[k[len(prefix):]] = v
                elif isinstance(v, (dict, list)):
                    nested = get_hints(v, prefix)
                    if nested: hints[k] = nested
        return hints
    
    schema_hints = get_hints(schema)

    llm_context = {
        "kandidat": {
            "name": f"{cv_data.get('Vorname', '')} {cv_data.get('Nachname', '')}",
            "hauptrolle": cv_data.get("Hauptrolle", {}).get("Titel", ""),
            "kurzprofil": cv_data.get("Kurzprofil", ""),
            "starke_skills": match_data.get("skill_abdeckung", {}).get("starke_skills", []) if match_data else []
        },
        "stelle": {
            "titel": stellenprofil_data.get("rolle", {}).get("titel", ""),
            "kunde": stellenprofil_data.get("projekt_kontext", {}).get("auftraggeber", ""),
            "organisation": stellenprofil_data.get("projekt_kontext", {}).get("organisationseinheit", ""),
            "aufgaben": stellenprofil_data.get("rolle", {}).get("aufgaben", [])[:5] if isinstance(stellenprofil_data.get("rolle", {}).get("aufgaben"), list) else []
        },
        "gefundene_top_matches": top_matches[:10], # Send top 10 matches for deep analysis
        "match": {
            "score": match_data.get("match_score", {}).get("score_gesamt", 0) if match_data else 0,
            "fazit": match_data.get("gesamt_fazit", {}).get("kurzbegruendung", "") if match_data else ""
        },
        "ausgabesprache": language
    }

    # Select language name for the prompt
    lang_map = {
        "de": "Deutsch",
        "en": "Englisch",
        "fr": "Französisch"
    }
    lang_name = lang_map.get(language, "Deutsch")

    system_prompt = (
        f"Du bist ein Experte für die Erstellung von professionellen IT-Dienstleistungsangeboten in **{lang_name}**. "
        f"Erstelle die qualitativen Abschnitte eines Angebots basierend auf dem bereitgestellten Kontext in **{lang_name}**.\n\n"
        "WICHTIGE REGELN:\n"
        f"1. SPRACHE: Generiere alle Texte (Werte im JSON) konsequent in **{lang_name}**.\n"
        "2. TONALITÄT: Professionell, empathisch, überzeugend. Falls die Ausgabe in Deutsch erfolgt: Nutze Schweizer Rechtschreibung (ss statt ß).\n"
        "3. WIR-FORM: Verwende konsequent die 'Wir-Form' (Wir als Orange Business), niemals die 'Ich-Form'.\n"
        "4. STRIKT POSITIV: Alle Kriterien gelten als erfüllt. Weise NIEMALS auf Lücken, fehlende Erfahrung oder Defizite hin (NICHT: 'Trotz fehlender...', 'Obwohl XY nicht...'). Formuliere ausschliesslich Stärken und Übereinstimmungen.\n"
        "5. MEHRWERT: Fasse den Mehrwert in **genau 3-5 aussagekräftigen Aufzählungspunkten** zusammen. Jeder Punkt muss ein vollständiger, überzeugender Satz sein, der die Kompetenz des Kandidaten direkt mit dem Nutzen für den Kunden verknüpft. Vermeide abgehackte Sätze oder rein technische Aufzählungen.\n"
        "6. STRUKTUR: Gib ein JSON-Objekt mit exakt diesen Feldern zurück. Beachte dabei unbedingt die HINWEISE (Hints) für jedes Feld:\n"
    )

    # Inject hints into system prompt
    prompt_hints = {
        "kurzkontext": schema_hints.get("stellenbezug", {}).get("kurzkontext", "Persönliche Einleitung."),
        "eignungs_summary": schema_hints.get("kandidatenvorschlag", {}).get("eignungs_summary", "Zusammenfassung der Eignung."),
        "methoden_technologien": schema_hints.get("profil_und_kompetenzen", {}).get("methoden_und_technologien", "Relevante Skills."),
        "erfahrung_ops_führung": schema_hints.get("profil_und_kompetenzen", {}).get("operative_und_fuehrungserfahrung", "Erfahrung in Betrieb/Führung."),
        "zusammenfassung": schema_hints.get("gesamtbeurteilung", {}).get("zusammenfassung", "Detaillierte Argumentation."),
        "mehrwert": schema_hints.get("gesamtbeurteilung", {}).get("mehrwert_fuer_kunden", "Impact-Punkte."),
        "empfehlung": schema_hints.get("gesamtbeurteilung", {}).get("empfehlung", "Kurze Empfehlung."),
        "verfuegbarkeit_gespraech": schema_hints.get("abschluss", {}).get("verfuegbarkeit_gespraech", "Gesprächsbereitschaft."),
        "kontakt_hinweis": schema_hints.get("abschluss", {}).get("kontakt_hinweis", "Rückmeldung.")
    }

    for field, hint in prompt_hints.items():
        system_prompt += f"   - '{field}': {hint}\n"
    
    system_prompt += "\nWICHTIG: Nutze für Schlagworte, Technologien und wichtige Begriffe konsequent **Fettschrift**. Besonders im 'kurzkontext' sollen der Kundenname, die Rolle und 2-3 Kernkompetenzen fett markiert werden.\n"
    
    user_prompt = f"Kontext für die Angebotserstellung:\n{json.dumps(llm_context, ensure_ascii=False, indent=2)}"

    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    
    if model_name == "mock":
        # ... keep mock logic if needed ...
        llm_response = {
            "kurzkontext": f"Wir freuen uns, den {llm_context['stelle']['kunde']} ein qualifiziertes Angebot als **{llm_context['stelle']['titel']}** zu unterbreiten...",
            "eignungs_summary": f"Der vorgeschlagene Experte {llm_context['kandidat']['name']} erfüllt alle Anforderungen...",
            "methoden_technologien": llm_context['kandidat']['starke_skills'][:5],
            "erfahrung_ops_führung": ["Langjährige operative Erfahrung", "Projektführung"],
            "zusammenfassung": "Ein hervorragender Kandidat mit passgenauem Profil.",
            "mehrwert": ["Schneller Start möglich", "Hohe Fachkompetenz in **Cloud**"],
            "empfehlung": f"Wir empfehlen, {llm_context['kandidat']['name'].split(' ')[0]} einzuladen."
        }
    else:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        llm_response = json.loads(response.choices[0].message.content)

    # Post-process LLM response to ensure list fields are actually lists
    # This prevents the "each letter on a new line" bug in the dashboard
    def ensure_list(val):
        original_list = []
        if isinstance(val, list):
            original_list = val
        elif isinstance(val, str):
            # Split by bullet points or newlines if it's a long string
            if "\n" in val:
                original_list = [p.strip() for p in val.split("\n") if p.strip()]
            else:
                original_list = [val]
        else:
            return []

        # Fix fragmented lists (e.g. if LLM splits sentence at comma or bolding)
        fixed_list = []
        for item in original_list:
            item = item.strip()
            if not item: continue
            
            # If item starts with a comma or is a continuation (lowercase and not a bullet)
            # and we already have items, append it to the last one.
            if fixed_list and (item.startswith(",") or item.startswith(".") or (item[0].islower() and not item.startswith("http"))):
                if item.startswith(",") or item.startswith("."):
                    fixed_list[-1] = f"{fixed_list[-1]}{item}"
                else:
                    fixed_list[-1] = f"{fixed_list[-1]} {item}"
            else:
                fixed_list.append(item)
        
        return fixed_list

    # 4. Final Assembly
    check_marker = translations.get("system", {}).get("missing_data_marker", {}).get(language, "! bitte prüfen !")
    acc_manager_label = translations.get("offer", {}).get("account_manager", {}).get(language, "Account Manager")
    
    angebot_json = {
        "angebots_metadata": {
            "angebots_id": stellenprofil_data.get("metadata", {}).get("document_id", check_marker),
            "anbieter": "Orange Business",
            "kunde": llm_context["stelle"]["kunde"],
            "datum": datetime.now().strftime("%d.%m.%Y"),
            "ansprechpartner": {
                "name": check_marker,
                "rolle": acc_manager_label,
                "kontakt": check_marker
            }
        },
        "stellenbezug": {
            "rollenbezeichnung": llm_context["stelle"]["titel"],
            "organisationseinheit": llm_context["stelle"]["organisation"],
            "kurzkontext": llm_response.get("kurzkontext", "")
        },
        "kandidatenvorschlag": {
            "name": llm_context["kandidat"]["name"],
            "angebotene_rolle": llm_context["kandidat"]["hauptrolle"],
            "eignungs_summary": llm_response.get("eignungs_summary", "")
        },
        "profil_und_kompetenzen": {
            "methoden_und_technologien": ensure_list(llm_response.get("methoden_technologien", [])),
            "operative_und_fuehrungserfahrung": ensure_list(llm_response.get("erfahrung_ops_führung", [])),
            "sprachen": [
                {
                    "sprache": s.get("Sprache", ""),
                    "level": get_text(translations, 'levels', f"level_{s.get('Level', 0)}", language) if s.get("Level") else ""
                } for s in cv_data.get("Sprachen", [])
            ]
        },
        "einsatzkonditionen": {
            "pensum": stellenprofil_data.get("einsatzrahmen", {}).get("pensum", "100%"),
            "verfuegbarkeit": stellenprofil_data.get("einsatzrahmen", {}).get("zeitraum", {}).get("start", translations.get("offer", {}).get("asap", {}).get(language, "ab sofort")),
            "stundensatz": "165.00 CHF (exkl. MWST)",
            "subunternehmen": translations.get("offer", {}).get("no", {}).get(language, "Nein")
        },
        "kriterien_abgleich": abgleich,
        "gesamtbeurteilung": {
            "zusammenfassung": llm_response.get("zusammenfassung", ""),
            "mehrwert_fuer_kunden": ensure_list(llm_response.get("mehrwert", [])),
            "empfehlung": llm_response.get("empfehlung", "")
        },
        "abschluss": {
            "verfuegbarkeit_gespraech": llm_response.get("verfuegbarkeit_gespraech", translations.get("offer", {}).get("appointment_ready", {}).get(language, "Nach Absprache kurzfristig möglich.")),
            "kontakt_hinweis": llm_response.get("kontakt_hinweis", translations.get("offer", {}).get("feedback_welcome", {}).get(language, "Wir freuen uns auf Ihre Rückmeldung."))
        }
    }

    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(angebot_json, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Angebot JSON generiert (optimiert): {output_path}")
    return output_path
