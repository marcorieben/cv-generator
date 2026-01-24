"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
#!/usr/bin/env python3
"""Test sidebar active/inactive button logic"""
import yaml
import os

# Load config
config_path = os.path.join(os.path.dirname(__file__), "scripts", "sidebar_config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

print("=" * 60)
print("TESTING SIDEBAR BUTTON LOGIC")
print("=" * 60)

# Test Pages
test_cases = [
    ("app.py", "pages/01_Stellenprofile.py", "should be secondary (not matching)"),
    ("pages/01_Stellenprofile.py", "pages/01_Stellenprofile.py", "should be primary (exact match)"),
    ("pages/02_Kandidaten.py", "pages/02_Kandidaten.py", "should be primary (exact match)"),
    ("pages/02_Kandidaten.py", "pages/01_Stellenprofile.py", "should be secondary (not matching)"),
]

def check_button_type(current_page, button_page):
    """Simuliert die Logik aus _render_button"""
    current_page_normalized = current_page.replace("\\", "/").lower()
    page_normalized = button_page.replace("\\", "/").lower()
    
    # Wenn dieser Button die aktuelle Seite ist → primary
    if page_normalized in current_page_normalized or current_page_normalized in page_normalized:
        return "primary"
    return "secondary"

print("\nTest Cases:")
for current, button, expected in test_cases:
    result = check_button_type(current, button)
    status = "✅" if (("primary" in expected and result == "primary") or ("secondary" in expected and result == "secondary")) else "❌"
    print(f"{status} Current: {current:40} | Button: {button:40} | Result: {result:10} ({expected})")

print("\n" + "=" * 60)
print("Loaded Buttons from Config:")
print("=" * 60)

def print_buttons(items, indent=0):
    for item in items:
        if item.get("hidden"):
            continue
        if item.get("type") == "button":
            page = item.get("page", "N/A")
            label_key = item.get("label_key", "N/A")
            print(f"{'  ' * indent}Button: {label_key} -> {page}")
        elif item.get("type") in ["expander"]:
            label_key = item.get("label_key", "N/A")
            print(f"{'  ' * indent}Expander: {label_key}")
            if "children" in item:
                print_buttons(item["children"], indent + 1)

print_buttons(config["sidebar_structure"])

print("\n" + "=" * 60)
print("RESULT: All logic working correctly!" if all(
    (("primary" in expected and check_button_type(current, button) == "primary") or 
     ("secondary" in expected and check_button_type(current, button) == "secondary"))
    for current, button, expected in test_cases
) else "RESULT: Some tests FAILED!")
print("=" * 60)
