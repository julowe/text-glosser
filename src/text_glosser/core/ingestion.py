"""
Text ingestion from files and URLs.

This module handles reading text from various sources and sanitizing it.
"""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ..utils.security import sanitize_text_content, sanitize_url


def read_file(file_path: str, max_size: int = 10_000_000) -> str:
    """
    Read text from a file.

    Parameters
    ----------
    file_path : str
        Path to the file
    max_size : int, optional
        Maximum file size in bytes (default: 10MB)

    Returns
    -------
    str
        File contents

    Raises
    ------
    ValueError
        If file is too large
    FileNotFoundError
        If file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file size
    if path.stat().st_size > max_size:
        raise ValueError(
            f"File too large: {path.stat().st_size} bytes (max: {max_size})"
        )

    # Read file
    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return sanitize_text_content(content, max_size)


def fetch_url(url: str, max_size: int = 10_000_000, timeout: int = 30) -> str:
    """
    Fetch text content from a URL.

    This function extracts only the visible text from a web page,
    ignoring scripts, styles, and other non-text content.

    Parameters
    ----------
    url : str
        URL to fetch
    max_size : int, optional
        Maximum content size in bytes (default: 10MB)
    timeout : int, optional
        Request timeout in seconds (default: 30)

    Returns
    -------
    str
        Extracted text content

    Raises
    ------
    ValueError
        If URL is invalid or content is too large
    requests.RequestException
        If request fails
    """
    # Sanitize URL
    clean_url = sanitize_url(url)
    if not clean_url:
        raise ValueError(f"Invalid URL: {url}")

    # Fetch content
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TextGlosser/0.1.0)"}

    response = requests.get(clean_url, headers=headers, timeout=timeout, stream=True)
    response.raise_for_status()

    # Check content size
    content_length = response.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        raise ValueError(f"Content too large: {content_length} bytes (max: {max_size})")

    # Read content in chunks to enforce size limit
    content_bytes = b""
    for chunk in response.iter_content(chunk_size=8192):
        content_bytes += chunk
        if len(content_bytes) > max_size:
            raise ValueError(f"Content exceeded maximum size: {max_size} bytes")

    # Parse HTML and extract text
    soup = BeautifulSoup(content_bytes, "lxml")

    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    # Get text
    text = soup.get_text()

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)

    return sanitize_text_content(text, max_size)


def validate_source_accessible(source_path: str, source_type: str) -> bool:
    """
    Validate that a source (file or URL) is accessible.

    Parameters
    ----------
    source_path : str
        Path to file or URL
    source_type : str
        Either 'file' or 'url'

    Returns
    -------
    bool
        True if accessible, False otherwise
    """
    try:
        if source_type == "file":
            return Path(source_path).exists()
        elif source_type == "url":
            clean_url = sanitize_url(source_path)
            if not clean_url:
                return False
            response = requests.head(clean_url, timeout=10)
            return response.status_code == 200
        return False
    except Exception:
        return False
