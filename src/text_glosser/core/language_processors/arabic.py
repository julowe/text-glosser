"""
Arabic language processor.

This module provides Arabic text normalization and lemmatization
using pyarabic and qalsadi libraries to improve dictionary lookup accuracy.
"""

from typing import Any

from . import LanguageProcessor


class ArabicProcessor(LanguageProcessor):
    """
    Arabic language processor for normalization and lemmatization.

    Uses pyarabic for text normalization (removing diacritics, normalizing
    alef variants, removing tatweel) and qalsadi for lemmatization to
    extract root forms for dictionary lookup.

    Attributes
    ----------
    language_code : str
        ISO 639-1 code for Arabic ('ar')
    _lemmatizer : qalsadi.lemmatizer.Lemmatizer | None
        Cached lemmatizer instance (lazily loaded)

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
    """

    language_code: str = "ar"

    def __init__(self):
        """Initialize the Arabic processor."""
        # Lazily loaded lemmatizer instance (qalsadi.lemmatizer.Lemmatizer)
        self._lemmatizer: Any = None

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


def get_arabic_processor() -> ArabicProcessor:
    """
    Create a new instance of the Arabic processor.

    Returns
    -------
    ArabicProcessor
        A new Arabic processor instance
    """
    return ArabicProcessor()
