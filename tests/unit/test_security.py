"""Unit tests for security utilities."""

from text_glosser.utils.security import (
    is_safe_path,
    sanitize_filename,
    sanitize_session_id,
    sanitize_url,
    validate_iso_639_codes,
    validate_retention_days,
)


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_simple_filename(self):
        """Test sanitizing a simple filename."""
        assert sanitize_filename("test.txt") == "test.txt"

    def test_path_traversal(self):
        """Test preventing path traversal."""
        # os.path.basename removes all path components, leaving just the filename
        assert sanitize_filename("../../../etc/passwd") == "passwd"

    def test_spaces(self):
        """Test handling spaces."""
        assert sanitize_filename("my file.txt") == "my_file.txt"

    def test_hidden_files(self):
        """Test preventing hidden files."""
        assert sanitize_filename(".hidden") == "_hidden"

    def test_empty_string(self):
        """Test handling empty string."""
        assert sanitize_filename("") == "unnamed_file"


class TestSanitizeSessionId:
    """Tests for session ID validation."""

    def test_valid_session_id(self):
        """Test valid session ID."""
        assert sanitize_session_id("abc123-def456-ghi789") == "abc123-def456-ghi789"

    def test_invalid_characters(self):
        """Test invalid characters."""
        assert sanitize_session_id("../../../etc/passwd") is None

    def test_too_short(self):
        """Test too short ID."""
        assert sanitize_session_id("abc") is None

    def test_too_long(self):
        """Test too long ID."""
        assert sanitize_session_id("a" * 100) is None


class TestValidateIso639Codes:
    """Tests for ISO 639 code validation."""

    def test_valid_single_code(self):
        """Test valid single language code."""
        valid, codes, error = validate_iso_639_codes("en")
        assert valid is True
        assert codes == ["en"]
        assert error == ""

    def test_valid_multiple_codes(self):
        """Test valid multiple language codes."""
        valid, codes, error = validate_iso_639_codes("en, fr, de")
        assert valid is True
        assert codes == ["en", "fr", "de"]
        assert error == ""

    def test_invalid_code(self):
        """Test invalid language code."""
        valid, codes, error = validate_iso_639_codes("en, INVALID, de")
        assert valid is False
        assert "Invalid language code" in error

    def test_empty_string(self):
        """Test empty string."""
        valid, codes, error = validate_iso_639_codes("")
        assert valid is False
        assert "No language codes" in error

    def test_three_letter_codes(self):
        """Test three-letter codes."""
        valid, codes, error = validate_iso_639_codes("eng, fra")
        assert valid is True
        assert codes == ["eng", "fra"]


class TestSanitizeUrl:
    """Tests for URL sanitization."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        assert sanitize_url("http://example.com") == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        assert sanitize_url("https://example.com/page") == "https://example.com/page"

    def test_javascript_url(self):
        """Test blocking javascript: URLs."""
        assert sanitize_url("javascript:alert(1)") is None

    def test_data_url(self):
        """Test blocking data: URLs."""
        assert sanitize_url("data:text/html,<script>alert(1)</script>") is None

    def test_file_url(self):
        """Test blocking file: URLs."""
        assert sanitize_url("file:///etc/passwd") is None

    def test_no_protocol(self):
        """Test URL without protocol."""
        assert sanitize_url("example.com") is None


class TestIsSafePath:
    """Tests for path safety checking."""

    def test_safe_path(self, tmp_path):
        """Test safe path within base directory."""
        base_dir = str(tmp_path)
        safe_path = str(tmp_path / "file.txt")
        assert is_safe_path(safe_path, base_dir) is True

    def test_unsafe_path(self, tmp_path):
        """Test unsafe path outside base directory."""
        base_dir = str(tmp_path / "subdir")
        unsafe_path = "/etc/passwd"
        assert is_safe_path(unsafe_path, base_dir) is False


class TestValidateRetentionDays:
    """Tests for retention days validation."""

    def test_valid_days(self):
        """Test valid retention days."""
        valid, value, error = validate_retention_days(180)
        assert valid is True
        assert value == 180
        assert error == ""

    def test_none_value(self):
        """Test None (indefinite retention)."""
        valid, value, error = validate_retention_days(None)
        assert valid is True
        assert value is None
        assert error == ""

    def test_zero_converts_to_none(self):
        """Test zero converts to None."""
        valid, value, error = validate_retention_days(0)
        assert valid is True
        assert value is None
        assert error == ""

    def test_negative_value(self):
        """Test negative value is invalid."""
        valid, value, error = validate_retention_days(-1)
        assert valid is False
        assert "between 0 and 365" in error

    def test_too_large_value(self):
        """Test value > 365 is invalid."""
        valid, value, error = validate_retention_days(400)
        assert valid is False
        assert "between 0 and 365" in error
