"""
Data models for the text glosser application.

This module defines the core data structures used throughout the application
for representing dictionaries, resources, text sources, and analysis results.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LanguageCode(BaseModel):
    """
    Represents an ISO 639 language code.
    
    Attributes
    ----------
    set1 : str
        ISO 639-1 two-letter code (primary)
    set2 : Optional[List[str]]
        ISO 639-2 three-letter codes
    set3 : Optional[List[str]]
        ISO 639-3 three-letter codes
    """
    set1: str = Field(..., min_length=2, max_length=2, description="ISO 639-1 code")
    set2: Optional[List[str]] = Field(default=None, description="ISO 639-2 codes")
    set3: Optional[List[str]] = Field(default=None, description="ISO 639-3 codes")


class DictionaryFormat(str, Enum):
    """Supported dictionary file formats."""
    STARDICT = "stardict"
    MDICT = "mdict"
    HANZIPY = "hanzipy"
    GENERAL = "general"


class ResourceType(str, Enum):
    """Type of linguistic resource."""
    DICTIONARY = "dictionary"
    LIBRARY = "library"
    GRAMMAR_TOOL = "grammar_tool"
    GENERAL = "general"


class DictionaryResource(BaseModel):
    """
    Represents a dictionary or linguistic resource.
    
    Attributes
    ----------
    id : str
        Unique identifier for the resource
    name : str
        Human-readable name
    format : DictionaryFormat
        File format type
    resource_type : ResourceType
        Type of resource
    primary_language : str
        Primary ISO 639-1 language code
    secondary_languages : List[str]
        Additional language codes
    file_paths : Optional[List[str]]
        Paths to resource files (for file-based resources)
    source_url : Optional[str]
        Original source URL
    is_user_provided : bool
        Whether this was uploaded by a user
    set2_codes : Optional[List[str]]
        ISO 639-2 codes
    set3_codes : Optional[List[str]]
        ISO 639-3 codes
    """
    id: str
    name: str
    format: DictionaryFormat
    resource_type: ResourceType
    primary_language: str = Field(..., min_length=2, max_length=2)
    secondary_languages: List[str] = Field(default_factory=list)
    file_paths: Optional[List[str]] = None
    source_url: Optional[str] = None
    is_user_provided: bool = False
    set2_codes: Optional[List[str]] = None
    set3_codes: Optional[List[str]] = None


class TextSource(BaseModel):
    """
    Represents a text source to be analyzed.
    
    Attributes
    ----------
    id : str
        Unique identifier
    name : str
        Name/title of the source
    content : str
        The actual text content
    source_type : str
        Either 'file' or 'url'
    original_path : Optional[str]
        Original file path or URL
    """
    id: str
    name: str
    content: str
    source_type: str  # 'file' or 'url'
    original_path: Optional[str] = None


class WordDefinition(BaseModel):
    """
    Represents a word definition.
    
    Attributes
    ----------
    word : str
        The word being defined
    definitions : List[str]
        List of definitions
    source_dict : str
        ID of the dictionary providing the definition
    grammatical_info : Optional[Dict[str, Any]]
        Grammatical information if available
    """
    word: str
    definitions: List[str]
    source_dict: str
    grammatical_info: Optional[Dict[str, Any]] = None


class LineAnalysis(BaseModel):
    """
    Analysis results for a single line of text.
    
    Attributes
    ----------
    line_number : int
        Line number in source
    words : List[WordDefinition]
        Analysis for each word in the line
    """
    line_number: int
    words: List[WordDefinition]


class TextAnalysis(BaseModel):
    """
    Complete analysis of a text source.
    
    Attributes
    ----------
    source_id : str
        ID of the text source
    source_name : str
        Name of the text source
    total_lines : int
        Number of lines in source
    total_words : int
        Number of words in source
    dictionaries_used : List[str]
        IDs of dictionaries used
    lines : List[LineAnalysis]
        Line-by-line analysis
    errors : List[str]
        Any errors encountered
    timestamp : datetime
        When the analysis was performed
    """
    source_id: str
    source_name: str
    total_lines: int
    total_words: int
    dictionaries_used: List[str]
    lines: List[LineAnalysis]
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionConfig(BaseModel):
    """
    Configuration for a processing session.
    
    Attributes
    ----------
    session_id : str
        Unique session identifier
    text_sources : List[TextSource]
        Text sources to analyze
    selected_resources : List[str]
        IDs of selected dictionaries/resources
    retention_days : Optional[int]
        Days to retain session data (0-365, None for indefinite)
    created_at : datetime
        When the session was created
    last_accessed : datetime
        When the session was last accessed
    """
    session_id: str
    text_sources: List[TextSource]
    selected_resources: List[str]
    retention_days: Optional[int] = 180
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    
    @field_validator('retention_days')
    @classmethod
    def validate_retention(cls, v):
        """Validate retention days is in valid range."""
        if v is not None and (v < 0 or v > 365):
            raise ValueError('retention_days must be between 0 and 365')
        return v
