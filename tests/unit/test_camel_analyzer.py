"""Unit tests for CAMeL Tools Arabic analyzer."""

import os
from unittest.mock import MagicMock, patch

import pytest

from text_glosser.core.language_processors.base import (
    MorphologicalAnalyzer,
    TokenSegment,
)
from text_glosser.core.language_processors.camel_analyzer import (
    CAMEL_POS_MAP,
    PREFIX_GLOSSES,
    CamelToolsAnalyzer,
    _check_data_exists,
    _get_data_dir,
    download_camel_data,
    get_camel_tools_analyzer,
)


class TestCamelToolsAnalyzerBasics:
    """Basic tests for CamelToolsAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a test CAMeL Tools analyzer (without auto-download)."""
        return CamelToolsAnalyzer(auto_download=False)

    def test_analyzer_name(self, analyzer):
        """Test analyzer name."""
        assert analyzer.name == "CAMeL Tools Arabic Analyzer"

    def test_analyzer_language_code(self, analyzer):
        """Test analyzer language code."""
        assert analyzer.language_code == "ar"

    def test_analyzer_is_morphological_analyzer(self, analyzer):
        """Test that CamelToolsAnalyzer is a MorphologicalAnalyzer."""
        assert isinstance(analyzer, MorphologicalAnalyzer)

    def test_get_camel_tools_analyzer_factory(self):
        """Test factory function creates analyzer."""
        analyzer = get_camel_tools_analyzer()
        assert isinstance(analyzer, CamelToolsAnalyzer)
        assert analyzer._auto_download is False

    def test_get_camel_tools_analyzer_with_auto_download(self):
        """Test factory function with auto_download."""
        analyzer = get_camel_tools_analyzer(auto_download=True)
        assert analyzer._auto_download is True


class TestDataDirectoryHandling:
    """Tests for data directory handling."""

    def test_get_data_dir_default(self):
        """Test default data directory."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove CAMELTOOLS_DATA if present
            if "CAMELTOOLS_DATA" in os.environ:
                del os.environ["CAMELTOOLS_DATA"]
            data_dir = _get_data_dir()
            expected = os.path.join(os.path.expanduser("~"), ".camel_tools")
            assert data_dir == expected

    def test_get_data_dir_from_env(self):
        """Test data directory from environment variable."""
        test_dir = "/custom/camel/data"
        with patch.dict(os.environ, {"CAMELTOOLS_DATA": test_dir}):
            data_dir = _get_data_dir()
            assert data_dir == test_dir

    def test_check_data_exists_false(self):
        """Test data check returns False when data doesn't exist."""
        with patch.dict(os.environ, {"CAMELTOOLS_DATA": "/nonexistent/path"}):
            assert _check_data_exists() is False

    @patch("os.path.exists")
    def test_check_data_exists_true(self, mock_exists):
        """Test data check returns True when data exists."""
        mock_exists.return_value = True
        assert _check_data_exists() is True


