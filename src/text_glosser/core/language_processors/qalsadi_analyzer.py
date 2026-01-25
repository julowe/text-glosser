"""
Qalsadi-based morphological analyzer for Arabic.

This module implements the MorphologicalAnalyzer interface using
qalsadi and pyarabic libraries for Arabic morphological analysis.
"""

from typing import Any

from .base import MorphologicalAnalyzer, TokenSegment

# Arabic prefix glosses for common prefixes
ARABIC_PREFIX_GLOSSES = {
    "و": ("CONJ", "and"),
    "ف": ("CONJ", "so/then"),
    "ب": ("PREP", "with/by"),
    "ك": ("PREP", "like/as"),
    "ل": ("PREP", "to/for"),
    "ال": ("DEF", "the"),
    "س": ("FUT", "will"),
}

# Arabic POS type mapping from qalsadi to standard tags
QALSADI_POS_MAP = {
    "Noun": "NOUN",
    "Verb": "VERB",
    "Adj": "ADJ",
    "Particle": "PART",
    "Prep": "PREP",
    "Conj": "CONJ",
    "Pronoun": "PRON",
    "Adverb": "ADV",
    "مصدر": "NOUN",  # Masdar (verbal noun)
    "اسم": "NOUN",
    "فعل": "VERB",
    "حرف": "PART",
}


