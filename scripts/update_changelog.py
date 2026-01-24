"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-14
Last Updated: 2026-01-24
"""
import subprocess
import datetime
import os
import re

def get_latest_commit():
    # Get the full commit message and date
    # %s = subject, %cd = commit date, %h = short hash
    cmd = ["git", "log", "-1", "--format=%cd|%s", "--date=format:%Y-%m-%d %H:%M:%S"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def parse_commit_message(message):
    # Common prefixes mapping
    prefixes = {
        'feat': 'FEATURE',
        'fix': 'BUGFIX',
        'docs': 'DOCS',
        'style': 'STYLE',
        'refactor': 'REFACTOR',
        'test': 'TEST',
        'chore': 'CHORE',
        'ui': 'UI',
        'perf': 'PERF',
        'ci': 'CI',
        'build': 'BUILD'
    }
    
    # Try to find a prefix like "feat: message" or "feat(scope): message"
    match = re.match(r'^(\w+)(?:\(.*\))?:\s*(.*)', message)
    
    if match:
        prefix = match.group(1).lower()
        text = match.group(2)
        category = prefixes.get(prefix, prefix.upper())
    else:
        # Fallback if no standard prefix found
        category = "UPDATE"
        text = message
        
    return category, text

def update_changelog():
    commit_data = get_latest_commit()
    if not commit_data:
        print("Error: Could not read git log.")
        return

    try:
        date_str, message = commit_data.split('|', 1)
    except ValueError:
        print("Error: Unexpected git log format.")
        return

    category, text = parse_commit_message(message)
    
    # Format: Timestamp | Categorization | Text
    log_entry = f"{date_str} | {category} | {text}"
    
    changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'CHANGELOG.md')
    
    # Read existing content to avoid duplicates (simple check)
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if log_entry in content:
                print("Entry already exists in CHANGELOG.md")
                return

    # Append to file
    with open(changelog_path, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")
    
    print(f"Added to CHANGELOG.md: {log_entry}")

if __name__ == "__main__":
    update_changelog()
