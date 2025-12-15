"""
Text processing and analysis engine.

This module processes text sources using selected dictionaries and resources
to generate word-by-word analysis with definitions.
"""

import re
from datetime import datetime

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
        self.parsers: dict[str, any] = {}

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
                import hanzipy

                parser = hanzipy
            except ImportError:
                print("hanzipy not available")
                parser = None

        self.parsers[resource.id] = parser
        return parser

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
        This is a simple tokenization that splits on whitespace and punctuation.
        More sophisticated tokenization could be added for specific languages.
        """
        # Split on whitespace and common punctuation
        # Keep words, remove empty strings
        words = re.findall(r"\b\w+\b", text)
        return words

    def _lookup_word(self, word: str, resource: DictionaryResource) -> list[str] | None:
        """
        Look up a word in a specific resource.

        Parameters
        ----------
        word : str
            Word to look up
        resource : DictionaryResource
            Resource to use

        Returns
        -------
        Optional[List[str]]
            List of definitions, or None if not found
        """
        parser = self._get_parser(resource)
        if not parser:
            return None

        definitions = []

        if resource.format == DictionaryFormat.STARDICT:
            if hasattr(parser, "lookup"):
                result = parser.lookup(word)
                if result:
                    definitions.append(result)

        elif resource.format == DictionaryFormat.HANZIPY:
            # Use hanzipy for Chinese characters
            try:
                # Check if it's a Chinese character
                if any("\u4e00" <= char <= "\u9fff" for char in word):
                    # Get character information
                    for char in word:
                        if "\u4e00" <= char <= "\u9fff":
                            info = parser.decompose(char)
                            if info:
                                definition = f"Character: {char}, Decomposition: {info}"
                                definitions.append(definition)
            except Exception as e:
                print(f"Error using hanzipy: {e}")

        return definitions if definitions else None

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
                    definitions = self._lookup_word(word, resource)
                    if definitions:
                        word_defs.append(
                            WordDefinition(
                                word=word,
                                definitions=definitions,
                                source_dict=resource.id,
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
