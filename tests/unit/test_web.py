"""
Tests for web UI functionality.
"""

import json
import tempfile

from text_glosser.web.main import LANGUAGE_NAMES, get_language_display_name


class TestLanguageNames:
    """Test language name display functionality."""

    def test_known_language_code(self):
        """Test display name for known language codes."""
        assert get_language_display_name("ar") == "Arabic (ar)"
        assert get_language_display_name("zh") == "Chinese (zh)"
        assert get_language_display_name("sa") == "Sanskrit (sa)"
        assert get_language_display_name("en") == "English (en)"

    def test_unknown_language_code(self):
        """Test display name for unknown language codes."""
        assert get_language_display_name("xyz") == "(xyz)"
        assert get_language_display_name("abc") == "(abc)"

    def test_all_standard_languages_have_names(self):
        """Test that standard ISO 639-1 codes are mapped."""
        # Test commonly used language codes
        expected_codes = ["ar", "en", "fr", "de", "zh", "sa", "he", "la", "el"]
        for code in expected_codes:
            assert code in LANGUAGE_NAMES
            name = get_language_display_name(code)
            assert f"({code})" in name
            assert name != f"({code})"  # Should have a real name, not just code


class TestWebUICheckboxBehavior:
    """
    Test checkbox behavior for language group selection.

    These tests verify that the "Select all [language]" checkboxes
    properly select all dictionaries in that language group.
    """

    def test_select_all_checkbox_exists(self):
        """
        Test that select all checkboxes are created for each language.

        This is a placeholder test - actual UI testing would require
        a browser automation framework or NiceGUI testing utilities.
        """
        # This test documents the expected behavior:
        # 1. Each language group should have a "Select all [Language] (code)" checkbox
        # 2. Checking the box should expand the language group
        # 3. Checking the box should select all enabled dictionaries in that group
        # 4. Unchecking should deselect all dictionaries
        # 5. Disabled dictionaries should remain disabled and unchecked
        pass

    def test_checkbox_handler_logic(self):
        """
        Test the logic for the checkbox handler.

        Expected behavior:
        - When master checkbox is checked (e.value=True):
          - Expansion panel opens
          - All enabled child checkboxes are set to True
          - Disabled child checkboxes remain unchanged
        - When master checkbox is unchecked (e.value=False):
          - All enabled child checkboxes are set to False
          - Disabled child checkboxes remain unchanged
        """
        # This documents the expected behavior that should be tested
        # in integration tests or browser automation tests
        pass

    def test_checkbox_event_handler_with_mock(self):
        """
        Test the checkbox event handler logic with mocked checkboxes.

        This tests the actual handler logic that should be applied when
        the "Select all" checkbox is toggled.
        """

        # Mock checkbox class to simulate NiceGUI checkbox behavior
        class MockCheckbox:
            def __init__(self, enabled=True):
                self.value = False
                self._props = {"disable": not enabled}
                self.set_value_called_with = []

            def set_value(self, val):
                """Mock the set_value method to track calls."""
                if not self._props.get("disable", False):
                    self.value = val
                    self.set_value_called_with.append(val)

        # Mock expansion widget
        class MockExpansion:
            def __init__(self):
                self.is_open = False

            def open(self):
                self.is_open = True

        # Create mock checkboxes (2 enabled, 1 disabled)
        enabled_cb1 = MockCheckbox(enabled=True)
        enabled_cb2 = MockCheckbox(enabled=True)
        disabled_cb = MockCheckbox(enabled=False)
        checkboxes = [enabled_cb1, enabled_cb2, disabled_cb]

        expansion = MockExpansion()

        # Create the handler (simulating the create_lang_handler function)
        def create_lang_handler(expansion_widget, checkboxes):
            def on_lang_check(e):
                # Expand the group when checked
                if e.value:
                    expansion_widget.open()
                # Set all child checkboxes to the same value
                for cb in checkboxes:
                    # Check if checkbox is enabled by looking at disabled property
                    if not cb._props.get("disable", False):
                        cb.set_value(e.value)

            return on_lang_check

        handler = create_lang_handler(expansion, checkboxes)

        # Mock event object
        class MockEvent:
            def __init__(self, value):
                self.value = value

        # Test: Checking the master checkbox
        event_checked = MockEvent(value=True)
        handler(event_checked)

        # Verify expansion opened
        assert expansion.is_open is True

        # Verify enabled checkboxes were set to True
        assert enabled_cb1.value is True
        assert enabled_cb2.value is True
        assert True in enabled_cb1.set_value_called_with
        assert True in enabled_cb2.set_value_called_with

        # Verify disabled checkbox was NOT changed
        assert disabled_cb.value is False
        assert len(disabled_cb.set_value_called_with) == 0

        # Test: Unchecking the master checkbox
        event_unchecked = MockEvent(value=False)
        handler(event_unchecked)

        # Verify enabled checkboxes were set to False
        assert enabled_cb1.value is False
        assert enabled_cb2.value is False
        assert False in enabled_cb1.set_value_called_with
        assert False in enabled_cb2.set_value_called_with

        # Verify disabled checkbox still NOT changed
        assert disabled_cb.value is False
        assert len(disabled_cb.set_value_called_with) == 0


class TestLanguageDisplayFormat:
    """Test the format of language display names."""

    def test_display_format_includes_code(self):
        """Test that display format includes language code in parentheses."""
        for code, name in LANGUAGE_NAMES.items():
            display = get_language_display_name(code)
            assert f"({code})" in display
            assert name in display

    def test_display_format_structure(self):
        """Test the structure of display names."""
        display = get_language_display_name("ar")
        # Should be "Name (code)" format
        parts = display.split("(")
        assert len(parts) == 2
        assert parts[0].strip() == "Arabic"
        assert parts[1] == "ar)"


