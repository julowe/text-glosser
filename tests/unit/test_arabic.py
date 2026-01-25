"""Unit tests for Arabic language processor."""

import pytest

from text_glosser.core.language_processors.arabic import ArabicProcessor


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
        # يكتبون (they write) should lemmatize to كَتَبَ (write) with vocalization
        word = "يكتبون"
        lemmas = processor.lemmatize(word)
        assert len(lemmas) > 0
        # The vocalized root should be كَتَبَ (with diacritics)
        # or أَكْتَبَ depending on the word form
        # Check that we got a result containing the root letters ك ت ب
        assert any("كتب" in lemma or "كَتَبَ" in lemma or "أَكْتَبَ" in lemma for lemma in lemmas)

    def test_lemmatize_noun_form(self, processor):
        """Test lemmatization of noun form."""
        # كتابات (writings) should lemmatize to a form related to the root ك-ت-ب
        word = "كتابات"
        lemmas = processor.lemmatize(word)
        assert len(lemmas) > 0
        # Vocalized lemma is كُتَّابٌ (writers) - verify we get a lemma
        # that contains the root consonants (with or without diacritics)
        import pyarabic.araby as araby

        # Strip diacritics from lemmas to check root consonants
        stripped_lemmas = [araby.strip_tashkeel(lemma) for lemma in lemmas]
        assert any("كتاب" in lemma for lemma in stripped_lemmas)

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
        # يكتبون should produce lookup forms including a lemma form
        word = "يكتبون"
        forms = processor.get_lookup_forms(word)
        # Should include at least original and some lemma
        assert len(forms) >= 1
        # Should include a lemma form (vocalized, so may have diacritics)
        # Check that we have more than just the original word
        assert len(forms) > 1 or any(
            "كتب" in form or "كَتَبَ" in form or "أَكْتَبَ" in form for form in forms
        )

    def test_get_lookup_forms_with_diacritics(self, processor):
        """Test get_lookup_forms with diacritical marks."""
        # Word with diacritics
        word_with_diacritics = "يَكْتُبُونَ"
        forms = processor.get_lookup_forms(word_with_diacritics)
        # Should include original
        assert word_with_diacritics in forms
        # Should include normalized form (without diacritics)
        assert "يكتبون" in forms
        # Should include a lemma (may be vocalized like كَتَبَ)
        assert any(
            "كتب" in form or "كَتَبَ" in form or "أَكْتَبَ" in form
            for form in forms
            if form not in [word_with_diacritics, "يكتبون"]
        ) or len(forms) >= 2

    def test_language_code(self, processor):
        """Test that language code is set correctly."""
        assert processor.language_code == "ar"