class QalsadiAnalyzer(MorphologicalAnalyzer):
    """
    Arabic morphological analyzer using qalsadi library.

    This analyzer uses qalsadi's analex module to break down Arabic words
    into their constituent parts (prefixes, stem, suffixes) for word-by-word
    glossing. It follows the Strategy Pattern, allowing easy replacement
    with other analyzers (CAMeL Tools, Stanza) in the future.

    Attributes
    ----------
    name : str
        Human-readable name of this analyzer
    language_code : str
        ISO 639-1 code for Arabic ("ar")

    Examples
    --------
    >>> analyzer = QalsadiAnalyzer()
    >>> segments = analyzer.analyze_word("وبكتاب")
    >>> for seg in segments:
    ...     print(f"{seg.segment_text}: {seg.pos} - {seg.gloss}")
    و: CONJ - and
    ب: PREP - with/by
    كتاب: NOUN - book
    """

    name: str = "Qalsadi Arabic Analyzer"
    language_code: str = "ar"

    def __init__(self):
        """Initialize the Qalsadi analyzer."""
        self._analyzer: Any = None

    def _get_analyzer(self):
        """
        Get or create the qalsadi analyzer instance.

        Returns
        -------
        qalsadi.analex.Analex | None
            The analyzer instance, or None if qalsadi is not available
        """
        if self._analyzer is None:
            try:
                import qalsadi.analex as analex

                self._analyzer = analex.Analex()
            except ImportError:
                pass
        return self._analyzer

    def is_available(self) -> bool:
        """
        Check if qalsadi is available.

        Returns
        -------
        bool
            True if qalsadi can be imported, False otherwise
        """
        try:
            import qalsadi.analex  # noqa: F401

            return True
        except ImportError:
            return False

    def _normalize(self, text: str) -> str:
        """
        Normalize Arabic text using pyarabic.

        Parameters
        ----------
        text : str
            Arabic text to normalize

        Returns
        -------
        str
            Normalized text
        """
        try:
            import pyarabic.araby as araby

            result = araby.strip_tashkeel(text)
            result = araby.strip_tatweel(result)
            return result
        except ImportError:
            return text

    def _parse_prefix(self, prefix: str) -> list[TokenSegment]:
        """
        Parse a prefix string into individual prefix segments.

        The prefix string from qalsadi may contain multiple prefixes
        concatenated together (e.g., "وب" for "و" + "ب").

        Parameters
        ----------
        prefix : str
            Concatenated prefix string from qalsadi

        Returns
        -------
        list[TokenSegment]
            List of individual prefix segments
        """
        segments = []

        if not prefix:
            return segments

        # Normalize the prefix
        prefix = self._normalize(prefix)

        # Try to identify individual prefixes
        remaining = prefix
        i = 0
        max_iterations = 10  # Prevent infinite loops

        while remaining and i < max_iterations:
            i += 1
            matched = False

            # Try longest prefixes first (e.g., "ال" before "ا")
            for known_prefix in sorted(
                ARABIC_PREFIX_GLOSSES.keys(), key=len, reverse=True
            ):
                if remaining.startswith(known_prefix):
                    pos, gloss = ARABIC_PREFIX_GLOSSES[known_prefix]
                    segments.append(
                        TokenSegment(
                            segment_text=known_prefix,
                            lemma=known_prefix,
                            root="",
                            pos=pos,
                            gloss=gloss,
                        )
                    )
                    remaining = remaining[len(known_prefix) :]
                    matched = True
                    break

            # If no known prefix matched, treat the rest as unknown
            if not matched and remaining:
                segments.append(
                    TokenSegment(
                        segment_text=remaining,
                        lemma=remaining,
                        root="",
                        pos="PREFIX",
                        gloss="",
                    )
                )
                break

        return segments

    def _map_pos(self, qalsadi_type: str) -> str:
        """
        Map qalsadi type string to standard POS tag.

        Parameters
        ----------
        qalsadi_type : str
            Type string from qalsadi (e.g., "Noun:مصدر:مصدر")

        Returns
        -------
        str
            Standard POS tag (e.g., "NOUN")
        """
        if not qalsadi_type:
            return "UNKNOWN"

        # Split on colon and check each part
        parts = qalsadi_type.split(":")
        for part in parts:
            if part in QALSADI_POS_MAP:
                return QALSADI_POS_MAP[part]

        return "UNKNOWN"

    def analyze_word(self, word: str) -> list[TokenSegment]:
        """
        Analyze an Arabic word and return its morphological segments.

        This method breaks down an Arabic word into prefixes, stem, and suffixes.
        For example, "وبكتاب" (wa-bi-kitaab) becomes:
        - "و" (wa) - conjunction "and"
        - "ب" (bi) - preposition "with"
        - "كتاب" (kitaab) - noun "book"

        Parameters
        ----------
        word : str
            Arabic word to analyze

        Returns
        -------
        list[TokenSegment]
            List of token segments. Returns a single segment with
            the original word if analysis fails.

        Examples
        --------
        >>> analyzer = QalsadiAnalyzer()
        >>> segments = analyzer.analyze_word("وبكتاب")
        >>> len(segments)
        3
        """
        analyzer = self._get_analyzer()

        # Fallback: return whole word as single segment
        if not analyzer:
            return [
                TokenSegment(
                    segment_text=word,
                    lemma=word,
                    root="",
                    pos="UNKNOWN",
                    gloss="",
                )
            ]

        try:
            results = analyzer.check_word(word)

            if not results:
                return [
                    TokenSegment(
                        segment_text=word,
                        lemma=word,
                        root="",
                        pos="UNKNOWN",
                        gloss="",
                    )
                ]

            # Get the best analysis (highest frequency)
            best = max(results, key=lambda x: x.get_freq())

            segments = []

            # Get affix components: (prefix, infix, case_suffix, suffix)
            # Note: infix and case_suffix are not currently used but may be
            # useful for future enhancements
            affix = best.get_affix()
            prefix = affix[0] if affix and len(affix) > 0 else ""
            suffix = affix[3] if affix and len(affix) > 3 else ""

            # Parse and add prefix segments
            prefix_segments = self._parse_prefix(prefix)
            segments.extend(prefix_segments)

            # Add stem segment
            stem = best.get_stem()
            lemma = best.get_lemma() or stem
            root = best.root or ""
            pos = self._map_pos(best.get_type())

            if stem:
                # Normalize the stem and lemma
                stem = self._normalize(stem)
                lemma_normalized = self._normalize(lemma)

                segments.append(
                    TokenSegment(
                        segment_text=stem,
                        lemma=lemma_normalized,
                        root=root,
                        pos=pos,
                        gloss="",  # Gloss comes from dictionary lookup
                        features={
                            "original": best.get_original(),
                            "vocalized": best.get_vocalized(),
                            "tags": best.get_tags(),
                        },
                    )
                )

            # Add suffix if present (excluding case markers)
            if suffix:
                suffix = self._normalize(suffix)
                segments.append(
                    TokenSegment(
                        segment_text=suffix,
                        lemma=suffix,
                        root="",
                        pos="SUFFIX",
                        gloss="",
                    )
                )

            # If no segments were created, return original word
            if not segments:
                return [
                    TokenSegment(
                        segment_text=word,
                        lemma=word,
                        root="",
                        pos="UNKNOWN",
                        gloss="",
                    )
                ]

            return segments

        except (AttributeError, TypeError, ValueError, KeyError):
            # On analysis error, return the original word as a single segment
            return [
                TokenSegment(
                    segment_text=word,
                    lemma=word,
                    root="",
                    pos="UNKNOWN",
                    gloss="",
                )
            ]


def get_qalsadi_analyzer() -> QalsadiAnalyzer:
    """
    Create a new instance of the Qalsadi analyzer.

    Returns
    -------
    QalsadiAnalyzer
        A new Qalsadi analyzer instance
    """
    return QalsadiAnalyzer()
