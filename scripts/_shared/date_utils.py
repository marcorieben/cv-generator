"""
Date normalization utilities.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
import re


def normalize_date_format(date_str):
    """
    Konvertiert verschiedene Datumsformate zu MM/YYYY.

    Beispiele:
    - "2020" -> "01/2020"
    - "Jan 2020" -> "01/2020"
    - "Januar 2020" -> "01/2020"
    - "2020 - 2021" -> "01/2020 - 01/2021"
    - "heute" -> "heute" (unverändert)
    """
    if not date_str or not isinstance(date_str, str):
        return date_str

    if date_str.strip().lower() in ['heute', 'today', 'present', 'aktuell', "aujourd'hui", 'maintenant']:
        return date_str

    months_map = {
        'januar': '01', 'jan': '01', 'jan.': '01', 'january': '01', 'janvier': '01', 'janv': '01',
        'februar': '02', 'feb': '02', 'feb.': '02', 'february': '02', 'février': '02', 'fév': '02',
        'märz': '03', 'mrz': '03', 'mar': '03', 'mar.': '03', 'mär': '03', 'mär.': '03', 'march': '03', 'mars': '03',
        'april': '04', 'apr': '04', 'apr.': '04', 'avril': '04', 'avr': '04',
        'mai': '05', 'may': '05',
        'juni': '06', 'jun': '06', 'jun.': '06', 'june': '06', 'juin': '06',
        'juli': '07', 'jul': '07', 'jul.': '07', 'july': '07', 'juillet': '07', 'juil': '07',
        'august': '08', 'aug': '08', 'aug.': '08', 'août': '08',
        'september': '09', 'sep': '09', 'sep.': '09', 'sept': '09', 'sept.': '09', 'septembre': '09',
        'oktober': '10', 'okt': '10', 'okt.': '10', 'oct': '10', 'oct.': '10', 'october': '10', 'octobre': '10',
        'november': '11', 'nov': '11', 'nov.': '11', 'novembre': '11',
        'dezember': '12', 'dez': '12', 'dez.': '12', 'dec': '12', 'dec.': '12', 'december': '12', 'décembre': '12', 'déc': '12'
    }

    # Pattern: Ranges ("YYYY - YYYY")
    for sep in [' - ', ' – ', ' — ', '-']:
        if sep in date_str:
            parts = date_str.split(sep)
            if len(parts) == 2:
                def norm_part(p):
                    p = p.strip()
                    if p.lower() in ['heute', 'today', 'present', 'aktuell', "aujourd'hui", 'maintenant']:
                        return p
                    if re.match(r'^\d{4}$', p):
                        return f"01/{p}"
                    for m_name, m_num in months_map.items():
                        if m_name in p.lower():
                            year_match = re.search(r'\d{4}', p)
                            if year_match:
                                return f"{m_num}/{year_match.group(0)}"
                    return p

                return f"{norm_part(parts[0])} - {norm_part(parts[1])}"

    # Pattern: "MM/YYYY" oder "MM.YYYY"
    if re.match(r'^\d{2}[/\.]\d{4}$', date_str.strip()):
        return date_str.replace('.', '/')

    # Pattern: "YYYY" -> "01/YYYY"
    if re.match(r'^\d{4}$', date_str.strip()):
        return f"01/{date_str.strip()}"

    # Pattern: "Monat YYYY"
    parts = re.split(r'[\s.]+', date_str.lower().strip())
    parts = [p for p in parts if p]

    if len(parts) >= 2:
        month_part = parts[0].strip('.').lower()
        year_part = parts[-1]

        if month_part in months_map and re.match(r'^\d{4}$', year_part):
            return f"{months_map[month_part]}/{year_part}"

    return date_str
