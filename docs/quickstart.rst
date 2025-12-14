.. _quickstart:

Quick Start
===========

This guide will help you get started with Text Glosser.

CLI Quick Start
---------------

List available dictionaries::

    text-glosser list-dictionaries

Process a text file::

    text-glosser process mytext.txt -r mw-sanskrit-english -o ./output

Process a URL::

    text-glosser process https://example.com/article.html -r hanzipy-chinese

Web UI Quick Start
------------------

Start the web server::

    python -m uvicorn text_glosser.web.main:app --host 0.0.0.0 --port 8080

Then open http://localhost:8080 in your browser.

Basic Workflow
--------------

1. Select dictionaries/resources to use
2. Upload text files or enter URLs
3. Click "Process Text"
4. View and download results

Output Formats
--------------

Text Glosser supports three output formats:

* **Markdown**: Human-readable format with headers and lists
* **JSON**: Machine-readable format with full metadata
* **CoNLL-U**: Universal Dependencies format for linguistic analysis
