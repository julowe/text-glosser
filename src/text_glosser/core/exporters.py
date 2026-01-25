"""
Output formatters for analysis results.

This module provides functions to export analysis results in various formats:
- Markdown
- JSON
- CoNLL-U
"""

import html
import json
import re

from ..core.models import SessionConfig, TextAnalysis


def _convert_html_to_markdown(text: str) -> str:
    """
    Convert HTML tags to Markdown syntax and clean up the text.

    Parameters
    ----------
    text : str
        Text potentially containing HTML tags

    Returns
    -------
    str
        Text with HTML converted to Markdown or stripped
    """
    if not text:
        return text

    # Convert bold tags to markdown
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL
    )

    # Convert italic tags to markdown
    text = re.sub(r"<i>(.*?)</i>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)

    # Convert line breaks and paragraph markers to newlines
    # Handle consecutive tags by first normalizing, then collapsing
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)

    # Strip font color tags (keep content)
    text = re.sub(
        r"<font[^>]*>(.*?)</font>", r"\1", text, flags=re.IGNORECASE | re.DOTALL
    )

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = html.unescape(text)

    # Collapse multiple consecutive newlines into single newline
    text = re.sub(r"\n{2,}", "\n", text)

    # Clean up whitespace
    text = text.strip()

    return text


def _strip_html_for_conllu(text: str) -> str:
    """
    Strip HTML tags and convert line breaks to ;; for CoNLL-U format.

    Parameters
    ----------
    text : str
        Text potentially containing HTML tags

    Returns
    -------
    str
        Clean text suitable for CoNLL-U format
    """
    if not text:
        return text

    # Convert line breaks and paragraph markers to ;;
    # First normalize all line break types
    text = re.sub(r"(<br\s*/?>|<p\s*/?>|</p>)+", ";;", text, flags=re.IGNORECASE)

    # Strip font color tags (keep content)
    text = re.sub(
        r"<font[^>]*>(.*?)</font>", r"\1", text, flags=re.IGNORECASE | re.DOTALL
    )

    # Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = html.unescape(text)

    # Clean up multiple ;; into single ;;
    text = re.sub(r"(;;)+", ";;", text)

    # Remove tabs and newlines (not allowed in CoNLL-U fields)
    text = text.replace("\t", " ").replace("\n", " ")

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def format_markdown(analysis: TextAnalysis) -> str:
    """
    Format analysis results as Markdown.

    Parameters
    ----------
    analysis : TextAnalysis
        Analysis results to format

    Returns
    -------
    str
        Markdown-formatted text

    Notes
    -----
    The output follows this structure:
    # Analysis of [source name]
    - Line count: N
    - Word count: N
    - Dictionaries used: [list]
    - Errors: [list]

    ## Line 1
    word1:
    Lemma(s):
    lemma1
    Definition(s):
    definition1;
    definition2

    ## Line 2
    ...
    """
    lines = []

    # Header
    lines.append(f"# Analysis of {analysis.source_name}")
    lines.append("")

    # Metadata
    lines.append(f"**Line count:** {analysis.total_lines}")
    lines.append(f"**Word count:** {analysis.total_words}")
    lines.append(f"**Dictionaries used:** {', '.join(analysis.dictionaries_used)}")

    if analysis.errors:
        lines.append("")
        lines.append("**Problems encountered:**")
        for error in analysis.errors:
            lines.append(f"- {error}")

    lines.append("")

    # Line-by-line analysis
    for line_analysis in analysis.lines:
        lines.append(f"## Line {line_analysis.line_number}")
        lines.append("")

        for word_def in line_analysis.words:
            # Word on its own line followed by colon
            lines.append(f"{word_def.word}:")

            # Add lemmas if available
            lemmas = []
            if word_def.grammatical_info:
                if "lemma" in word_def.grammatical_info:
                    lemma_val = word_def.grammatical_info["lemma"]
                    if isinstance(lemma_val, list):
                        lemmas.extend(lemma_val)
                    else:
                        lemmas.append(lemma_val)
                if "lemmas" in word_def.grammatical_info:
                    lemma_val = word_def.grammatical_info["lemmas"]
                    if isinstance(lemma_val, list):
                        lemmas.extend(lemma_val)
                    else:
                        lemmas.append(lemma_val)

            if lemmas:
                lines.append("Lemma(s):")
                for lemma in lemmas:
                    cleaned_lemma = _convert_html_to_markdown(str(lemma))
                    lines.append(cleaned_lemma)

            # Definitions
            lines.append("Definition(s):")
            for definition in word_def.definitions:
                # Convert HTML to markdown and clean up
                cleaned_def = _convert_html_to_markdown(definition)
                # Replace any newlines within the definition with space
                # to avoid blank lines in the definition section
                cleaned_def = re.sub(r"\n+", " ", cleaned_def)
                # Add semicolon after each definition
                lines.append(f"{cleaned_def};")

            # Blank line before next word (not after last word in line)
            lines.append("")

    return "\n".join(lines)


