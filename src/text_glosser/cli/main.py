"""
Command-line interface for text-glosser.

This module provides the CLI entry point using Click for argument parsing.
"""

import click
import sys
from pathlib import Path
from typing import List
from ..core.registry import get_registry
from ..core.models import TextSource
from ..core.ingestion import read_file, fetch_url
from ..core.processor import TextProcessor
from ..core.exporters import export_all_formats, format_markdown, format_json, format_conllu
import uuid


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Text Glosser - Analyze text using linguistic dictionaries and resources.
    
    This tool processes text files or URLs and provides word-by-word definitions
    and grammatical information using selected dictionaries.
    """
    pass


@cli.command()
@click.option(
    '--language', '-l',
    help='Filter by language code (e.g., en, ar, sa, zh)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['simple', 'detailed', 'json']),
    default='simple',
    help='Output format'
)
def list_dictionaries(language: str, format: str):
    """List all available dictionaries and resources."""
    registry = get_registry()
    
    if format == 'json':
        import json
        resources = registry.get_all_resources()
        output = [
            {
                'id': res.id,
                'name': res.name,
                'format': res.format.value,
                'type': res.resource_type.value,
                'primary_language': res.primary_language,
                'secondary_languages': res.secondary_languages,
                'is_user_provided': res.is_user_provided,
                'file_paths': res.file_paths
            }
            for res in resources
        ]
        if language:
            output = [r for r in output if r['primary_language'] == language]
        click.echo(json.dumps(output, indent=2))
        return
    
    # Get resources grouped by language
    grouped = registry.get_resources_grouped_by_language()
    
    if language:
        # Filter to specific language
        if language not in grouped:
            click.echo(f"No resources found for language: {language}", err=True)
            return
        grouped = {language: grouped[language]}
    
    # Display
    for lang_code, resources in sorted(grouped.items()):
        click.echo(f"\n{click.style(f'Language: {lang_code}', bold=True, fg='blue')}")
        click.echo("=" * 50)
        
        for res in resources:
            prefix = "[User]" if res.is_user_provided else "[Built-in]"
            click.echo(f"\n{prefix} {click.style(res.name, bold=True)}")
            click.echo(f"  ID: {res.id}")
            click.echo(f"  Format: {res.format.value}")
            click.echo(f"  Type: {res.resource_type.value}")
            
            if res.secondary_languages:
                click.echo(f"  Secondary languages: {', '.join(res.secondary_languages)}")
            
            if format == 'detailed' and res.file_paths:
                click.echo(f"  Files:")
                for fp in res.file_paths:
                    exists = "✓" if Path(fp).exists() else "✗"
                    click.echo(f"    {exists} {fp}")


@cli.command()
@click.argument('sources', nargs=-1, required=True)
@click.option(
    '--resource', '-r',
    'resources',
    multiple=True,
    required=True,
    help='Resource ID to use (can be specified multiple times)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='./output',
    help='Output directory for results'
)
@click.option(
    '--format', '-f',
    'output_format',
    type=click.Choice(['markdown', 'json', 'conllu', 'all']),
    default='all',
    help='Output format'
)
@click.option(
    '--preview/--no-preview',
    default=True,
    help='Show preview of text before processing'
)
def process(sources: tuple, resources: tuple, output: str, output_format: str, preview: bool):
    """
    Process text sources with selected dictionaries.
    
    SOURCES can be file paths or URLs.
    
    Example:
        text-glosser process mytext.txt -r mw-sanskrit-english -o ./results
    """
    # Initialize components
    registry = get_registry()
    processor = TextProcessor(registry)
    
    # Verify resources exist
    for res_id in resources:
        if not registry.get_resource(res_id):
            click.echo(f"Error: Resource not found: {res_id}", err=True)
            click.echo("Use 'text-glosser list-dictionaries' to see available resources.", err=True)
            sys.exit(1)
    
    # Load sources
    text_sources: List[TextSource] = []
    for source in sources:
        source_path = Path(source)
        
        try:
            if source.startswith('http://') or source.startswith('https://'):
                # URL source
                click.echo(f"Fetching URL: {source}...")
                content = fetch_url(source)
                text_sources.append(TextSource(
                    id=str(uuid.uuid4()),
                    name=source,
                    content=content,
                    source_type='url',
                    original_path=source
                ))
            elif source_path.exists():
                # File source
                click.echo(f"Reading file: {source}...")
                content = read_file(str(source_path))
                text_sources.append(TextSource(
                    id=str(uuid.uuid4()),
                    name=source_path.name,
                    content=content,
                    source_type='file',
                    original_path=str(source_path)
                ))
            else:
                click.echo(f"Error: Source not found: {source}", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"Error loading source {source}: {e}", err=True)
            sys.exit(1)
    
    # Preview
    if preview:
        for src in text_sources:
            click.echo(f"\n{click.style(f'Preview: {src.name}', bold=True, fg='green')}")
            click.echo("=" * 60)
            lines = src.content.split('\n')[:10]
            for line in lines:
                click.echo(line)
            if len(src.content.split('\n')) > 10:
                click.echo(f"... ({len(src.content.split('\n')) - 10} more lines)")
            click.echo("")
        
        if not click.confirm("Proceed with processing?"):
            click.echo("Cancelled.")
            return
    
    # Process each source
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for src in text_sources:
        click.echo(f"\nProcessing: {src.name}...")
        
        try:
            analysis = processor.analyze_text(src, list(resources))
            
            # Export based on format
            base_filename = Path(src.name).stem if src.source_type == 'file' else f"url_{src.id[:8]}"
            
            if output_format == 'all':
                file_paths = export_all_formats(analysis, str(output_path), base_filename)
                click.echo(f"Exported to:")
                for fmt, path in file_paths.items():
                    click.echo(f"  {fmt}: {path}")
            else:
                # Single format
                if output_format == 'markdown':
                    content = format_markdown(analysis)
                    ext = 'md'
                elif output_format == 'json':
                    content = format_json(analysis)
                    ext = 'json'
                elif output_format == 'conllu':
                    content = format_conllu(analysis)
                    ext = 'conllu'
                
                file_path = output_path / f"{base_filename}.{ext}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                click.echo(f"Exported to: {file_path}")
            
            # Show summary
            click.echo(f"\nSummary:")
            click.echo(f"  Lines: {analysis.total_lines}")
            click.echo(f"  Words: {analysis.total_words}")
            if analysis.errors:
                click.echo(f"  Errors: {len(analysis.errors)}")
                for error in analysis.errors[:3]:
                    click.echo(f"    - {error[:100]}...")
        
        except Exception as e:
            click.echo(f"Error processing {src.name}: {e}", err=True)
            import traceback
            traceback.print_exc()
    
    click.echo(f"\n{click.style('Processing complete!', bold=True, fg='green')}")


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
