"""Unit tests for exporters module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from text_glosser.core.exporters import (
    _convert_html_to_markdown,
    _strip_html_for_conllu,
    export_all_formats,
    format_conllu,
    format_json,
    format_markdown,
)
from text_glosser.core.models import (
    LineAnalysis,
    SessionConfig,
    TextAnalysis,
    TextSource,
    WordDefinition,
)


class TestConvertHtmlToMarkdown:
    """Tests for _convert_html_to_markdown function."""

    def test_bold_tags_to_markdown(self):
        """Test conversion of bold HTML tags to markdown."""
        assert _convert_html_to_markdown("<b>bold</b>") == "**bold**"
        assert _convert_html_to_markdown("<strong>strong</strong>") == "**strong**"

    def test_italic_tags_to_markdown(self):
        """Test conversion of italic HTML tags to markdown."""
        assert _convert_html_to_markdown("<i>italic</i>") == "*italic*"
        assert _convert_html_to_markdown("<em>emphasis</em>") == "*emphasis*"

    def test_line_breaks_to_newlines(self):
        """Test conversion of HTML line breaks to newlines."""
        assert _convert_html_to_markdown("line1<br>line2") == "line1\nline2"
        assert _convert_html_to_markdown("line1<br/>line2") == "line1\nline2"
        assert _convert_html_to_markdown("line1<br />line2") == "line1\nline2"

    def test_paragraphs_to_newlines(self):
        """Test conversion of paragraph tags to newlines."""
        result = _convert_html_to_markdown("<p>para1</p><p>para2</p>")
        assert "para1" in result
        assert "para2" in result

    def test_font_tags_stripped(self):
        """Test that font tags are stripped but content is kept."""
        result = _convert_html_to_markdown('<font color="red">colored text</font>')
        assert result == "colored text"

    def test_html_entities_decoded(self):
        """Test that HTML entities are decoded."""
        assert _convert_html_to_markdown("&amp;") == "&"
        assert _convert_html_to_markdown("&lt;") == "<"
        assert _convert_html_to_markdown("&gt;") == ">"
        assert _convert_html_to_markdown("&quot;") == '"'

    def test_empty_string(self):
        """Test handling of empty string."""
        assert _convert_html_to_markdown("") == ""

    def test_none_input(self):
        """Test handling of None input."""
        assert _convert_html_to_markdown(None) is None

    def test_multiple_consecutive_newlines_collapsed(self):
        """Test that multiple consecutive newlines are collapsed."""
        result = _convert_html_to_markdown("<br><br><br>text")
        # Should not have more than one newline before text
        assert "\n\n\n" not in result


class TestStripHtmlForConllu:
    """Tests for _strip_html_for_conllu function."""

    def test_line_breaks_to_semicolons(self):
        """Test conversion of line breaks to ;;."""
        result = _strip_html_for_conllu("line1<br>line2")
        assert ";;" in result

    def test_paragraphs_to_semicolons(self):
        """Test conversion of paragraphs to ;;."""
        result = _strip_html_for_conllu("<p>para1</p><p>para2</p>")
        assert ";;" in result

    def test_tabs_and_newlines_removed(self):
        """Test that tabs and newlines are converted to spaces."""
        result = _strip_html_for_conllu("text\twith\ttabs")
        assert "\t" not in result
        result = _strip_html_for_conllu("text\nwith\nnewlines")
        assert "\n" not in result

    def test_html_entities_decoded(self):
        """Test that HTML entities are decoded."""
        result = _strip_html_for_conllu("&amp;")
        assert result == "&"

    def test_empty_string(self):
        """Test handling of empty string."""
        assert _strip_html_for_conllu("") == ""

    def test_none_input(self):
        """Test handling of None input."""
        assert _strip_html_for_conllu(None) is None


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis for testing."""
        return TextAnalysis(
            source_id="test-1",
            source_name="Test Source",
            total_lines=2,
            total_words=4,
            dictionaries_used=["dict1", "dict2"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="hello",
                            definitions=["a greeting"],
                            source_dict="dict1",
                            grammatical_info={"lemma": "hello"},
                        ),
                        WordDefinition(
                            word="world",
                            definitions=["the earth"],
                            source_dict="dict1",
                        ),
                    ],
                ),
                LineAnalysis(
                    line_number=2,
                    words=[
                        WordDefinition(
                            word="test",
                            definitions=["a trial", "an examination"],
                            source_dict="dict2",
                            grammatical_info={"lemmas": ["test", "testing"]},
                        ),
                    ],
                ),
            ],
            errors=["Some words not found"],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

    def test_header_includes_source_name(self, sample_analysis):
        """Test that header includes source name."""
        result = format_markdown(sample_analysis)
        assert "# Analysis of Test Source" in result

    def test_metadata_section(self, sample_analysis):
        """Test that metadata section is included."""
        result = format_markdown(sample_analysis)
        assert "**Line count:** 2" in result
        assert "**Word count:** 4" in result
        assert "dict1" in result
        assert "dict2" in result

    def test_errors_section(self, sample_analysis):
        """Test that errors are included."""
        result = format_markdown(sample_analysis)
        assert "**Problems encountered:**" in result
        assert "Some words not found" in result

    def test_word_definitions(self, sample_analysis):
        """Test that word definitions are formatted correctly."""
        result = format_markdown(sample_analysis)
        assert "hello:" in result
        assert "a greeting;" in result
        assert "world:" in result
        assert "the earth;" in result

    def test_lemmas_displayed(self, sample_analysis):
        """Test that lemmas are displayed when available."""
        result = format_markdown(sample_analysis)
        assert "Lemma(s):" in result
        assert "hello" in result

    def test_multiple_lemmas_displayed(self, sample_analysis):
        """Test that multiple lemmas are displayed."""
        result = format_markdown(sample_analysis)
        assert "test" in result
        assert "testing" in result

    def test_line_numbers(self, sample_analysis):
        """Test that line numbers are included."""
        result = format_markdown(sample_analysis)
        assert "## Line 1" in result
        assert "## Line 2" in result

    def test_html_in_definitions_converted(self):
        """Test that HTML in definitions is converted to markdown."""
        analysis = TextAnalysis(
            source_id="test-1",
            source_name="Test",
            total_lines=1,
            total_words=1,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="test",
                            definitions=["<b>bold</b> definition"],
                            source_dict="dict1",
                        ),
                    ],
                ),
            ],
            timestamp=datetime.now(),
        )
        result = format_markdown(analysis)
        assert "**bold**" in result
        assert "<b>" not in result


