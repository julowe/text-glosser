# Text Glosser 📚

A comprehensive text analysis and glossing application that provides word-by-word definitions and grammatical information using multiple linguistic dictionaries and resources.

## 🌟 Features

### Core Functionality
- **Multi-Dictionary Support**: Analyze text using multiple dictionaries simultaneously
- **Multiple Input Sources**: Process text from files or web URLs
- **Multiple Output Formats**: Export results as Markdown, JSON, and CoNLL-U
- **Session Management**: Web UI sessions with configurable data retention (0-365 days)
- **Language Support**: ISO 639 compliant language organization and identification

### Supported Dictionaries & Resources

#### Built-in Dictionaries
- **Sanskrit-English**: Monier-Williams Dictionary (Cologne Digital Sanskrit Dictionaries)
- **Arabic-English**: 
  - Lane's Arabic-English Lexicon
  - Salmone's Arabic-English Lexicon
- **Chinese**: HanziPy library for Chinese character analysis

#### Supported Formats
- StarDict dictionary format (.ifo, .idx, .dict/.dict.dz files)
- Python library integration (e.g., hanzipy)
- Extensible architecture for adding MDict and other formats

### Interfaces

#### Command-Line Interface (CLI)
- Built with Click for robust argument parsing
- List available dictionaries
- Process files and URLs
- Multiple output format options
- Preview mode before processing

#### Web Interface
- Built with FastAPI + NiceGUI
- Interactive dictionary selection
- File upload with drag-and-drop
- URL fetching and processing
- Session-based result management
- Downloadable results in ZIP format
- Configurable data retention policies

### Security Features
- Input sanitization for all user inputs
- URL validation (HTTP/HTTPS only)
- File size limits to prevent DoS attacks
- Path traversal prevention
- Safe file naming
- HTML/JavaScript tag removal from fetched content

## 🚀 Quick Start

### Using Docker (Recommended for End Users)

The easiest way to use Text Glosser is with Docker:

```bash
# Pull and run the latest version
docker pull ghcr.io/julowe/text-glosser:latest
docker run -p 8080:8080 ghcr.io/julowe/text-glosser:latest

# Access the web UI at http://localhost:8080
```

Or use docker-compose:

```bash
# Pull the docker-compose.yml from the repository or create one:
docker-compose up -d

# Access at http://localhost:8080
```

### From Source (For Developers)

```bash
# Clone the repository
git clone https://github.com/julowe/text-glosser.git
cd text-glosser

# Install package in editable mode (Python 3.12+ required)
# This installs all runtime dependencies from pyproject.toml
pip install -e .

# For development with additional tools
pip install -e ".[dev]"
# Or alternatively:
# pip install -r requirements-dev.txt
```
pip install -e .
```

See the [Development Guide](docs/development.rst) for detailed setup instructions.

### Web UI Usage

1. Open http://localhost:8080 in your browser
2. **Select Dictionaries**: Choose one or more dictionaries organized by language
3. **Upload Text**: Upload files or enter URLs
4. **Process**: Click "Process Text" to analyze
5. **Download Results**: Get results in Markdown, JSON, or CoNLL-U format

### CLI Usage

If installed from source:

```bash
# List available dictionaries
text-glosser list-dictionaries

# List dictionaries for a specific language
text-glosser list-dictionaries --language ar

# Process a file with a specific dictionary
text-glosser process mytext.txt -r mw-sanskrit-english -o ./results

# Process multiple files with multiple dictionaries
text-glosser process file1.txt file2.txt \
    -r mw-sanskrit-english \
    -r lane-arabic-english \
    -o ./output

# Process a URL
text-glosser process https://example.com/article.html \
    -r hanzipy-chinese \
    -o ./output
```

## 📖 Output Formats

### Markdown Format

```markdown
# Analysis of mytext.txt

**Line count:** 10
**Word count:** 52
**Dictionaries used:** mw-sanskrit-english

