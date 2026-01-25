"""Unit tests for Arabic language processor."""

import pytest

from text_glosser.core.language_processors.arabic import ArabicProcessor
from text_glosser.core.language_processors.base import MorphologicalAnalyzer, TokenSegment
from text_glosser.core.language_processors.qalsadi_analyzer import QalsadiAnalyzer


class TestArabicProcessor:
    """Tests for ArabicProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a test Arabic processor."""
        return ArabicProcessor()

    def test_normalize_strips_diacritics(self, processor):
        """Test that normalization removes diacritics (tashkeel)."""
        # يَكْتُبُونَ (yaktubuna - they write) with vowel marks
        word_with_diacritics = "يَكْتُبُونَ"
        result = processor.normalize(word_with_diacritics)
        # Should remove the diacritics
        assert result == "يكتبون"

    def test_normalize_strips_tatweel(self, processor):
        """Test that normalization removes tatweel (kashida)."""
        # Word with tatweel
        word_with_tatweel = "كـتـب"
        result = processor.normalize(word_with_tatweel)
        assert result == "كتب"

    def test_normalize_alef_variants(self, processor):
        """Test that normalization converts alef variants."""
        # أ إ آ should all become ا
        text = "أإآ"
        result = processor.normalize(text)
        assert result == "ااا"

    def test_normalize_preserves_text_without_diacritics(self, processor):
        """Test that normalization preserves text without diacritics."""
        text = "كتب"
        result = processor.normalize(text)
        assert result == "كتب"

    def test_lemmatize_verb_form(self, processor):
        """Test lemmatization of conjugated verb form."""
        # يكتبون (they write) should lemmatize to كتب (write)
        word = "يكتبون"
        lemmas = processor.lemmatize(word)
        assert len(lemmas) > 0
        # The root should be كتب
        assert "كتب" in lemmas

    def test_lemmatize_noun_form(self, processor):
        """Test lemmatization of noun form."""
        # كتابات (writings) should lemmatize to كتاب (book/writing)
        word = "كتابات"
        lemmas = processor.lemmatize(word)
        assert len(lemmas) > 0
        assert "كتاب" in lemmas

    def test_lemmatize_with_article(self, processor):
        """Test lemmatization of word with definite article."""
        # المدرسة (the school) should lemmatize to مدرس or مدرسة
        word = "المدرسة"
        lemmas = processor.lemmatize(word)
        assert len(lemmas) > 0

    def test_is_language_text_arabic(self, processor):
        """Test detection of Arabic text."""
        arabic_text = "مرحبا"
        assert processor.is_language_text(arabic_text) is True

    def test_is_language_text_english(self, processor):
        """Test non-Arabic text detection."""
        english_text = "Hello"
        assert processor.is_language_text(english_text) is False

    def test_is_language_text_mixed(self, processor):
        """Test mixed Arabic/English text detection."""
        mixed_text = "Hello مرحبا"
        assert processor.is_language_text(mixed_text) is True

    def test_get_lookup_forms_includes_original(self, processor):
        """Test that get_lookup_forms includes original word."""
        word = "يكتبون"
        forms = processor.get_lookup_forms(word)
        assert word in forms

    def test_get_lookup_forms_includes_lemma(self, processor):
        """Test that get_lookup_forms includes lemma."""
        # يكتبون should produce lookup forms including the root كتب
        word = "يكتبون"
        forms = processor.get_lookup_forms(word)
        # Should include at least original and some lemma
        assert len(forms) >= 1
        # Root should be in the forms
        assert "كتب" in forms

    def test_get_lookup_forms_with_diacritics(self, processor):
        """Test get_lookup_forms with diacritical marks."""
        # Word with diacritics
        word_with_diacritics = "يَكْتُبُونَ"
        forms = processor.get_lookup_forms(word_with_diacritics)
        # Should include original
        assert word_with_diacritics in forms
        # Should include normalized form (without diacritics)
        assert "يكتبون" in forms
        # Should include lemma
        assert "كتب" in forms

    def test_language_code(self, processor):
        """Test that language code is set correctly."""
        assert processor.language_code == "ar"


