"""Unit tests for StarDict parser."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from text_glosser.core.parsers.stardict import (
    FallbackStarDictParser,
    PyStarDictParser,
    StarDictParser,
)


class TestStarDictParserFactory:
    """Tests for the StarDictParser factory function."""

    def test_factory_returns_protocol_compliant_parser(self, tmp_path):
        """Test that factory returns a parser implementing the protocol."""
        # Create minimal StarDict files for testing
        ifo_content = """StarDict's dict iance file format info
wordcount=1
idxfilesize=10
bookname=Test Dict
sametypesequence=m
"""
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text(ifo_content)

        # Create minimal idx file (word + null + offset + size)
        idx_file = tmp_path / "test.idx"
        import struct

        word = b"test\x00"
        offset = struct.pack(">I", 0)
        size = struct.pack(">I", 4)
        idx_file.write_bytes(word + offset + size)

        # Create minimal dict file
        dict_file = tmp_path / "test.dict"
        dict_file.write_text("definition")

        parser = StarDictParser(str(ifo_file))

        # Verify it has the required methods
        assert hasattr(parser, "lookup")
        assert hasattr(parser, "search")
        assert hasattr(parser, "get_all_words")
        assert callable(parser.lookup)
        assert callable(parser.search)
        assert callable(parser.get_all_words)

    @patch("text_glosser.core.parsers.stardict.PyStarDictParser")
    def test_factory_uses_pystardict_when_available(self, mock_pystardict, tmp_path):
        """Test that factory prefers pystardict when available."""
        # Create minimal files
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("StarDict's dict ifo file\nwordcount=1\n")
        (tmp_path / "test.idx").write_bytes(b"test\x00\x00\x00\x00\x00\x00\x00\x00\x04")
        (tmp_path / "test.dict").write_text("def")

        mock_parser = MagicMock()
        mock_pystardict.return_value = mock_parser

        result = StarDictParser(str(ifo_file))

        mock_pystardict.assert_called_once_with(str(ifo_file))
        assert result == mock_parser

    @patch("text_glosser.core.parsers.stardict.PyStarDictParser")
    def test_factory_falls_back_on_import_error(self, mock_pystardict, tmp_path):
        """Test that factory falls back to FallbackStarDictParser on ImportError."""
        # Create minimal files
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("StarDict's dict ifo file\nwordcount=1\n")
        (tmp_path / "test.idx").write_bytes(b"test\x00\x00\x00\x00\x00\x00\x00\x00\x04")
        (tmp_path / "test.dict").write_text("def")

        mock_pystardict.side_effect = ImportError("pystardict not installed")

        result = StarDictParser(str(ifo_file))

        assert isinstance(result, FallbackStarDictParser)

    @patch("text_glosser.core.parsers.stardict.PyStarDictParser")
    def test_factory_falls_back_on_exception(self, mock_pystardict, tmp_path):
        """Test that factory falls back on any pystardict exception."""
        # Create minimal files
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("StarDict's dict ifo file\nwordcount=1\n")
        (tmp_path / "test.idx").write_bytes(b"test\x00\x00\x00\x00\x00\x00\x00\x00\x04")
        (tmp_path / "test.dict").write_text("def")

        mock_pystardict.side_effect = Exception("pystardict failed to load")

        result = StarDictParser(str(ifo_file))

        assert isinstance(result, FallbackStarDictParser)


class TestFallbackStarDictParser:
    """Tests for the FallbackStarDictParser class."""

    @pytest.fixture
    def sample_dict(self, tmp_path):
        """Create a sample StarDict dictionary for testing."""
        import struct

        # Create .ifo file
        ifo_content = """StarDict's dict ifo file
