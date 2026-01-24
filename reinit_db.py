"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
import os
from core.database.db import Database
from core.database.translations import initialize_translations

if os.path.exists('cv_generator.db'):
    os.remove('cv_generator.db')
    print('🗑️  Old database removed')

db = Database('cv_generator.db')
print('✅ Database initialized')

tm = initialize_translations(db)
print('✅ Translations initialized')

print('\n✨ Done!')
