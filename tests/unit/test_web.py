"""
Tests for web UI functionality.
"""


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
