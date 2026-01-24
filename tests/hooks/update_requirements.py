"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-24
"""
import subprocess
import re
import os
import sys

def get_installed_packages():
    """Get dictionary of installed packages {name: version}"""
    try:
        # Use sys.executable to ensure we use the same python environment
        result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
        packages = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if "==" in line:
                name, version = line.split("==", 1)
                packages[name.lower()] = version
            elif " @ " in line:
                # Handle direct URL installs if necessary, or ignore
                pass
        return packages
    except Exception as e:
        print(f"Error getting installed packages: {e}")
        return {}

def update_requirements_file(path, installed_packages, known_packages):
    """Update versions in the file and track known packages"""
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        original_line = line.rstrip()
        line_content = original_line.strip()
        
        # Skip comments and empty lines
        if not line_content or line_content.startswith("#"):
            new_lines.append(original_line)
            continue
        
        # Parse package name
        # Regex to match package name at start of line
        match = re.match(r"^([a-zA-Z0-9_\-]+)", line_content)
        if match:
            name = match.group(1).lower()
            known_packages.add(name)
            
            if name in installed_packages:
                current_version = installed_packages[name]
                # Determine operator (preserve existing or default to >=)
                operator = ">="
                if "==" in line_content: operator = "=="
                elif "~=" in line_content: operator = "~="
                elif ">" in line_content: operator = ">="
                
                # Reconstruct line with new version
                # We try to preserve comments if they exist on the same line? 
                # For simplicity, we just rewrite the requirement part
                new_lines.append(f"{match.group(1)}{operator}{current_version}")
            else:
                new_lines.append(original_line)
        else:
            new_lines.append(original_line)

    return new_lines

def main():
    print("🔄 Checking requirements.txt...")
    
    # Paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req_path = os.path.join(root_dir, "requirements.txt")
    dev_req_path = os.path.join(root_dir, "requirements-dev.txt")
    
    installed = get_installed_packages()
    if not installed:
        print("⚠️ Could not determine installed packages. Skipping update.")
        return

    known = set()
    
    # 1. Update existing requirements.txt
    new_req_lines = update_requirements_file(req_path, installed, known)
    
    # 2. Scan dev requirements to add to known (so we don't add them to main requirements)
    if os.path.exists(dev_req_path):
        with open(dev_req_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"^([a-zA-Z0-9_\-]+)", line.strip())
                if match:
                    known.add(match.group(1).lower())

    # 3. Find new packages (installed but not in requirements or dev-requirements)
    # We filter out some common system packages or tools that might be installed but not needed
    # For now, we add everything to ensure "it just works"
    new_packages = []
    for name, version in installed.items():
        if name not in known and not name.startswith("-e"):
            # Optional: Filter out known dev tools if they are not in dev-reqs?
            # For now, add them.
            new_packages.append(f"{name}>={version}")
            
    # 4. Append new packages
    if new_packages:
        print(f"➕ Adding {len(new_packages)} new dependencies to requirements.txt")
        # Check if last line is empty
        if new_req_lines and new_req_lines[-1].strip():
            new_req_lines.append("")
            
        new_req_lines.append("# Auto-added dependencies")
        for pkg in new_packages:
            new_req_lines.append(pkg)
            
    # 5. Write back to file
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_req_lines) + "\n")
        
    print("✅ requirements.txt updated.")

if __name__ == "__main__":
    main()
