"""
Base classes for morphological analysis.

This module defines abstract interfaces for morphological analyzers
that can break down words into their constituent parts (prefixes, stems, suffixes).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TokenSegment:
    """
    Represents a distinct segment of a word after morphological analysis.

    A single source word may be split into multiple segments
    (e.g., prefix + stem + suffix). Each segment contains linguistic
    information for glossing purposes.

    Attributes
    ----------
    segment_text : str
        The distinct part of the word (e.g., "وَ" for "and")
    lemma : str
        The dictionary form (e.g., "و" for conjunction "wa")
    root : str
        The trilateral/quadrilateral root (e.g., "و-ي" or "ك-ت-ب")
    pos : str
        Part of speech tag (e.g., "CONJ", "PREP", "NOUN", "VERB")
    gloss : str
        English gloss/translation for this segment (e.g., "and", "with")
    features : dict
        Additional grammatical features (e.g., {"case": "genitive"})

    Examples
    --------
    >>> segment = TokenSegment(
    ...     segment_text="وَ",
    ...     lemma="و",
    ...     root="",
    ...     pos="CONJ",
    ...     gloss="and"
    ... )
    """

    segment_text: str
    lemma: str = ""
    root: str = ""
    pos: str = ""
    gloss: str = ""
    features: dict = field(default_factory=dict)


class MorphologicalAnalyzer(ABC):
    """
    Abstract base class for morphological analyzers.

    Morphological analyzers break down words into their constituent parts
    for word-by-word glossing. Different implementations can use different
    analysis backends (qalsadi, CAMeL Tools, Stanza, etc.).

    This follows the Strategy Pattern to allow easy swapping of analysis
    backends without changing the main application logic.

    Attributes
    ----------
    name : str
        Human-readable name of this analyzer
    language_code : str
        ISO 639-1 language code (e.g., "ar" for Arabic)

    Examples
    --------
    >>> class MyAnalyzer(MorphologicalAnalyzer):
    ...     name = "My Custom Analyzer"
    ...     language_code = "ar"
    ...     def analyze_word(self, word: str) -> list[TokenSegment]:
    ...         return [TokenSegment(segment_text=word)]
    """

    name: str = "Base Analyzer"
    language_code: str = ""

    @abstractmethod
    def analyze_word(self, word: str) -> list[TokenSegment]:
        """
        Analyze a single word and return its morphological segments.

        This method breaks down a word into its constituent parts
        (prefixes, stem, suffixes) for glossing purposes.

        Parameters
        ----------
        word : str
            The word to analyze

        Returns
        -------
        list[TokenSegment]
            List of token segments. May contain multiple segments
            if the word has prefixes/suffixes (e.g., "وبكتاب" -> ["و", "ب", "كتاب"]).
            Returns a single segment with the original word if analysis fails.

        Examples
        --------
        >>> analyzer = QalsadiAnalyzer()
        >>> segments = analyzer.analyze_word("وبكتاب")
        >>> [s.segment_text for s in segments]
        ['و', 'ب', 'كتاب']
        """
        pass

    def analyze_text(self, text: str) -> list[list[TokenSegment]]:
        """
        Analyze a text string and return segments for each word.

        Parameters
        ----------
        text : str
            The text to analyze

        Returns
        -------
        list[list[TokenSegment]]
            List of segment lists, one per word in the input text
        """
        # Simple whitespace tokenization - can be overridden for better tokenization
        words = text.split()
        return [self.analyze_word(word) for word in words]

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this analyzer's dependencies are available.

        Returns
        -------
        bool
            True if the analyzer can be used, False otherwise
        """
        pass