class TestAnalyzerAvailability:
    """Tests for analyzer availability checking."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer()

    def test_is_data_available_calls_check(self, analyzer):
        """Test is_data_available calls _check_data_exists."""
        with patch(
            "text_glosser.core.language_processors.camel_analyzer._check_data_exists"
        ) as mock_check:
            mock_check.return_value = True
            assert analyzer.is_data_available() is True
            mock_check.assert_called_once()

    def test_needs_data_download_when_data_missing(self, analyzer):
        """Test needs_data_download returns True when data is missing."""
        with patch(
            "text_glosser.core.language_processors.camel_analyzer._check_data_exists"
        ) as mock_check:
            mock_check.return_value = False
            assert analyzer.needs_data_download() is True

    def test_needs_data_download_when_data_exists(self, analyzer):
        """Test needs_data_download returns False when data exists."""
        with patch(
            "text_glosser.core.language_processors.camel_analyzer._check_data_exists"
        ) as mock_check:
            mock_check.return_value = True
            assert analyzer.needs_data_download() is False


class TestPOSMapping:
    """Tests for POS tag mapping."""

    def test_pos_map_contains_common_tags(self):
        """Test that POS map contains common tags."""
        expected_keys = ["noun", "verb", "adj", "adv", "prep", "conj", "pron"]
        for key in expected_keys:
            assert key in CAMEL_POS_MAP

    def test_pos_map_values_are_standard(self):
        """Test that POS map values are standard tags."""
        standard_tags = {
            "NOUN",
            "PROPN",
            "VERB",
            "ADJ",
            "ADV",
            "PRON",
            "DET",
            "PREP",
            "CONJ",
            "SCONJ",
            "PART",
            "INTJ",
            "PUNCT",
            "NUM",
            "X",
        }
        for value in CAMEL_POS_MAP.values():
            assert value in standard_tags


class TestPrefixGlosses:
    """Tests for prefix gloss mapping."""

    def test_prefix_glosses_contains_common_prefixes(self):
        """Test that prefix glosses contains common Arabic prefixes."""
        expected_prefixes = ["wa", "fa", "bi", "li", "Al"]
        for prefix in expected_prefixes:
            assert prefix in PREFIX_GLOSSES

    def test_prefix_glosses_values_are_strings(self):
        """Test that prefix gloss values are strings."""
        for value in PREFIX_GLOSSES.values():
            assert isinstance(value, str)


class TestAnalyzeWordFallback:
    """Tests for analyze_word fallback behavior."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer(auto_download=False)

    def test_analyze_word_returns_segments(self, analyzer):
        """Test that analyze_word returns list of TokenSegment."""
        # Without data, should return fallback
        with patch.object(analyzer, "_get_disambiguator", return_value=None):
            segments = analyzer.analyze_word("كتاب")
            assert isinstance(segments, list)
            assert len(segments) >= 1
            assert all(isinstance(s, TokenSegment) for s in segments)

    def test_analyze_word_fallback_has_original_text(self, analyzer):
        """Test fallback returns original word."""
        with patch.object(analyzer, "_get_disambiguator", return_value=None):
            word = "كتاب"
            segments = analyzer.analyze_word(word)
            assert segments[0].segment_text == word

    def test_analyze_word_fallback_has_unknown_pos(self, analyzer):
        """Test fallback has UNKNOWN POS tag."""
        with patch.object(analyzer, "_get_disambiguator", return_value=None):
            segments = analyzer.analyze_word("كتاب")
            assert segments[0].pos == "UNKNOWN"


class TestAnalyzeWordWithMockDisambiguator:
    """Tests for analyze_word with mocked disambiguator."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer(auto_download=False)

    @pytest.fixture
    def mock_disambiguator(self):
        """Create a mock disambiguator."""
        mock = MagicMock()

        # Create mock analysis result
        mock_analysis = MagicMock()
        mock_analysis.analysis = {
            "prc0": "",
            "prc1": "",
            "prc2": "",
            "prc3": "",
            "stem": "كتاب",
            "lex": "كتاب",
            "root": "ك.ت.ب",
            "pos": "noun",
            "enc0": "",
            "diac": "كِتَاب",
            "asp": "",
            "vox": "",
            "mod": "",
            "per": "",
            "gen": "m",
            "num": "s",
            "stt": "",
            "cas": "",
        }

        mock_result = MagicMock()
        mock_result.analyses = [mock_analysis]

        mock.disambiguate.return_value = [mock_result]

        return mock

    def test_analyze_word_with_disambiguator(self, analyzer, mock_disambiguator):
        """Test analyze_word with working disambiguator."""
        with patch.object(
            analyzer, "_get_disambiguator", return_value=mock_disambiguator
        ):
            segments = analyzer.analyze_word("كتاب")
            assert len(segments) >= 1
            # Should have stem segment
            stem_segment = segments[-1]
            assert stem_segment.segment_text == "كتاب"
            assert stem_segment.pos == "NOUN"
            assert stem_segment.root == "ك.ت.ب"

    def test_analyze_word_with_prefix(self, analyzer):
        """Test analyze_word handles prefixes."""
        mock = MagicMock()

        mock_analysis = MagicMock()
        mock_analysis.analysis = {
            "prc0": "و",
            "prc1": "",
            "prc2": "",
            "prc3": "",
            "stem": "كتاب",
            "lex": "كتاب",
            "root": "ك.ت.ب",
            "pos": "noun",
            "enc0": "",
        }

        mock_result = MagicMock()
        mock_result.analyses = [mock_analysis]
        mock.disambiguate.return_value = [mock_result]

        with patch.object(analyzer, "_get_disambiguator", return_value=mock):
            segments = analyzer.analyze_word("وكتاب")
            assert len(segments) >= 1
            # Should have prefix + stem
            segment_texts = [s.segment_text for s in segments]
            assert "كتاب" in segment_texts or "وكتاب" in segment_texts

    def test_analyze_word_empty_result(self, analyzer):
        """Test analyze_word handles empty result."""
        mock = MagicMock()
        mock_result = MagicMock()
        mock_result.analyses = []
        mock.disambiguate.return_value = [mock_result]

        with patch.object(analyzer, "_get_disambiguator", return_value=mock):
            segments = analyzer.analyze_word("كتاب")
            # Should return fallback
            assert len(segments) == 1
            assert segments[0].segment_text == "كتاب"
            assert segments[0].pos == "UNKNOWN"


class TestTokenSegmentStructure:
    """Tests for TokenSegment structure from analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer(auto_download=False)

    def test_segment_has_all_attributes(self, analyzer):
        """Test that returned segments have all required attributes."""
        with patch.object(analyzer, "_get_disambiguator", return_value=None):
            segments = analyzer.analyze_word("test")
            segment = segments[0]
            assert hasattr(segment, "segment_text")
            assert hasattr(segment, "lemma")
            assert hasattr(segment, "root")
            assert hasattr(segment, "pos")
            assert hasattr(segment, "gloss")
            assert hasattr(segment, "features")


