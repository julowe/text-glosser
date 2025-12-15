"""
Output formatters for analysis results.

This module provides functions to export analysis results in various formats:
- Markdown
- JSON
- CoNLL-U
"""

import json

from ..core.models import SessionConfig, TextAnalysis


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
    word1: definition
    word2: definition

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
            # Format definitions
            defs = "; ".join(word_def.definitions)
            lines.append(f"{word_def.word}: {defs}")

        lines.append("")

    return "\n".join(lines)


def format_json(
    analysis: TextAnalysis,
    config: SessionConfig = None,
    include_config: bool = True
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
            "timestamp": analysis.timestamp.isoformat()
        },
        "lines": []
    }

    # Add line-by-line analysis
    for line_analysis in analysis.lines:
        line_data = {
            "line_number": line_analysis.line_number,
            "words": []
        }

        for word_def in line_analysis.words:
            word_data = {
                "word": word_def.word,
                "definitions": word_def.definitions,
                "source_dict": word_def.source_dict
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
                    "original_path": src.original_path
                }
                for src in config.text_sources
            ],
            "selected_resources": config.selected_resources,
            "created_at": config.created_at.isoformat()
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
    3. LEMMA: Lemma (base form)
    4. UPOS: Universal POS tag
    5. XPOS: Language-specific POS tag
    6. FEATS: Morphological features
    7. HEAD: Head of dependency relation
    8. DEPREL: Dependency relation to HEAD
    9. DEPS: Enhanced dependency graph
    10. MISC: Any other annotation

    For now, we populate FORM and MISC (with definitions).
    Other fields will be populated as grammar parsing is added.
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

        # Add each word
        word_id = 1
        for word_def in line_analysis.words:
            # Format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
            # We only populate FORM and MISC for now
            form = word_def.word
            lemma = "_"  # Unknown
            upos = "_"  # Unknown
            xpos = "_"  # Unknown
            feats = "_"  # Unknown
            head = "_"  # Unknown
            deprel = "_"  # Unknown
            deps = "_"  # Unknown

            # Put definitions in MISC field
            definitions_str = "|".join(word_def.definitions).replace("\t", " ").replace("\n", " ")
            misc = f"Definitions={definitions_str}|SourceDict={word_def.source_dict}"

            # Create CoNLL-U line
            conllu_line = "\t".join([
                str(word_id),
                form,
                lemma,
                upos,
                xpos,
                feats,
                head,
                deprel,
                deps,
                misc
            ])

            lines.append(conllu_line)
            word_id += 1

        # Blank line between sentences
        lines.append("")

    return "\n".join(lines)


def export_all_formats(
    analysis: TextAnalysis,
    output_dir: str,
    base_filename: str,
    config: SessionConfig = None
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
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    file_paths['markdown'] = str(md_path)

    # Export JSON
    json_path = output_path / f"{base_filename}.json"
    json_content = format_json(analysis, config=config)
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    file_paths['json'] = str(json_path)

    # Export CoNLL-U
    conllu_path = output_path / f"{base_filename}.conllu"
    conllu_content = format_conllu(analysis)
    with open(conllu_path, 'w', encoding='utf-8') as f:
        f.write(conllu_content)
    file_paths['conllu'] = str(conllu_path)

    return file_paths
