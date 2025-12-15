# Copilot Instructions for text-glosser

This document provides guidance for GitHub Copilot when working with the text-glosser repository.

## Project Overview

Text Glosser is a web-based and CLI application that creates word-by-word glosses/trots on provided texts using multiple linguistic dictionaries and resources. It supports:

- **Languages**: Sanskrit, Arabic, Chinese (with potential for more)
- **Dictionary formats**: StarDict format, Python library integration (e.g., hanzipy)
- **Output formats**: Markdown, JSON, CoNLL-U (Universal Dependencies)
- **Interfaces**: Command-line interface (CLI) and web interface

## Architecture

### Directory Structure

```
src/text_glosser/
├── core/           # Core functionality
│   ├── models.py       # Pydantic data models
│   ├── registry.py     # Dictionary resource registry
│   ├── ingestion.py    # Text input from files/URLs
│   ├── processor.py    # Text processing engine
│   ├── exporters.py    # Output formatters (MD, JSON, CoNLL-U)
│   ├── session.py      # Web UI session management
│   └── parsers/        # Dictionary parsers (StarDict, etc.)
├── utils/          # Utility modules
│   └── security.py     # Input sanitization and validation
├── cli/            # Command-line interface
│   └── main.py         # Click-based CLI
└── web/            # Web interface
    └── main.py         # FastAPI + NiceGUI web app
```

### Key Components

1. **ResourceRegistry**: Manages available dictionaries organized by language (ISO 639 codes)
2. **TextProcessor**: Analyzes text word-by-word using selected dictionaries
3. **SessionManager**: Handles web UI session persistence and cleanup
4. **StarDictParser**: Reads StarDict format dictionaries (.ifo, .idx, .dict/.dict.dz)
5. **Security Module**: Sanitizes all user inputs to prevent security vulnerabilities

## Coding Standards

### Python Style

- **Python version**: 3.12+ required
- **PEP 8**: Follow Python style guide
- **Type hints**: Use throughout the codebase
- **Imports**: Organized using isort (part of ruff)
- **Line length**: Default limit (88 chars with Black/ruff)

### Documentation

- **Docstring style**: NumPy/SciPy convention for compatibility with Sphinx
- **Always include**: Parameters, Returns, Raises sections
- **Example docstring format**:

```python
def process_text(source: str, resources: List[str]) -> Analysis:
    """
    Process text using selected resources.
    
    Parameters
    ----------
    source : str
        Text to analyze
    resources : List[str]
        Resource IDs to use
    
    Returns
    -------
    Analysis
        Analysis results
    
    Raises
    ------
    ValueError
        If no resources selected
    """
```

### Code Quality Tools

```bash
# Formatting and linting with ruff
ruff format src/ tests/           # Format code
ruff check src/ tests/            # Lint code
ruff check --fix src/ tests/      # Auto-fix issues

# Type checking
mypy src/ --ignore-missing-imports

# Testing
PYTHONPATH=src pytest                              # Run all tests
PYTHONPATH=src pytest --cov=text_glosser          # With coverage
PYTHONPATH=src pytest tests/unit/test_models.py   # Specific test
```

## Testing Guidelines

### Test Organization

- **Unit tests**: `tests/unit/` - Test individual components
- **Integration tests**: `tests/integration/` - Test component interactions (if added)
- **Test naming**: `test_*.py` files, `test_*` functions, `Test*` classes

### Test Requirements

- Use pytest framework
- Use pytest-asyncio for async tests
- Maintain or improve code coverage
- Add tests for new functionality
- Ensure all tests pass before committing

### Running Tests

```bash
# All tests
PYTHONPATH=src pytest

# With coverage
PYTHONPATH=src pytest --cov=text_glosser --cov-report=html

# Specific test file
PYTHONPATH=src pytest tests/unit/test_security.py

# Skip slow tests
PYTHONPATH=src pytest -m "not slow"
```

## Security Considerations

### Input Sanitization

**CRITICAL**: All user inputs must be sanitized using functions from `utils/security.py`:

- `sanitize_filename()`: Clean file names
- `sanitize_session_id()`: Validate session IDs
- `sanitize_iso_code()`: Validate language codes
- `sanitize_url()`: Validate and clean URLs
- `sanitize_text_content()`: Remove HTML/JS from text
- `is_safe_path()`: Prevent directory traversal

### Security Best Practices

1. **Never trust user input**: Always sanitize before use
2. **File operations**: Use `is_safe_path()` to prevent traversal attacks
3. **URLs**: Restrict to HTTP/HTTPS protocols only
4. **File sizes**: Enforce limits (default: 10MB)
5. **Session IDs**: Use `secrets.token_urlsafe()` for generation
6. **Avoid eval/exec**: Never execute user-provided code
7. **Regular expressions**: Be cautious with complex patterns that could cause ReDoS

### CodeQL and Security Scanning

- CodeQL analysis runs on every PR
- Trivy scans Docker images for vulnerabilities
- Address all security findings before merging

## Right-to-Left (RTL) Text Considerations

