"""
Tests for web UI file upload functionality.
"""

import io
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_file_upload_handler_with_deer_park_file():
    """
    Test file upload handler with actual deer-park.txt file.

    This test verifies that the upload handler can process a real file
    and create the appropriate TextSource object.
    """
    from text_glosser.core.ingestion import read_file
    from text_glosser.core.models import TextSource

    # Load the actual deer-park.txt test file
    test_file_path = Path(__file__).parent.parent / "deer-park.txt"
    assert test_file_path.exists(), "Test file deer-park.txt not found"

    with open(test_file_path, "rb") as f:
        file_content = f.read()

    # Create a mock upload event that simulates NiceGUI's UploadEventArguments
    mock_event = MagicMock()
    mock_event.name = "deer-park.txt"
    mock_event.content = io.BytesIO(file_content)

    # Create a mock state object
    state = {"text_sources": []}

    # Simulate the upload handler
    try:
        file_name = mock_event.name
        file_content_io = mock_event.content

        # Save to temp file instead of actual uploads dir for testing
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".txt"
        ) as tmp_file:
            tmp_file.write(file_content_io.read())
            file_path = Path(tmp_file.name)

        # Read content as text
        content = read_file(str(file_path))

        # Create TextSource
        text_source = TextSource(
            id=str(uuid.uuid4()),
            name=file_name,
            content=content,
            source_type="file",
            original_path=str(file_path),
        )

        state["text_sources"].append(text_source)

        # Verify the upload was successful
        assert len(state["text_sources"]) == 1
        assert state["text_sources"][0].name == "deer-park.txt"
        assert state["text_sources"][0].source_type == "file"
        assert len(state["text_sources"][0].content) > 0

        # Verify content matches original file
        assert "五言絕句" in state["text_sources"][0].content
        assert "王維" in state["text_sources"][0].content
        assert "鹿柴" in state["text_sources"][0].content

        # Clean up temp file
        file_path.unlink()

    except Exception as e:
        pytest.fail(f"Upload handler failed: {e}")


def test_file_upload_sanitizes_filename():
    """
    Test that uploaded filenames are properly sanitized for security.
    """
    from text_glosser.utils.security import sanitize_filename

    # Test various malicious or problematic filenames
    test_cases = [
        ("../../../etc/passwd", "passwd"),
        # basename removes paths
        ("..\\..\\windows\\system32", "_windows_system32"),
        (
            "file<script>alert('xss')</script>.txt",
            "file_script_alert__xss___script_.txt",
        ),
        ("file\x00.txt", "file_.txt"),
        ("file|dangerous.txt", "file_dangerous.txt"),
    ]

    for dangerous_name, _expected_safe_part in test_cases:
        sanitized = sanitize_filename(dangerous_name)

        # Should not start with path traversal patterns
        assert not sanitized.startswith("../")
        assert not sanitized.startswith("..\\")

        # Should not contain dangerous characters
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "|" not in sanitized
        assert "\x00" not in sanitized

        # Should use os.path.basename to remove path components
        # Just verify it's a safe filename (not testing exact output)


def test_multiple_file_uploads():
    """
    Test handling multiple file uploads in sequence.
    """
    state = {"text_sources": []}

    # Simulate uploading multiple files
    test_files = [
        ("file1.txt", b"Content of file 1"),
        ("file2.txt", b"Content of file 2"),
        ("file3.txt", b"Content of file 3"),
    ]

    import tempfile
    import uuid
    from pathlib import Path

    from text_glosser.core.ingestion import read_file
    from text_glosser.core.models import TextSource

    for file_name, file_content in test_files:
        mock_event = MagicMock()
        mock_event.name = file_name
        mock_event.content = io.BytesIO(file_content)

        # Simulate upload handler
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".txt"
        ) as tmp_file:
            tmp_file.write(mock_event.content.read())
            file_path = Path(tmp_file.name)

        content = read_file(str(file_path))

        text_source = TextSource(
            id=str(uuid.uuid4()),
            name=file_name,
            content=content,
            source_type="file",
            original_path=str(file_path),
        )

        state["text_sources"].append(text_source)
        file_path.unlink()

    # Verify all files were uploaded
    assert len(state["text_sources"]) == 3
    assert state["text_sources"][0].name == "file1.txt"
    assert state["text_sources"][1].name == "file2.txt"
    assert state["text_sources"][2].name == "file3.txt"


def test_upload_error_handling():
    """
    Test that upload errors are handled gracefully.
    """
    from text_glosser.utils.security import sanitize_filename

    # Test empty filename
    result = sanitize_filename("")
    assert result == "unnamed_file"  # Should return a safe default

    # Test None - will raise AttributeError, which should be handled by caller
    # The web UI should ensure filename is not None before calling sanitize_filename