wordcount=3
idxfilesize=36
bookname=Test Dictionary
sametypesequence=m
"""
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text(ifo_content)

        # Create .idx file with three words
        idx_data = b""
        words = [
            ("apple", 0, 17),
            ("banana", 17, 18),
            ("cherry", 35, 17),
        ]
        for word, offset, size in words:
            idx_data += word.encode("utf-8") + b"\x00"
            idx_data += struct.pack(">I", offset)
            idx_data += struct.pack(">I", size)

        idx_file = tmp_path / "test.idx"
        idx_file.write_bytes(idx_data)

        # Create .dict file with definitions
        dict_content = "A round red fruit" + "A yellow long fruit" + "A small red fruit"
        dict_file = tmp_path / "test.dict"
        dict_file.write_text(dict_content)

        return tmp_path / "test.ifo"

    def test_init_loads_index(self, sample_dict):
        """Test that initialization loads the index."""
        parser = FallbackStarDictParser(str(sample_dict))

        assert len(parser.index) == 3
        assert "apple" in parser.index
        assert "banana" in parser.index
        assert "cherry" in parser.index

    def test_init_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            FallbackStarDictParser(str(tmp_path / "nonexistent.ifo"))

    def test_init_missing_dict_file(self, tmp_path):
        """Test that FileNotFoundError is raised when dict file is missing."""
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("StarDict's dict ifo file\nwordcount=1\n")
        (tmp_path / "test.idx").write_bytes(b"test\x00\x00\x00\x00\x00\x00\x00\x00\x04")
        # Intentionally not creating .dict file

        with pytest.raises(FileNotFoundError, match="Dictionary file not found"):
            FallbackStarDictParser(str(ifo_file))

    def test_lookup_existing_word(self, sample_dict):
        """Test looking up an existing word."""
        parser = FallbackStarDictParser(str(sample_dict))

        result = parser.lookup("apple")

        assert result is not None
        assert "round red fruit" in result

    def test_lookup_nonexistent_word(self, sample_dict):
        """Test looking up a word that doesn't exist."""
        parser = FallbackStarDictParser(str(sample_dict))

        result = parser.lookup("nonexistent")

        assert result is None

    def test_search_with_prefix(self, sample_dict):
        """Test searching for words with a prefix."""
        parser = FallbackStarDictParser(str(sample_dict))

        # Test prefix that matches one word
        results = parser.search("app")
        assert "apple" in results

        # Test prefix that matches no words
        results = parser.search("xyz")
        assert len(results) == 0

    def test_search_with_limit(self, sample_dict):
        """Test that search respects the limit parameter."""
        parser = FallbackStarDictParser(str(sample_dict))

        # All words start with different letters, but test limit anyway
        results = parser.search("", limit=2)
        assert len(results) <= 2

    def test_get_all_words(self, sample_dict):
        """Test getting all words from the dictionary."""
        parser = FallbackStarDictParser(str(sample_dict))

        words = parser.get_all_words()

        assert len(words) == 3
        assert "apple" in words
        assert "banana" in words
        assert "cherry" in words

    def test_compressed_dict_file(self, tmp_path):
        """Test loading a compressed .dict.dz file."""
        import gzip
        import struct

        # Create .ifo file
        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("StarDict's dict ifo file\nwordcount=1\n")

        # Create .idx file
        idx_data = b"test\x00" + struct.pack(">I", 0) + struct.pack(">I", 11)
        (tmp_path / "test.idx").write_bytes(idx_data)

        # Create compressed .dict.dz file
        dict_content = b"A test word"
        dict_dz_file = tmp_path / "test.dict.dz"
        with gzip.open(dict_dz_file, "wb") as f:
            f.write(dict_content)

        parser = FallbackStarDictParser(str(ifo_file))

        assert parser.is_compressed is True
        result = parser.lookup("test")
        assert result == "A test word"