class TestNormalization:
    """Tests for Arabic text normalization."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer()

    def test_normalize_strips_diacritics(self, analyzer):
        """Test that normalization removes diacritics."""
        # Word with diacritics
        word_with_diacritics = "كِتَابٌ"
        result = analyzer._normalize(word_with_diacritics)
        assert result == "كتاب"

    def test_normalize_preserves_base_text(self, analyzer):
        """Test that normalization preserves text without diacritics."""
        text = "كتاب"
        result = analyzer._normalize(text)
        assert result == "كتاب"


class TestDownloadFunction:
    """Tests for the download_camel_data function."""

    @patch("text_glosser.core.language_processors.camel_analyzer.os.makedirs")
    @patch("text_glosser.core.language_processors.camel_analyzer._get_data_dir")
    def test_download_creates_directory(self, mock_get_dir, mock_makedirs):
        """Test that download creates data directory."""
        mock_get_dir.return_value = "/test/data"

        # Mock the import to fail (camel_tools not installed scenario)
        with patch.dict("sys.modules", {"camel_tools.data": None}):
            result = download_camel_data()
            # Should handle ImportError gracefully
            assert result is False

    def test_download_with_progress_callback(self):
        """Test download calls progress callback."""
        messages = []

        def callback(msg):
            messages.append(msg)

        # Mock camel_tools not being installed
        with patch.dict("sys.modules", {"camel_tools.data": None}):
            download_camel_data(progress_callback=callback)

        # Should have called callback with error message
        assert any("camel-tools" in msg.lower() for msg in messages)


class TestAsyncDownload:
    """Tests for async download functionality."""

    @pytest.mark.asyncio
    async def test_async_download_returns_result(self):
        """Test async download returns result."""
        from text_glosser.core.language_processors.camel_analyzer import (
            download_camel_data_async,
        )

        # Mock the sync function
        with patch(
            "text_glosser.core.language_processors.camel_analyzer.download_camel_data"
        ) as mock_download:
            mock_download.return_value = False  # Simulate not installed
            result = await download_camel_data_async()
            assert result is False
            mock_download.assert_called_once()


class TestPOSMappingFunction:
    """Tests for _map_pos function."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer()

    def test_map_pos_noun(self, analyzer):
        """Test mapping noun POS."""
        assert analyzer._map_pos("noun") == "NOUN"

    def test_map_pos_verb(self, analyzer):
        """Test mapping verb POS."""
        assert analyzer._map_pos("verb") == "VERB"

    def test_map_pos_adj(self, analyzer):
        """Test mapping adjective POS."""
        assert analyzer._map_pos("adj") == "ADJ"

    def test_map_pos_unknown(self, analyzer):
        """Test mapping unknown POS."""
        assert analyzer._map_pos("xyz_unknown") == "UNKNOWN"

    def test_map_pos_empty(self, analyzer):
        """Test mapping empty POS."""
        assert analyzer._map_pos("") == "UNKNOWN"

    def test_map_pos_none(self, analyzer):
        """Test mapping None POS."""
        assert analyzer._map_pos(None) == "UNKNOWN"


class TestGlossFunction:
    """Tests for _get_gloss function."""

    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        return CamelToolsAnalyzer()

    def test_get_gloss_wa(self, analyzer):
        """Test gloss for 'wa' prefix."""
        assert analyzer._get_gloss("wa", "PART") == "and"

    def test_get_gloss_unknown(self, analyzer):
        """Test gloss for unknown morpheme."""
        assert analyzer._get_gloss("unknown_morpheme", "NOUN") == ""
