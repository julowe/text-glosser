# Copilot Instructions for text-glosser

## Repository Overview

This repository contains a text glosser application with language resources for various languages. The primary focus is on providing lexicon data for text glossing and translation purposes.

## Project Structure

```
text-glosser/
├── language_resources/    # Language-specific lexicon data
│   ├── ar/               # Arabic language resources
│   │   ├── lane-lexicon/     # Lane's Arabic-English Lexicon
│   │   └── salmone-lexicon/  # Salmone's Arabic-English Lexicon
│   └── sa/               # Sanskrit language resources
│       └── monier-williams-cologne/  # Monier-Williams Sanskrit Lexicon
```

## Language Resources

### Supported Languages
- **ar**: Arabic
- **sa**: Sanskrit

### Lexicon File Formats

The repository uses StarDict dictionary format with the following file types:
- `.ifo` - Dictionary information file (metadata)
- `.idx` - Index file (word list and offsets)
- `.dict.dz` - Compressed dictionary data
- `.syn` - Synonym file (optional)

When working with lexicon files:
- Do not modify the binary files (.dict.dz, .idx) directly
- The .ifo files contain metadata in INI-like format
- Always preserve the file structure and naming conventions

## Development Guidelines

### Python Project
This is a Python project. Follow these conventions:

1. **Code Style**: Follow PEP 8 guidelines
2. **Dependencies**: Use standard Python package management
3. **Environment**: Virtual environments are managed and ignored in version control (`.venv`, `venv/`, etc.)

### File Organization
- Keep language resources organized by language code (ISO 639-1)
- Each lexicon should have its own subdirectory
- Maintain consistent naming conventions for lexicon files

### Version Control
- The `.gitignore` is configured for Python projects
- Build artifacts, virtual environments, and cache files are ignored
- Language resource files are tracked in version control

## Best Practices

1. **When adding new language resources:**
   - Create a new directory under `language_resources/` using the ISO 639-1 language code
   - Include all required StarDict format files (.ifo, .idx, .dict.dz)
   - Document the lexicon source and license information

2. **When modifying code:**
   - Ensure compatibility with the existing lexicon file structure
   - Test with multiple language resources to ensure broad compatibility
   - Preserve backwards compatibility with existing lexicon formats

3. **Testing:**
   - Test with various lexicon sizes (Lane's lexicon is large, others may be smaller)
   - Verify handling of compressed dictionary data
   - Check proper parsing of .ifo metadata

## Special Considerations

- **Large Files**: Some lexicon files are quite large (especially compressed .dict.dz files)
- **Binary Data**: Dictionary data files are binary and should not be treated as text
- **Character Encodings**: Support Unicode properly for non-Latin scripts (Arabic, Sanskrit)
- **Resource Loading**: Optimize for efficient loading and memory usage of lexicon data
