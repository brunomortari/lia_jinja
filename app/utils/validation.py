"""
Utilities for data validation and sanitization.

This module provides validation and sanitization helpers for schemas and
business logic, including text sanitization, dictionary validation, and
field name validation to prevent injection attacks.
"""

import re
import html
from typing import Dict, Any

# ========== VALIDATION CONSTANTS ==========

# Maximum character limits for various field types
MAX_FIELD_LENGTH = 50000  # 50KB per field
MAX_PROMPT_LENGTH = 5000  # 5KB for prompts
MAX_CAMPO_NAME_LENGTH = 100  # Field name


# ========== SANITIZATION HELPERS ==========

def sanitize_text(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Sanitize text by removing potentially dangerous content and limiting size.

    This function:
    - Escapes HTML to prevent XSS attacks
    - Truncates text to maximum allowed length
    - Returns empty string if input is None/empty

    Args:
        text (str): Input text to sanitize.
        max_length (int, optional): Maximum allowed length. Defaults to MAX_FIELD_LENGTH.

    Returns:
        str: Sanitized and truncated text.
    """
    if not text:
        return ""
    # Limit size
    text = text[:max_length]
    # Escape HTML (prevents XSS)
    text = html.escape(text)
    return text


def validate_campo_name(campo: str) -> bool:
    """Validate if a field name is safe.

    Only allows alphanumeric characters and underscores to prevent
    dictionary key injection attacks.

    Args:
        campo (str): Field name to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not campo or len(campo) > MAX_CAMPO_NAME_LENGTH:
        return False
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', campo))


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """Recursively sanitize a dictionary.

    Traverses the dictionary structure and applies sanitization to all
    string values, removes invalid keys, and limits nesting depth.

    Args:
        data (Dict[str, Any]): Dictionary to sanitize.
        max_depth (int, optional): Maximum recursion depth to prevent infinite loops.
            Defaults to 5.

    Returns:
        Dict[str, Any]: New sanitized dictionary.
    """
    if max_depth <= 0:
        return {}

    result = {}
    for key, value in data.items():
        # Validate key
        if not isinstance(key, str) or len(key) > MAX_CAMPO_NAME_LENGTH:
            continue

        # Sanitize value
        if isinstance(value, str):
            result[key] = sanitize_text(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, max_depth - 1) if isinstance(item, dict)
                else sanitize_text(item) if isinstance(item, str)
                else item
                for item in value[:1000]  # Limit list to 1000 items
            ]
        elif isinstance(value, (int, float, bool, type(None))):
            result[key] = value
        # Ignore other types

    return result
