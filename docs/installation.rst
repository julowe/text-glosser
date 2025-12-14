.. _installation:

Installation
============

Using pip
---------

The easiest way to install Text Glosser is using pip::

    pip install text-glosser

From Source
-----------

To install from source::

    git clone https://github.com/julowe/text-glosser.git
    cd text-glosser
    pip install -e .

Using Docker
------------

You can also run Text Glosser using Docker::

    docker pull ghcr.io/julowe/text-glosser:latest
    docker run -p 8080:8080 ghcr.io/julowe/text-glosser:latest

Or use docker-compose::

    docker-compose up -d

Requirements
------------

* Python 3.11 or higher
* See requirements.txt for full list of dependencies
