"""
CAMeL Tools-based morphological analyzer for Arabic.

This module implements the MorphologicalAnalyzer interface using
CAMeL Tools (https://github.com/CAMeL-Lab/camel_tools) for high-accuracy
Arabic morphological analysis.

CAMeL Tools requires large data files (~200MB+) which are downloaded on-demand
the first time the analyzer is used. The data directory location is controlled
by the CAMELTOOLS_DATA environment variable.
"""

import asyncio
import logging
import os
from typing import Any

from .base import MorphologicalAnalyzer, TokenSegment

# Logger for this module
_logger = logging.getLogger(__name__)

# Package name for CAMeL Tools disambiguator data
CAMEL_DISAMBIG_PACKAGE = "disambig-mle-calima-msa-r13"

# CAMeL Tools POS tag mapping to standard tags
CAMEL_POS_MAP = {
    "noun": "NOUN",
    "noun_prop": "PROPN",
    "adj": "ADJ",
    "adj_comp": "ADJ",
    "adj_num": "ADJ",
    "adv": "ADV",
    "adv_interrog": "ADV",
    "adv_rel": "ADV",
    "pron": "PRON",
    "pron_dem": "PRON",
    "pron_exclam": "PRON",
    "pron_interrog": "PRON",
    "pron_rel": "PRON",
    "verb": "VERB",
    "verb_pseudo": "VERB",
    "part": "PART",
    "part_det": "DET",
    "part_focus": "PART",
    "part_fut": "PART",
    "part_interrog": "PART",
    "part_neg": "PART",
    "part_restrict": "PART",
    "part_verb": "PART",
    "part_voc": "PART",
    "prep": "PREP",
    "conj": "CONJ",
    "conj_sub": "SCONJ",
    "interj": "INTJ",
    "abbrev": "X",
    "punc": "PUNCT",
    "digit": "NUM",
    "foreign": "X",
    "suffix": "PART",  # Map suffix to PART for consistency
}

# Gloss mapping for common prefixes/particles
PREFIX_GLOSSES = {
    "wa": "and",
    "fa": "so/then",
    "bi": "with/by",
    "ka": "like/as",
    "li": "to/for",
    "Al": "the",
    "sa": "will",
}


def _get_data_dir() -> str:
    """
    Get the CAMeL Tools data directory.

    Returns the directory path from CAMELTOOLS_DATA environment variable,
    or a default path if not set.

    Returns
    -------
    str
        Path to the CAMeL Tools data directory
    """
    default_dir = os.path.join(os.path.expanduser("~"), ".camel_tools")
    return os.environ.get("CAMELTOOLS_DATA", default_dir)


def _check_data_exists() -> bool:
    """
    Check if CAMeL Tools data exists in the data directory.

    Returns
    -------
    bool
        True if data exists, False otherwise
    """
    data_dir = _get_data_dir()
    # Check for morphology database which is required
    morphology_db_path = os.path.join(data_dir, "data", "disambig", "mle")
    return os.path.exists(morphology_db_path)


def download_camel_data(progress_callback: Any = None) -> bool:
    """
    Download CAMeL Tools data package.

    Downloads the 'light' data package which includes basic morphological
    analysis capabilities. This is a blocking operation that may take
    several minutes depending on network speed.

    Parameters
    ----------
    progress_callback : callable, optional
        Function to call with progress updates. Called with (message: str).

    Returns
    -------
    bool
        True if download succeeded, False otherwise

    Notes
    -----
    The download location is determined by the CAMELTOOLS_DATA
    environment variable, or defaults to ~/.camel_tools.
    """
    try:
        from camel_tools.data import CATALOGUE, downloader

        data_dir = _get_data_dir()

        # Ensure directory exists
        os.makedirs(data_dir, exist_ok=True)

        if progress_callback:
            progress_callback("Starting CAMeL Tools data download...")
            progress_callback(f"Download location: {data_dir}")
            progress_callback("This may take several minutes...")

        # Set the CAMELTOOLS_DATA environment variable for the downloader
        os.environ["CAMELTOOLS_DATA"] = data_dir

        # Download the light package which includes essential data
        # The 'light' package includes morphology-db-r13 and other essentials
        packages_to_download = []

        # Get packages from catalogue
        for pkg_name in CATALOGUE.packages:
            # Download essential packages for morphological analysis
            if CAMEL_DISAMBIG_PACKAGE in pkg_name:
                packages_to_download.append(pkg_name)

        if not packages_to_download:
            # Fallback: try to download default/light packages
            if progress_callback:
                progress_callback("Downloading default disambiguation data...")

            # Use download_all_datasets for essential data
            try:
                downloader.download_package(CAMEL_DISAMBIG_PACKAGE, data_dir)
            except Exception as e:
                _logger.warning(f"Could not download {CAMEL_DISAMBIG_PACKAGE}: {e}")

        for pkg_name in packages_to_download:
            if progress_callback:
                progress_callback(f"Downloading {pkg_name}...")
            try:
                downloader.download_package(pkg_name, data_dir)
            except Exception as e:
                _logger.warning(f"Could not download {pkg_name}: {e}")
                if progress_callback:
                    progress_callback(f"Warning: Could not download {pkg_name}: {e}")

        if progress_callback:
            progress_callback("Download complete!")

        return True

    except ImportError:
        if progress_callback:
            progress_callback("Error: camel-tools is not installed")
        return False
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error downloading CAMeL Tools data: {e}")
        return False


