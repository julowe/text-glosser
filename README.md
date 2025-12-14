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

### Installation

```bash
# Clone the repository
git clone https://github.com/julowe/text-glosser.git
cd text-glosser

# Install dependencies
pip install -r requirements.txt
```

### Using Docker

```bash
# Build the image
docker build -t text-glosser .

# Run with docker-compose
docker-compose up -d

# Access the web UI at http://localhost:8080
```

### CLI Usage

#### List Available Dictionaries

```bash
# List all dictionaries
python -m text_glosser.cli.main list-dictionaries

# List dictionaries for a specific language
python -m text_glosser.cli.main list-dictionaries --language ar

# JSON output
python -m text_glosser.cli.main list-dictionaries --format json
```

#### Process Text

```bash
# Process a file with a specific dictionary
python -m text_glosser.cli.main process mytext.txt -r mw-sanskrit-english -o ./results

# Process multiple files with multiple dictionaries
python -m text_glosser.cli.main process file1.txt file2.txt \
    -r mw-sanskrit-english \
    -r lane-arabic-english \
    -o ./output

# Process a URL
python -m text_glosser.cli.main process https://example.com/article.html \
    -r hanzipy-chinese \
    -o ./output

# Skip preview
python -m text_glosser.cli.main process mytext.txt \
    -r mw-sanskrit-english \
    --no-preview

# Specific output format
python -m text_glosser.cli.main process mytext.txt \
    -r mw-sanskrit-english \
    --format json
```

### Web UI Usage

```bash
# Start the web server
python -m uvicorn text_glosser.web.main:app --host 0.0.0.0 --port 8080

# Access at http://localhost:8080
```

#### Web UI Workflow

1. **Configure Session Settings**
   - Set data retention period (0-365 days, or indefinite)
   
2. **Select Dictionaries**
   - Browse dictionaries organized by language
   - Select one or more resources for analysis
   - Upload custom dictionaries (coming soon)

3. **Upload Text Sources**
   - Upload text files (drag and drop supported)
   - Enter URLs for web content extraction

4. **Process**
   - Click "Process Text" to analyze
   - View results in the web interface
   - Download results as ZIP file

5. **Session Management**
   - Sessions are saved with unique IDs
   - Results accessible via session URL
   - Data automatically cleaned up based on retention policy

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

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=text_glosser --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/
```

### Adding New Dictionaries

1. Place dictionary files in `language_resources/<ISO-639-1-code>/`
2. Update `registry.py` to register the new resource
3. Implement parser if new format (see `parsers/` directory)

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
