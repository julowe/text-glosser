"""
Arabic language processor.

This module provides Arabic text normalization and lemmatization
using pyarabic and qalsadi libraries to improve dictionary lookup accuracy.
"""

from typing import Any

from . import LanguageProcessor
from .base import MorphologicalAnalyzer, TokenSegment
from .qalsadi_analyzer import QalsadiAnalyzer


class ArabicProcessor(LanguageProcessor):
    """
    Arabic language processor for normalization and lemmatization.

    Uses pyarabic for text normalization (removing diacritics, normalizing
    alef variants, removing tatweel) and qalsadi for lemmatization to
    extract root forms for dictionary lookup.

    This processor supports morphological analysis via a configurable
    analyzer (Strategy Pattern). The default analyzer is QalsadiAnalyzer,
    but this can be swapped for other implementations (CAMeL Tools, Stanza)
    without changing the main application logic.

    Attributes
    ----------
    language_code : str
        ISO 639-1 code for Arabic ('ar')
    _lemmatizer : qalsadi.lemmatizer.Lemmatizer | None
        Cached lemmatizer instance (lazily loaded)
    _analyzer : MorphologicalAnalyzer
        Morphological analyzer for word segmentation

    Notes
    -----
    Arabic dictionaries like Lane's Lexicon are often root-based, meaning
    words are organized by their trilateral or quadrilateral roots rather
    than by inflected forms. This processor helps map conjugated words
    back to their roots for successful dictionary lookups.

    Examples
    --------
    >>> processor = ArabicProcessor()
    >>> processor.normalize("يَكْتُبُونَ")
    'يكتبون'
    >>> processor.lemmatize("يكتبون")
    ['كتب']
    >>> segments = processor.analyze_word("وبكتاب")
    >>> [s.segment_text for s in segments]
    ['و', 'ب', 'كتاب']
    """

    language_code: str = "ar"

    def __init__(self, analyzer: MorphologicalAnalyzer | None = None):
        """
        Initialize the Arabic processor.

        Parameters
        ----------
        analyzer : MorphologicalAnalyzer | None, optional
            Morphological analyzer to use for word segmentation.
            Defaults to QalsadiAnalyzer if not provided.
        """
        # Lazily loaded lemmatizer instance (qalsadi.lemmatizer.Lemmatizer)
        self._lemmatizer: Any = None
        # Morphological analyzer (defaults to Qalsadi)
        self._analyzer: MorphologicalAnalyzer = analyzer or QalsadiAnalyzer()

    def _get_lemmatizer(self):
        """
        Get or create the lemmatizer instance.

        Returns
        -------
        qalsadi.lemmatizer.Lemmatizer
            The lemmatizer instance

        Notes
        -----
        Lazily loads the lemmatizer to avoid import overhead if not used.
        """
        if self._lemmatizer is None:
            try:
                import qalsadi.lemmatizer as qlemmatizer

                self._lemmatizer = qlemmatizer.Lemmatizer()
            except ImportError:
                pass
        return self._lemmatizer

    def normalize(self, text: str) -> str:
        """
        Normalize Arabic text for consistent processing.

        Removes diacritics (tashkeel/harakat), tatweel (kashida),
        and normalizes alef variants (أ إ آ → ا).

        Parameters
        ----------
        text : str
            Arabic text to normalize

        Returns
        -------
        str
            Normalized Arabic text

        Examples
        --------
        >>> processor = ArabicProcessor()
        >>> processor.normalize("يَكْتُبُونَ")
        'يكتبون'
        >>> processor.normalize("كـتـب")
        'كتب'
        """
        try:
            import pyarabic.araby as araby

            # Strip diacritics (tashkeel)
            result = araby.strip_tashkeel(text)
            # Strip tatweel (kashida)
            result = araby.strip_tatweel(result)
            # Normalize alef variants (أ إ آ → ا)
            result = araby.normalize_alef(result)

            return result
        except ImportError:
            return text

    def lemmatize(self, word: str) -> list[str]:
        """
        Get lemmas/roots for an Arabic word.

        Uses qalsadi to extract the root form of conjugated Arabic words.
        This is essential for looking up words in root-based dictionaries
        like Lane's Lexicon.

        Parameters
        ----------
        word : str
            Arabic word to lemmatize

        Returns
        -------
        list[str]
            List of possible lemmas/roots for the word

        Examples
        --------
        >>> processor = ArabicProcessor()
        >>> processor.lemmatize("يكتبون")
        ['كتب']
        >>> processor.lemmatize("كتابات")
        ['كتاب']
        """
        lemmatizer = self._get_lemmatizer()
        if not lemmatizer:
            return []

        try:
            result = lemmatizer.lemmatize(word)
            # Result can be a string or list depending on qalsadi version
            if isinstance(result, str):
                return [result] if result else []
            if isinstance(result, list):
                return result
            return [str(result)] if result else []
        except Exception:
            return []

    def is_language_text(self, text: str) -> bool:
        """
        Check if text contains Arabic characters.

        Parameters
        ----------
        text : str
            Text to check

        Returns
        -------
        bool
            True if text contains Arabic characters

        Examples
        --------
        >>> processor = ArabicProcessor()
        >>> processor.is_language_text("مرحبا")
        True
        >>> processor.is_language_text("Hello")
        False
        """
        try:
            import pyarabic.araby as araby

            return any(araby.is_arabicrange(char) for char in text)
        except ImportError:
            # Fallback: check Arabic Unicode range
            for char in text:
                if "\u0600" <= char <= "\u06ff":
                    return True
            return False

    def analyze_word(self, word: str) -> list[TokenSegment]:
        """
        Analyze an Arabic word into its morphological segments.

        This method uses the configured morphological analyzer to break down
        a word into its constituent parts (prefixes, stem, suffixes).
        For example, "وبكتاب" becomes ["و" (and), "ب" (with), "كتاب" (book)].

        Parameters
        ----------
        word : str
            Arabic word to analyze

        Returns
        -------
        list[TokenSegment]
            List of token segments representing the word's morphological parts.
            Each segment contains segment_text, lemma, root, pos, and gloss.

        Examples
        --------
        >>> processor = ArabicProcessor()
        >>> segments = processor.analyze_word("وبكتاب")
        >>> [s.segment_text for s in segments]
        ['و', 'ب', 'كتاب']
        >>> segments[0].pos
        'CONJ'
        """
        return self._analyzer.analyze_word(word)

    def set_analyzer(self, analyzer: MorphologicalAnalyzer) -> None:
        """
        Set the morphological analyzer to use.

        This allows swapping the analysis backend at runtime for
        different analysis strategies (Qalsadi, CAMeL Tools, Stanza).

        Parameters
        ----------
        analyzer : MorphologicalAnalyzer
            The analyzer to use for morphological analysis

        Examples
        --------
        >>> from text_glosser.core.language_processors.qalsadi_analyzer import (
        ...     QalsadiAnalyzer,
        ... )
        >>> processor = ArabicProcessor()
        >>> processor.set_analyzer(QalsadiAnalyzer())
        """
        self._analyzer = analyzer

    def get_analyzer(self) -> MorphologicalAnalyzer:
        """
        Get the current morphological analyzer.

        Returns
        -------
        MorphologicalAnalyzer
            The currently configured analyzer
        """
        return self._analyzer


def get_arabic_processor(
    analyzer: MorphologicalAnalyzer | None = None,
) -> ArabicProcessor:
    """
    Create a new instance of the Arabic processor.

    Parameters
    ----------
    analyzer : MorphologicalAnalyzer | None, optional
        Morphological analyzer to use. Defaults to QalsadiAnalyzer.

    Returns
    -------
    ArabicProcessor
        A new Arabic processor instance
    """
    return ArabicProcessor(analyzer=analyzer)
