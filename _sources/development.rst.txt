.. _development:

Development Guide
=================

This guide describes how to set up a development environment for Text Glosser.

Prerequisites
-------------

* Python 3.12 or higher
* python3-pip
* git
* docker (optional, for container development)

Setting Up Development Environment
-----------------------------------

Clone and Install
^^^^^^^^^^^^^^^^^

1. Clone the repository::

    git clone https://github.com/julowe/text-glosser.git
    cd text-glosser

2. Create a virtual environment::

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install the package in editable mode with development dependencies::

    pip install -e .[dev]

Running the Application
-----------------------

Web UI (Development Mode)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the web server with auto-reload::

    uvicorn text_glosser.web.main:app --reload --host 0.0.0.0 --port 8080

Or set PYTHONPATH and run::

    PYTHONPATH=src uvicorn text_glosser.web.main:app --reload --host 0.0.0.0 --port 8080

Access at http://localhost:8080

CLI (Development Mode)
^^^^^^^^^^^^^^^^^^^^^^^

Run the CLI from source::

    # With package installed in editable mode
    text-glosser list-dictionaries

    # Or directly with PYTHONPATH
    PYTHONPATH=src python -m text_glosser.cli.main list-dictionaries

Using Docker for Development
-----------------------------

Build and Run Locally
^^^^^^^^^^^^^^^^^^^^^

Use the development docker-compose file::

    # Build and run
    docker-compose -f docker-compose.dev.yml up --build

    # Run in background
    docker-compose -f docker-compose.dev.yml up -d --build

    # View logs
    docker-compose -f docker-compose.dev.yml logs -f

    # Stop
    docker-compose -f docker-compose.dev.yml down

The development compose file mounts your source code as volumes, so changes are reflected immediately (with server restart).

Build Docker Image Manually
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    docker build -t text-glosser:dev .
    docker run -p 8080:8080 text-glosser:dev

Running Tests
-------------

Run All Tests
^^^^^^^^^^^^^

::

    PYTHONPATH=src pytest

Run with Coverage
^^^^^^^^^^^^^^^^^

::

    PYTHONPATH=src pytest --cov=text_glosser --cov-report=html --cov-report=term

View coverage report at ``htmlcov/index.html``

Run Specific Tests
^^^^^^^^^^^^^^^^^^

::

    # Run tests in a specific file
    PYTHONPATH=src pytest tests/unit/test_models.py

    # Run a specific test
    PYTHONPATH=src pytest tests/unit/test_models.py::TestLanguageCode::test_create_simple

Code Quality
------------

Linting with Ruff
^^^^^^^^^^^^^^^^^

::

    # Check all code
    ruff check src/ tests/

    # Auto-fix issues
    ruff check --fix src/ tests/

Type Checking with MyPy
^^^^^^^^^^^^^^^^^^^^^^^

::

    mypy src/ --ignore-missing-imports

Building Documentation
----------------------

Build Sphinx Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    cd docs
    make html

View the documentation at ``docs/_build/html/index.html``

Project Structure
-----------------

::

    text-glosser/
    ├── src/
    │   └── text_glosser/
    │       ├── core/           # Core processing logic
    │       ├── cli/            # Command-line interface
    │       ├── web/            # Web interface
    │       └── utils/          # Utility functions
    ├── tests/
    │   ├── unit/               # Unit tests
    │   └── integration/        # Integration tests
    ├── docs/                   # Sphinx documentation
    ├── language_resources/     # Built-in dictionaries
    ├── requirements.txt        # Runtime dependencies
    ├── requirements-dev.txt    # Development dependencies
    ├── pyproject.toml          # Tool configuration
    ├── setup.py                # Package setup
    ├── Dockerfile              # Production container
    ├── docker-compose.yml      # Production container
    └── docker-compose.dev.yml  # Development container

Adding New Features
-------------------

1. Create a new branch::

    git checkout -b feature/my-new-feature

2. Write tests first (TDD approach)::

    # Add tests to tests/unit/ or tests/integration/
    PYTHONPATH=src pytest tests/unit/test_my_feature.py

3. Implement the feature in ``src/text_glosser/``

4. Run tests and linting::

    PYTHONPATH=src pytest
    ruff check src/ tests/
    mypy src/ --ignore-missing-imports

5. Update documentation if needed

6. Commit and push your changes

7. Open a pull request

Code Style Guidelines
---------------------

* Follow PEP 8 style guide
* Use type hints for function parameters and return values
* Write NumPy/SciPy style docstrings
* Use ruff for linting (not black)
* Maximum line length: default (88 characters)
* Use meaningful variable and function names

Example Function Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    def analyze_text(source: TextSource, resources: List[str]) -> TextAnalysis:
        """
        Analyze a text source using selected resources.
        
        Parameters
        ----------
        source : TextSource
            Text source to analyze
        resources : List[str]
            IDs of resources to use
        
        Returns
        -------
        TextAnalysis
            Analysis results with word definitions
        
        Raises
        ------
        ValueError
            If no resources are selected
        
        Examples
        --------
        >>> source = TextSource(id="1", name="test", content="hello", source_type="file")
        >>> result = analyze_text(source, ["dict-1"])
        """
        pass

Debugging
---------

Using IPython
^^^^^^^^^^^^^

IPython is included in development dependencies::

    ipython
    >>> from text_glosser.core.processor import TextProcessor
    >>> # Interactive debugging and testing

Using Python Debugger
^^^^^^^^^^^^^^^^^^^^^

Add breakpoints in your code::

    import pdb; pdb.set_trace()

Or use the built-in ``breakpoint()`` function (Python 3.7+)::

    breakpoint()

Contributing
------------

1. Ensure all tests pass
2. Update documentation
3. Follow code style guidelines
4. Write clear commit messages
5. Submit pull request with description of changes

For more information, see the main README.md file.