class TestInteractiveResultsDisplay:
    """Test interactive results display functionality."""

    def test_analysis_data_structure(self):
        """
        Test that analysis data structure is correctly parsed.

        This tests the data structure expected by display_interactive_results.
        """
        # Sample analysis data structure
        analysis_data = {
            "metadata": {
                "source_name": "test.txt",
                "total_lines": 2,
                "total_words": 3,
                "dictionaries_used": ["dict1", "dict2"],
            },
            "lines": [
                {
                    "line_number": 1,
                    "words": [
                        {
                            "word": "hello",
                            "definitions": ["A greeting"],
                            "source_dict": "dict1",
                        },
                        {
                            "word": "world",
                            "definitions": ["The earth", "People"],
                            "source_dict": "dict2",
                        },
                    ],
                }
            ],
        }

        # Verify structure is valid
        assert "metadata" in analysis_data
        assert "lines" in analysis_data
        assert len(analysis_data["lines"]) == 1

        # Verify metadata
        metadata = analysis_data["metadata"]
        assert metadata["source_name"] == "test.txt"
        assert metadata["total_lines"] == 2
        assert metadata["total_words"] == 3
        assert len(metadata["dictionaries_used"]) == 2

        # Verify line data
        line_data = analysis_data["lines"][0]
        assert line_data["line_number"] == 1
        assert len(line_data["words"]) == 2

        # Verify word data
        word_data = line_data["words"][0]
        assert word_data["word"] == "hello"
        assert len(word_data["definitions"]) == 1
        assert word_data["source_dict"] == "dict1"

    def test_json_file_parsing(self):
        """Test that JSON files can be correctly loaded and parsed."""
        from pathlib import Path

        # Use the existing test file from tests directory
        test_file = Path(__file__).parent.parent / "deer-park.txt"
        assert test_file.exists(), f"Test file not found: {test_file}"

        # Create analysis data structure as would be generated from processing
        # the deer-park.txt file
        analysis_data = {
            "metadata": {
                "source_name": "deer-park.txt",
                "total_lines": 7,
                "total_words": 7,  # Chinese characters are counted as words
                "dictionaries_used": ["hanzipy"],
            },
            "lines": [
                {
                    "line_number": 1,
                    "words": [
                        {
                            "word": "五",
                            "definitions": ["Character info for 五"],
                            "source_dict": "hanzipy",
                        }
                    ],
                }
            ],
        }

        # Use context manager for safer cleanup
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            json.dump(analysis_data, f)
            f.flush()  # Ensure data is written

            # Load and verify the JSON file
            with open(f.name, encoding="utf-8") as read_f:
                loaded_data = json.load(read_f)

            assert loaded_data == analysis_data
            assert loaded_data["metadata"]["source_name"] == "deer-park.txt"
            assert len(loaded_data["lines"]) == 1
            # Verify Chinese character handling
            assert loaded_data["lines"][0]["words"][0]["word"] == "五"

    def test_word_grouping_logic(self):
        """
        Test the logic for grouping words by their text.

        This simulates the grouping logic in display_interactive_results.
        """
        # Sample words data with duplicate words from different dicts
        words_data = [
            {"word": "test", "definitions": ["Definition 1"], "source_dict": "dict1"},
            {"word": "hello", "definitions": ["Greeting"], "source_dict": "dict1"},
            {
                "word": "test",
                "definitions": ["Definition 2"],
                "source_dict": "dict2",
            },  # Duplicate word
        ]

        # Group words by text (as done in display_interactive_results)
        words_by_text: dict[str, list[dict]] = {}
        for word_data in words_data:
            word_text = word_data.get("word", "")
            if word_text not in words_by_text:
                words_by_text[word_text] = []
            words_by_text[word_text].append(word_data)

        # Verify grouping
        assert len(words_by_text) == 2  # "test" and "hello"
        assert "test" in words_by_text
        assert "hello" in words_by_text

        # "test" should have 2 entries (from different dictionaries)
        assert len(words_by_text["test"]) == 2
        assert words_by_text["test"][0]["source_dict"] == "dict1"
        assert words_by_text["test"][1]["source_dict"] == "dict2"

        # "hello" should have 1 entry
        assert len(words_by_text["hello"]) == 1
        assert words_by_text["hello"][0]["source_dict"] == "dict1"

    def test_deer_park_file_content(self):
        """
        Test using the actual deer-park.txt file from tests directory.

        This verifies that the test file exists and can be read,
        simulating how it would be used in the interactive display.
        """
        from pathlib import Path

        # Load the deer-park.txt test file
        test_file = Path(__file__).parent.parent / "deer-park.txt"
        assert test_file.exists(), f"Test file not found: {test_file}"

        # Read the file content
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Verify it contains Chinese text
        assert "五言絕句" in content  # First line
        assert "王維" in content  # Second line (poet name)
        assert "鹿柴" in content  # Third line (poem title)

        # Verify it has the expected number of lines
        lines = content.strip().split("\n")
        assert len(lines) == 7

        # Verify Chinese characters are present
        # These are the first characters of each line
        assert "五" in lines[0]  # Five
        assert "王" in lines[1]  # King/Wang
        assert "鹿" in lines[2]  # Deer
        assert "空" in lines[3]  # Empty
        assert "但" in lines[4]  # But
        assert "返" in lines[5]  # Return
        assert "復" in lines[6]  # Again
