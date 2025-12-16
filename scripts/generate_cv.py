import json
import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from tkinter import Tk, filedialog, Toplevel, Label, Button, CENTER

# Globale Konstante für fehlende Daten
MISSING_DATA_MARKER = "! bitte prüfen !"

# -------------------------------------
# Hilfsfunktion: Absoluten Pfad bilden
# -------------------------------------
def validate_json_structure(data):
    """Validiert die Struktur der JSON-Daten und gibt kritische Fehler und Info zurück"""
    critical = []
    info = []
    
    # Erforderliche Top-Level-Felder
    required_fields = [
        "Vorname", "Nachname", "Hauptrolle", "Nationalität", "Hauptausbildung",
        "Kurzprofil", "Fachwissen_und_Schwerpunkte", "Aus_und_Weiterbildung",
        "Trainings_und_Zertifizierungen", "Sprachen", "Ausgewählte_Referenzprojekte"
    ]
    
    # Prüfe Arrays
    array_fields = [
        "Fachwissen_und_Schwerpunkte", "Aus_und_Weiterbildung",
        "Trainings_und_Zertifizierungen", "Sprachen", "Ausgewählte_Referenzprojekte"
    ]
    
    for field in required_fields:
        if field not in data:
            critical.append(f"Fehlendes Feld: {field}")
        elif data[field] is None:
            critical.append(f"Feld ist None: {field}")
        else:
            # Typ-Prüfungen
            if field == "Hauptrolle":
                if not isinstance(data[field], dict) or "Titel" not in data[field] or "Beschreibung" not in data[field]:
                    critical.append(f"Feld 'Hauptrolle' muss ein Objekt mit 'Titel' und 'Beschreibung' sein")
                else:
                    beschreibung = data[field]["Beschreibung"]
                    word_count = len(beschreibung.split())
                    if word_count < 5 or word_count > 10:
                        info.append(f"Hauptrolle.Beschreibung sollte 5-10 Wörter haben (aktuell {word_count})")
            elif field in ["Vorname", "Nachname", "Nationalität", "Hauptausbildung", "Kurzprofil"]:
                if not isinstance(data[field], str):
                    info.append(f"Feld '{field}' sollte ein String sein (ist {type(data[field]).__name__})")
            elif field in array_fields:
                if not isinstance(data[field], list):
                    critical.append(f"Feld '{field}' muss ein Array sein")
    
    # Entferne die doppelte Definition
    # array_fields = [...
    
    # Prüfe Fachwissen_und_Schwerpunkte Struktur
    if "Fachwissen_und_Schwerpunkte" in data and isinstance(data["Fachwissen_und_Schwerpunkte"], list):
        for i, item in enumerate(data["Fachwissen_und_Schwerpunkte"]):
            if not isinstance(item, dict):
                critical.append(f"Fachwissen_und_Schwerpunkte[{i}]: Muss ein Objekt sein")
                continue
            if "Kategorie" not in item:
                critical.append(f"Fachwissen_und_Schwerpunkte[{i}]: Fehlendes Feld 'Kategorie'")
            if "Inhalt" not in item or not isinstance(item["Inhalt"], list):
                critical.append(f"Fachwissen_und_Schwerpunkte[{i}]: 'Inhalt' muss ein Array sein")
    
    # Prüfe Aus_und_Weiterbildung Struktur
    if "Aus_und_Weiterbildung" in data and isinstance(data["Aus_und_Weiterbildung"], list):
        for i, item in enumerate(data["Aus_und_Weiterbildung"]):
            if not isinstance(item, dict):
                critical.append(f"Aus_und_Weiterbildung[{i}]: Muss ein Objekt sein")
                continue
            required = ["Zeitraum", "Institution", "Abschluss"]
            for req in required:
                if req not in item:
                    critical.append(f"Aus_und_Weiterbildung[{i}]: Fehlendes Feld '{req}'")
    
    # Prüfe Trainings_und_Zertifizierungen Struktur
    if "Trainings_und_Zertifizierungen" in data and isinstance(data["Trainings_und_Zertifizierungen"], list):
        for i, item in enumerate(data["Trainings_und_Zertifizierungen"]):
            if not isinstance(item, dict):
                critical.append(f"Trainings_und_Zertifizierungen[{i}]: Muss ein Objekt sein")
                continue
            required = ["Zeitraum", "Institution", "Titel"]
            for req in required:
                if req not in item:
                    critical.append(f"Trainings_und_Zertifizierungen[{i}]: Fehlendes Feld '{req}'")
    
    # Prüfe Sprachen Struktur
    if "Sprachen" in data and isinstance(data["Sprachen"], list):
        for i, item in enumerate(data["Sprachen"]):
            if not isinstance(item, dict):
                critical.append(f"Sprachen[{i}]: Muss ein Objekt sein")
                continue
            if "Sprache" not in item:
                critical.append(f"Sprachen[{i}]: Fehlendes Feld 'Sprache'")
            if "Level" not in item or not is_valid_level(item["Level"]):
                info.append(f"Sprachen[{i}]: Ungültiges oder fehlendes Feld 'Level' (muss eine Zahl 1-5, Text wie 'Muttersprache' oder Kombination sein)")
    
    # Prüfe Referenzprojekte Struktur
    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], list):
        for i, item in enumerate(data["Ausgewählte_Referenzprojekte"]):
            if not isinstance(item, dict):
                critical.append(f"Ausgewählte_Referenzprojekte[{i}]: Muss ein Objekt sein")
                continue
            required = ["Zeitraum", "Rolle", "Kunde", "Tätigkeiten"]
            for req in required:
                if req not in item:
                    critical.append(f"Ausgewählte_Referenzprojekte[{i}]: Fehlendes Feld '{req}'")
            if "Tätigkeiten" in item and not isinstance(item["Tätigkeiten"], list):
                critical.append(f"Ausgewählte_Referenzprojekte[{i}]: 'Tätigkeiten' muss ein Array sein")
    
    return critical, info


def parse_level(level):
    """Parst das Level zu einer Zahl 1-5"""
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        import re
        level = level.strip()
        # Versuche Zahl am Anfang
        match = re.match(r'(\d+)', level)
        if match:
            return int(match.group(1))
        # Mappe Text
        text_to_num = {
            "Muttersprache": 5,
            "Verhandlungssicher": 4,
            "Sehr gute Kenntnisse": 3,
            "Gute Kenntnisse": 2,
            "Grundkenntnisse": 1
        }
        return text_to_num.get(level, 0)
    return 0