## Line 1
karma: action; deed; work
dharma: duty; righteousness; law
```

### JSON Format

```json
{
  "metadata": {
    "source_name": "mytext.txt",
    "total_lines": 10,
    "total_words": 52,
    "dictionaries_used": ["mw-sanskrit-english"]
  },
  "lines": [
    {
      "line_number": 1,
      "words": [
        {
          "word": "karma",
          "definitions": ["action", "deed"],
          "source_dict": "mw-sanskrit-english"
        }
      ]
    }
  ],
  "configuration": {
    "session_id": "...",
    "selected_resources": ["mw-sanskrit-english"]
  }
}
```

### CoNLL-U Format

Standard Universal Dependencies CoNLL-U format with word definitions stored in the MISC field. Compatible with UD tools and parsers.

```
# sent_id = line_1
1	karma	_	_	_	_	_	_	_	Definitions=action|deed|SourceDict=mw-sanskrit-english
```

## 🏗️ Architecture

### Project Structure

```
text-glosser/
├── src/
│   └── text_glosser/
│       ├── core/           # Core processing logic
│       │   ├── models.py       # Data models
│       │   ├── registry.py     # Resource registry
│       │   ├── ingestion.py    # File/URL reading
│       │   ├── processor.py    # Text analysis engine
│       │   ├── exporters.py    # Output formatters
│       │   ├── session.py      # Session management
│       │   └── parsers/        # Dictionary parsers
│       │       └── stardict.py
│       ├── cli/            # Command-line interface
│       │   └── main.py
│       ├── web/            # Web interface
│       │   └── main.py
│       └── utils/          # Utilities
│           └── security.py     # Input sanitization
├── language_resources/     # Built-in dictionaries
│   ├── ar/                 # Arabic resources
│   │   ├── lane-lexicon/
│   │   └── salmone-lexicon/
│   └── sa/                 # Sanskrit resources
│       └── monier-williams-cologne/
├── tests/                  # Test suite
├── docs/                   # Documentation
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Key Components

- **ResourceRegistry**: Manages available dictionaries and resources
- **TextProcessor**: Analyzes text using selected resources
- **SessionManager**: Handles web UI session persistence
- **StarDictParser**: Reads StarDict format dictionaries
- **Security Module**: Sanitizes all user inputs

## 🔒 Security

### Input Sanitization
- All user inputs are sanitized to prevent injection attacks
- File paths validated to prevent directory traversal
- URLs restricted to HTTP/HTTPS protocols
- Content size limits enforced

### File Upload Security
- Filename sanitization
- File size limits (default: 10MB)
- Type validation
- Malicious content detection (planned)

### Session Security
- Random session ID generation (URL-safe tokens)
- Session data isolation
- Automatic cleanup of expired sessions

## 🧪 Development

For detailed development instructions, see the [Development Guide](docs/development.rst).

### Quick Development Setup

```bash
# Clone repository
git clone https://github.com/julowe/text-glosser.git
cd text-glosser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .
```

### Running Locally

**Web UI (with auto-reload):**
```bash
uvicorn text_glosser.web.main:app --reload --host 0.0.0.0 --port 8080
```

**CLI:**
```bash
text-glosser list-dictionaries
text-glosser process mytext.txt -r mw-sanskrit-english -o ./output
```

### Docker Development

```bash
# Build and run locally
docker-compose -f docker-compose.dev.yml up --build

# Or build manually
docker build -t text-glosser:dev .
docker run -p 8080:8080 text-glosser:dev
```

### Running Tests

```bash
# Run all tests
PYTHONPATH=src pytest

# With coverage
PYTHONPATH=src pytest --cov=text_glosser --cov-report=html

# Run specific tests
PYTHONPATH=src pytest tests/unit/test_models.py
```

### Code Quality

```bash
# Lint with ruff
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Type checking
mypy src/ --ignore-missing-imports
```

### Project Structure

```
text-glosser/
├── src/text_glosser/      # Source code
│   ├── core/              # Core processing logic
│   ├── cli/               # CLI interface
│   ├── web/               # Web interface
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── docs/                  # Sphinx documentation
├── language_resources/    # Built-in dictionaries
├── requirements.txt       # Runtime dependencies
└── requirements-dev.txt   # Development dependencies
```

### Dependencies

The project uses two requirements files:

- **requirements.txt**: Runtime dependencies only (for Docker and end users)
- **requirements-dev.txt**: Development dependencies (testing, docs, linting)

Both files are referenced in **pyproject.toml** for tool configuration.

## 📝 Documentation Style

All code follows NumPy/SciPy docstring conventions for compatibility with Sphinx documentation generation.

Example:
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

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Use type hints
- Write comprehensive docstrings
- Add unit tests for new features
- Update documentation

## 📜 License

[Add license information]

## 🙏 Acknowledgments

### Dictionary Sources

- **Monier-Williams Sanskrit Dictionary**: Cologne Digital Sanskrit Dictionaries
- **Lane's Arabic-English Lexicon**: Public domain
- **Salmone's Arabic-English Lexicon**: Public domain
- **HanziPy**: Python library for Chinese character information

## 🗺️ Roadmap

### Planned Features

- [ ] MDict format support
- [ ] Additional dictionary uploads via web UI
- [ ] Grammar parsing integration
- [ ] Word frequency analysis
- [ ] Concordance generation
- [ ] Custom dictionary creation tools
- [ ] API endpoints for programmatic access
- [ ] Multi-user support with authentication
- [ ] Advanced search and filtering
- [ ] Bulk processing capabilities

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- [Add contact information]

## Version History

### 0.1.0 (Initial Release)
- Core text processing functionality
- CLI interface
- Web UI with FastAPI + NiceGUI
- StarDict dictionary support
- Multiple output formats
- Session management
- Built-in dictionaries (Sanskrit, Arabic, Chinese)
