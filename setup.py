"""
Setup configuration for text-glosser package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="text-glosser",
    version="0.1.0",
    author="Text Glosser Contributors",
    description="A comprehensive text analysis and glossing application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/julowe/text-glosser",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.104.0",
        "nicegui>=1.4.0",
        "uvicorn[standard]>=0.24.0",
        "textual>=0.41.0",
        "pydantic>=2.4.0",
        "pydantic-settings>=2.0.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "lxml>=4.9.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "rich>=13.7.0",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "httpx>=0.25.0",
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "text-glosser=text_glosser.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    include_package_data=True,
    package_data={
        "text_glosser": ["py.typed"],
    },
)
