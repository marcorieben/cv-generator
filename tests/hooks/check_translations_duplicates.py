import json
import sys
import os

def check_duplicates(file_path):
    def dict_raise_duplicates(ordered_pairs):
        """Reject duplicate keys."""
        d = {}
        for k, v in ordered_pairs:
            if k in d:
                raise ValueError(f"Duplicate key found: {k}")
            d[k] = v
        return d

    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f, object_pairs_hook=dict_raise_duplicates)
        return True, ""
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error parsing JSON: {str(e)}"

if __name__ == "__main__":
    # Path relative to script (now in tests/hooks/)
    # Root is two levels up, then scripts/translations.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    trans_path = os.path.join(root_dir, "scripts", "translations.json")
    
    # Fallback/Safety check
    if not os.path.exists(trans_path):
        # Maybe we are in root?
        trans_path = os.path.join(os.getcwd(), "scripts", "translations.json")

    success, message = check_duplicates(trans_path)
    if success:
        print(f"✅ No duplicate keys found in translations.json")
        sys.exit(0)
    else:
        print(f"\n============================================================")
        print(f"❌ DUPLICATE KEY ERROR in translations.json")
        print(f"Details: {message}")
        print(f"============================================================\n")
        sys.exit(1)