def is_valid_level(level):
    """Prüft, ob das Level gültig ist"""
    if isinstance(level, int) and 1 <= level <= 5:
        return True
    if isinstance(level, str):
        import re
        level = level.strip()
        if level in ["Muttersprache", "Verhandlungssicher", "Sehr gute Kenntnisse", "Gute Kenntnisse", "Grundkenntnisse"]:
            return True
        if re.match(r'^\d+', level):
            num = int(re.match(r'^\d+', level).group())
            return 1 <= num <= 5
    return False


def abs_path(relative_path):
    """Gibt den absoluten Pfad relativ zum Skript-Verzeichnis zurück"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, relative_path)


# -------------------------------------
# Stil-Funktionen für Formatierung
# -------------------------------------


# Styles aus JSON laden
def load_styles(filename="styles.json"):
    path = abs_path(filename)
    with open(path, "r", encoding="utf-8") as sf:
        return json.load(sf)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    s = styles["heading1"]
    run.font.name = s["font"]
    run.font.size = Pt(s["size"])
    run.font.bold = s["bold"]
    c = s["color"]
    run.font.color.rgb = RGBColor(c[0], c[1], c[2])
    return p


def add_heading_2(doc, text, bold=None):
    p = doc.add_paragraph()
    s = styles["heading2"]
    p.paragraph_format.space_before = Pt(s["space_before"])
    p.paragraph_format.space_after = Pt(s["space_after"])

    run = p.add_run(text)
    run.font.name = s["font"]
    run.font.size = Pt(s["size"])
    run.font.bold = bold if bold is not None else s["bold"]
    c = s["color"]
    run.font.color.rgb = RGBColor(c[0], c[1], c[2])
    return p


def add_normal_text(doc, text):
    p = doc.add_paragraph()
    s = styles["text"]
    add_text_with_highlight(p, text, s["font"], s["size"], s["color"])
    return p


def add_text_with_highlight(paragraph, text, font_name, font_size, font_color, bold=False):
    """Helper function to add text (highlighting wird am Ende global durchgeführt)"""
    run = paragraph.add_run(text)
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(*font_color) if isinstance(font_color, (list, tuple)) else font_color
    if bold:
        run.font.bold = True


def highlight_missing_data_in_document(doc):
    """
    Durchsucht das gesamte Dokument nach verschiedenen Varianten des Fehlenden-Daten-Markers,
    normalisiert sie auf die einheitliche Version und hebt alle Vorkommen gelb hervor.
    """
    from docx.enum.text import WD_COLOR_INDEX
    
    # Alle möglichen Varianten des Markers (OpenAI verwendet oft andere Bindestriche/Leerzeichen)
    marker_variants = [
        "! bitte prüfen!",           # Ohne Leerzeichen vor !
        "! bitte prüfen !",          # Mit Leerzeichen vor ! (unser Standard)
        "! fehlt – bitte prüfen!",   # Alt: Gedankenstrich ohne Leerzeichen vor !
        "! fehlt – bitte prüfen !",  # Alt: Gedankenstrich mit Leerzeichen vor !
        "! fehlt - bitte prüfen!",   # Alt: Normaler Bindestrich ohne Leerzeichen vor !
        "! fehlt - bitte prüfen !",  # Alt: Normaler Bindestrich mit Leerzeichen vor !
        "! fehlt — bitte prüfen!",   # Alt: Em-Dash ohne Leerzeichen vor !
        "! fehlt — bitte prüfen !",  # Alt: Em-Dash mit Leerzeichen vor !
    ]
    
    # Durchsuche alle Paragraphen im Hauptdokument
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            # Prüfe alle Varianten
            found_variant = None
            for variant in marker_variants:
                if variant in run.text:
                    found_variant = variant
                    break
            
            if found_variant:
                # Split den Run-Text am gefundenen Marker
                parts = run.text.split(found_variant)
                
                # Lösche den aktuellen Run-Text
                run.text = ""
                
                # Füge Teile und normalisierte Marker hinzu
                for i, part in enumerate(parts):
                    if i > 0:
                        # Füge neuen Run mit normalisiertem Marker und Highlighting hinzu
                        new_run = paragraph.add_run(MISSING_DATA_MARKER)
                        new_run.font.name = run.font.name
                        new_run.font.size = run.font.size
                        new_run.font.color.rgb = run.font.color.rgb
                        new_run.font.bold = run.font.bold
                        new_run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                    
                    if part:
                        # Füge Text-Teil hinzu
                        text_run = paragraph.add_run(part)
                        text_run.font.name = run.font.name
                        text_run.font.size = run.font.size
                        text_run.font.color.rgb = run.font.color.rgb
                        text_run.font.bold = run.font.bold
    
    # Durchsuche auch Tabellen
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        # Prüfe alle Varianten
                        found_variant = None
                        for variant in marker_variants:
                            if variant in run.text:
                                found_variant = variant
                                break
                        
                        if found_variant:
                            parts = run.text.split(found_variant)
                            run.text = ""
                            
                            for i, part in enumerate(parts):
                                if i > 0:
                                    new_run = paragraph.add_run(MISSING_DATA_MARKER)
                                    new_run.font.name = run.font.name
                                    new_run.font.size = run.font.size
                                    new_run.font.color.rgb = run.font.color.rgb
                                    new_run.font.bold = run.font.bold
                                    new_run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                                
                                if part:
                                    text_run = paragraph.add_run(part)
                                    text_run.font.name = run.font.name
                                    text_run.font.size = run.font.size
                                    text_run.font.color.rgb = run.font.color.rgb
                                    text_run.font.bold = run.font.bold

                                    text_run.font.bold = run.font.bold


def add_bullet_item(doc, text):
    s = styles["bullet"]
    s_text = styles["text"]
    
    # Erstelle Absatz mit List Bullet Style
    p = doc.add_paragraph(style='List Bullet')
    
    # Wende Formatierung aus styles.json an
    p.paragraph_format.left_indent = Pt(s["indent"])
    p.paragraph_format.space_before = Pt(s["space_before"])
    p.paragraph_format.space_after = Pt(s["space_after"])
    p.paragraph_format.line_spacing = s["line_spacing"]
    
    # Hanging indent: Text-Zeilen rücken ein, erste Zeile (mit Symbol) nicht
    if "hanging_indent" in s:
        hanging = s["hanging_indent"]
        p.paragraph_format.left_indent = Pt(hanging)
        p.paragraph_format.first_line_indent = Pt(-hanging)
    
    # Konfiguriere das Bullet-Zeichen auf "■" mit Farbe aus styles.json
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    
    pPr = p._element.get_or_add_pPr()
    
    # Numbering-Eigenschaften für custom bullet
    numPr = pPr.find(qn('w:numPr'))
    if numPr is None:
        numPr = OxmlElement('w:numPr')
        pPr.append(numPr)
        
        # Level setzen (0 = erste Ebene)
        ilvl = OxmlElement('w:ilvl')
        ilvl.set(qn('w:val'), '0')
        numPr.append(ilvl)
    
    # Run-Properties für das Bullet-Symbol erstellen
    rPr = OxmlElement('w:rPr')
    
    # Font für Bullet-Symbol
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), s["font"])
    rFonts.set(qn('w:hAnsi'), s["font"])
    rPr.append(rFonts)
    
    # Farbe für Bullet-Symbol aus styles.json
    color = OxmlElement('w:color')
    bullet_color = s["color"]
    color_hex = '%02x%02x%02x' % (bullet_color[0], bullet_color[1], bullet_color[2])
    color.set(qn('w:val'), color_hex.upper())
    rPr.append(color)
    
    # Größe für Bullet-Symbol
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(s.get("symbol_size", s["size"]) * 2))  # Word verwendet halbe Punkte
    rPr.append(sz)
    
    # Text mit Highlighting hinzufügen
    add_text_with_highlight(p, text, s_text["font"], s_text["size"], s_text["color"])
    
    return p


def get_available_width(doc):
    """Calculate available page width in inches based on margins"""
    from docx.shared import Inches, Cm
    section = doc.sections[0]
    page_width = Inches(8.5)  # Standard US Letter width
    left_margin = section.left_margin
    right_margin = section.right_margin
    return page_width - left_margin - right_margin


def add_basic_info_table(doc, hauptrolle_desc, nationalität, ausbildung):
    """
    Render basic info as a 3-column borderless table with white background.
    Column 1 (20%): Labels (bold)
    Column 2 (60%): Values
    Column 3 (20%): Image placeholder (merged across all 3 rows)
    """
    from docx.shared import Inches
    from docx.oxml import parse_xml, OxmlElement
    from docx.oxml.ns import nsdecls
    
    table = doc.add_table(rows=3, cols=3)
    # Don't set a style that may not exist; instead, manually remove borders below

    # Remove all table borders completely
    tbl = table._element
    tblPr = tbl.tblPr
    
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)
    
    # Create and add borders element with no borders
    tblBorders = parse_xml(r'<w:tBorders %s><w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/></w:tBorders>' % nsdecls('w'))
    
    # Remove existing borders if any
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)

    # Set column widths: 20%, 60%, 20%
    available_width = get_available_width(doc)
    widths = [available_width * 0.20, available_width * 0.50, available_width * 0.30]
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width

    # Helper function to set cell background to white and remove individual cell borders
    def set_cell_background_and_borders(cell, fill_color='FFFFFF'):
        """Set cell background color and remove borders"""
        tcPr = cell._element.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill', fill_color)
        tcPr.append(shd)
        
        # Remove cell borders
        tcBorders = parse_xml(r'<w:tcBorders %s><w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/><w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/></w:tcBorders>' % nsdecls('w'))
        tcPr.append(tcBorders)

    s = styles["text"]
    
    # Row 1: Hauptrolle
    cell_label = table.rows[0].cells[0]
    cell_value = table.rows[0].cells[1]
    cell_image = table.rows[0].cells[2]
    
    set_cell_background_and_borders(cell_label, 'FFFFFF')
    set_cell_background_and_borders(cell_value, 'FFFFFF')
    set_cell_background_and_borders(cell_image, 'FFFFFF')
    
    cell_label.text = ""
    cell_value.text = ""
    cell_image.text = ""
    
    p_label = cell_label.paragraphs[0]
    p_label.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    run_label = p_label.add_run("Hauptrolle:")
    run_label.font.name = s["font"]
    run_label.font.size = Pt(s["size"])
    run_label.font.bold = True
    run_label.font.color.rgb = RGBColor(*s["color"])
    
    p_value = cell_value.paragraphs[0]
    p_value.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    add_text_with_highlight(p_value, hauptrolle_desc, s["font"], s["size"], s["color"])
    
    # Row 2: Nationalität
    cell_label2 = table.rows[1].cells[0]
    cell_value2 = table.rows[1].cells[1]
    cell_image2 = table.rows[1].cells[2]
    
    set_cell_background_and_borders(cell_label2, 'FFFFFF')
    set_cell_background_and_borders(cell_value2, 'FFFFFF')
    set_cell_background_and_borders(cell_image2, 'FFFFFF')
    
    cell_label2.text = ""
    cell_value2.text = ""
    cell_image2.text = ""
    
    p_label2 = cell_label2.paragraphs[0]
    p_label2.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    run_label2 = p_label2.add_run("Nationalität:")
    run_label2.font.name = s["font"]
    run_label2.font.size = Pt(s["size"])
    run_label2.font.bold = True
    run_label2.font.color.rgb = RGBColor(*s["color"])
    
    p_value2 = cell_value2.paragraphs[0]
    p_value2.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    add_text_with_highlight(p_value2, nationalität, s["font"], s["size"], s["color"])
    
    # Row 3: Hauptausbildung
    cell_label3 = table.rows[2].cells[0]
    cell_value3 = table.rows[2].cells[1]
    cell_image3 = table.rows[2].cells[2]
    
    set_cell_background_and_borders(cell_label3, 'FFFFFF')
    set_cell_background_and_borders(cell_value3, 'FFFFFF')
    set_cell_background_and_borders(cell_image3, 'FFFFFF')
    
    cell_label3.text = ""
    cell_value3.text = ""
    cell_image3.text = ""
    
    p_label3 = cell_label3.paragraphs[0]
    p_label3.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    run_label3 = p_label3.add_run("Hauptausbildung:")
    run_label3.font.name = s["font"]
    run_label3.font.size = Pt(s["size"])
    run_label3.font.bold = True
    run_label3.font.color.rgb = RGBColor(*s["color"])
    
    p_value3 = cell_value3.paragraphs[0]
    p_value3.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    add_text_with_highlight(p_value3, ausbildung, s["font"], s["size"], s["color"])
    
    # Merge image cells vertically across all 3 rows and add placeholder
    try:
        table.cell(0, 2).merge(table.cell(2, 2))
        merged_cell = table.cell(0, 2)
        merged_cell.text = ""
        p_merged = merged_cell.paragraphs[0]
        p_merged.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run_merged = p_merged.add_run("BILD EINFÜGEN")
        run_merged.font.name = s["font"]
        run_merged.font.size = Pt(s["size"])
        run_merged.font.color.rgb = RGBColor(*s["color"])
        from docx.enum.text import WD_COLOR_INDEX
        run_merged.font.highlight_color = WD_COLOR_INDEX.YELLOW
    except Exception:
        # Fallback: attempt element merge for older versions
        try:
            cell_image._element.merge(cell_image2._element)
            cell_image._element.merge(cell_image3._element)
        except Exception:
            pass


def add_bullet_table(doc, items, max_items_per_column=4):
    # Calculate number of columns based on item count
    num_cols = max(1, (len(items) + max_items_per_column - 1) // max_items_per_column)
    
    if num_cols == 1:
        # Single column: just use regular bullet items
        for item in items:
            add_bullet_item(doc, item)
        return

    # Multi-column: create a table with no visible borders
    rows_per_col = (len(items) + num_cols - 1) // num_cols
    table = doc.add_table(rows=rows_per_col, cols=num_cols)

    # Remove table borders via XML (don't rely on built-in styles)
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)

    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'</w:tBorders>' % nsdecls('w'))
    # remove existing and append
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)

    # helper to remove cell borders (ensures no visible lines)
    def remove_cell_borders(cell):
        tcPr = cell._element.get_or_add_tcPr()
        tcBorders = parse_xml(r'<w:tcBorders %s>'
                              r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'</w:tcBorders>' % nsdecls('w'))
        # remove any existing tcBorders
        existing = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders')
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(tcBorders)

    # Fill table cells with items (column-wise distribution)
    s = styles["bullet"]
    for idx, item in enumerate(items):
        col = idx // rows_per_col
        row = idx % rows_per_col
        cell = table.rows[row].cells[col]
        
        # Remove any cell borders so the table is visually borderless
        try:
            remove_cell_borders(cell)
        except Exception:
            pass

        # Clear default paragraph
        cell.text = ""

        # Add bullet paragraph to cell
        p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(s.get("space_before", 0))
        p.paragraph_format.space_after = Pt(s.get("space_after", 0))
        p.paragraph_format.line_spacing = s.get("line_spacing", 1.0)
        
        # Hanging indent: Text-Zeilen rücken ein, erste Zeile (mit Symbol) nicht
        if "hanging_indent" in s:
            hanging = s["hanging_indent"]
            p.paragraph_format.left_indent = Pt(hanging)
            p.paragraph_format.first_line_indent = Pt(-hanging)

        # Bullet-Symbol aus styles.json
        bullet_symbol = s.get("symbol", "■") + " "
        bullet = p.add_run(bullet_symbol)
        bullet.font.name = s["font"]
        bullet.font.size = Pt(s.get("symbol_size", s["size"]))
        c = s["color"]
        bullet.font.color.rgb = RGBColor(c[0], c[1], c[2])

        run = p.add_run(item)
        run.font.name = s["font"]
        run.font.size = Pt(s["size"])


def add_fachwissen_table(doc, skills_data):
    """
    Render Fachwissen_und_Schwerpunkte as a 2-column table.
    Column 1: Category (bold) - 20%
    Column 2: Bullet list of Inhalt items - 80%
    """
    from docx.shared import Inches
    from docx.oxml import parse_xml, OxmlElement
    from docx.oxml.ns import nsdecls
    
    if not skills_data:
        return
    
    # Create table: one row per category
    table = doc.add_table(rows=len(skills_data), cols=2)
    
    # Remove table borders
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)
    
    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'</w:tBorders>' % nsdecls('w'))
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)
    
    # Set column widths: 20% for category, 80% for content
    available_width = get_available_width(doc)
    widths = [available_width * 0.20, available_width * 0.80]
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width
    
    # Helper to remove cell borders
    def remove_cell_borders(cell):
        tcPr = cell._element.get_or_add_tcPr()
        tcBorders = parse_xml(r'<w:tcBorders %s>'
                              r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'</w:tcBorders>' % nsdecls('w'))
        existing = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders')
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(tcBorders)
    
    s_text = styles["text"]
    s_bullet = styles["bullet"]
    
    # Fill rows
    for row_idx, item in enumerate(skills_data):
        kategorie = item.get("Kategorie", "")
        inhalt = item.get("Inhalt", item.get("BulletList", []))  # Support both formats
        
        cell_cat = table.rows[row_idx].cells[0]
        cell_list = table.rows[row_idx].cells[1]
        
        remove_cell_borders(cell_cat)
        remove_cell_borders(cell_list)
        
        # Clear and populate category cell
        cell_cat.text = ""
        p_cat = cell_cat.paragraphs[0]
        run_cat = p_cat.add_run(kategorie)
        run_cat.font.name = s_text["font"]
        run_cat.font.size = Pt(s_text["size"])
        run_cat.font.bold = True
        run_cat.font.color.rgb = RGBColor(*s_text["color"])
        
        # Clear and populate content cell with comma-separated list
        cell_list.text = ""
        p = cell_list.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = s_text.get("line_spacing", 1.0)
        
        # Join all items with comma and space
        comma_separated = ", ".join(inhalt)
        
        # Add as single run
        run = p.add_run(comma_separated)
        run.font.name = s_text["font"]
        run.font.size = Pt(s_text["size"])
        run.font.color.rgb = RGBColor(*s_text["color"])


def add_education_table(doc, education_data):
    """
    Render Aus_und_Weiterbildung as a 2-column table.
    Column 1: Time Range (YYYY - YYYY or single year)
    Column 2: Row1 = Institution, Row2 = Ausbildung/Titel
    """
    from docx.shared import Inches
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    
    if not education_data:
        return
    
    # Create table: one row per education item
    table = doc.add_table(rows=len(education_data), cols=2)
    
    # Remove table borders
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)
    
    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'</w:tBorders>' % nsdecls('w'))
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)
    
    # Set column widths: 20% for time range, 80% for institution/title
    available_width = get_available_width(doc)
    widths = [available_width * 0.20, available_width * 0.80]
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width
    
    # Helper to remove cell borders
    def remove_cell_borders(cell):
        tcPr = cell._element.get_or_add_tcPr()
        tcBorders = parse_xml(r'<w:tcBorders %s>'
                              r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'</w:tcBorders>' % nsdecls('w'))
        existing = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders')
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(tcBorders)
    
    s_text = styles["text"]
    
    # Fill rows
    for row_idx, item in enumerate(education_data):
        zeitraum = item.get("Zeitraum", "")
        institution = item.get("Institution", "")
        ausbildung_titel = item.get("Abschluss", "")
        
        cell_time = table.rows[row_idx].cells[0]
        cell_info = table.rows[row_idx].cells[1]
        
        remove_cell_borders(cell_time)
        remove_cell_borders(cell_info)
        
        # Column 1: Time Range
        cell_time.text = ""
        p_time = cell_time.paragraphs[0]
        p_time.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        add_text_with_highlight(p_time, zeitraum, s_text["font"], s_text["size"], s_text["color"])
        
        # Column 2: Institution and Title in one paragraph separated by soft line break
        cell_info.text = ""
        p_info = cell_info.paragraphs[0]
        p_info.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        # Institution (bold)
        add_text_with_highlight(p_info, institution, s_text["font"], s_text["size"], s_text["color"], bold=True)

        # soft line break (shift+Enter)
        from docx.enum.text import WD_BREAK
        p_info.runs[-1].add_break(WD_BREAK.LINE)

        # Title on the next visual line (same paragraph)
        add_text_with_highlight(p_info, ausbildung_titel, s_text["font"], s_text["size"], s_text["color"])

        # Add spacing after the combined paragraph so rows are visually separated
        p_info.paragraph_format.space_after = Pt(6)


def add_trainings_table(doc, trainings_data):
    """
    Render Trainings_und_Zertifizierungen as a 2-column table.
    Column 1: Time Range (YYYY - YYYY)
    Column 2: Row1 = Institution (bold), Row2 = Ausbildung/Titel or Zertifizierung
    """
    from docx.shared import Inches
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    if not trainings_data:
        return

    table = doc.add_table(rows=len(trainings_data), cols=3)

    # Remove table borders
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)

    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'</w:tBorders>' % nsdecls('w'))
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)

    # Column widths: 20% time, 20% institution, 60% certification/title
    available_width = get_available_width(doc)
    widths = [available_width * 0.20, available_width * 0.20, available_width * 0.60]
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width

    def remove_cell_borders(cell):
        tcPr = cell._element.get_or_add_tcPr()
        tcBorders = parse_xml(r'<w:tcBorders %s>'
                              r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'</w:tcBorders>' % nsdecls('w'))
        existing = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders')
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(tcBorders)

    s_text = styles["text"]

    for row_idx, item in enumerate(trainings_data):
        zeitraum = item.get("Zeitraum", "")
        institution = item.get("Institution", "")
        titel = item.get("Titel", item.get("Ausbildung_Titel", ""))

        cell_time = table.rows[row_idx].cells[0]
        cell_inst = table.rows[row_idx].cells[1]
        cell_title = table.rows[row_idx].cells[2]

        remove_cell_borders(cell_time)
        remove_cell_borders(cell_inst)
        remove_cell_borders(cell_title)

        # Time
        cell_time.text = ""
        p_time = cell_time.paragraphs[0]
        add_text_with_highlight(p_time, zeitraum, s_text["font"], s_text["size"], s_text["color"])
        p_time.paragraph_format.space_after = Pt(3)  # Reduced spacing

        # Institution (bold)
        cell_inst.text = ""
        p_inst = cell_inst.paragraphs[0]
        add_text_with_highlight(p_inst, institution, s_text["font"], s_text["size"], s_text["color"], bold=True)
        p_inst.paragraph_format.space_after = Pt(3)  # Reduced spacing

        # Certification / Training (title)
        cell_title.text = ""
        p_t = cell_title.paragraphs[0]
        add_text_with_highlight(p_t, titel, s_text["font"], s_text["size"], s_text["color"])
        p_t.paragraph_format.space_after = Pt(3)  # Reduced spacing


# -------------------------------------
# Hauptfunktion zum Erstellen des CVs
# -------------------------------------

def add_header_with_logo(doc):
    """Add a header with 3-column table: logo (40%), empty (10%), text (50%)."""
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    import os
    
    header_config = styles.get("header", {})
    logo_path = header_config.get("logo_path", "")
    logo_width = header_config.get("logo_width_cm", 4.0)
    logo_height = header_config.get("logo_height_cm", 1.5)
    header_text = header_config.get("text", "")
    text_font = header_config.get("text_font", "Aptos")
    text_size = header_config.get("text_size", 10)
    text_color = header_config.get("text_color", [68, 68, 68])
    
    # Access the header section
    section = doc.sections[0]
    header = section.header
    
    # Use the first paragraph for the table
    header_paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    header_paragraph.text = ""
    
    # Create table in document (will be moved to header manually)
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    
    # Set column widths: 40%, 10%, 50%
    available_width = get_available_width(doc)
    col_widths = [available_width * 0.40, available_width * 0.10, available_width * 0.50]
    for idx, width in enumerate(col_widths):
        table.columns[idx].width = int(width)
    
    # Remove table borders
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)
    
    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'</w:tBorders>' % nsdecls('w'))
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)
    
    # Remove cell borders for all cells
    def remove_cell_borders(cell):
        tcPr = cell._element.get_or_add_tcPr()
        tcBorders = parse_xml(r'<w:tcBorders %s>'
                              r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'</w:tcBorders>' % nsdecls('w'))
        existing = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders')
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(tcBorders)
    
    for cell in table.rows[0].cells:
        remove_cell_borders(cell)
    
    # Column 1: Logo (left aligned)
    cell_logo = table.rows[0].cells[0]
    cell_logo.text = ""
    p_logo = cell_logo.paragraphs[0]
    p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    if logo_path:
        full_logo_path = abs_path(logo_path)
        if os.path.exists(full_logo_path):
            try:
                run = p_logo.add_run()
                # Only set width, let Word calculate height to maintain aspect ratio
                run.add_picture(full_logo_path, width=Cm(logo_width))
                print(f"✅ Logo erfolgreich eingefügt: {full_logo_path}")
            except Exception as e:
                print(f"⚠️  Logo konnte nicht geladen werden: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  Logo-Datei nicht gefunden: {full_logo_path}")
    
    # Column 2: Empty (10%)
    cell_empty = table.rows[0].cells[1]
    cell_empty.text = ""
    
    # Column 3: Text (right aligned)
    cell_text = table.rows[0].cells[2]
    cell_text.text = ""
    p_text = cell_text.paragraphs[0]
    p_text.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    if header_text:
        run_text = p_text.add_run(header_text)
        run_text.font.name = text_font
        run_text.font.size = Pt(text_size)
        run_text.font.color.rgb = RGBColor(*text_color)
    
    # Move table to header
    table_element = table._element
    # Find the table in the body and get its parent
    body_element = doc._body._element
    if table_element in body_element:
        body_element.remove(table_element)
    # Insert into header
    header._element.insert(0, table_element)
    
    # Remove default empty paragraph in header if it exists
    if header.paragraphs and len(header.paragraphs) > 0:
        if not header.paragraphs[0].text.strip():
            p_element = header.paragraphs[0]._element
            if p_element.getparent() is not None:
                p_element.getparent().remove(p_element)


def generate_cv(json_path):

    json_path = abs_path(json_path)

    # JSON einlesen
    with open(json_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
    
    # JSON-Struktur validieren
    critical, info = validate_json_structure(data)
    if critical or info:
        # Erstelle Liste aller Validierungsfehler für Fallback
        validation_errors = []
        if critical:
            validation_errors.extend(["Kritische Fehler:"] + critical)
        if info:
            validation_errors.extend(["Info (nicht kritisch):"] + info)
        
        error_message = "Warnung: Die JSON-Datei hat mögliche Strukturprobleme:\n\n"
        if critical:
            error_message += "Kritische Fehler:\n" + "\n".join(critical) + "\n\n"
        if info:
            error_message += "Info (nicht kritisch):\n" + "\n".join(info) + "\n\n"
        error_message += "Trotzdem fortfahren?"
        try:
            from tkinter import messagebox
            root = Tk()
            root.withdraw()
            proceed = messagebox.askyesno("JSON-Validierungswarnung", error_message, icon='warning')
            root.destroy()
            if not proceed:
                print("❌ Benutzer hat abgebrochen.")
                return None
        except:
            print("Warnung:", "\n".join(validation_errors))
            user_input = input("Trotzdem fortfahren? (j/n): ")
            if user_input.lower() not in ['j', 'ja', 'y', 'yes']:
                return None

    # Lade Template-Datei mit Header/Footer oder erstelle leeres Dokument
    template_path = abs_path("../templates/cv_template.docx")
    if os.path.exists(template_path):
        doc = Document(template_path)
        # Template bringt bereits Header, Footer und Seitenränder mit
    else:
        print(f"Warnung: Template nicht gefunden ({template_path}). Erstelle leeres Dokument.")
        doc = Document()
        # Set page margins: 1.5 cm all sides
        from docx.shared import Cm
        sections = doc.sections
        for section in sections:
            section.top_margin = Cm(1.5)
            section.bottom_margin = Cm(1.5)
            section.left_margin = Cm(1.5)
            section.right_margin = Cm(1.5)
        # Add header with logo
        add_header_with_logo(doc)

    firstname = str(data.get("Vorname", "Unbekannt"))
    lastname = str(data.get("Nachname", "Unbekannt"))

    # -----------------------------
    # Überschrift 1 (Name)
    # -----------------------------
    add_heading_1(doc, f"{firstname} {lastname}")

    # -----------------------------
    # Basisinfos
    # -----------------------------
    hauptrolle = data.get("Hauptrolle", {})
    rolle_desc = hauptrolle.get("Beschreibung", "") if isinstance(hauptrolle, dict) else str(hauptrolle)
    add_basic_info_table(doc, 
                         rolle_desc,
                         str(data.get("Nationalität", "")),
                         str(data.get("Hauptausbildung", "")))

    # -----------------------------
    # Kurzprofil
    # -----------------------------
    add_heading_1(doc, "Kurzprofil")
    add_normal_text(doc, str(data.get("Kurzprofil", "")))

    # -----------------------------
    # Expertise & Fachwissen
    # -----------------------------
    add_heading_1(doc, "Expertise")
    add_heading_2(doc, "Fachwissen & Schwerpunkte")
    skills = data.get("Fachwissen_und_Schwerpunkte", [])
    add_fachwissen_table(doc, skills)

    # -----------------------------
    # Aus- und Weiterbildung
    # -----------------------------
    add_heading_2(doc, "Aus- und Weiterbildung")
    education = data.get("Aus_und_Weiterbildung", [])
    add_education_table(doc, education)

    # -----------------------------
    # Trainings & Zertifizierungen
    # -----------------------------
    add_heading_2(doc, "Trainings & Zertifizierungen")
    trainings = data.get("Trainings_und_Zertifizierungen", [])
    add_trainings_table(doc, trainings)

    # -----------------------------
    # Sprachen
    # -----------------------------
    add_heading_2(doc, "Sprachen")
    sprachen = data.get("Sprachen", [])
    add_sprachen_table(doc, sprachen)

    # -----------------------------
    # Referenzprojekte
    # -----------------------------
    doc.add_page_break()
    add_heading_1(doc, "Ausgewählte Referenzprojekte")
    referenzprojekte = data.get("Ausgewählte_Referenzprojekte", [])
    for projekt in referenzprojekte:
        add_referenzprojekt_section(doc, projekt)


    # -----------------------------
    # Dateien speichern
    # -----------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_docx = abs_path(f"../output/word/{firstname}_{lastname}_{timestamp}.docx")

    # Vor dem Speichern: Highlight alle fehlenden Daten im gesamten Dokument
    highlight_missing_data_in_document(doc)
    
    doc.save(out_docx)
    print(f"✅ Word-Datei erstellt: {out_docx}")
    return out_docx


def show_initial_dialog():
    """Zeigt ein initiales Dialogfenster mit Anweisungen und Optionen"""
    result = {'file_path': None}
    
    def select_file():
        root.destroy()
        file_path = select_json_file()
        result['file_path'] = file_path
    
    def cancel():
        root.destroy()
        result['file_path'] = None
    
    root = Tk()
    root.title("CV Generator")
    root.geometry("400x200")
    root.resizable(False, False)
    
    # Zentriere das Fenster
    root.eval('tk::PlaceWindow . center')
    
    # Anweisungstext
    label = Label(root, text="Willkommen beim CV Generator!\n\n"
                            "Wählen Sie eine JSON-Datei aus, um ein CV zu erstellen.\n"
                            "Die JSON-Datei sollte sich im Ordner 'input/json/' befinden.",
                  justify=CENTER, padx=20, pady=20)
    label.pack()
    
    # Buttons
    button_frame = Label(root)
    button_frame.pack(pady=10)
    
    select_button = Button(button_frame, text="JSON Datei auswählen", command=select_file, width=20)
    select_button.pack(side="left", padx=10)
    
    cancel_button = Button(button_frame, text="Abbrechen", command=cancel, width=20)
    cancel_button.pack(side="right", padx=10)
    
    root.mainloop()
    return result['file_path']


def select_json_file():
    """Öffnet einen Datei-Dialog zur Auswahl einer JSON-Datei"""
    root = Tk()
    root.withdraw()  # Versteckt das Hauptfenster
    root.attributes('-topmost', True)  # Bringt Dialog nach vorne
    
    # Standard-Verzeichnis auf input/json/ setzen
    default_dir = abs_path("../input/json/")
    
    file_path = filedialog.askopenfilename(
        title="Wählen Sie eine JSON-Datei für den CV",
        initialdir=default_dir,
        filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
    )
    
    root.destroy()
    return file_path


def add_sprachen_table(doc, sprachen_data):
    """
    Render Sprachen as a 6-column table (2 rows max).
    Columns: Sprache | Level (stars) | Sprache | Level (stars) | Sprache | Level (stars)
    Sorted by star count descending, max 6 languages (2 rows × 3 pairs)
    Stars: ★ = full, ☆ = empty
    """
    from docx.shared import Inches
    from docx.oxml import parse_xml, OxmlElement
    from docx.oxml.ns import nsdecls
    
    if not sprachen_data:
        return
    
    # Define level to star count mapping (supports both strings and numbers)
    level_stars = {
        "Muttersprache": 5,
        "Verhandlungssicher": 4,
        "Sehr gute Kenntnisse": 3,
        "Gute Kenntnisse": 2,
        "Grundkenntnisse": 1,
        5: 5,
        4: 4,
        3: 3,
        2: 2,
        1: 1
    }
    
    # Sort languages by star count descending
    sorted_sprachen = sorted(sprachen_data, 
                           key=lambda x: level_stars.get(x.get("Level", ""), 0), 
                           reverse=True)
    
    # Take max 6 languages (2 rows × 3 pairs)
    display_sprachen = sorted_sprachen[:6]
    
    # Create table: 2 rows, 6 columns
    table = doc.add_table(rows=2, cols=6)
    
    # Remove table borders
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)
    
    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'</w:tBorders>' % nsdecls('w'))
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)
    
    # Set column widths: equal distribution
    available_width = get_available_width(doc)
    col_width = available_width / 6
    for row in table.rows:
        for idx in range(6):
            row.cells[idx].width = col_width
        # Set smaller row height for compact display
        from docx.shared import Pt
        row.height = Pt(18)  # Smaller row height
        row.height_rule = 2  # WD_ROW_HEIGHT_RULE.AT_LEAST
    
    # Fill table cells
    s_text = styles["text"]
    
    for i, sprache in enumerate(display_sprachen):
        row_idx = i // 3  # 0 or 1
        col_start = (i % 3) * 2  # 0, 2, 4
        
        if row_idx >= 2:  # Safety check
            break
            
        # Sprache cell
        cell_sprache = table.rows[row_idx].cells[col_start]
        cell_sprache.text = ""
        p_sprache = cell_sprache.paragraphs[0]
        p_sprache.paragraph_format.line_spacing = 0.8  # Tighter spacing
        run_sprache = p_sprache.add_run(sprache.get("Sprache", ""))
        run_sprache.font.name = s_text["font"]
        run_sprache.font.size = Pt(s_text["size"])
        run_sprache.font.color.rgb = RGBColor(*s_text["color"])
        
        # Level cell (stars)
        cell_level = table.rows[row_idx].cells[col_start + 1]
        cell_level.text = ""
        p_level = cell_level.paragraphs[0]
        p_level.paragraph_format.line_spacing = 0.8  # Tighter spacing
        
        level = sprache.get("Level", "")
        star_count = parse_level(level)
        
        # Add full stars
        for _ in range(star_count):
            run_star = p_level.add_run("★")
            run_star.font.name = s_text["font"]
            run_star.font.size = Pt(s_text["size"])
            run_star.font.color.rgb = RGBColor(255, 121, 0)  # Orange color
        
        # Add empty stars
        for _ in range(5 - star_count):
            run_empty = p_level.add_run("☆")
            run_empty.font.name = s_text["font"]
            run_empty.font.size = Pt(s_text["size"])
            run_empty.font.color.rgb = RGBColor(128, 128, 128)  # Gray color

            run_empty.font.color.rgb = RGBColor(128, 128, 128)  # Gray color


def add_referenzprojekt_section(doc, projekt):
    """
    Render a single reference project as a unified 5-row table block:
    Row 1: Kunde (100% width, Heading 2)
    Row 2: Zeitraum (20%) | Rolle (80%) (text style)
    Row 3: Tätigkeiten (100% width, bullets)
    Row 4: Technologien Titel (20%) | Technologien Inhalt (80%) (text style)
    Row 5: Methodik Titel (20%) | Methodik Inhalt (80%) (text style)
    """
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    from docx.shared import Pt, Cm, RGBColor
    
    kunde = projekt.get("Kunde", "")
    zeitraum = projekt.get("Zeitraum", "")
    rolle = projekt.get("Rolle", "")
    taetigkeiten = projekt.get("Tätigkeiten", [])
    technologien = projekt.get("Technologien", "")
    methodik = projekt.get("Methodik", "")
    
    # Create unified 5-row table with 2 columns
    table = doc.add_table(rows=5, cols=2)
    
    # Remove table borders
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(r'<w:tblPr %s></w:tblPr>' % nsdecls('w'))
        tbl.insert(0, tblPr)
    
    tblBorders = parse_xml(r'<w:tBorders %s>'
                          r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                          r'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'  
                          r'</w:tBorders>' % nsdecls('w'))
    existing_borders = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tBorders')
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(tblBorders)
    
    # Set column widths: 20% for col1, 80% for col2
    available_width = get_available_width(doc)
    widths = [available_width * 0.20, available_width * 0.80]
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width
    
    # Remove cell borders function
    def remove_cell_borders(cell):
        tcPr = cell._element.get_or_add_tcPr()
        tcBorders = parse_xml(r'<w:tcBorders %s>'
                              r'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'  
                              r'</w:tcBorders>' % nsdecls('w'))
        existing = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcBorders')
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(tcBorders)
    
    # Row 1: Kunde (merge both columns for 100% width)
    row1_cell = table.rows[0].cells[0].merge(table.rows[0].cells[1])
    remove_cell_borders(row1_cell)
    row1_cell.text = ""
    p_kunde = row1_cell.paragraphs[0]
    s_heading2 = styles["heading2"]
    add_text_with_highlight(p_kunde, kunde, s_heading2["font"], s_heading2["size"], s_heading2["color"], bold=s_heading2.get("bold", False))
    p_kunde.paragraph_format.space_before = Pt(0)
    p_kunde.paragraph_format.space_after = Pt(3)
    
    # Row 2: Zeitraum (20%) | Rolle (80%)
    cell_zeitraum = table.rows[1].cells[0]
    cell_rolle = table.rows[1].cells[1]
    remove_cell_borders(cell_zeitraum)
    remove_cell_borders(cell_rolle)
    
    s_heading2 = styles["heading2"]
    s_text = styles["text"]
    
    cell_zeitraum.text = ""
    p_zeitraum = cell_zeitraum.paragraphs[0]
    add_text_with_highlight(p_zeitraum, zeitraum, s_heading2["font"], s_heading2["size"], s_heading2["color"], bold=s_heading2.get("bold", False))
    p_zeitraum.paragraph_format.space_before = Pt(0)
    p_zeitraum.paragraph_format.space_after = Pt(0)
    
    cell_rolle.text = ""
    p_rolle = cell_rolle.paragraphs[0]
    add_text_with_highlight(p_rolle, rolle, s_heading2["font"], s_heading2["size"], s_heading2["color"], bold=s_heading2.get("bold", False))
    p_rolle.paragraph_format.space_before = Pt(0)
    p_rolle.paragraph_format.space_after = Pt(0)
    
    # Row 3: Tätigkeiten (merge both columns for 100% width)
    row3_cell = table.rows[2].cells[0].merge(table.rows[2].cells[1])
    remove_cell_borders(row3_cell)
    row3_cell.text = ""
    
    # Add activities as bullets in the merged cell
    if taetigkeiten:
        # Clear default paragraph
        row3_cell._element.clear_content()
        
        s_bullet = styles["bullet"]
        
        for taetigkeit in taetigkeiten:
            if taetigkeit.strip():
                p = row3_cell.add_paragraph()
                
                # Add bullet symbol from styles.json
                bullet_symbol = s_bullet.get("symbol", "■") + " "
                symbol_run = p.add_run(bullet_symbol)
                symbol_run.font.name = s_bullet["font"]
                symbol_run.font.size = Pt(s_bullet.get("symbol_size", s_bullet["size"]))
                symbol_run.font.color.rgb = RGBColor(*s_bullet["color"])
                
                # Add text with normal size
                add_text_with_highlight(p, taetigkeit, s_text["font"], s_text["size"], s_text["color"])
                
                # Hanging indent aus styles.json
                if "hanging_indent" in s_bullet:
                    hanging = s_bullet["hanging_indent"]
                    p.paragraph_format.left_indent = Pt(hanging)
                    p.paragraph_format.first_line_indent = Pt(-hanging)
                else:
                    p.paragraph_format.left_indent = Cm(0.5)
                
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(3)
    
    # Row 4: Technologien (label 20% | content 80%)
    cell_tech_label = table.rows[3].cells[0]
    cell_tech_content = table.rows[3].cells[1]
    remove_cell_borders(cell_tech_label)
    remove_cell_borders(cell_tech_content)
    
    cell_tech_label.text = ""
    p_tech_label = cell_tech_label.paragraphs[0]
    run_tech_label = p_tech_label.add_run("Technologien")
    run_tech_label.font.name = s_text["font"]
    run_tech_label.font.size = Pt(s_text["size"])
    run_tech_label.font.color.rgb = RGBColor(*s_text["color"])
    run_tech_label.bold = True
    p_tech_label.paragraph_format.space_before = Pt(0)
    p_tech_label.paragraph_format.space_after = Pt(0)
    
    cell_tech_content.text = ""
    p_tech_content = cell_tech_content.paragraphs[0]
    add_text_with_highlight(p_tech_content, technologien, s_text["font"], s_text["size"], s_text["color"])
    p_tech_content.paragraph_format.space_before = Pt(0)
    p_tech_content.paragraph_format.space_after = Pt(0)
    
    # Row 5: Methodik (label 20% | content 80%)
    cell_meth_label = table.rows[4].cells[0]
    cell_meth_content = table.rows[4].cells[1]
    remove_cell_borders(cell_meth_label)
    remove_cell_borders(cell_meth_content)
    
    cell_meth_label.text = ""
    p_meth_label = cell_meth_label.paragraphs[0]
    run_meth_label = p_meth_label.add_run("Methodik")
    run_meth_label.font.name = s_text["font"]
    run_meth_label.font.size = Pt(s_text["size"])
    run_meth_label.font.color.rgb = RGBColor(*s_text["color"])
    run_meth_label.bold = True
    p_meth_label.paragraph_format.space_before = Pt(0)
    p_meth_label.paragraph_format.space_after = Pt(0)
    
    cell_meth_content.text = ""
    p_meth_content = cell_meth_content.paragraphs[0]
    add_text_with_highlight(p_meth_content, methodik, s_text["font"], s_text["size"], s_text["color"])
    p_meth_content.paragraph_format.space_before = Pt(0)
    p_meth_content.paragraph_format.space_after = Pt(0)
    
    # Add spacing after the project block by adding an empty paragraph
    spacing_paragraph = doc.add_paragraph()
    spacing_paragraph.paragraph_format.space_after = Pt(24)


def show_success_dialog(file_path):
    """Zeigt ein Erfolgsdialog mit Option zum Öffnen der Datei"""
    import os
    
    def open_file():
        try:
            os.startfile(file_path)  # Öffnet die Datei mit dem Standardprogramm
        except Exception as e:
            print(f"Fehler beim Öffnen der Datei: {e}")
        root.destroy()
    
    def close():
        root.destroy()
    
    root = Tk()
    root.title("CV erfolgreich erstellt")
    root.geometry("450x150")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')
    
    # Erfolgsmeldung
    output_dir = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    success_text = f"✅ CV-Datei erfolgreich erstellt!\n\nOutput Directory: {output_dir}\nFilename: {filename}"
    label = Label(root, text=success_text, justify="left", padx=20, pady=20)
    label.pack()
    
    # Buttons
    button_frame = Label(root)
    button_frame.pack(pady=10)
    
    open_button = Button(button_frame, text="Datei öffnen", command=open_file, width=15)
    open_button.pack(side="left", padx=10)
    
    close_button = Button(button_frame, text="Schließen", command=close, width=15)
    close_button.pack(side="right", padx=10)
    
    root.mainloop()


# Lade Stile global nach allen Definitionen
styles = load_styles("styles.json")
if __name__ == "__main__":
    json_file = show_initial_dialog()
    if json_file:
        output_file = generate_cv(json_file)
        if output_file:
            show_success_dialog(output_file)
        else:
            print("❌ JSON-Validierung fehlgeschlagen. Programm abgebrochen.")
    else:
        print("❌ Programm abgebrochen.")
