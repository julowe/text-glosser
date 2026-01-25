"""
Text processing and analysis engine.

This module processes text sources using selected dictionaries and resources
to generate word-by-word analysis with definitions.
"""

import unicodedata
from datetime import datetime
from typing import Any

from ..core.language_processors import LanguageProcessor
from ..core.language_processors.arabic import ArabicProcessor
from ..core.models import (
    DictionaryFormat,
    DictionaryResource,
    LineAnalysis,
    TextAnalysis,
    TextSource,
    WordDefinition,
)
from ..core.parsers.stardict import StarDictParser
from ..core.registry import ResourceRegistry


class TextProcessor:
    """
    Process text sources using linguistic resources.

    This class analyzes text word-by-word using selected dictionaries
    and linguistic resources to provide definitions and grammatical information.

    Attributes
    ----------
    registry : ResourceRegistry
        Registry of available resources
    parsers : Dict[str, Any]
        Cache of loaded dictionary parsers
    """

    def __init__(self, registry: ResourceRegistry):
        """
        Initialize the text processor.

        Parameters
        ----------
        registry : ResourceRegistry
            Resource registry instance
        """
        self.registry = registry
        self.parsers: dict[str, Any] = {}
        self._language_processors: dict[str, LanguageProcessor] = {}

    def _get_language_processor(self, language_code: str) -> LanguageProcessor | None:
        """
        Get or create a language processor for a specific language.

        Parameters
        ----------
        language_code : str
            ISO 639-1 language code

        Returns
        -------
        LanguageProcessor | None
            Language processor instance or None if not available
        """
        if language_code in self._language_processors:
            return self._language_processors[language_code]

        processor = None
        if language_code == "ar":
            processor = ArabicProcessor()

        if processor:
            self._language_processors[language_code] = processor

        return processor

    def _get_parser(self, resource: DictionaryResource):
        """
        Get or create a parser for a resource.

        Parameters
        ----------
        resource : DictionaryResource
            The resource to get a parser for

        Returns
        -------
        Any
            Parser instance or None if not applicable
        """
        if resource.id in self.parsers:
            return self.parsers[resource.id]

        parser = None

        if resource.format == DictionaryFormat.STARDICT:
            if resource.file_paths:
                # Find the .ifo file
                ifo_file = next(
                    (fp for fp in resource.file_paths if fp.endswith(".ifo")), None
                )
                if ifo_file:
                    try:
                        parser = StarDictParser(ifo_file)
                    except Exception as e:
                        print(f"Error loading StarDict {resource.name}: {e}")

        elif resource.format == DictionaryFormat.HANZIPY:
            # hanzipy will be used differently - import on demand
            try:
                # import hanzipy
                # parser = hanzipy

                # import decomposer
                # from hanzipy.decomposer import HanziDecomposer
                # hDecomposer = HanziDecomposer()
                # import dictionary
                from hanzipy.dictionary import HanziDictionary

                # hDictionary = HanziDictionary()
                parser = HanziDictionary()  # hack to test exsting hacky code

            except ImportError:
                print("hanzipy not available")
                parser = None

        self.parsers[resource.id] = parser
        return parser

    def _is_chinese_char(self, char: str) -> bool:
        """
        Check if a character is a Chinese character.

        Parameters
        ----------
        char : str
            Character to check

        Returns
        -------
        bool
            True if character is in the CJK Unified Ideographs range
        """
        return "\u4e00" <= char <= "\u9fff"

    def _is_word_char(self, char: str) -> bool:
        """
        Check if a character is a word character (letter or number).

        Uses Unicode categories to properly identify letters and numbers
        across all scripts (Arabic, Hebrew, Greek, Sanskrit, Latin, etc.).

        Parameters
        ----------
        char : str
            Character to check

        Returns
        -------
        bool
            True if character is a letter or number
        """
        category = unicodedata.category(char)
        # L* = Letter (Lu, Ll, Lt, Lm, Lo)
        # N* = Number (Nd, Nl, No)
        # M* = Mark (Mn, Mc, Me) - combining marks for diacritics
        return category[0] in ("L", "N", "M")

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words.

        Parameters
        ----------
        text : str
            Text to tokenize

        Returns
        -------
        List[str]
            List of words

        Notes
        -----
        This tokenization handles Chinese characters individually while keeping
        other languages' words together. Chinese characters (CJK Unified Ideographs)
        are treated as separate tokens, while other scripts (Arabic, Hebrew, Greek,
        Sanskrit, Latin, etc.) are tokenized as words based on whitespace and
        punctuation boundaries.

        Uses Unicode character categories to properly identify word characters
        across all scripts.
        """
        tokens = []
        i = 0
        while i < len(text):
            char = text[i]

            # If it's a Chinese character, add it as a separate token
            if self._is_chinese_char(char):
                tokens.append(char)
                i += 1
            # If it's not a word character (whitespace, punctuation, etc.), skip it
            elif not self._is_word_char(char):
                i += 1
            # Otherwise, it's part of a word in any script
            else:
                # Collect consecutive word characters (including combining marks)
                word = ""
                while (
                    i < len(text)
                    and self._is_word_char(text[i])
                    and not self._is_chinese_char(text[i])
                ):
                    word += text[i]
                    i += 1
                if word:
                    tokens.append(word)

        return tokens

    def _lookup_word(
        self, word: str, resource: DictionaryResource
    ) -> dict[str, Any] | None:
        """
        Look up a word in a specific resource.

        For Arabic resources, uses the Arabic language processor to try
        multiple forms (original, normalized, lemmatized) for lookup.

        Parameters
        ----------
        word : str
            Word to look up
        resource : DictionaryResource
            Resource to use

        Returns
        -------
        Optional[Dict[str, Any]]
            Dictionary containing:
            - 'definitions': List of definition strings
            - 'grammatical_info': Dict with lemmas and other grammatical data
            Or None if not found
        """
        parser = self._get_parser(resource)
        if not parser:
            return None

        definitions = []
        grammatical_info: dict[str, Any] = {}

        if resource.format == DictionaryFormat.STARDICT:
            if hasattr(parser, "lookup"):
                # For Arabic resources, try multiple forms of the word
                if resource.primary_language == "ar":
                    lang_processor = self._get_language_processor("ar")
                    if lang_processor:
                        # Get all forms to try (original, normalized, lemmas)
                        lookup_forms = lang_processor.get_lookup_forms(word)

                        # Store lemmas in grammatical_info
                        # lookup_forms typically include: original, normalized, lemmas
                        # We want to capture the lemmas specifically
                        if hasattr(lang_processor, "lemmatize"):
                            lemma = lang_processor.lemmatize(word)
                            if lemma and lemma != word:
                                grammatical_info["lemmas"] = [lemma]

                        # Also store the normalized form if different
                        if hasattr(lang_processor, "normalize"):
                            normalized = lang_processor.normalize(word)
                            if normalized and normalized != word:
                                grammatical_info["normalized_form"] = normalized

                        matched_form = None
                        for form in lookup_forms:
                            result = parser.lookup(form)
                            if result:
                                definitions.append(result)
                                matched_form = form
                                break  # Stop after first successful lookup

                        # Record which form matched
                        if matched_form and matched_form != word:
                            grammatical_info["matched_form"] = matched_form
                    else:
                        # Fallback: direct lookup
                        result = parser.lookup(word)
                        if result:
                            definitions.append(result)
                else:
                    # Non-Arabic: direct lookup
                    result = parser.lookup(word)
                    if result:
                        definitions.append(result)

        elif resource.format == DictionaryFormat.HANZIPY:
            # Use hanzipy for Chinese characters
            try:
                # Check if it's a Chinese character
                if any(self._is_chinese_char(char) for char in word):
                    # Get character information
                    for char in word:
                        if self._is_chinese_char(char):
                            info = parser.definition_lookup(char)
                            if info:
                                definition = f"Character: {char}, Decomposition: {info}"
                                definitions.append(definition)
            except Exception as e:
                print(f"Error using hanzipy: {e}")

        if definitions:
            return {
                "definitions": definitions,
                "grammatical_info": grammatical_info if grammatical_info else None,
            }
        return None

    def analyze_text(
        self, source: TextSource, selected_resource_ids: list[str]
    ) -> TextAnalysis:
        """
        Analyze a text source using selected resources.

        Parameters
        ----------
        source : TextSource
            Text source to analyze
        selected_resource_ids : List[str]
            IDs of resources to use

        Returns
        -------
        TextAnalysis
            Analysis results
        """
        # Split text into lines
        lines = source.content.split("\n")

        # Get selected resources
        resources = [
            self.registry.get_resource(rid)
            for rid in selected_resource_ids
            if self.registry.get_resource(rid)
        ]

        line_analyses = []
        total_words = 0
        errors = []
        words_without_definitions = set()

        for line_num, line_text in enumerate(lines, 1):
            if not line_text.strip():
                continue

            # Tokenize line
            words = self._tokenize(line_text)
            total_words += len(words)

            word_defs = []
            for word in words:
                # Look up word in all resources
                found_definitions = False

                for resource in resources:
                    lookup_result = self._lookup_word(word, resource)
                    if lookup_result:
                        word_defs.append(
                            WordDefinition(
                                word=word,
                                definitions=lookup_result["definitions"],
                                source_dict=resource.id,
                                grammatical_info=lookup_result.get("grammatical_info"),
                            )
                        )
                        found_definitions = True

                if not found_definitions:
                    words_without_definitions.add(word)

            if word_defs:
                line_analyses.append(
                    LineAnalysis(line_number=line_num, words=word_defs)
                )

        # Add error for words without definitions
        if words_without_definitions:
            errors.append(
                f"No definitions found for {len(words_without_definitions)}"
                f" unique words: "
                f"{', '.join(sorted(words_without_definitions)[:10])}"
                + ("..." if len(words_without_definitions) > 10 else "")
            )

        return TextAnalysis(
            source_id=source.id,
            source_name=source.name,
            total_lines=len(lines),
            total_words=total_words,
            dictionaries_used=selected_resource_ids,
            lines=line_analyses,
            errors=errors,
            timestamp=datetime.now(),
        )
