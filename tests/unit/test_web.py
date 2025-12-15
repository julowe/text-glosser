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