class TestPyStarDictParser:
    """Tests for the PyStarDictParser class."""

    @pytest.fixture
    def mock_pystardict(self):
        """Create a mock pystardict module."""
        with patch.dict("sys.modules", {"pystardict": MagicMock()}):
            yield

    def test_init_with_mock(self, tmp_path, mock_pystardict):
        """Test initialization with mocked pystardict."""
        import sys

        mock_dict = MagicMock()
        mock_dict.idx._idx.keys.return_value = [b"word1", b"word2"]
        sys.modules["pystardict"].Dictionary.return_value = mock_dict

        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("test")

        _ = PyStarDictParser(str(ifo_file))

        # Verify Dictionary was called with correct prefix
        expected_prefix = str(tmp_path / "test")
        sys.modules["pystardict"].Dictionary.assert_called_once_with(
            expected_prefix, in_memory=True
        )

    def test_lookup_with_mock(self, tmp_path, mock_pystardict):
        """Test lookup with mocked pystardict."""
        import sys

        mock_dict = MagicMock()
        mock_dict.get.return_value = "test definition"
        mock_dict.idx._idx.keys.return_value = []
        sys.modules["pystardict"].Dictionary.return_value = mock_dict

        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("test")

        parser = PyStarDictParser(str(ifo_file))
        result = parser.lookup("testword")

        mock_dict.get.assert_called_once_with("testword", None)
        assert result == "test definition"

    def test_lookup_returns_none_for_empty_result(self, tmp_path, mock_pystardict):
        """Test that lookup returns None for empty results."""
        import sys

        mock_dict = MagicMock()
        mock_dict.get.return_value = ""
        mock_dict.idx._idx.keys.return_value = []
        sys.modules["pystardict"].Dictionary.return_value = mock_dict

        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("test")

        parser = PyStarDictParser(str(ifo_file))
        result = parser.lookup("testword")

        assert result is None

    def test_get_all_words_decodes_bytes(self, tmp_path, mock_pystardict):
        """Test that get_all_words properly decodes bytes keys."""
        import sys

        mock_dict = MagicMock()
        mock_dict.idx._idx.keys.return_value = [b"word1", b"word2", "word3"]
        sys.modules["pystardict"].Dictionary.return_value = mock_dict

        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("test")

        parser = PyStarDictParser(str(ifo_file))
        words = parser.get_all_words()

        assert words == ["word1", "word2", "word3"]

    def test_get_all_words_caches_result(self, tmp_path, mock_pystardict):
        """Test that get_all_words caches the word list."""
        import sys

        mock_dict = MagicMock()
        mock_dict.idx._idx.keys.return_value = [b"word1"]
        sys.modules["pystardict"].Dictionary.return_value = mock_dict

        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("test")

        parser = PyStarDictParser(str(ifo_file))

        # Call twice
        words1 = parser.get_all_words()
        words2 = parser.get_all_words()

        # Should only access keys once due to caching
        assert mock_dict.idx._idx.keys.call_count == 1
        assert words1 is words2

    def test_search_filters_by_prefix(self, tmp_path, mock_pystardict):
        """Test that search correctly filters by prefix."""
        import sys

        mock_dict = MagicMock()
        mock_dict.idx._idx.keys.return_value = [b"apple", b"application", b"banana"]
        sys.modules["pystardict"].Dictionary.return_value = mock_dict

        ifo_file = tmp_path / "test.ifo"
        ifo_file.write_text("test")

        parser = PyStarDictParser(str(ifo_file))
        results = parser.search("app", limit=10)

        assert "apple" in results
        assert "application" in results
        assert "banana" not in results


class TestIntegrationWithRealDictionaries:
    """Integration tests with real dictionary files if available."""

    @pytest.fixture
    def sanskrit_dict_path(self):
        """Get path to Sanskrit dictionary if available."""
        path = Path("./language_resources/sa/monier-williams-cologne/mw-cologne.ifo")
        if not path.exists():
            pytest.skip("Sanskrit dictionary not available")
        return str(path)

    @pytest.fixture
    def arabic_lane_dict_path(self):
        """Get path to Arabic Lane dictionary if available."""
        path = Path(
            "./language_resources/ar/lane-lexicon/Lane-Arabic-English-Lexicon.ifo"
        )
        if not path.exists():
            pytest.skip("Arabic Lane dictionary not available")
        return str(path)

    def test_load_sanskrit_dictionary(self, sanskrit_dict_path):
        """Test loading the Sanskrit dictionary."""
        parser = StarDictParser(sanskrit_dict_path)

        words = parser.get_all_words()
        assert len(words) > 0

    def test_lookup_sanskrit_word(self, sanskrit_dict_path):
        """Test looking up a word in the Sanskrit dictionary."""
        parser = StarDictParser(sanskrit_dict_path)

        # Get a word we know exists
        words = parser.get_all_words()
        if words:
            result = parser.lookup(words[0])
            assert result is not None

    def test_search_sanskrit_dictionary(self, sanskrit_dict_path):
        """Test searching the Sanskrit dictionary."""
        parser = StarDictParser(sanskrit_dict_path)

        results = parser.search("abhi", limit=5)
        assert len(results) <= 5
        for word in results:
            assert word.startswith("abhi")

    def test_load_arabic_dictionary(self, arabic_lane_dict_path):
        """Test loading the Arabic dictionary."""
        parser = StarDictParser(arabic_lane_dict_path)

        words = parser.get_all_words()
        assert len(words) > 0

    def test_lookup_arabic_word(self, arabic_lane_dict_path):
        """Test looking up a word in the Arabic dictionary."""
        parser = StarDictParser(arabic_lane_dict_path)

        words = parser.get_all_words()
        if words:
            result = parser.lookup(words[0])
            assert result is not None