### Arabic and Other RTL Languages

The application supports Arabic dictionaries (Lane's and Salmone's lexicons). When working with RTL text:

1. **Text Direction**:
   - Arabic text flows right-to-left (RTL)
   - Dictionary entries may contain both RTL Arabic and LTR English
   - Ensure proper Unicode handling for bidirectional text

2. **Character Encoding**:
   - Always use UTF-8 encoding
   - Be aware of Arabic diacritics (tashkeel/harakat)
   - Preserve Unicode normalization (NFC/NFD considerations)

3. **Word Tokenization**:
   - Arabic words may include diacritics that should be preserved
   - Consider contextual forms of Arabic letters (initial, medial, final, isolated)
   - Respect language-specific whitespace and punctuation rules

4. **Display and Output**:
   - Markdown and JSON output should preserve RTL text direction
   - Web UI should support proper RTL text rendering (CSS: `direction: rtl`)
   - CoNLL-U format should handle RTL text correctly

5. **Testing RTL Text**:
   - Test with Arabic text samples when modifying text processing
   - Verify bidirectional text handling in output formats
   - Ensure dictionary lookups work with Arabic script variations

6. **Other RTL Languages**:
   - Consider Hebrew, Persian, Urdu if future dictionaries are added
   - Same principles apply: encoding, direction, tokenization

### Example RTL Handling

```python
# When processing text, preserve RTL markers
def process_line(text: str) -> str:
    """
    Process a line of text, preserving RTL text direction.
    
    Parameters
    ----------
    text : str
        Input text (may contain RTL characters)
    
    Returns
    -------
    str
        Processed text with preserved direction
    """
    # Tokenization should respect RTL word boundaries
    # Unicode bidi algorithm handles direction automatically
    return text  # UTF-8 encoding preserves RTL
```

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/julowe/text-glosser.git
cd text-glosser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .[dev]
```

### Running Locally

```bash
# Web UI (with auto-reload)
uvicorn text_glosser.web.main:app --reload --host 0.0.0.0 --port 8080

# CLI
text-glosser list-dictionaries
text-glosser process mytext.txt -r mw-sanskrit-english -o ./output
```

### Docker Development

```bash
# Build and run with docker-compose
docker-compose -f docker-compose.dev.yml up --build

# Or manually
docker build -t text-glosser:dev .
docker run -p 8080:8080 text-glosser:dev
```

## Common Tasks

### Adding a New Dictionary

1. Place dictionary files in `language_resources/{iso_code}/`
2. Update `ResourceRegistry` in `core/registry.py`
3. Add appropriate parser if new format
4. Update documentation

### Adding a New Output Format

1. Add formatter function to `core/exporters.py`
2. Follow pattern of existing formatters (markdown, JSON, CoNLL-U)
3. Add tests in `tests/unit/test_exporters.py`
4. Update CLI and web UI to support new format

### Modifying Text Processing

1. Update `TextProcessor` in `core/processor.py`
2. Consider impact on RTL text handling
3. Add/update tests in `tests/unit/test_processor.py`
4. Verify with sample texts in different languages

## Dependencies

### Core Dependencies

- **FastAPI**: Web framework for API and web UI
- **NiceGUI**: Modern UI framework built on FastAPI
- **Click**: CLI framework
- **Pydantic**: Data validation and settings
- **BeautifulSoup4**: HTML parsing for URL content
- **pystardict**: StarDict dictionary parser
- **hanzipy**: Chinese character analysis
- **conllu**: CoNLL-U format support

### Development Dependencies

- **pytest**: Testing framework
- **ruff**: Fast Python linter and formatter (replaces Black, isort, flake8)
- **mypy**: Static type checker
- **sphinx**: Documentation generator

## CI/CD

### GitHub Actions Workflows

1. **tests.yml**: Runs tests on Python 3.11 and 3.12, uploads coverage
2. **docker-build.yml**: Builds and publishes Docker images, runs Trivy security scan
3. **docs.yml**: Builds and deploys Sphinx documentation to GitHub Pages

### Pre-commit Checks

Before pushing:
- Run tests: `PYTHONPATH=src pytest`
- Run linter: `ruff check src/ tests/`
- Run formatter: `ruff format src/ tests/`
- Run type checker: `mypy src/`

## Common Issues and Solutions

### Import Errors

- Ensure `PYTHONPATH=src` when running pytest
- Use absolute imports from `text_glosser` package

### Dictionary Loading Issues

- Verify dictionary files exist in `language_resources/`
- Check `.ifo` file format and paths
- Ensure compressed `.dict.dz` files are readable

### RTL Text Display Issues

- Verify UTF-8 encoding throughout pipeline
- Check that web UI CSS includes RTL support
- Test with actual Arabic text samples

## Additional Resources

- [Project README](../README.md)
- [Implementation Summary](../IMPLEMENTATION.md)
- [Installation Guide](../docs/installation.rst)
- [Sphinx Documentation](../docs/)

## Questions?

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review test files for usage examples
