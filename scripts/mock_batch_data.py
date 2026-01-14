"""
Mock data for Batch Comparison Mode testing
Creates realistic test CVs and a job profile for testing without API calls
"""

import os
import json
from io import BytesIO
from typing import List, Tuple


def create_mock_cv_json(name: str, vorname: str, match_score: int = 0) -> dict:
    """Create a mock CV JSON structure for testing"""
    return {
        "Vorname": vorname,
        "Nachname": name,
        "Nationalität": "Deutschland",
        "Hauptrolle": {
            "Titel": "Senior Software Engineer",
            "Beschreibung": "Erfahrener Entwickler mit Expertise in modernen Web-Technologien"
        },
        "Kurzprofil": f"{vorname} {name} ist ein erfahrener Software Engineer mit umfassender Erfahrung in der Softwareentwicklung.",
        "Ausbildung": [
            {
                "Abschluss": "Bachelor of Science",
                "Studiengang": "Informatik",
                "Institution": "Universität München",
                "Von": "09/2015",
                "Bis": "06/2018"
            }
        ],
        "Fachwissen_und_Schwerpunkte": [
            {
                "Kategorie": "Projektmethodik",
                "Skills": ["Agile", "Scrum", "Kanban"]
            },
            {
                "Kategorie": "Tech Stack",
                "Skills": ["Python", "JavaScript", "React", "Docker", "Kubernetes"]
            },
            {
                "Kategorie": "Weitere Fähigkeiten / Skills",
                "Skills": ["Cloud Architecture", "DevOps", "Microservices"]
            }
        ],
        "Aus_und_Weiterbildung": [
            {
                "Titel": "AWS Certified Solutions Architect",
                "Institution": "Amazon Web Services",
                "Von": "03/2021",
                "Bis": "03/2023"
            }
        ],
        "Trainings_und_Zertifizierungen": [
            {
                "Titel": "Docker Advanced Training",
                "Institution": "Linux Academy",
                "Von": "01/2022",
                "Bis": "03/2022"
            }
        ],
        "Sprachen": [
            {
                "Sprache": "Deutsch",
                "Level": 5
            },
            {
                "Sprache": "Englisch",
                "Level": 4
            }
        ],
        "Ausgewählte_Referenzprojekte": [
            {
                "Kundenname": "Tech Startup GmbH",
                "Zeitraum": "01/2021 - 12/2022",
                "Hauptrolle": {
                    "Titel": "Lead Developer",
                    "Beschreibung": "Leitung des Entwicklungsteams"
                },
                "Tätigkeiten": [
                    "Architektur und Design von Microservices-System",
                    "Migration zu Kubernetes-basierter Infrastruktur",
                    "Mentoring von Junior Entwicklern",
                    "Code Review und Qualitätssicherung",
                    "Performance-Optimierung der API"
                ],
                "Technologien_Methodologien": "Python, FastAPI, Kubernetes, PostgreSQL, Docker",
                "Ergebnis_Erfolg": "Reduktion der API-Latenz um 60%, Verbesserung der Deployment-Häufigkeit auf täglich"
            }
        ]
    }


def create_mock_job_profile_json() -> dict:
    """Create a mock job profile for testing"""
    return {
        "Jobtitle": "Senior Full Stack Engineer",
        "Unternehmen": "Acme Tech Solutions",
        "Kurzbeschreibung": "Wir suchen einen erfahrenen Full Stack Engineer für unser innovatives Team.",
        "Anforderungen": {
            "Muss": [
                "5+ Jahre Erfahrung in Software-Entwicklung",
                "Expertise in Python oder JavaScript",
                "AWS oder GCP Erfahrung",
                "Git und Versionskontrolle",
                "Englische Sprachkenntnisse auf Geschäftsniveau"
            ],
            "Soll": [
                "Erfahrung mit Kubernetes",
                "Microservices Architektur",
                "Agile/Scrum",
                "Machine Learning Grundlagen",
                "Deutschkenntnisse von Vorteil"
            ]
        },
        "Kernkompetenzen": [
            "Software Architecture",
            "Full Stack Development",
            "Cloud Infrastructure",
            "Team Leadership",
            "DevOps"
        ]
    }


def create_mock_batch_data() -> Tuple[List[dict], dict]:
    """
    Create realistic mock batch data with 3 candidate CVs and 1 job profile.
    Returns: (cv_list, job_profile)
    """
    candidates = [
        ("Schmidt", "Marco", 85),
        ("Mueller", "Sarah", 72),
        ("Weber", "Thomas", 65)
    ]
    
    cvs = [create_mock_cv_json(name, vorname, score) for name, vorname, score in candidates]
    job_profile = create_mock_job_profile_json()
    
    return cvs, job_profile


def get_mock_match_results(cv_vorname: str, cv_nachname: str) -> dict:
    """Generate mock match results for a CV"""
    base_score = hash(f"{cv_vorname}{cv_nachname}") % 40 + 60  # 60-99%
    
    return {
        "match_score": base_score,
        "Muss_coverage": min(100, base_score + 10),
        "Soll_coverage": max(0, base_score - 20),
        "critical_points": [
            "Strong cloud experience",
            "Leadership skills demonstrated",
            "Good cultural fit"
        ] if base_score > 75 else [
            "More Kubernetes experience needed",
            "Limited DevOps background"
        ]
    }


def save_mock_data_to_temp_files() -> Tuple[List[str], str, str]:
    """
    Save mock CVs and job profile to temporary JSON files for testing.
    Returns: (cv_json_paths, job_profile_json_path, batch_dir)
    """
    import tempfile
    import shutil
    
    # Create temp directory for mock data
    temp_dir = tempfile.mkdtemp(prefix="batch_mock_")
    
    cvs, job_profile = create_mock_batch_data()
    
    cv_paths = []
    for i, cv in enumerate(cvs):
        cv_path = os.path.join(temp_dir, f"mock_cv_{i+1}_{cv['Vorname']}_{cv['Nachname']}.json")
        with open(cv_path, 'w', encoding='utf-8') as f:
            json.dump(cv, f, ensure_ascii=False, indent=2)
        cv_paths.append(cv_path)
    
    job_profile_path = os.path.join(temp_dir, "mock_job_profile.json")
    with open(job_profile_path, 'w', encoding='utf-8') as f:
        json.dump(job_profile, f, ensure_ascii=False, indent=2)
    
    return cv_paths, job_profile_path, temp_dir