class TestFormatJson:
    """Tests for format_json function."""

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis for testing."""
        return TextAnalysis(
            source_id="test-1",
            source_name="Test Source",
            total_lines=1,
            total_words=2,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="hello",
                            definitions=["a greeting"],
                            source_dict="dict1",
                            grammatical_info={"pos": "noun"},
                        ),
                    ],
                ),
            ],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

    @pytest.fixture
    def sample_config(self):
        """Create a sample session config for testing."""
        return SessionConfig(
            session_id="session-123",
            text_sources=[
                TextSource(
                    id="src-1",
                    name="Source 1",
                    content="hello world",
                    source_type="file",
                    original_path="/path/to/file.txt",
                ),
            ],
            selected_resources=["dict1", "dict2"],
            created_at=datetime(2026, 1, 25, 11, 0, 0),
        )

    def test_valid_json_output(self, sample_analysis):
        """Test that output is valid JSON."""
        result = format_json(sample_analysis)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_metadata_section(self, sample_analysis):
        """Test that metadata is included."""
        result = format_json(sample_analysis)
        parsed = json.loads(result)
        assert parsed["metadata"]["source_id"] == "test-1"
        assert parsed["metadata"]["source_name"] == "Test Source"
        assert parsed["metadata"]["total_lines"] == 1
        assert parsed["metadata"]["total_words"] == 2

    def test_lines_section(self, sample_analysis):
        """Test that lines are included."""
        result = format_json(sample_analysis)
        parsed = json.loads(result)
        assert len(parsed["lines"]) == 1
        assert parsed["lines"][0]["line_number"] == 1
        assert len(parsed["lines"][0]["words"]) == 1

    def test_word_data(self, sample_analysis):
        """Test that word data is complete."""
        result = format_json(sample_analysis)
        parsed = json.loads(result)
        word = parsed["lines"][0]["words"][0]
        assert word["word"] == "hello"
        assert word["definitions"] == ["a greeting"]
        assert word["source_dict"] == "dict1"
        assert word["grammatical_info"]["pos"] == "noun"

    def test_config_included_when_provided(self, sample_analysis, sample_config):
        """Test that config is included when provided."""
        result = format_json(sample_analysis, config=sample_config)
        parsed = json.loads(result)
        assert "configuration" in parsed
        assert parsed["configuration"]["session_id"] == "session-123"

    def test_config_excluded_when_not_requested(self, sample_analysis, sample_config):
        """Test that config is excluded when include_config=False."""
        result = format_json(
            sample_analysis, config=sample_config, include_config=False
        )
        parsed = json.loads(result)
        assert "configuration" not in parsed

    def test_unicode_preserved(self):
        """Test that Unicode characters are preserved."""
        analysis = TextAnalysis(
            source_id="test-1",
            source_name="اختبار",  # Arabic "test"
            total_lines=1,
            total_words=1,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="كتاب",
                            definitions=["book"],
                            source_dict="dict1",
                        ),
                    ],
                ),
            ],
            timestamp=datetime.now(),
        )
        result = format_json(analysis)
        assert "اختبار" in result
        assert "كتاب" in result


class TestFormatConllu:
    """Tests for format_conllu function."""

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis for testing."""
        return TextAnalysis(
            source_id="test-1",
            source_name="Test Source",
            total_lines=1,
            total_words=2,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="hello",
                            definitions=["a greeting"],
                            source_dict="dict1",
                            grammatical_info={"lemma": "hello"},
                        ),
                        WordDefinition(
                            word="world",
                            definitions=["the earth"],
                            source_dict="dict1",
                        ),
                    ],
                ),
            ],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

    def test_metadata_comments(self, sample_analysis):
        """Test that metadata comments are included."""
        result = format_conllu(sample_analysis)
        assert "# source_name = Test Source" in result
        assert "# total_lines = 1" in result
        assert "# total_words = 2" in result

    def test_sent_id_comment(self, sample_analysis):
        """Test that sent_id comment is included."""
        result = format_conllu(sample_analysis)
        assert "# sent_id = line_1" in result

    def test_text_comment(self, sample_analysis):
        """Test that text comment is included."""
        result = format_conllu(sample_analysis)
        assert "# text = hello world" in result

    def test_word_format(self, sample_analysis):
        """Test that words are formatted with tab-separated fields."""
        result = format_conllu(sample_analysis)
        lines = result.split("\n")
        # Find the first word line (non-comment, non-empty)
        word_lines = [line for line in lines if line and not line.startswith("#")]
        assert len(word_lines) == 2

        # Check first word has correct format
        fields = word_lines[0].split("\t")
        assert len(fields) == 10  # CoNLL-U has 10 fields
        assert fields[0] == "1"  # ID
        assert fields[1] == "hello"  # FORM
        assert fields[2] == "hello"  # LEMMA

    def test_lemma_column(self, sample_analysis):
        """Test that lemma is placed in correct column."""
        result = format_conllu(sample_analysis)
        lines = result.split("\n")
        word_lines = [line for line in lines if line and not line.startswith("#")]
        fields = word_lines[0].split("\t")
        assert fields[2] == "hello"  # LEMMA column

    def test_underscore_for_missing_lemma(self, sample_analysis):
        """Test that underscore is used for missing lemma."""
        result = format_conllu(sample_analysis)
        lines = result.split("\n")
        word_lines = [line for line in lines if line and not line.startswith("#")]
        # Second word has no lemma
        fields = word_lines[1].split("\t")
        assert fields[2] == "_"  # LEMMA column

    def test_misc_contains_definitions(self, sample_analysis):
        """Test that MISC field contains definitions."""
        result = format_conllu(sample_analysis)
        assert "Definitions=" in result
        assert "a greeting" in result

    def test_misc_contains_source_dict(self, sample_analysis):
        """Test that MISC field contains source dictionary."""
        result = format_conllu(sample_analysis)
        assert "SourceDict=dict1" in result

    def test_html_stripped_from_definitions(self):
        """Test that HTML is stripped from definitions."""
        analysis = TextAnalysis(
            source_id="test-1",
            source_name="Test",
            total_lines=1,
            total_words=1,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="test",
                            definitions=["<b>bold</b> text"],
                            source_dict="dict1",
                        ),
                    ],
                ),
            ],
            timestamp=datetime.now(),
        )
        result = format_conllu(analysis)
        assert "<b>" not in result
        assert "bold text" in result

    def test_multiple_lemmas_comma_separated(self):
        """Test that multiple lemmas are comma-separated."""
        analysis = TextAnalysis(
            source_id="test-1",
            source_name="Test",
            total_lines=1,
            total_words=1,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="test",
                            definitions=["definition"],
                            source_dict="dict1",
                            grammatical_info={"lemmas": ["lemma1", "lemma2"]},
                        ),
                    ],
                ),
            ],
            timestamp=datetime.now(),
        )
        result = format_conllu(analysis)
        lines = result.split("\n")
        word_lines = [line for line in lines if line and not line.startswith("#")]
        fields = word_lines[0].split("\t")
        assert "lemma1,lemma2" in fields[2]


