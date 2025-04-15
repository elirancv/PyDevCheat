# 🧠 PyDevCheat - Your CLI Programming Companion

<div align="center">

![PyDevCheat Demo](docs/images/demo.gif)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/pypi/dm/pydevcheat)](https://pypi.org/project/pydevcheat/)
[![PyPI Version](https://img.shields.io/pypi/v/pydevcheat)](https://pypi.org/project/pydevcheat/)

A lightning-fast command-line tool to instantly access programming cheat sheets and command snippets.

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Examples](#-examples) • [Contributing](#-contributing)

</div>

## 📸 Screenshots

<div align="center">
  <img src="docs/images/screenshot1.png" alt="Basic Search" width="45%">
  <img src="docs/images/screenshot2.png" alt="Source Selection" width="45%">
</div>

## 🚀 Features

- 🔍 **Smart Search** - Find commands instantly with natural language queries
- 🧵 **Multiple Sources** - Access content from:
  - [tldr-pages](https://tldr.sh/) - Community-driven command examples
  - [cheat.sh](https://cheat.sh/) - Programming language cheatsheets
  - Local JSON/YAML files - Your custom snippets
- ⚡ **Performance** - Lightning-fast results with intelligent caching
- 📎 **Clipboard Integration** - One-click copy with `--copy` flag
- 📡 **Offline Mode** - Work without internet using local tldr pages
- 🔖 **Custom Snippets** - Save and manage your own cheat sheets

## 🛠️ Installation

### Quick Install

```bash
pip install pydevcheat
```

### Development Install

```bash
# Clone the repository
git clone https://github.com/elirancv/PyDevCheat.git
cd PyDevCheat

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## 💻 Usage

### Basic Commands

```bash
# Search for a command (uses TLDR by default)
pydevcheat cheat git
pydevcheat cheat "python list comprehension"

# Specify source
pydevcheat cheat git commit --source cheatsh
pydevcheat cheat docker run --source cheatsh

# Copy to clipboard
pydevcheat cheat git commit --copy

# Sync TLDR pages for offline use
pydevcheat sync
```

### Command Options

```bash
pydevcheat cheat --help
```

Output:
```
Usage: pydevcheat cheat [OPTIONS] QUERY

  Search for cheat sheets and command snippets.

Arguments:
  QUERY  The command or topic to search for  [required]

Options:
  --source TEXT  Source to search from (tldr, cheatsh)  [default: tldr]
  --copy         Copy result to clipboard
  --help         Show this message and exit.
```

## 🗂️ Project Structure

```
pydevcheat/
├── main.py             # CLI entry point using Typer
├── sources/
│   ├── tldr.py         # Parse tldr Markdown files
│   ├── cheatsh.py      # Fetch from cheat.sh API
│   └── local.py        # Load from user's local snippets
├── cache/
│   └── cheats.json     # Store previous results
├── snippets.json       # Optional custom snippet storage
├── utils.py            # Formatting, clipboard, helpers
└── README.md
```

## 🔌 Data Sources

### TLDR Pages
- Community-curated command examples
- Platform-specific pages (Linux, Windows, macOS)
- Offline support through local sync
- Markdown-based format
- Best for basic command usage

### Cheat.sh
- Real-time programming language cheatsheets
- Simple HTTP API integration
- Rich content with examples
- Multiple language support
- Best for detailed programming examples

## 🧪 Examples

### Git Commands (TLDR)
```bash
$ pydevcheat cheat git

Description:
Git is a distributed version control system.

Commands:
  git init                  # Initialize a new repository
  git clone <url>          # Clone a repository
  git add <file>           # Add file to staging
  git commit -m "<msg>"    # Commit staged changes
```

### Python Lists (cheat.sh)
```bash
$ pydevcheat cheat "python list" --source cheatsh

Description:
Python list operations and methods

Commands:
  my_list = [1, 2, 3]          # Create a list
  my_list.append(4)            # Add item to end
  my_list.extend([5, 6])       # Add multiple items
  my_list.sort()               # Sort in place
```

## 🛠️ Advanced Features

- 🔍 **Fuzzy Search** - Find commands even with typos
- 🎯 **Interactive Mode** - Search and select with arrow keys
- 📝 **Command History** - Auto-complete from previous searches
- 📚 **Bookmarks** - Import/export your favorite snippets
- 🌐 **Web Interface** - Access via browser (planned)
- 📱 **TUI Mode** - Text-based user interface (planned)
- 📦 **Binary Distribution** - Cross-platform executable

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
black .
flake8
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [tldr-pages](https://tldr.sh/) for their amazing command examples
- [cheat.sh](https://cheat.sh/) for their comprehensive cheatsheets
- All contributors and users of this tool

---

<div align="center">
Made with ❤️ by [Eliran Cohen](https://github.com/elirancv)

[⬆ Back to top](#-pydevcheat---your-cli-programming-companion)
</div> 