def format_json(
    analysis: TextAnalysis,
    config: SessionConfig = None,
    include_config: bool = True,
) -> str:
    """
    Format analysis results as JSON.

    Parameters
    ----------
    analysis : TextAnalysis
        Analysis results to format
    config : SessionConfig, optional
        Session configuration (for re-running analysis)
    include_config : bool, optional
        Whether to include configuration section (default: True)

    Returns
    -------
    str
        JSON-formatted text

    Notes
    -----
    The JSON includes:
    - metadata: source info, counts, dictionaries used, errors
    - lines: array of line analyses with words and definitions
    - configuration: (optional) session config for re-running analysis
    """
    output = {
        "metadata": {
            "source_id": analysis.source_id,
            "source_name": analysis.source_name,
            "total_lines": analysis.total_lines,
            "total_words": analysis.total_words,
            "dictionaries_used": analysis.dictionaries_used,
            "errors": analysis.errors,
            "timestamp": analysis.timestamp.isoformat(),
        },
        "lines": [],
    }

    # Add line-by-line analysis
    for line_analysis in analysis.lines:
        line_data = {
            "line_number": line_analysis.line_number,
            "words": [],
        }

        for word_def in line_analysis.words:
            word_data = {
                "word": word_def.word,
                "definitions": word_def.definitions,
                "source_dict": word_def.source_dict,
            }
            if word_def.grammatical_info:
                word_data["grammatical_info"] = word_def.grammatical_info

            line_data["words"].append(word_data)

        output["lines"].append(line_data)

    # Add configuration if requested
    if include_config and config:
        output["configuration"] = {
            "session_id": config.session_id,
            "text_sources": [
                {
                    "id": src.id,
                    "name": src.name,
                    "source_type": src.source_type,
                    "original_path": src.original_path,
                }
                for src in config.text_sources
            ],
            "selected_resources": config.selected_resources,
            "created_at": config.created_at.isoformat(),
        }

    return json.dumps(output, indent=2, ensure_ascii=False)


