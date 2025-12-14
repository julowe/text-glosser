"""Unit tests for core models."""

import pytest
from datetime import datetime
from text_glosser.core.models import (
    LanguageCode,
    DictionaryResource,
    DictionaryFormat,
    ResourceType,
    TextSource,
    WordDefinition,
    LineAnalysis,
    TextAnalysis,
    SessionConfig
)


class TestLanguageCode:
    """Tests for LanguageCode model."""
    
    def test_create_simple(self):
        """Test creating a simple language code."""
        lang = LanguageCode(set1="en")
        assert lang.set1 == "en"
        assert lang.set2 is None
        assert lang.set3 is None
    
    def test_create_with_all_codes(self):
        """Test creating with all code sets."""
        lang = LanguageCode(
            set1="sa",
            set2=["san"],
            set3=["cls", "vsn"]
        )
        assert lang.set1 == "sa"
        assert "san" in lang.set2
        assert "cls" in lang.set3


class TestDictionaryResource:
    """Tests for DictionaryResource model."""
    
    def test_create_stardict_resource(self):
        """Test creating a StarDict resource."""
        res = DictionaryResource(
            id="test-dict",
            name="Test Dictionary",
            format=DictionaryFormat.STARDICT,
            resource_type=ResourceType.DICTIONARY,
            primary_language="en",
            secondary_languages=["fr"],
            file_paths=["/path/to/dict.ifo"]
        )
        assert res.id == "test-dict"
        assert res.format == DictionaryFormat.STARDICT
        assert res.is_user_provided is False
    
    def test_user_provided_resource(self):
        """Test marking resource as user-provided."""
        res = DictionaryResource(
            id="user-dict",
            name="User Dictionary",
            format=DictionaryFormat.MDICT,
            resource_type=ResourceType.DICTIONARY,
            primary_language="zh",
            is_user_provided=True
        )
        assert res.is_user_provided is True


class TestTextSource:
    """Tests for TextSource model."""
    
    def test_create_file_source(self):
        """Test creating a file source."""
        source = TextSource(
            id="src-1",
            name="test.txt",
            content="Hello, world!",
            source_type="file",
            original_path="/path/to/test.txt"
        )
        assert source.source_type == "file"
        assert source.content == "Hello, world!"
    
    def test_create_url_source(self):
        """Test creating a URL source."""
        source = TextSource(
            id="src-2",
            name="https://example.com",
            content="Web content",
            source_type="url",
            original_path="https://example.com"
        )
        assert source.source_type == "url"


class TestWordDefinition:
    """Tests for WordDefinition model."""
    
    def test_create_simple_definition(self):
        """Test creating a simple word definition."""
        word_def = WordDefinition(
            word="karma",
            definitions=["action", "deed"],
            source_dict="test-dict"
        )
        assert word_def.word == "karma"
        assert len(word_def.definitions) == 2
        assert word_def.grammatical_info is None
    
    def test_with_grammatical_info(self):
        """Test definition with grammatical information."""
        word_def = WordDefinition(
            word="test",
            definitions=["definition"],
            source_dict="dict-id",
            grammatical_info={"pos": "noun", "gender": "neuter"}
        )
        assert word_def.grammatical_info["pos"] == "noun"


class TestLineAnalysis:
    """Tests for LineAnalysis model."""
    
    def test_create_line_analysis(self):
        """Test creating line analysis."""
        word_def = WordDefinition(
            word="test",
            definitions=["def"],
            source_dict="dict-1"
        )
        line = LineAnalysis(
            line_number=1,
            words=[word_def]
        )
        assert line.line_number == 1
        assert len(line.words) == 1


class TestTextAnalysis:
    """Tests for TextAnalysis model."""
    
    def test_create_analysis(self):
        """Test creating text analysis."""
        word_def = WordDefinition(
            word="test",
            definitions=["def"],
            source_dict="dict-1"
        )
        line = LineAnalysis(line_number=1, words=[word_def])
        
        analysis = TextAnalysis(
            source_id="src-1",
            source_name="test.txt",
            total_lines=1,
            total_words=1,
            dictionaries_used=["dict-1"],
            lines=[line]
        )
        
        assert analysis.source_name == "test.txt"
        assert analysis.total_words == 1
        assert len(analysis.errors) == 0
        assert isinstance(analysis.timestamp, datetime)


class TestSessionConfig:
    """Tests for SessionConfig model."""
    
    def test_create_session(self):
        """Test creating a session config."""
        source = TextSource(
            id="src-1",
            name="test.txt",
            content="content",
            source_type="file"
        )
        
        session = SessionConfig(
            session_id="test-session-123",
            text_sources=[source],
            selected_resources=["dict-1", "dict-2"],
            retention_days=180
        )
        
        assert session.session_id == "test-session-123"
        assert len(session.text_sources) == 1
        assert session.retention_days == 180
        assert isinstance(session.created_at, datetime)
    
    def test_indefinite_retention(self):
        """Test session with indefinite retention."""
        session = SessionConfig(
            session_id="test-session",
            text_sources=[],
            selected_resources=[],
            retention_days=None
        )
        assert session.retention_days is None
    
    def test_invalid_retention_days(self):
        """Test invalid retention days raises error."""
        with pytest.raises(ValueError, match="between 0 and 365"):
            SessionConfig(
                session_id="test",
                text_sources=[],
                selected_resources=[],
                retention_days=400
            )
