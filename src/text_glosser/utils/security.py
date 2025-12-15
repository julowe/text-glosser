"""
Security utilities for input sanitization and validation.

This module provides functions to sanitize user inputs and prevent
code injection attacks and other security vulnerabilities.
"""

import os
import re
from pathlib import Path

# ISO 639 language code patterns
ISO_639_1_PATTERN = re.compile(r"^[a-z]{2}$")
# ISO 639-2 and 639-3 both use 3-letter codes with the same pattern
ISO_639_2_PATTERN = re.compile(r"^[a-z]{3}$")
ISO_639_3_PATTERN = ISO_639_2_PATTERN  # Same pattern as ISO 639-2


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.

    Parameters
    ----------
    filename : str
        The filename to sanitize

    Returns
    -------
    str
        Sanitized filename

    Examples
    --------
    >>> sanitize_filename("../../../etc/passwd")
    'passwd'
    >>> sanitize_filename("my file.txt")
    'my_file.txt'
    """
    # Remove any path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    # Allow only alphanumeric, dash, underscore, and period
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Prevent hidden files
    if filename.startswith("."):
        filename = "_" + filename[1:]

    # Ensure it's not empty
    if not filename:
        filename = "unnamed_file"

    return filename


def sanitize_session_id(session_id: str) -> str | None:
    """
    Validate and sanitize a session ID.

    Parameters
    ----------
    session_id : str
        Session ID to validate

    Returns
    -------
    Optional[str]
        Sanitized session ID or None if invalid

    Examples
    --------
    >>> sanitize_session_id("abc123-def456")
    'abc123-def456'
    >>> sanitize_session_id("../../../etc/passwd")
    None
    """
    # Session IDs should be alphanumeric with optional hyphens
    if not re.match(r"^[a-zA-Z0-9-]{8,64}$", session_id):
        return None

    return session_id


def validate_iso_639_codes(codes_str: str) -> tuple[bool, list[str], str]:
    """
    Validate and parse ISO 639 language codes from a comma-separated string.

    Parameters
    ----------
    codes_str : str
        Comma-separated language codes

    Returns
    -------
    tuple[bool, List[str], str]
        (is_valid, cleaned_codes_list, error_message)

    Examples
    --------
    >>> validate_iso_639_codes("en, fr, de")
    (True, ['en', 'fr', 'de'], '')
    >>> validate_iso_639_codes("en, INVALID, de")
    (False, [], 'Invalid language code: INVALID')
    """
    # Remove extra whitespace and split
    codes = [code.strip().lower() for code in codes_str.split(",") if code.strip()]

    if not codes:
        return False, [], "No language codes provided"

    valid_codes = []
    for code in codes:
        # Check if it matches any ISO 639 pattern
        if (
            ISO_639_1_PATTERN.match(code)
            or ISO_639_2_PATTERN.match(code)
            or ISO_639_3_PATTERN.match(code)
        ):
            valid_codes.append(code)
        else:
            return False, [], f"Invalid language code: {code}"

    return True, valid_codes, ""


def sanitize_url(url: str) -> str | None:
    """
    Validate and sanitize a URL.

    Parameters
    ----------
    url : str
        URL to validate

    Returns
    -------
    Optional[str]
        Sanitized URL or None if invalid

    Examples
    --------
    >>> sanitize_url("https://example.com/page")
    'https://example.com/page'
    >>> sanitize_url("javascript:alert(1)")
    None
    """
    # Only allow http and https
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return None

    # Prevent javascript: and data: URLs
    if re.search(r"(javascript|data|file):", url, re.IGNORECASE):
        return None

    return url


def sanitize_text_content(content: str, max_length: int = 10_000_000) -> str:
    """
    Sanitize text content to prevent script injection.

    Parameters
    ----------
    content : str
        Text content to sanitize
    max_length : int, optional
        Maximum allowed length (default: 10MB as characters)

    Returns
    -------
    str
        Sanitized text content

    Notes
    -----
    This removes any HTML/JavaScript tags and limits the content length.
    """
    # Limit content length to prevent DoS
    content = content[:max_length]

    # Remove any HTML tags
    content = re.sub(r"<[^>]+>", "", content)

    # Remove any script-like patterns
    # (handle various whitespace and attributes in closing tags)
    # Use a more robust pattern that handles edge cases like </script attr>
    # or </script \t\n>
    content = re.sub(
        r"<script[^>]*>.*?</script[\s\S]*?>",
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return content


def is_safe_path(path: str, base_dir: str) -> bool:
    """
    Check if a path is safe (within base_dir and doesn't traverse).

    Parameters
    ----------
    path : str
        Path to check
    base_dir : str
        Base directory that path should be within

    Returns
    -------
    bool
        True if path is safe, False otherwise

    Examples
    --------
    >>> is_safe_path("/app/data/file.txt", "/app/data")
    True
    >>> is_safe_path("/etc/passwd", "/app/data")
    False
    """
    try:
        base = Path(base_dir).resolve()
        target = Path(path).resolve()

        # Check if target is relative to base
        target.relative_to(base)
        return True
    except (ValueError, RuntimeError):
        return False


def validate_retention_days(days: int | None) -> tuple[bool, int | None, str]:
    """
    Validate session retention days setting.

    Parameters
    ----------
    days : Optional[int]
        Number of days to retain session data

    Returns
    -------
    tuple[bool, Optional[int], str]
        (is_valid, validated_value, error_message)

    Examples
    --------
    >>> validate_retention_days(180)
    (True, 180, '')
    >>> validate_retention_days(400)
    (False, None, 'Retention days must be between 0 and 365')
    """
    if days is None:
        return True, None, ""

    if not isinstance(days, int):
        return False, None, "Retention days must be an integer"

    if days < 0 or days > 365:
        return False, None, "Retention days must be between 0 and 365"

    # Convert 0 to None (indefinite)
    if days == 0:
        return True, None, ""

    return True, days, ""
