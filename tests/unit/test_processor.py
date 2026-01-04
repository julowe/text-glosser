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