def format_conllu(analysis: TextAnalysis) -> str:
    """
    Format analysis results as CoNLL-U.

    Parameters
    ----------
    analysis : TextAnalysis
        Analysis results to format

    Returns
    -------
    str
        CoNLL-U formatted text

    Notes
    -----
    CoNLL-U format (https://universaldependencies.org/format.html):
    Each word is on a line with tab-separated fields:
    1. ID: Word index
    2. FORM: Word form
    3. LEMMA: Lemma (base form) - comma-separated if multiple
    4. UPOS: Universal POS tag
    5. XPOS: Language-specific POS tag
    6. FEATS: Morphological features
    7. HEAD: Head of dependency relation
    8. DEPREL: Dependency relation to HEAD
    9. DEPS: Enhanced dependency graph
    10. MISC: Any other annotation

    Line breaks and HTML tags in definitions are converted to ;; or stripped.
    """
    lines = []

    # Add metadata comments
    lines.append(f"# source_name = {analysis.source_name}")
    lines.append(f"# total_lines = {analysis.total_lines}")
    lines.append(f"# total_words = {analysis.total_words}")
    lines.append(f"# dictionaries = {', '.join(analysis.dictionaries_used)}")
    lines.append(f"# timestamp = {analysis.timestamp.isoformat()}")
    lines.append("")

    # Process each line
    for line_analysis in analysis.lines:
        # Add sentence ID comment
        lines.append(f"# sent_id = line_{line_analysis.line_number}")

        # Add original text of the line
        original_text = " ".join(word_def.word for word_def in line_analysis.words)
        lines.append(f"# text = {original_text}")

        # Add each word
        word_id = 1
        for word_def in line_analysis.words:
            # Format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
            form = word_def.word

            # Extract lemmas from grammatical_info
            lemmas = []
            if word_def.grammatical_info:
                if "lemma" in word_def.grammatical_info:
                    lemma_val = word_def.grammatical_info["lemma"]
                    if isinstance(lemma_val, list):
                        lemmas.extend(lemma_val)
                    else:
                        lemmas.append(lemma_val)
                if "lemmas" in word_def.grammatical_info:
                    lemma_val = word_def.grammatical_info["lemmas"]
                    if isinstance(lemma_val, list):
                        lemmas.extend(lemma_val)
                    else:
                        lemmas.append(lemma_val)

            # Format lemma column - comma-separated if multiple, underscore if none
            if lemmas:
                # Strip HTML from lemmas and join with comma
                cleaned_lemmas = [
                    _strip_html_for_conllu(str(lem)) for lem in lemmas
                ]
                lemma = ",".join(cleaned_lemmas)
            else:
                lemma = "_"

            upos = "_"  # Unknown
            xpos = "_"  # Unknown
            feats = "_"  # Unknown
            head = "_"  # Unknown
            deprel = "_"  # Unknown
            deps = "_"  # Unknown

            # Put definitions in MISC field - strip HTML and convert line breaks to ;;
            cleaned_definitions = [
                _strip_html_for_conllu(d) for d in word_def.definitions
            ]
            definitions_str = "|".join(cleaned_definitions)
            misc = f"Definitions={definitions_str}|SourceDict={word_def.source_dict}"

            # Create CoNLL-U line
            conllu_line = "\t".join(
                [
                    str(word_id),
                    form,
                    lemma,
                    upos,
                    xpos,
                    feats,
                    head,
                    deprel,
                    deps,
                    misc,
                ]
            )

            lines.append(conllu_line)
            word_id += 1

        # Blank line between sentences
        lines.append("")

    return "\n".join(lines)


def export_all_formats(
    analysis: TextAnalysis,
    output_dir: str,
    base_filename: str,
    config: SessionConfig = None,
) -> dict[str, str]:
    """
    Export analysis in all formats.

    Parameters
    ----------
    analysis : TextAnalysis
        Analysis results to export
    output_dir : str
        Directory to write files to
    base_filename : str
        Base filename (without extension)
    config : SessionConfig, optional
        Session configuration for JSON export

    Returns
    -------
    Dict[str, str]
        Dictionary mapping format names to file paths

    Examples
    --------
    >>> paths = export_all_formats(analysis, "/output", "mytext")
    >>> print(paths)
    {'markdown': '/output/mytext.md', 'json': '/output/mytext.json', ...}
    """
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_paths = {}

    # Export Markdown
    md_path = output_path / f"{base_filename}.md"
    md_content = format_markdown(analysis)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    file_paths["markdown"] = str(md_path)

    # Export JSON
    json_path = output_path / f"{base_filename}.json"
    json_content = format_json(analysis, config=config)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_content)
    file_paths["json"] = str(json_path)

    # Export CoNLL-U
    conllu_path = output_path / f"{base_filename}.conllu"
    conllu_content = format_conllu(analysis)
    with open(conllu_path, "w", encoding="utf-8") as f:
        f.write(conllu_content)
    file_paths["conllu"] = str(conllu_path)

    return file_paths
