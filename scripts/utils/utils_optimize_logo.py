"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-24
"""
import os
from PIL import Image

def optimize_logo(input_path, output_path=None, max_width=800, max_height=300, dpi=150):
    """
    Optimiert ein Logo für die Verwendung in Word-Dokumenten.
    
    Empfohlene Werte für Header:
    - Maximale Breite: 800 Pixel (für 4cm bei 150 DPI ~ 472 Pixel)
    - Maximale Höhe: 300 Pixel
    - DPI: 150 (guter Kompromiss zwischen Qualität und Dateigrösse)
    - Format: PNG mit Transparenz
    """
    if output_path is None:
        output_path = input_path
    
    print(f"Analysiere Logo: {input_path}")
    
    # Originalbild laden
    img = Image.open(input_path)
    
    # Originale Eigenschaften anzeigen
    print(f"\nOriginale Eigenschaften:")
    print(f"  Format: {img.format}")
    print(f"  Modus: {img.mode}")
    print(f"  Dimensionen: {img.size[0]}x{img.size[1]} Pixel")
    print(f"  Dateigrösse: {os.path.getsize(input_path):,} Bytes ({os.path.getsize(input_path)/1024:.2f} KB)")
    
    # Berechne neue Grösse (Seitenverhältnis beibehalten)
    width, height = img.size
    aspect_ratio = width / height
    
    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)
        
        print(f"\n✅ Skaliere auf: {new_width}x{new_height} Pixel")
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        print(f"\n✅ Keine Skalierung notwendig")
    
    # Konvertiere zu RGB oder RGBA falls notwendig
    if img.mode not in ('RGB', 'RGBA'):
        if 'transparency' in img.info:
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
        print(f"✅ Konvertiert zu: {img.mode}")
    
    # Speichere optimiertes Bild
    img.save(output_path, 'PNG', dpi=(dpi, dpi), optimize=True)
    
    print(f"\n✅ Optimiertes Logo gespeichert: {output_path}")
    print(f"  Neue Dimensionen: {img.size[0]}x{img.size[1]} Pixel")
    print(f"  Neue Dateigrösse: {os.path.getsize(output_path):,} Bytes ({os.path.getsize(output_path)/1024:.2f} KB)")
    print(f"  DPI: {dpi}")
    
    print(f"\n📋 Empfohlene Einstellungen in styles.json:")
    print(f'  "logo_width_cm": {img.size[0] / (dpi / 2.54):.1f}')
    

if __name__ == "__main__":
    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "logo.png")
    
    if not os.path.exists(logo_path):
        print(f"❌ Logo nicht gefunden: {logo_path}")
    else:
        # Backup erstellen
        backup_path = logo_path.replace(".png", "_original.png")
        if not os.path.exists(backup_path):
            print(f"📦 Erstelle Backup: {backup_path}")
            Image.open(logo_path).save(backup_path)
        
        # Logo optimieren
        optimize_logo(logo_path, max_width=800, max_height=300, dpi=150)
        
        print("\n✅ Fertig! Du kannst jetzt generate_cv.py ausführen.")
