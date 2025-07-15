# JAR Analyzer

opencode-ai with claude-sonnet-3.7 coded this useful java tool.

- https://github.com/opencode-ai/opencode

This Python tool implements jar indexing and class searching for Java JAR/WAR files.

## Features

- Indexes Java class names from JAR and WAR files into a SQLite database
- Provides a command-line tool to scan directories of JAR files with progress information
- Offers an interactive search interface (similar to fzf) to find classes and their containing JAR files

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/jar-analyzer.git
cd jar-analyzer

# Install the package
pip install -e .
```

## Usage

### Indexing JAR Files

```bash
# Index all JAR files in a directory and its subdirectories
jar-indexer /path/to/java/project

# Index JAR files in a single directory (no subdirectories)
jar-indexer --no-recursive /path/to/java/project

# Specify a custom database location
jar-indexer --db /path/to/custom/database.db /path/to/java/project

# Get help
jar-indexer --help
```

### Searching for Classes

```bash
# Launch the interactive search interface (uses ~/.jar_analyzer/jar_index.db by default)
jar-search

# Use a custom database location
jar-search --db /path/to/custom/database.db

# Get help
jar-search --help
```

## How to Use the Search Interface

1. Type to search for classes
2. Use up/down arrow keys to navigate through results
3. Press Enter to select a class and see details
4. Press Esc or Ctrl+C to exit

## Dependencies

- Python 3.8+
- prompt_toolkit
- tqdm

## License

MIT