class TestExportAllFormats:
    """Tests for export_all_formats function."""

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis for testing."""
        return TextAnalysis(
            source_id="test-1",
            source_name="Test Source",
            total_lines=1,
            total_words=1,
            dictionaries_used=["dict1"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="hello",
                            definitions=["a greeting"],
                            source_dict="dict1",
                        ),
                    ],
                ),
            ],
            timestamp=datetime.now(),
        )

    def test_creates_all_three_formats(self, sample_analysis):
        """Test that all three formats are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_all_formats(sample_analysis, tmpdir, "test")
            assert "markdown" in paths
            assert "json" in paths
            assert "conllu" in paths

    def test_files_exist(self, sample_analysis):
        """Test that files are actually created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_all_formats(sample_analysis, tmpdir, "test")
            assert Path(paths["markdown"]).exists()
            assert Path(paths["json"]).exists()
            assert Path(paths["conllu"]).exists()

    def test_correct_extensions(self, sample_analysis):
        """Test that files have correct extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_all_formats(sample_analysis, tmpdir, "test")
            assert paths["markdown"].endswith(".md")
            assert paths["json"].endswith(".json")
            assert paths["conllu"].endswith(".conllu")

    def test_files_contain_content(self, sample_analysis):
        """Test that files contain actual content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_all_formats(sample_analysis, tmpdir, "test")

            # Check markdown
            with open(paths["markdown"], encoding="utf-8") as f:
                md_content = f.read()
            assert "hello" in md_content

            # Check JSON
            with open(paths["json"], encoding="utf-8") as f:
                json_content = f.read()
            assert "hello" in json_content

            # Check CoNLL-U
            with open(paths["conllu"], encoding="utf-8") as f:
                conllu_content = f.read()
            assert "hello" in conllu_content

    def test_creates_output_directory(self, sample_analysis):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "subdir" / "another"
            paths = export_all_formats(sample_analysis, str(new_dir), "test")
            assert new_dir.exists()
            assert Path(paths["markdown"]).exists()

    def test_with_config(self, sample_analysis):
        """Test export with session config."""
        config = SessionConfig(
            session_id="test-session",
            text_sources=[
                TextSource(
                    id="src-1",
                    name="Test",
                    content="hello",
                    source_type="file",
                ),
            ],
            selected_resources=["dict1"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_all_formats(sample_analysis, tmpdir, "test", config=config)

            # Check that JSON includes config
            with open(paths["json"], encoding="utf-8") as f:
                data = json.load(f)
            assert "configuration" in data
            assert data["configuration"]["session_id"] == "test-session"


class TestArabicTextExport:
    """Tests for exporting Arabic text."""

    @pytest.fixture
    def arabic_analysis(self):
        """Create an analysis with Arabic text."""
        return TextAnalysis(
            source_id="test-ar",
            source_name="اختبار عربي",
            total_lines=1,
            total_words=2,
            dictionaries_used=["lane-arabic-english"],
            lines=[
                LineAnalysis(
                    line_number=1,
                    words=[
                        WordDefinition(
                            word="كتاب",
                            definitions=["a book", "a writing"],
                            source_dict="lane-arabic-english",
                            grammatical_info={
                                "lemma": "كِتَابٌ",
                                "root": "كتب",
                            },
                        ),
                        WordDefinition(
                            word="جميل",
                            definitions=["beautiful", "handsome"],
                            source_dict="lane-arabic-english",
                            grammatical_info={"lemmas": ["جَمِيلٌ"]},
                        ),
                    ],
                ),
            ],
            timestamp=datetime.now(),
        )

    def test_markdown_preserves_arabic(self, arabic_analysis):
        """Test that markdown format preserves Arabic text."""
        result = format_markdown(arabic_analysis)
        assert "كتاب" in result
        assert "جميل" in result
        assert "كِتَابٌ" in result

    def test_json_preserves_arabic(self, arabic_analysis):
        """Test that JSON format preserves Arabic text."""
        result = format_json(arabic_analysis)
        parsed = json.loads(result)
        assert parsed["metadata"]["source_name"] == "اختبار عربي"
        assert parsed["lines"][0]["words"][0]["word"] == "كتاب"

    def test_conllu_preserves_arabic(self, arabic_analysis):
        """Test that CoNLL-U format preserves Arabic text."""
        result = format_conllu(arabic_analysis)
        assert "كتاب" in result
        assert "جميل" in result
        # Lemmas should be in the output
        assert "كِتَابٌ" in result
