.. _quickstart:

Quick Start
===========

This guide will help you get started with Text Glosser as an end user.

Using Docker (Recommended)
---------------------------

The easiest way to use Text Glosser is with Docker::

    # Pull and run the latest version
    docker pull ghcr.io/julowe/text-glosser:latest
    docker run -p 8080:8080 ghcr.io/julowe/text-glosser:latest

Then open http://localhost:8080 in your browser.

Or use docker-compose (save this as ``docker-compose.yml``)::

    version: '3.8'
    
    services:
      text-glosser:
        image: ghcr.io/julowe/text-glosser:latest
        ports:
          - "8080:8080"
        volumes:
          - text-glosser-data:/app/data
        restart: unless-stopped
    
    volumes:
      text-glosser-data:

Then run::

    docker-compose up -d

Web UI Quick Start
------------------

1. Open http://localhost:8080 in your browser
2. Select dictionaries/resources to use for your language
3. Upload text files or enter URLs
4. Click "Process Text"
5. View and download results in Markdown, JSON, or CoNLL-U format

CLI Quick Start
---------------

If you've installed from source, you can use the CLI::

    # List available dictionaries
    text-glosser list-dictionaries

    # Process a text file
    text-glosser process mytext.txt -r mw-sanskrit-english -o ./output

    # Process a URL
    text-glosser process https://example.com/article.html -r hanzipy-chinese

Output Formats
--------------

Text Glosser supports three output formats:

* **Markdown**: Human-readable format with headers and lists
* **JSON**: Machine-readable format with full metadata and configuration for re-running analysis
* **CoNLL-U**: Universal Dependencies format for linguistic analysis
