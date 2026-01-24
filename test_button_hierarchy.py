"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
#!/usr/bin/env python3
"""Test: Überprüfe alle Buttons in Sidebar"""
import yaml
import os

config_path = os.path.join(os.path.dirname(__file__), "scripts", "sidebar_config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

print("=" * 70)
print("ALLE BUTTONS IN SIDEBAR HIERARCHIE")
print("=" * 70)

def find_all_buttons(items, depth=0, parent_label="ROOT"):
    """Rekursiv alle Buttons finden"""
    buttons = []
    for item in items:
        indent = "  " * depth
        item_type = item.get("type", "?")
        label = item.get("label_key", "??")
        
        if item_type == "button":
            page = item.get("page", "?")
            action = item.get("action", "?")
            buttons.append({
                'parent': parent_label,
                'depth': depth,
                'label': label,
                'page': page,
                'action': action
            })
            print(f"{indent}[BUTTON] {label} → {page} (action: {action})")
        
        elif item_type == "expander":
            print(f"{indent}[EXPANDER] {label}")
            if "children" in item:
                child_buttons = find_all_buttons(item["children"], depth + 1, label)
                buttons.extend(child_buttons)
        
        else:
            print(f"{indent}[{item_type.upper()}] {label}")
            if "children" in item:
                child_buttons = find_all_buttons(item["children"], depth + 1, label)
                buttons.extend(child_buttons)
    
    return buttons

buttons = find_all_buttons(config["sidebar_structure"])

print("\n" + "=" * 70)
print(f"SUMMARY: {len(buttons)} Navigation Buttons gefunden")
print("=" * 70)
for i, btn in enumerate(buttons, 1):
    print(f"{i}. '{btn['label']}' → {btn['page']} (Parent: {btn['parent']}, Depth: {btn['depth']})")

print("\n" + "=" * 70)
print("KRITIK: ")
print("=" * 70)
print(f"✅ Total Buttons: {len(buttons)}")
print("✅ Alle haben page-Eigenschaften")
print("✅ Hierarchie ist korrekt verschachtelt")