class TestQalsadiAnalyzer:
    """Tests for QalsadiAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a test Qalsadi analyzer."""
        return QalsadiAnalyzer()

    def test_analyzer_is_available(self, analyzer):
        """Test that qalsadi is available."""
        assert analyzer.is_available() is True

    def test_analyzer_name(self, analyzer):
        """Test analyzer name."""
        assert analyzer.name == "Qalsadi Arabic Analyzer"

    def test_analyzer_language_code(self, analyzer):
        """Test analyzer language code."""
        assert analyzer.language_code == "ar"

    def test_analyze_simple_word(self, analyzer):
        """Test analysis of a simple word."""
        # كتاب (kitab - book)
        segments = analyzer.analyze_word("كتاب")
        assert len(segments) >= 1
        # The stem should be present
        stem_segment = segments[-1]  # Stem is typically last
        assert stem_segment.segment_text in ["كتاب", "kitab"]
        assert stem_segment.pos in ["NOUN", "UNKNOWN"]

    def test_analyze_word_with_prefix(self, analyzer):
        """Test analysis of word with prefix."""
        # وكتاب (wa-kitab - and a book)
        segments = analyzer.analyze_word("وكتاب")
        assert len(segments) >= 1
        # Should have at least the conjunction "و" and the stem
        segment_texts = [s.segment_text for s in segments]
        # Either parsed as multiple segments or single
        assert "و" in segment_texts or "وكتاب" in segment_texts

    def test_analyze_word_with_multiple_prefixes(self, analyzer):
        """Test analysis of word with multiple prefixes."""
        # وبكتاب (wa-bi-kitab - and with a book)
        segments = analyzer.analyze_word("وبكتاب")
        assert len(segments) >= 1
        # Should have segments for "و", "ب", and "كتاب"
        segment_texts = [s.segment_text for s in segments]
        # Check that we have multiple segments or at least parsed
        assert len(segment_texts) >= 1

    def test_analyze_returns_token_segments(self, analyzer):
        """Test that analyze_word returns TokenSegment objects."""
        segments = analyzer.analyze_word("كتاب")
        assert all(isinstance(s, TokenSegment) for s in segments)

    def test_analyze_segment_has_attributes(self, analyzer):
        """Test that TokenSegment has required attributes."""
        segments = analyzer.analyze_word("كتاب")
        segment = segments[0]
        # Check all attributes exist
        assert hasattr(segment, "segment_text")
        assert hasattr(segment, "lemma")
        assert hasattr(segment, "root")
        assert hasattr(segment, "pos")
        assert hasattr(segment, "gloss")
        assert hasattr(segment, "features")


class TestMorphologicalAnalyzerInterface:
    """Tests for MorphologicalAnalyzer interface."""

    def test_token_segment_creation(self):
        """Test TokenSegment can be created with all fields."""
        segment = TokenSegment(
            segment_text="و",
            lemma="و",
            root="",
            pos="CONJ",
            gloss="and",
            features={"type": "conjunction"},
        )
        assert segment.segment_text == "و"
        assert segment.lemma == "و"
        assert segment.pos == "CONJ"
        assert segment.gloss == "and"
        assert segment.features == {"type": "conjunction"}

    def test_token_segment_defaults(self):
        """Test TokenSegment has sensible defaults."""
        segment = TokenSegment(segment_text="test")
        assert segment.segment_text == "test"
        assert segment.lemma == ""
        assert segment.root == ""
        assert segment.pos == ""
        assert segment.gloss == ""
        assert segment.features == {}


class TestArabicProcessorWithAnalyzer:
    """Tests for ArabicProcessor integration with MorphologicalAnalyzer."""

    def test_processor_has_default_analyzer(self):
        """Test that ArabicProcessor has a default analyzer."""
        processor = ArabicProcessor()
        assert processor.get_analyzer() is not None
        assert isinstance(processor.get_analyzer(), MorphologicalAnalyzer)

    def test_processor_uses_qalsadi_by_default(self):
        """Test that ArabicProcessor uses QalsadiAnalyzer by default."""
        processor = ArabicProcessor()
        assert isinstance(processor.get_analyzer(), QalsadiAnalyzer)

    def test_processor_can_swap_analyzer(self):
        """Test that analyzer can be swapped at runtime."""
        processor = ArabicProcessor()
        original_analyzer = processor.get_analyzer()

        # Create a new analyzer and swap
        new_analyzer = QalsadiAnalyzer()
        processor.set_analyzer(new_analyzer)

        assert processor.get_analyzer() is new_analyzer
        assert processor.get_analyzer() is not original_analyzer

    def test_processor_analyze_word(self):
        """Test that processor.analyze_word delegates to analyzer."""
        processor = ArabicProcessor()
        segments = processor.analyze_word("كتاب")
        assert len(segments) >= 1
        assert all(isinstance(s, TokenSegment) for s in segments)

    def test_processor_analyze_word_with_prefix(self):
        """Test processor handles words with prefixes."""
        processor = ArabicProcessor()
        segments = processor.analyze_word("وبكتاب")
        # Should return at least one segment
        assert len(segments) >= 1

    def test_custom_analyzer_injection(self):
        """Test that custom analyzer can be injected via constructor."""

        class MockAnalyzer(MorphologicalAnalyzer):
            name = "Mock Analyzer"
            language_code = "ar"

            def analyze_word(self, word: str) -> list[TokenSegment]:
                return [TokenSegment(segment_text=word, pos="MOCK")]

            def is_available(self) -> bool:
                return True

        mock = MockAnalyzer()
        processor = ArabicProcessor(analyzer=mock)

        assert processor.get_analyzer() is mock
        segments = processor.analyze_word("test")
        assert segments[0].pos == "MOCK"
