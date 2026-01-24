"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
#!/usr/bin/env python3
"""
Pre-commit hook for data protection
Prevents accidentally committing database files and other production data
"""

import subprocess
import sys
from pathlib import Path


def check_database_protection():
    """
    🛡️ Database Data Protection Check
    Prevents committing actual database files to Git
    Only allows *.sql migration files
    """
    print("\n🛡️  Database Data Protection Check")
    print("=" * 60)
    
    # Get list of staged files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return True  # No files to check
    
    if not staged_files or staged_files == ['']:
        return True
    
    # Check for database files
    dangerous_extensions = ['.db', '.sqlite', '.sqlite3']
    dangerous_patterns = ['data/cv_generator', 'database.', '.db.bak']
    
    violations = []
    
    for file in staged_files:
        if not file:
            continue
        
        # Check file extensions
        for ext in dangerous_extensions:
            if file.endswith(ext):
                violations.append(f"  ❌ Database file: {file}")
        
        # Check patterns
        for pattern in dangerous_patterns:
            if pattern in file:
                violations.append(f"  ❌ Database file: {file}")
    
    if violations:
        print("\n⚠️  CRITICAL: Database files detected in staged changes!")
        print("\nViolations found:")
        for v in violations:
            print(v)
        
        print("\n" + "=" * 60)
        print("🛡️  DATA PROTECTION RULES:")
        print("=" * 60)
        print("""
✅ ALLOWED to commit:
   - data/migrations/*.sql (schema changes only)
   - Core application code
   - Configuration files

❌ NEVER commit:
   - data/cv_generator.db (production data!)
   - data/*.sqlite (local instance data!)
   - Any database backup files

💡 FIX:
   1. Run: git reset data/cv_generator.db
   2. Verify with: git status
   3. Add to .gitignore if not already there
   4. Try commit again
        """)
        print("=" * 60)
        return False
    
    print("✅ No database files detected in staged changes")
    print("✅ Safe to commit!")
    return True


def check_migrations_only():
    """
    Verify that only schema migration files are in data/ directory
    """
    print("\n📋 Migration Files Check")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return True
    
    data_files = [f for f in staged_files if f.startswith('data/') and f not in ['data/migrations/']]
    migration_files = [f for f in staged_files if f.startswith('data/migrations/') and f.endswith('.sql')]
    
    if migration_files:
        print(f"✅ Found {len(migration_files)} migration files:")
        for f in migration_files:
            print(f"   - {f}")
    
    if data_files:
        # Check if any non-.sql, non-dir files
        non_migration = [f for f in data_files if not f.endswith('.sql') and not f.endswith('/')]
        if non_migration:
            print(f"\n⚠️  WARNING: Non-migration files in data/:")
            for f in non_migration:
                print(f"   - {f}")
            return False
    
    return True


def main():
    """Run all protection checks"""
    print("\n" + "=" * 60)
    print("🔒 PRE-COMMIT DATA PROTECTION CHECKS")
    print("=" * 60)
    
    checks = [
        ("Database Protection", check_database_protection),
        ("Migration Validation", check_migrations_only),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n⚠️  Error in {check_name}: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if not all_passed:
        print("\n❌ Commit blocked due to data protection violations!")
        print("   Fix the issues above and try again.")
        print("\n   Use --no-verify to skip (NOT RECOMMENDED):")
        print("   git commit --no-verify")
        return 1
    else:
        print("\n✅ All protection checks passed!")
        print("   Ready to commit safely.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
