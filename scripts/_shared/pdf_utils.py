"""
PDF text extraction utilities.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    """
    Extrahiert Text aus einer PDF-Datei.

    Args:
        pdf_path: Pfad zur PDF-Datei oder File-Objekt (Streamlit UploadedFile)

    Returns:
        String mit dem extrahierten Text
    """
    try:
        if pdf_path is None:
            raise ValueError("PDF-Datei ist leer (None). Bitte laden Sie eine gültige PDF-Datei hoch.")

        # Wenn Streamlit UploadedFile, seek auf Position 0 zurücksetzen
        if hasattr(pdf_path, 'seek'):
            try:
                pdf_path.seek(0)
            except Exception as seek_err:
                raise ValueError(f"Fehler beim Zugriff auf PDF-Datei: {str(seek_err)}. Bitte laden Sie eine neue Datei hoch.")

        if hasattr(pdf_path, 'size') and pdf_path.size == 0:
            raise ValueError("Die hochgeladene PDF-Datei ist leer. Bitte laden Sie eine gültige PDF-Datei hoch.")

        reader = PdfReader(pdf_path)

        if not reader.pages:
            raise ValueError("Die PDF-Datei enthält keine Seiten. Bitte laden Sie eine gültige PDF-Datei hoch.")

        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Seite {page_num} ---\n{page_text}"
            except Exception as page_err:
                print(f"Warning: Seite {page_num} konnte nicht gelesen werden: {str(page_err)}")
                continue

        if not text.strip():
            raise ValueError("Keine Text-Inhalte in PDF gefunden. Überprüfen Sie, ob die Datei Text enthält.")

        return text

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Fehler beim Lesen der PDF: {str(e)}")
