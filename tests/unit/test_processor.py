"""Unit tests for text processor."""

import pytest

from text_glosser.core.models import (
    DictionaryFormat,
    DictionaryResource,
    ResourceType,
    TextSource,
)
from text_glosser.core.processor import TextProcessor
from text_glosser.core.registry import ResourceRegistry


class TestTextProcessor:
    """Tests for TextProcessor class."""

    @pytest.fixture
    def registry(self):
        """Create a test registry."""
        return ResourceRegistry(resources_dir="/tmp/test_resources")

    @pytest.fixture
    def processor(self, registry):
        """Create a test processor."""
        return TextProcessor(registry)

    def test_tokenize_english_text(self, processor):
        """Test tokenization of English text."""
        text = "Hello world, this is a test."
        tokens = processor._tokenize(text)
        assert tokens == ["Hello", "world", "this", "is", "a", "test"]

    def test_tokenize_chinese_characters(self, processor):
        """Test that Chinese characters are tokenized individually."""
        text = "五言絕句"
        tokens = processor._tokenize(text)
        # Each Chinese character should be a separate token
        assert tokens == ["五", "言", "絕", "句"]

    def test_tokenize_mixed_chinese_and_english(self, processor):
        """Test tokenization of mixed Chinese and English text."""
        text = "Hello 世界 test"
        tokens = processor._tokenize(text)
        # English words stay together, Chinese chars separate
        assert "Hello" in tokens
        assert "test" in tokens
        assert "世" in tokens
        assert "界" in tokens

    def test_tokenize_chinese_with_punctuation(self, processor):
        """Test Chinese text with punctuation."""
        text = "王維，空山不見人"
        tokens = processor._tokenize(text)
        # Each character should be separate, punctuation excluded
        expected = ["王", "維", "空", "山", "不", "見", "人"]
        assert tokens == expected

    def test_tokenize_multiline_chinese(self, processor):
        """Test tokenization preserves behavior across lines."""
        text = "五言絕句\n但聞人語響"
        # Tokenize doesn't handle newlines, that's done at a higher level
        # Just test that the characters are separated
        tokens = processor._tokenize(text)
        assert "五" in tokens
        assert "言" in tokens
        assert "但" in tokens
        assert "聞" in tokens

    def test_tokenize_arabic_text(self, processor):
        """Test that Arabic text is tokenized as words (not character-by-character)."""
        text = "مرحبا بك"
        tokens = processor._tokenize(text)
        # Arabic should be tokenized as words, not individual characters
        assert len(tokens) == 2

    def test_tokenize_empty_string(self, processor):
        """Test tokenization of empty string."""
        tokens = processor._tokenize("")
        assert tokens == []

    def test_tokenize_whitespace_only(self, processor):
        """Test tokenization of whitespace."""
        tokens = processor._tokenize("   \n\t  ")
        assert tokens == []

    def test_tokenize_hebrew_text(self, processor):
        """Test that Hebrew text is tokenized as words."""
        text = "שָׁלוֹם עוֹלָם"  # "Peace world" with vowel points
        tokens = processor._tokenize(text)
        # Hebrew should be tokenized as words, vowel points preserved
        assert len(tokens) == 2

    def test_tokenize_greek_text(self, processor):
        """Test that Greek text is tokenized as words."""
        text = "Ἐν ἀρχῇ ἦν ὁ λόγος"  # "In the beginning was the Word"
        tokens = processor._tokenize(text)
        # Greek should be tokenized as words
        assert len(tokens) == 5
        assert "Ἐν" in tokens
        assert "λόγος" in tokens

    def test_tokenize_sanskrit_devanagari(self, processor):
        """Test that Sanskrit/Devanagari text is tokenized as words."""
        text = "नमस्ते जगत्"  # "Greetings world"
        tokens = processor._tokenize(text)
        # Devanagari should be tokenized as words
        assert len(tokens) == 2

    def test_tokenize_latin_with_diacritics(self, processor):
        """Test that Latin text with macrons is tokenized correctly."""
        text = "Gallia omnis dīvīsa est"  # With macrons
        tokens = processor._tokenize(text)
        assert len(tokens) == 4
        assert "dīvīsa" in tokens

    def test_tokenize_arabic_with_diacritics(self, processor):
        """Test Arabic text with tashkeel (vowel marks)."""
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"  # Bismillah with full diacritics
        tokens = processor._tokenize(text)
        # Should be tokenized as 4 words, preserving diacritics
        assert len(tokens) == 4

    def test_tokenize_mixed_scripts(self, processor):
        """Test tokenization of text with multiple scripts."""
        text = "Hello שָׁלוֹם مرحبا 你好"
        tokens = processor._tokenize(text)
        # English, Hebrew, Arabic as words; Chinese as individual chars
        assert "Hello" in tokens
        assert "שָׁלוֹם" in tokens
        assert "مرحبا" in tokens
        assert "你" in tokens
        assert "好" in tokens
        assert len(tokens) == 5

    def test_analyze_text_with_chinese_characters(self, registry, processor):
        """Test full analysis with Chinese characters."""
        # Register a mock Chinese resource
        registry.register_resource(
            DictionaryResource(
                id="test-chinese",
                name="Test Chinese",
                format=DictionaryFormat.HANZIPY,
                resource_type=ResourceType.LIBRARY,
                primary_language="zh",
                secondary_languages=["en"],
            )
        )

        source = TextSource(
            id="test-1",
            name="Chinese Test",
            content="五言",
            source_type="file",
        )

        analysis = processor.analyze_text(source, ["test-chinese"])

        # Should process 2 characters
        assert analysis.total_words == 2
        # Each character should be analyzed separately
        if len(analysis.lines) > 0:
            # Check that we have individual character lookups
            assert any(
                wd.word == "五" for line in analysis.lines for wd in line.words
            ) or any("五" in err for err in analysis.errors)


