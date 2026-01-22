"""
Language processors for text-glosser.

This module provides language-specific text processing capabilities
including normalization, tokenization, and lemmatization.
"""

from abc import ABC, abstractmethod


class LanguageProcessor(ABC):
    """
    Abstract base class for language-specific text processors.

    Language processors provide normalization and lemmatization
    for specific languages to improve dictionary lookup accuracy.

    Attributes
    ----------
    language_code : str
        ISO 639-1 language code for this processor
    """

    language_code: str = ""

    @abstractmethod
    def normalize(self, text: str) -> str:
        """
        Normalize text for consistent processing.

        Parameters
        ----------
        text : str
            Input text to normalize

        Returns
        -------
        str
            Normalized text
        """
        pass

    @abstractmethod
    def lemmatize(self, word: str) -> list[str]:
        """
        Get lemmas/roots for a word.

        Parameters
        ----------
        word : str
            Word to lemmatize

        Returns
        -------
        list[str]
            List of possible lemmas/roots for the word
        """
        pass

    @abstractmethod
    def is_language_text(self, text: str) -> bool:
        """
        Check if text contains characters from this language.

        Parameters
        ----------
        text : str
            Text to check

        Returns
        -------
        bool
            True if text contains characters from this language
        """
        pass

    def get_lookup_forms(self, word: str) -> list[str]:
        """
        Get all forms of a word to try for dictionary lookup.

        Returns the original word, normalized form, and lemmas.

        Parameters
        ----------
        word : str
            Word to process

        Returns
        -------
        list[str]
            List of forms to try in order (original, normalized, lemmas)
        """
        forms = [word]

        # Add normalized form
        normalized = self.normalize(word)
        if normalized and normalized != word:
            forms.append(normalized)

        # Add lemmas
        lemmas = self.lemmatize(normalized if normalized else word)
        for lemma in lemmas:
            if lemma and lemma not in forms:
                forms.append(lemma)

        return forms
