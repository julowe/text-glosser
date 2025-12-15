.. _installation:

Installation
============

Text Glosser is not yet available on PyPI. You can install it using Docker or from source.

Using Docker (Recommended)
--------------------------

The easiest way to run Text Glosser is using Docker::

    docker pull ghcr.io/julowe/text-glosser:latest
    docker run -p 8080:8080 ghcr.io/julowe/text-glosser:latest

Then open http://localhost:8080 in your browser.

Or use docker-compose::

    # Create a docker-compose.yml file or use the one from the repository
    docker-compose up -d

From Source
-----------

To install from source::

    git clone https://github.com/julowe/text-glosser.git
    cd text-glosser
    pip install -e .

Or install just the dependencies::

    pip install -r requirements.txt

Requirements
------------

* Python 3.12 or higher
* See ``requirements.txt`` and ``pyproject.toml`` for full list of dependencies

Development Installation
------------------------

For development, install additional dependencies::

    pip install -r requirements-dev.txt

This includes testing tools, documentation builders, and code quality tools.