class TestCamelToolsIntegration:
    """Tests for CAMeL Tools processor integration."""

    @pytest.fixture
    def registry(self):
        """Create a test registry with CAMeL Tools."""
        return ResourceRegistry(resources_dir="/tmp/test_resources")

    @pytest.fixture
    def processor(self, registry):
        """Create a test processor."""
        return TextProcessor(registry)

    def test_camel_tools_resource_registered(self, registry):
        """Test that CAMeL Tools is registered in the registry."""
        resource = registry.get_resource("camel-tools-arabic")
        assert resource is not None
        assert resource.name == "CAMeL Tools - Arabic Morphological Analyzer"
        assert resource.resource_type == ResourceType.GRAMMAR_TOOL
        assert resource.primary_language == "ar"

    def test_get_parser_creates_camel_tools_analyzer(self, processor, registry):
        """Test that _get_parser creates a CamelToolsAnalyzer for camel-tools-arabic."""
        resource = registry.get_resource("camel-tools-arabic")
        assert resource is not None

        # Get the parser (analyzer)
        parser = processor._get_parser(resource)

        # Parser should be a CamelToolsAnalyzer instance
        from text_glosser.core.language_processors.camel_analyzer import (
            CamelToolsAnalyzer,
        )

        assert isinstance(parser, CamelToolsAnalyzer)

    def test_lookup_word_with_camel_tools_fallback(self, processor, registry):
        """Test that _lookup_word works with CAMeL Tools in fallback mode."""
        from unittest.mock import MagicMock, patch

        from text_glosser.core.language_processors.base import TokenSegment

        resource = registry.get_resource("camel-tools-arabic")
        assert resource is not None

        # Create a mock analyzer that returns fallback (word analysis unavailable)
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_word.return_value = [
            TokenSegment(
                segment_text="كتاب",
                lemma="كتاب",
                root="",
                pos="UNKNOWN",
                gloss="",
            )
        ]

        # Patch the parser
        processor.parsers["camel-tools-arabic"] = mock_analyzer

        result = processor._lookup_word("كتاب", resource)

        # Should get a result with morphological analysis
        assert result is not None
        assert "definitions" in result
        assert len(result["definitions"]) > 0
        assert "Morphological Analysis" in result["definitions"][0]

    def test_lookup_word_with_camel_tools_segments(self, processor, registry):
        """Test that _lookup_word correctly parses CAMeL Tools segments."""
        from unittest.mock import MagicMock

        from text_glosser.core.language_processors.base import TokenSegment

        resource = registry.get_resource("camel-tools-arabic")
        assert resource is not None

        # Create a mock analyzer that returns proper segmentation
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_word.return_value = [
            TokenSegment(
                segment_text="و",
                lemma="و",
                root="",
                pos="CONJ",
                gloss="and",
            ),
            TokenSegment(
                segment_text="كتاب",
                lemma="كتاب",
                root="ك.ت.ب",
                pos="NOUN",
                gloss="",
            ),
        ]

        # Patch the parser
        processor.parsers["camel-tools-arabic"] = mock_analyzer

        result = processor._lookup_word("وكتاب", resource)

        # Should get a result with both segments
        assert result is not None
        assert "definitions" in result
        assert len(result["definitions"]) > 0

        # Check grammatical info contains segments
        assert result.get("grammatical_info") is not None
        assert "segments" in result["grammatical_info"]
        assert len(result["grammatical_info"]["segments"]) == 2
