"""
Log Formatter Utility - Provides formatted log messages with timestamps and icons.

Usage:
    from scripts.log_formatter import format_log
    
    print(format_log("PROFILE", "Processing Stellenprofil PDF..."))
    print(format_log("RETRY", "Extraction attempt 1/3"))
    print(format_log("API", "Sending request to OpenAI API..."))
    
Output:
    [10:15:23] 📋 [PROFILE] Processing Stellenprofil PDF...
    [10:15:24] 🔄 [RETRY] Extraction attempt 1/3
    [10:15:28] 🌐 [API] Sending request to OpenAI API...
"""

from datetime import datetime
from typing import Optional


# Icon mapping for different log tags
ICON_MAP = {
    "PROFILE": "📋",      # Job Profile
    "RETRY": "🔄",        # Retry attempt
    "PDF": "📄",          # PDF processing
    "SCHEMA": "⚙️",       # Schema loading
    "API": "🌐",          # API call
    "OK": "✅",           # Success
    "ERROR": "❌",        # Error
    "WARN": "⚠️",         # Warning
    "INFO": "ℹ️",         # Information
    "FOLDER": "📂",       # Folder creation
    "SAVE": "💾",         # File save
    "START": "🚀",        # Start
    "PARALLEL": "⚡",     # Parallel processing
    "COMPARE": "📊",      # Comparison
    "PARSE": "🔍",        # Parsing
    "VALIDATE": "✔️",     # Validation
    "MATCH": "🎯",        # Match/Matching
    "EXTRACT": "📥",      # Extraction
    "GENERATE": "✨",     # Generation
    "DOWNLOAD": "📥",     # Download
    "UPLOAD": "📤",       # Upload
    "DELETE": "🗑️",       # Delete
    "UPDATE": "🔄",       # Update
    "LOAD": "⏳",          # Loading
    "PROCESS": "⚙️",      # Processing
}


def format_log(tag: str, message: str, include_timestamp: bool = True) -> str:
    """
    Format a log message with timestamp and icon.
    
    Args:
        tag: Log tag/category (e.g., "PROFILE", "API", "ERROR")
        message: The log message
        include_timestamp: Whether to include timestamp (default: True)
        
    Returns:
        Formatted log string ready for printing
        
    Examples:
        >>> print(format_log("API", "Calling OpenAI API"))
        [10:15:28] 🌐 [API] Calling OpenAI API
        
        >>> print(format_log("ERROR", "Connection failed"))
        [10:15:30] ❌ [ERROR] Connection failed
    """
    # Get icon for tag, default to generic 📌 if tag not found
    icon = ICON_MAP.get(tag, "📌")
    
    # Format timestamp if requested
    if include_timestamp:
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] {icon} [{tag}] {message}"
    else:
        return f"{icon} [{tag}] {message}"


def batch_log(tag: str, message: str) -> str:
    """
    Convenience function for batch processing logs (always includes timestamp).
    
    Args:
        tag: Log tag/category
        message: The log message
        
    Returns:
        Formatted log string
    """
    return format_log(tag, message, include_timestamp=True)
