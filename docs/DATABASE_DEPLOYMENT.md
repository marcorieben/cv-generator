# Database Deployment & Instance Management

## 🎯 Overview

This system ensures that **database schema changes are deployed safely across instances** (dev, staging, production) **without data loss or conflicts**.

**Key Principle:** Only structural changes (schema) are versioned in Git. Production data stays in each instance.

## 📊 Architecture

```
Git Repository (schema versioning)
    ↓
data/migrations/*.sql (schema changes only)
    ↓
Each Instance (dev, staging, prod)
    ├── data/cv_generator.db (INSTANCE DATA - NOT in Git)
    ├── schema_migrations table (tracks which migrations applied)
    └── ... data remains unchanged
```

## ❌ What NOT to do

**NEVER commit the actual database file:**
```bash
# WRONG ❌
git add data/cv_generator.db
git commit -m "update db"

# RIGHT ✅
# Database files are ignored (.gitignore)
# Only .sql migration files are committed
```

## ✅ Deployment Workflow

### Step 1: Develop on your instance (dev machine)

```bash
# Work with your local database
python -c "from core.database import Database; db = Database('data/cv_generator.db')"

# Your data stays local - no shared data
# Only your instance sees your test data
```

### Step 2: Make schema changes (new migrations)

If you need to add tables, columns, or indexes:

```bash
# Create new migration file
cat > data/migrations/002_add_new_feature.sql << 'EOF'
-- Migration: 002_add_new_feature
-- Add new column to track feature X

ALTER TABLE candidates ADD COLUMN new_field VARCHAR(255);
CREATE INDEX idx_candidates_new_field ON candidates(new_field);
EOF

# Test on your instance
python data/migrations/__init__.py

# Commit ONLY the SQL file
git add data/migrations/002_add_new_feature.sql
git commit -m "feat(database): Add new_field to candidates table"
```

### Step 3: Deploy to another instance (dev → staging)

On the staging machine:

```bash
# Pull latest code (includes new .sql migration files)
git pull origin development

# Apply pending migrations to staging's own database
python data/migrations/__init__.py

# Output:
# ✅ Applied migration: 001_initial_schema
# ✅ Applied migration: 002_add_new_feature
# ✅ Database schema is up-to-date!
```

**Result:** Staging's data is preserved, only schema is updated!

### Step 4: Deploy to production

```bash
# On production server
git pull origin development
python data/migrations/__init__.py

# Staging and Production both now have the same schema
# But keep their own separate data
```

## 🔄 Data Synchronization (Optional)

If you need to sync specific data (not schema) between instances:

```python
# Export candidate list from dev
from core.database import Database
db_dev = Database("data/cv_generator.db")
candidates = db_dev.get_all_candidates()

# Manual export to JSON
import json
with open("export_candidates.json", "w") as f:
    json.dump([c.to_dict() for c in candidates], f)

# Manually import on staging (with review)
# This is separate from schema migrations!
```

## 📋 Check Migration Status

```bash
# See what's applied and what's pending
python data/migrations/__init__.py

# Output:
# ============================================================
# DATABASE SCHEMA STATUS
# ============================================================
# 
# ✅ Applied migrations (2):
#    - 001_initial_schema
#    - 002_add_new_feature
# 
# ✅ All migrations applied!
```

## 🚨 Data Protection Rules

| Action | Dev | Staging | Production |
|--------|-----|---------|-----------|
| Run migrations | ✅ Yes | ✅ Yes | ✅ Yes |
| Commit .sql files | ✅ Yes | ✅ Yes | ✅ Yes |
| Commit .db file | ❌ No | ❌ No | ❌ No |
| Share data between instances | ⚠️ Manual only | ⚠️ Manual only | ⚠️ Manual only |

## 🛡️ Safety Checks

All migrations use **IF NOT EXISTS** to be idempotent:

```sql
-- Safe - can run multiple times
CREATE TABLE IF NOT EXISTS candidates (...);
CREATE INDEX IF NOT EXISTS idx_candidates ON candidates(email);

-- Dangerous - avoid in migrations
ALTER TABLE candidates ADD COLUMN field VARCHAR(255);
-- ^ This will fail if column already exists
```

If you need to add columns safely:

```sql
-- Safe way to add column
ALTER TABLE candidates ADD COLUMN new_field VARCHAR(255) DEFAULT NULL;
```

## 📝 Migration File Naming

```
data/migrations/NNN_descriptive_name.sql
```

- `NNN` = 3-digit number (001, 002, 003...)
- Names must be unique and never change once applied
- Applied migrations are tracked in `schema_migrations` table

## 🔍 Examples

### Add a new table

```sql
-- Migration: 003_add_job_applications.sql
CREATE TABLE IF NOT EXISTS job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    job_profile_id INTEGER NOT NULL,
    status TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id)
);

CREATE INDEX IF NOT EXISTS idx_job_applications_candidate 
    ON job_applications(candidate_id);
```

### Add a column (safely)

```sql
-- Migration: 004_add_rating_to_candidates.sql
ALTER TABLE candidates ADD COLUMN rating INTEGER DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_candidates_rating ON candidates(rating);
```

### Fix data consistency (careful!)

```sql
-- Migration: 005_fix_null_emails.sql
UPDATE candidates SET email = 'unknown@example.com' WHERE email IS NULL;
```

## ⚠️ Common Mistakes

❌ **Committing database file:**
```bash
git add data/cv_generator.db  # WRONG!
```

❌ **Modifying applied migrations:**
```bash
# WRONG - never modify files after they're applied!
# data/migrations/001_initial_schema.sql was applied, 
# don't change it now!
```

❌ **Using database state to track schema:**
```bash
# WRONG - schema lives in Git, not in .db file
git ignore data/cv_generator.db
git add data/cv_generator.db  # contradiction!
```

✅ **Correct approach:**
```bash
git add data/migrations/*.sql   # Schema only
git ignore data/cv_generator.db  # Data stays local
```

## 🚀 For CI/CD Automation

```bash
#!/bin/bash
# deploy.sh - Run on each instance

echo "🔄 Pulling latest code..."
git pull origin development

echo "🔄 Applying database migrations..."
python data/migrations/__init__.py || exit 1

echo "✅ Deployment complete!"
echo "   Each instance has its own data"
echo "   All instances share same schema"
```

## 📞 Summary

- ✅ `.sql` migration files = version controlled
- ✅ `data/cv_generator.db` = local to each instance  
- ✅ Each instance independently applies migrations
- ✅ No data conflicts between instances
- ✅ Safe for parallel production & staging environments
