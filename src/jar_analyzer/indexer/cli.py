"""Command line interface for the JAR indexer."""
import os
import sys
from pathlib import Path

import click

from jar_analyzer.indexer.scanner import JarScanner


@click.command(help="Index Java classes in JAR and WAR files")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--db", 
    type=click.Path(), 
    help="Path to the SQLite database file (optional)"
)
@click.option(
    "--no-recursive", 
    is_flag=True, 
    help="Don't scan subdirectories"
)
def main(directory, db, no_recursive):
    """Main entry point for the JAR indexer CLI."""
    try:
        with JarScanner(db_path=db) as scanner:
            jar_count = scanner.scan_directory(
                directory, 
                recursive=not no_recursive
            )
            click.echo(f"\nIndexing complete. Processed {jar_count} JAR/WAR files.")
        return 0
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())