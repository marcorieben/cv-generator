import os
import json
from openai import OpenAI
from datetime import datetime

def generate_angebot_json(cv_json_path, stellenprofil_json_path, match_json_path, output_path, schema_path):
    """
    Generate an Offer (Angebot) JSON using the provided CV, Stellenprofil, and Match JSONs.
    """
    # Load schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Load input data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    with open(stellenprofil_json_path, 'r', encoding='utf-8') as f:
        stellenprofil_data = json.load(f)
        
    match_data = None
    if os.path.exists(match_json_path):
        with open(match_json_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)

    # Prepare prompt for OpenAI
    system_prompt = (
        "Du bist ein Experte für die Erstellung von professionellen IT-Dienstleistungsangeboten. "
        "Erstelle ein strukturiertes Angebot basierend auf dem Stellenprofil, dem Kandidaten-CV und dem Matching-Ergebnis. "
        "Halte dich strikt an das vorgegebene JSON-Schema. "
        "Erfinde keine Fakten, sondern leite alles aus den Eingabedaten ab. "
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )
    
    user_prompt = (
        "Stellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2) +
        "\n\nCV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )
    
    if match_data:
        user_prompt += "\n\nMatching Ergebnis JSON:\n" + json.dumps(match_data, ensure_ascii=False, indent=2)

    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    
    if model_name == "mock":
        print("🧪 TEST-MODUS (Angebot): Verwende Mock-Daten")
        # Create a mock offer based on the schema structure
        angebot_json = {
            "angebots_metadata": {
                "angebots_id": "OFFER-2025-001",
                "anbieter": "Ihre Firma AG",
                "kunde": "Bundesamt für Informatik und Telekommunikation BIT",
                "datum": datetime.now().strftime("%d.%m.%Y"),
                "ansprechpartner": {
                    "name": "Hans Muster",
                    "rolle": "Key Account Manager",
                    "kontakt": "hans.muster@ihrefirma.ch | +41 79 123 45 67"
                }
            },
            "stellenbezug": {
                "rollenbezeichnung": "Senior Software Engineer (Java/Spring)",
                "organisationseinheit": "Abteilung Entwicklung",
                "kurzkontext": "Unterstützung bei der Modernisierung der Fachanwendung 'SuperApp' im Rahmen des Programms 'Digitalisierung 2025'."
            },
            "kandidatenvorschlag": {
                "name": "Marco Rieben",
                "angebotene_rolle": "Senior Software Engineer & Architect",
                "eignungs_summary": "Marco Rieben ist ein erfahrener Software Engineer mit über 10 Jahren Erfahrung in der Entwicklung komplexer Enterprise-Anwendungen. Er verfügt über tiefgehende Expertise im geforderten Tech-Stack (Java, Spring Boot, Angular) und hat in ähnlichen Projekten beim Bund (z.B. Projekt 'Phoenix') bereits erfolgreich Architekturen modernisiert. Seine Stärke liegt in der Verbindung von technischer Exzellenz mit methodischer Kompetenz (Scrum, SAFe)."
            },
            "profil_und_kompetenzen": {
                "methoden_und_technologien": [
                    "Java / JEE (Expert Level, >10 Jahre)",
                    "Spring Boot / Spring Cloud (Expert Level)",
                    "Angular / TypeScript (Advanced Level)",
                    "Docker / Kubernetes / OpenShift",
                    "CI/CD (Jenkins, GitLab CI)",
                    "Datenbanken (PostgreSQL, Oracle)"
                ],
                "operative_und_fuehrungserfahrung": [
                    "Langjährige Erfahrung als Lead Developer in agilen Teams",
                    "Erfahrung in der technischen Projektleitung",
                    "Coaching von Junior-Entwicklern",
                    "Anforderungsanalyse und Solution Design in enger Zusammenarbeit mit dem Fachbereich"
                ]
            },
            "einsatzkonditionen": {
                "pensum": "80-100%",
                "verfuegbarkeit": "ab 01.02.2026",
                "stundensatz": "165.00 CHF (exkl. MWST)",
                "subunternehmen": "Nein, direkter Mitarbeiter"
            },
            "kriterien_abgleich": {
                "muss_kriterien": [
                    {"kriterium": "Hochschulabschluss in Informatik oder vergleichbar", "erfuellt": True, "begruendung": "Master of Science in Computer Science, ETH Zürich (2015)"},
                    {"kriterium": "Mind. 5 Jahre Erfahrung mit Java/Spring", "erfuellt": True, "begruendung": "Über 8 Jahre nachgewiesene Projekterfahrung mit Java Enterprise und Spring Framework."},
                    {"kriterium": "Erfahrung mit Container-Technologien", "erfuellt": True, "begruendung": "Einsatz von Docker und OpenShift in den letzten 3 Projekten."}
                ],
                "soll_kriterien": [
                    {"kriterium": "Erfahrung im öffentlichen Sektor", "erfuellt": True, "begruendung": "Diverse Mandate beim BIT und BAZG."},
                    {"kriterium": "Zertifizierung in SAFe", "erfuellt": True, "begruendung": "SAFe 5 Architect Zertifizierung vorhanden."},
                    {"kriterium": "Französischkenntnisse", "erfuellt": False, "begruendung": "Grundkenntnisse vorhanden, Projektsprache Deutsch bevorzugt."}
                ]
            },
            "gesamtbeurteilung": {
                "zusammenfassung": "Marco Rieben erfüllt alle Muss-Kriterien und die meisten Soll-Kriterien in hohem Masse. Durch seine Kombination aus technischer Tiefe und Verständnis für behördliche Prozesse ist er die ideale Besetzung für diese Schlüsselposition.",
                "mehrwert_fuer_kunden": [
                    "Sofortige Produktivität durch bekannten Tech-Stack",
                    "Risikominimierung durch Erfahrung im Bundesumfeld",
                    "Wissenstransfer ins interne Team durch Coaching-Erfahrung",
                    "Pragmatische und lösungsorientierte Arbeitsweise"
                ],
                "empfehlung": "Aufgrund der hohen Übereinstimmung mit dem Anforderungsprofil und der nachgewiesenen Erfolgsbilanz empfehlen wir Marco Rieben ausdrücklich für diese Position."
            },
            "abschluss": {
                "verfuegbarkeit_gespraech": "Für ein Vorstellungsgespräch steht Herr Rieben ab sofort zur Verfügung (bevorzugt Di/Do).",
                "kontakt_hinweis": "Wir freuen uns auf Ihre Rückmeldung und stehen für Rückfragen jederzeit gerne zur Verfügung."
            }
        }
    else:
        client = OpenAI()
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            angebot_json = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Fehler bei der Angebots-Generierung: {e}")
            raise e

    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(angebot_json, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Angebot JSON generiert: {output_path}")
    return output_path
