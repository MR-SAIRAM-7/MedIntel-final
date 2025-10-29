"""
Utility functions for MedIntel application.
"""
from datetime import datetime
from typing import Optional, Dict
import re
import logging

logger = logging.getLogger("medintel.utils")


def prepare_for_mongo(data: dict) -> dict:
    """
    Prepare data for MongoDB storage by converting datetime objects to ISO format.
    
    Args:
        data: Dictionary containing data to prepare
        
    Returns:
        Dictionary with datetime objects converted to ISO strings
    """
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
    return data


def detect_language_preference(msg: str) -> Optional[str]:
    """
    Detect language preference from user message.
    
    Args:
        msg: User message to analyze
        
    Returns:
        Detected language code or None
    """
    if not msg:
        return None
    
    message_lower = msg.lower()
    
    # Updated language patterns with correct regex
    language_patterns = {
        'english': [
            r'\b(english|speak english|talk in english|use english)\b',
        ],
        'hindi': [
            r'\b(hindi|हिंदी|हिन्दी|speak hindi|talk in hindi|use hindi)\b',
            r'(मुझसे हिंदी में बात करो|हिंदी में बोलो)',
        ],
        'spanish': [
            r'\b(spanish|español|espanol|speak spanish|talk in spanish|use spanish)\b',
            r'(habla español|en español)',
        ],
        'tamil': [
            r'\b(tamil|தமிழ்|speak tamil|talk in tamil|use tamil)\b',
            r'(தமிழில் பேசு|தமிழில் பேசவும்)',
        ],
        'telugu': [
            r'\b(telugu|తెలుగు|speak telugu|talk in telugu|use telugu)\b',
            r'(తెలుగులో మాట్లాడు|తెలుగులో మాట్లాడండి)',
        ],
        'kannada': [
            r'\b(kannada|ಕನ್ನಡ|speak kannada|talk in kannada|use kannada)\b',
            r'(ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ)',
        ],
        'malayalam': [
            r'\b(malayalam|മലയാളം|speak malayalam|talk in malayalam|use malayalam)\b',
            r'(മലയാളത്തിൽ സംസാരിക്കുക|മലയാളത്തിൽ സംസാരിക്കൂ)',
        ],
        'punjabi': [
            r'\b(punjabi|ਪੰਜਾਬੀ|speak punjabi|talk in punjabi|use punjabi)\b',
            r'(ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰੋ)',
        ],
        'gujarati': [
            r'\b(gujarati|ગુજરાતી|speak gujarati|talk in gujarati|use gujarati)\b',
            r'(ગુજરાતીમાં વાત કરો)',
        ],
        'marathi': [
            r'\b(marathi|मराठी|speak marathi|talk in marathi|use marathi)\b',
            r'(मराठीत बोल)',
        ],
        'bengali': [
            r'\b(bengali|বাংলা|speak bengali|talk in bengali|use bengali)\b',
            r'(বাংলায় কথা বলুন)',
        ],
        'odia': [
            r'\b(odia|ଓଡ଼ିଆ|speak odia|talk in odia|use odia)\b',
            r'(ଓଡ଼ିଆରେ କଥା ହୁଅନ୍ତୁ)',
        ],
        'assamese': [
            r'\b(assamese|অসমীয়া|speak assamese|talk in assamese|use assamese)\b',
            r'(অসমীয়াত কথা পাতক)',
        ],
        'urdu': [
            r'\b(urdu|اردو|speak urdu|talk in urdu|use urdu)\b',
        ],
        'chinese': [
            r'\b(chinese|中文|speak chinese|talk in chinese|use chinese)\b',
        ],
        'arabic': [
            r'\b(arabic|عربية|speak arabic|talk in arabic|use arabic)\b',
        ],
        'japanese': [
            r'\b(japanese|日本語|speak japanese|talk in japanese|use japanese)\b',
        ]
    }
    
    for language, patterns in language_patterns.items():
        for pattern in patterns:
            try:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return language
            except re.error as e:
                logger.error(f"Regex error for pattern {pattern}: {e}")
                continue
    
    return None


def validate_file_type(content_type: str, allowed_types: list) -> bool:
    """
    Validate if file content type is allowed.
    
    Args:
        content_type: MIME type of the file
        allowed_types: List of allowed MIME types or prefixes
        
    Returns:
        True if file type is allowed, False otherwise
    """
    for allowed_type in allowed_types:
        if content_type.startswith(allowed_type.rstrip("*")):
            return True
    return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