async def download_camel_data_async(progress_callback: Any = None) -> bool:
    """
    Download CAMeL Tools data package asynchronously.

    This is a non-blocking wrapper around download_camel_data that uses
    asyncio.to_thread to run the download in a background thread.

    Parameters
    ----------
    progress_callback : callable, optional
        Function to call with progress updates. Called with (message: str).

    Returns
    -------
    bool
        True if download succeeded, False otherwise
    """
    return await asyncio.to_thread(download_camel_data, progress_callback)


class CamelToolsAnalyzer(MorphologicalAnalyzer):
    """
    Arabic morphological analyzer using CAMeL Tools.

    This analyzer uses CAMeL Tools' MLEDisambiguator for high-accuracy
    Arabic morphological analysis. It breaks down Arabic words into their
    constituent parts (prefixes, stem, suffixes) for word-by-word glossing.

    CAMeL Tools requires large data files (~200MB+) which are downloaded
    on-demand the first time the analyzer is initialized if not already
    present.

    Attributes
    ----------
    name : str
        Human-readable name of this analyzer
    language_code : str
        ISO 639-1 code for Arabic ("ar")
    _disambiguator : MLEDisambiguator | None
        Cached disambiguator instance
    _data_downloaded : bool
        Whether data has been downloaded

    Examples
    --------
    >>> analyzer = CamelToolsAnalyzer()
    >>> if analyzer.is_available():
    ...     segments = analyzer.analyze_word("وبكتاب")
    ...     for seg in segments:
    ...         print(f"{seg.segment_text}: {seg.pos} - {seg.gloss}")
    """

    name: str = "CAMeL Tools Arabic Analyzer"
    language_code: str = "ar"

    def __init__(self, auto_download: bool = False):
        """
        Initialize the CAMeL Tools analyzer.

        Parameters
        ----------
        auto_download : bool, optional
            If True, automatically download data if not present.
            Default is False to avoid unexpected long operations.
        """
        self._disambiguator: Any = None
        self._data_downloaded: bool = False
        self._auto_download = auto_download
        self._init_error: str | None = None

    def _ensure_data(self, progress_callback: Any = None) -> bool:
        """
        Ensure CAMeL Tools data is available.

        Downloads data if not present and auto_download is enabled.

        Parameters
        ----------
        progress_callback : callable, optional
            Function to call with progress updates.

        Returns
        -------
        bool
            True if data is available, False otherwise
        """
        if _check_data_exists():
            self._data_downloaded = True
            return True

        if self._auto_download:
            return download_camel_data(progress_callback)

        return False

    def _get_disambiguator(self):
        """
        Get or create the CAMeL Tools disambiguator instance.

        Returns
        -------
        MLEDisambiguator | None
            The disambiguator instance, or None if not available
        """
        if self._disambiguator is None:
            if not self._ensure_data():
                return None

            try:
                from camel_tools.disambig.mle import MLEDisambiguator

                # Set data directory before initializing
                os.environ["CAMELTOOLS_DATA"] = _get_data_dir()

                # Initialize the MLE disambiguator
                self._disambiguator = MLEDisambiguator.pretrained()

            except ImportError as e:
                _logger.warning(f"CAMeL Tools import failed: {e}")
                self._init_error = str(e)
            except Exception as e:
                _logger.error(f"Failed to initialize CAMeL Tools disambiguator: {e}")
                self._init_error = str(e)

        return self._disambiguator

    def is_available(self) -> bool:
        """
        Check if CAMeL Tools is available and data is present.

        Returns
        -------
        bool
            True if camel-tools can be imported and data exists
        """
        try:
            import camel_tools  # noqa: F401

            return _check_data_exists()
        except ImportError:
            return False

    def is_data_available(self) -> bool:
        """
        Check if CAMeL Tools data is downloaded.

        Returns
        -------
        bool
            True if data exists, False otherwise
        """
        return _check_data_exists()

    def needs_data_download(self) -> bool:
        """
        Check if data needs to be downloaded.

        Returns
        -------
        bool
            True if camel-tools is installed but data is missing
        """
        try:
            import camel_tools  # noqa: F401

            return not _check_data_exists()
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

    def _map_pos(self, camel_pos: str) -> str:
        """
        Map CAMeL Tools POS tag to standard tag.

        Parameters
        ----------
        camel_pos : str
            POS tag from CAMeL Tools

        Returns
        -------
        str
            Standard POS tag
        """
        if not camel_pos:
            return "UNKNOWN"

        # Convert to lowercase for matching
        pos_lower = camel_pos.lower()

        # Direct lookup
        if pos_lower in CAMEL_POS_MAP:
            return CAMEL_POS_MAP[pos_lower]

        # Try prefix matching
        for key, value in CAMEL_POS_MAP.items():
            if pos_lower.startswith(key):
                return value

        return "UNKNOWN"

    def _get_gloss(self, morpheme: str, pos: str) -> str:
        """
        Get English gloss for a morpheme.

        Parameters
        ----------
        morpheme : str
            The morpheme text
        pos : str
            Part of speech

        Returns
        -------
        str
            English gloss or empty string
        """
        # Check prefix glosses
        if morpheme in PREFIX_GLOSSES:
            return PREFIX_GLOSSES[morpheme]

        # Return empty string - gloss will come from dictionary lookup
        return ""

    def analyze_word(self, word: str) -> list[TokenSegment]:
        """
        Analyze an Arabic word and return its morphological segments.

        This method uses CAMeL Tools' MLEDisambiguator to break down
        an Arabic word into prefixes, stem, and suffixes.

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
        >>> analyzer = CamelToolsAnalyzer()
        >>> segments = analyzer.analyze_word("وبكتاب")
        >>> len(segments) >= 1
        True
        """
        disambiguator = self._get_disambiguator()

        # Fallback: return whole word as single segment
        if not disambiguator:
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
            # Disambiguate the word
            result = disambiguator.disambiguate([word])

            if not result or not result[0].analyses:
                return [
                    TokenSegment(
                        segment_text=word,
                        lemma=word,
                        root="",
                        pos="UNKNOWN",
                        gloss="",
                    )
                ]

            # Get the top analysis
            top_analysis = result[0].analyses[0]
            analysis = top_analysis.analysis

            segments = []

            # Extract morphological components
            # CAMeL Tools provides d1tok, d2tok, d3tok for segments
            # and detailed morphological features

            # Get prefix (proclitic)
            prefix = (
                analysis.get("prc0", "")
                + analysis.get("prc1", "")
                + analysis.get("prc2", "")
                + analysis.get("prc3", "")
            )

            # Get stem
            stem = analysis.get("stem", word)
            lemma = analysis.get("lex", stem)
            root = analysis.get("root", "")
            pos = analysis.get("pos", "")

            # Get suffix (enclitic)
            suffix = analysis.get("enc0", "")

            # Parse prefixes into individual segments
            if prefix:
                # Split compound prefixes
                prefix_normalized = self._normalize(prefix)
                for prefix_char in prefix_normalized:
                    if prefix_char:
                        mapped_pos = self._map_pos("part")
                        gloss = self._get_gloss(prefix_char, mapped_pos)
                        segments.append(
                            TokenSegment(
                                segment_text=prefix_char,
                                lemma=prefix_char,
                                root="",
                                pos=mapped_pos,
                                gloss=gloss,
                            )
                        )

            # Add stem segment
            if stem:
                stem_normalized = self._normalize(stem)
                lemma_normalized = self._normalize(lemma) if lemma else stem_normalized
                mapped_pos = self._map_pos(pos)

                segments.append(
                    TokenSegment(
                        segment_text=stem_normalized,
                        lemma=lemma_normalized,
                        root=root,
                        pos=mapped_pos,
                        gloss="",  # Gloss comes from dictionary lookup
                        features={
                            "original": word,
                            "vocalized": analysis.get("diac", ""),
                            "pos_full": pos,
                            "aspect": analysis.get("asp", ""),
                            "voice": analysis.get("vox", ""),
                            "mood": analysis.get("mod", ""),
                            "person": analysis.get("per", ""),
                            "gender": analysis.get("gen", ""),
                            "number": analysis.get("num", ""),
                            "state": analysis.get("stt", ""),
                            "case": analysis.get("cas", ""),
                        },
                    )
                )

            # Add suffix segment if present
            if suffix:
                suffix_normalized = self._normalize(suffix)
                segments.append(
                    TokenSegment(
                        segment_text=suffix_normalized,
                        lemma=suffix_normalized,
                        root="",
                        pos="PART",  # Use PART for consistency with standard tags
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

        except (AttributeError, TypeError, ValueError, KeyError, IndexError):
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


def get_camel_tools_analyzer(auto_download: bool = False) -> CamelToolsAnalyzer:
    """
    Create a new instance of the CAMeL Tools analyzer.

    Parameters
    ----------
    auto_download : bool, optional
        If True, automatically download data if not present.
        Default is False.

    Returns
    -------
    CamelToolsAnalyzer
        A new CAMeL Tools analyzer instance
    """
    return CamelToolsAnalyzer(auto_download=auto_download)
