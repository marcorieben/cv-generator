import json
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def hex_to_rgb(hex_color):
    """Converts hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def set_cell_background(cell, color_hex):
    """Sets the background color of a table cell"""
    cell_properties = cell._element.get_or_add_tcPr()
    shading_element = OxmlElement('w:shd')
    shading_element.set(qn('w:val'), 'clear')
    shading_element.set(qn('w:color'), 'auto')
    shading_element.set(qn('w:fill'), color_hex)
    cell_properties.append(shading_element)

def create_element(name):
    return OxmlElement(name)

def create_attribute(element, name, value):
    element.set(qn(name), value)

def add_page_number(run):
    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')

    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = "PAGE"

    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'end')

    run._element.append(fldChar1)
    run._element.append(instrText)
    run._element.append(fldChar2)

def generate_angebot_word(json_path, output_path):
    """
    Generates a Word document for the Offer based on the JSON data.
    """
    # Load Data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load Styles (simplified for this script, ideally shared)
    ORANGE = RGBColor(255, 121, 0)
    GRAY = RGBColor(68, 68, 68)
    BLACK = RGBColor(0, 0, 0)
    FONT_NAME = "Aptos" # Fallback to Arial if not available

    doc = Document()
    
    # --- Styles Setup ---
    style = doc.styles['Normal']
    font = style.font
    font.name = FONT_NAME
    font.size = Pt(11)
    font.color.rgb = BLACK

    # Heading 1
    h1 = doc.styles['Heading 1']
    h1.font.name = FONT_NAME
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = ORANGE
    
    # Heading 2
    h2 = doc.styles['Heading 2']
    h2.font.name = FONT_NAME
    h2.font.size = Pt(12)
    h2.font.bold = True
    h2.font.color.rgb = GRAY

    # --- Header ---
    section = doc.sections[0]
    header = section.header
    header_table = header.add_table(1, 2, width=Inches(6))
    header_table.autofit = False
    header_table.columns[0].width = Inches(4)
    header_table.columns[1].width = Inches(2)
    
    # Logo (Placeholder logic - assumes logo exists in templates)
    # In a real scenario, we'd resolve the path properly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, "..", "templates", "logo.png")
    
    cell_logo = header_table.cell(0, 0)
    if os.path.exists(logo_path):
        paragraph = cell_logo.paragraphs[0]
        run = paragraph.add_run()
        run.add_picture(logo_path, width=Cm(4.0))
    else:
        cell_logo.text = "Orange Business"

    cell_text = header_table.cell(0, 1)
    paragraph = cell_text.paragraphs[0]
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    run = paragraph.add_run("digital.orange-business.com")
    run.font.color.rgb = ORANGE
    run.font.size = Pt(10)

    # --- Footer ---
    footer = section.footer
    footer_paragraph = footer.paragraphs[0]
    footer_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    run = footer_paragraph.add_run()
    add_page_number(run)

    # --- Content ---
    
    # Title
    meta = data.get("angebots_metadata", {})
    stellenbezug = data.get("stellenbezug", {})
    
    doc.add_heading(f"Angebot: {stellenbezug.get('rollenbezeichnung', 'IT-Spezialist')}", 0)
    
    # Metadata Table
    table = doc.add_table(rows=4, cols=2)
    table.style = 'Table Grid'
    
    rows = [
        ("Kunde:", meta.get("kunde", "")),
        ("Datum:", meta.get("datum", "")),
        ("Angebots-ID:", meta.get("angebots_id", "")),
        ("Ansprechpartner:", meta.get("ansprechpartner", {}).get("name", ""))
    ]
    
    for i, (label, value) in enumerate(rows):
        row = table.rows[i]
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[1].text = value
        # Highlight values that need manual check (Datum, ID, Ansprechpartner)
        if i > 0: # Skip Kunde, highlight others
             set_cell_background(row.cells[1], "FFFF00") # Yellow

    doc.add_paragraph() # Spacer

    # 1. Ausgangslage (Stellenbezug)
    doc.add_heading("1. Ausgangslage & Verständnis", level=1)
    doc.add_paragraph(stellenbezug.get("kurzkontext", ""))
    
    # 2. Kandidatenvorschlag
    kandidat = data.get("kandidatenvorschlag", {})
    doc.add_heading("2. Kandidatenvorschlag", level=1)
    p = doc.add_paragraph()
    p.add_run("Wir schlagen Ihnen folgenden Kandidaten vor: ").bold = False
    p.add_run(kandidat.get("name", "")).bold = True
    
    doc.add_paragraph(kandidat.get("eignungs_summary", ""))

    # 3. Profil & Kompetenzen
    profil = data.get("profil_und_kompetenzen", {})
    doc.add_heading("3. Profil & Kompetenzen", level=1)
    
    doc.add_heading("Methoden & Technologien", level=2)
    for item in profil.get("methoden_und_technologien", []):
        doc.add_paragraph(item, style='List Bullet')
        
    doc.add_heading("Operative & Führungserfahrung", level=2)
    for item in profil.get("operative_und_fuehrungserfahrung", []):
        doc.add_paragraph(item, style='List Bullet')

    # 4. Kriterien Abgleich
    abgleich = data.get("kriterien_abgleich", {})
    doc.add_heading("4. Abgleich mit Anforderungskriterien", level=1)
    
    # Muss-Kriterien
    doc.add_heading("Muss-Kriterien", level=2)
    muss = abgleich.get("muss_kriterien", [])
    if muss:
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Kriterium'
        hdr_cells[1].text = 'Erfüllt'
        hdr_cells[2].text = 'Begründung / Evidenz'
        
        # Header styling
        for cell in hdr_cells:
            set_cell_background(cell, "EEEEEE")
            cell.paragraphs[0].runs[0].font.bold = True

        for item in muss:
            row_cells = table.add_row().cells
            row_cells[0].text = item.get("kriterium", "")
            
            erfuellt = item.get("erfuellt", False)
            # Handle string "true"/"false" or boolean
            if isinstance(erfuellt, str):
                erfuellt = erfuellt.lower() == 'true'
            
            row_cells[1].text = "Ja" if erfuellt else "Nein"
            if erfuellt:
                row_cells[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 128, 0) # Green
            else:
                row_cells[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 0, 0) # Red
                
            row_cells[2].text = item.get("begruendung", "")
    else:
        doc.add_paragraph("Keine Muss-Kriterien definiert.")

    doc.add_paragraph()

    # Soll-Kriterien
    doc.add_heading("Soll-Kriterien", level=2)
    soll = abgleich.get("soll_kriterien", [])
    if soll:
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Kriterium'
        hdr_cells[1].text = 'Erfüllt'
        hdr_cells[2].text = 'Begründung / Evidenz'
        
        for cell in hdr_cells:
            set_cell_background(cell, "EEEEEE")
            cell.paragraphs[0].runs[0].font.bold = True

        for item in soll:
            row_cells = table.add_row().cells
            row_cells[0].text = item.get("kriterium", "")
            
            erfuellt = item.get("erfuellt", False)
            if isinstance(erfuellt, str):
                erfuellt = erfuellt.lower() == 'true'
                
            row_cells[1].text = "Ja" if erfuellt else "Nein"
            row_cells[2].text = item.get("begruendung", "")
    else:
        doc.add_paragraph("Keine Soll-Kriterien definiert.")

    # 5. Gesamtbeurteilung
    beurteilung = data.get("gesamtbeurteilung", {})
    doc.add_heading("5. Gesamtbeurteilung & Mehrwert", level=1)
    doc.add_paragraph(beurteilung.get("zusammenfassung", ""))
    
    doc.add_heading("Mehrwert für den Kunden", level=2)
    for item in beurteilung.get("mehrwert_fuer_kunden", []):
        doc.add_paragraph(item, style='List Bullet')
        
    doc.add_paragraph().add_run("Empfehlung: " + beurteilung.get("empfehlung", "")).bold = True

    # 6. Einsatzkonditionen
    konditionen = data.get("einsatzkonditionen", {})
    doc.add_heading("6. Einsatzkonditionen", level=1)
    
    table = doc.add_table(rows=4, cols=2)
    table.style = 'Table Grid'
    
    rows = [
        ("Pensum:", konditionen.get("pensum", "")),
        ("Verfügbarkeit:", konditionen.get("verfuegbarkeit", "")),
        ("Stundensatz (CHF):", konditionen.get("stundensatz", "")),
        ("Subunternehmen:", konditionen.get("subunternehmen", ""))
    ]
    
    for i, (label, value) in enumerate(rows):
        row = table.rows[i]
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[1].text = value
        # Highlight all condition values as they are critical
        set_cell_background(row.cells[1], "FFFF00") # Yellow

    # 7. Abschluss
    abschluss = data.get("abschluss", {})
    doc.add_heading("7. Abschluss", level=1)
    doc.add_paragraph(abschluss.get("verfuegbarkeit_gespraech", ""))
    doc.add_paragraph(abschluss.get("kontakt_hinweis", ""))

    # Save
    doc.save(output_path)
    print(f"✅ Angebot Word generiert: {output_path}")
    return output_path

if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 2:
        generate_angebot_word(sys.argv[1], sys.argv[2])
