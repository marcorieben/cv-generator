"""
Translations module for multilingual UI support
Handles loading and caching translations from database
Supports dynamic translation switching without app restart
"""

import json
from typing import Dict, Optional
from pathlib import Path


class TranslationsManager:
    """
    Manages multilingual translations from database
    Provides fallback to JSON for initialization
    """
    
    SUPPORTED_LANGUAGES = ['de', 'en', 'fr']
    SECTIONS = ['ui', 'cv', 'offer', 'job_profile']
    
    def __init__(self, db=None):
        """
        Initialize translations manager
        
        Args:
            db: Database instance (optional, for lazy loading)
        """
        self.db = db
        self._cache: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._json_fallback: Dict = {}
        self._load_json_fallback()
    
    def _load_json_fallback(self):
        """Load translations from JSON file as fallback"""
        paths = [
            Path(__file__).parent.parent / "scripts" / "translations.json",
            Path("scripts") / "translations.json",
            Path("translations.json")
        ]
        
        for path in paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self._json_fallback = json.load(f)
                    return
                except Exception as e:
                    print(f"⚠️ Error loading translations.json from {path}: {e}")
                    continue
    
    def load_from_database(self):
        """
        Load all translations from database
        Populates cache for faster access
        """
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT section, key, language, value 
                    FROM translations
                    ORDER BY section, key, language
                """)
                
                rows = cursor.fetchall()
                
                # Build cache structure
                cache = {}
                for row in rows:
                    section, key, language, value = row
                    
                    if section not in cache:
                        cache[section] = {}
                    if key not in cache[section]:
                        cache[section][key] = {}
                    
                    cache[section][key][language] = value
                
                self._cache = cache
                return True
        
        except Exception as e:
            print(f"⚠️ Error loading translations from database: {e}")
            return False
    
    def seed_from_json(self):
        """
        Seed database with translations from JSON file
        Called during initialization if DB is empty
        
        Returns: (success, message)
        """
        if not self.db or not self._json_fallback:
            return False, "Database or JSON fallback not available"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if translations already exist
                cursor.execute("SELECT COUNT(*) FROM translations")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    return True, f"Translations already seeded ({count} entries)"
                
                # Insert translations from JSON
                inserted = 0
                for section, keys in self._json_fallback.items():
                    if section not in self.SECTIONS:
                        continue
                    
                    for key, translations in keys.items():
                        if isinstance(translations, dict):
                            for language, value in translations.items():
                                if language in self.SUPPORTED_LANGUAGES:
                                    cursor.execute("""
                                        INSERT OR IGNORE INTO translations 
                                        (section, key, language, value)
                                        VALUES (?, ?, ?, ?)
                                    """, (section, key, language, value))
                                    inserted += cursor.rowcount
                
                conn.commit()
                return True, f"Seeded {inserted} translation entries"
        
        except Exception as e:
            return False, f"Error seeding translations: {str(e)}"
    
    def get(self, section: str, key: str, language: str = 'de') -> str:
        """
        Get translation for a specific key
        
        Falls back through: Cache → JSON → Key itself
        
        Args:
            section: Translation section (ui, cv, offer, job_profile)
            key: Translation key
            language: Language code (de, en, fr)
        
        Returns: Translated text or key if not found
        """
        # Try cache first
        if section in self._cache and key in self._cache[section]:
            if language in self._cache[section][key]:
                return self._cache[section][key][language]
        
        # Try JSON fallback
        if section in self._json_fallback and key in self._json_fallback[section]:
            trans = self._json_fallback[section][key]
            if isinstance(trans, dict) and language in trans:
                return trans[language]
        
        # Return key as fallback
        return key
    
    def get_all(self, section: str, language: str = 'de') -> Dict[str, str]:
        """
        Get all translations for a section in a specific language
        
        Args:
            section: Translation section
            language: Language code
        
        Returns: Dictionary of key -> translation
        """
        result = {}
        
        # Get from cache first
        if section in self._cache:
            for key, translations in self._cache[section].items():
                if language in translations:
                    result[key] = translations[language]
        
        # Fill gaps from JSON
        if section in self._json_fallback:
            for key, translations in self._json_fallback[section].items():
                if key not in result and isinstance(translations, dict) and language in translations:
                    result[key] = translations[language]
        
        return result
    
    def set(self, section: str, key: str, language: str, value: str) -> bool:
        """
        Set or update a translation in database
        
        Args:
            section: Translation section
            key: Translation key
            language: Language code
            value: Translation value
        
        Returns: Success status
        """
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO translations 
                    (section, key, language, value)
                    VALUES (?, ?, ?, ?)
                """, (section, key, language, value))
                conn.commit()
                
                # Update cache
                if section not in self._cache:
                    self._cache[section] = {}
                if key not in self._cache[section]:
                    self._cache[section][key] = {}
                
                self._cache[section][key][language] = value
                return True
        
        except Exception as e:
            print(f"❌ Error setting translation: {e}")
            return False
    
    def delete(self, section: str, key: str, language: Optional[str] = None) -> bool:
        """
        Delete translation(s) from database
        
        Args:
            section: Translation section
            key: Translation key
            language: Language code (if None, deletes all languages for this key)
        
        Returns: Success status
        """
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if language:
                    cursor.execute("""
                        DELETE FROM translations 
                        WHERE section = ? AND key = ? AND language = ?
                    """, (section, key, language))
                else:
                    cursor.execute("""
                        DELETE FROM translations 
                        WHERE section = ? AND key = ?
                    """, (section, key))
                
                conn.commit()
                
                # Update cache
                if section in self._cache and key in self._cache[section]:
                    if language:
                        if language in self._cache[section][key]:
                            del self._cache[section][key][language]
                    else:
                        del self._cache[section][key]
                
                return True
        
        except Exception as e:
            print(f"❌ Error deleting translation: {e}")
            return False


# Global instance
_translations_manager: Optional[TranslationsManager] = None


def initialize_translations(db=None) -> TranslationsManager:
    """
    Initialize global translations manager
    
    Args:
        db: Database instance
    
    Returns: TranslationsManager instance
    """
    global _translations_manager
    _translations_manager = TranslationsManager(db)
    
    # Load from database if available
    if db:
        if not _translations_manager.load_from_database():
            # Seed from JSON if database is empty
            success, msg = _translations_manager.seed_from_json()
            if success:
                _translations_manager.load_from_database()
    
    return _translations_manager


def get_translations() -> TranslationsManager:
    """Get global translations manager instance"""
    global _translations_manager
    if _translations_manager is None:
        _translations_manager = TranslationsManager()
    return _translations_manager


def t(section: str, key: str, language: str = 'de') -> str:
    """
    Convenience function to get translation
    
    Usage: t('ui', 'sidebar_title', 'de')
    """
    return get_translations().get(section, key, language)
