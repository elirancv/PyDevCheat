# PyDevCheat

<div align="center">
  <img src="assets/icons/logo-256.png" alt="PyDevCheat Logo" width="256"/>
  
  <h1>PyDevCheat</h1>
  
  <p>
    <a href="https://github.com/elirancv/PyDevCheat/actions"><img src="https://img.shields.io/github/workflow/status/elirancv/PyDevCheat/CI?style=flat-square" alt="Build Status"></a>
    <a href="https://github.com/elirancv/PyDevCheat/blob/main/LICENSE"><img src="https://img.shields.io/github/license/elirancv/PyDevCheat?style=flat-square" alt="License"></a>
    <a href="https://github.com/elirancv/PyDevCheat"><img src="https://img.shields.io/github/stars/elirancv/PyDevCheat?style=flat-square" alt="GitHub Stars"></a>
    <a href="https://github.com/elirancv/PyDevCheat/issues"><img src="https://img.shields.io/github/issues/elirancv/PyDevCheat?style=flat-square" alt="GitHub Issues"></a>
    <img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square" alt="Python versions">
    <img src="https://img.shields.io/badge/version-0.1.0-brightgreen?style=flat-square" alt="Version">
  </p>

  <h3>Your Ultimate Programming Companion for Instant Command Lookups and Code Snippets</h3>

  <p>
    <a href="#-overview">Overview</a> •
    <a href="#-key-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-installation">Installation</a> •
    <a href="#-usage">Usage</a> •
    <a href="#-development">Development</a> •
    <a href="#-troubleshooting">Troubleshooting</a> •
    <a href="#-faq">FAQ</a>
  </p>
  
  <img src="assets/docs/screenshot.png" alt="PyDevCheat Screenshot" width="800"/>
</div>

## 🌟 Overview

PyDevCheat is a modern, feature-rich development tool that combines multiple cheat sheet sources into one seamless interface. Built with PyQt6, it provides instant access to programming commands, snippets, and reference guides through both a sleek GUI and an efficient CLI.

### 🎯 Key Benefits

- **Unified Access**: Combines TLDR Pages, Cheat.sh, and DevHints in one interface
- **Instant Search**: Real-time filtering across all sources
- **Modern Interface**: Dark theme with syntax highlighting
- **Offline Support**: Local caching of frequently used commands
- **Cross-Platform**: Works on Windows, macOS, and Linux

## ✨ Key Features

### 🖥️ GUI Features

- **Smart Search System**
  - Real-time filtering across all sources
  - Category-based navigation
  - Instant results display
  - Clear search with one click

- **Modern Interface**
  - Dark theme with custom color palette
  - Syntax highlighting for code snippets
  - Tree-based command browser
  - Status bar with live updates
  - Smooth scrolling and animations

- **Productivity Tools**
  - Quick copy to clipboard
  - Source synchronization
  - Keyboard shortcuts
  - Resizable panels

### 💻 CLI Features

- **Fast Command Access**
  - Direct command lookups
  - Source-specific searches
  - Copy to clipboard option
  - Offline mode support

- **Management Tools**
  - Source synchronization
  - Cache management
  - GUI launcher
  - Version information

## 🚀 Quick Start

```bash
# Install PyDevCheat
pip install pydevcheat

# Launch GUI
pydevcheat gui

# Quick CLI lookup
pydevcheat git commit
```

## 📦 Installation

### System Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **Memory**: 256MB minimum
- **Storage**: 100MB for cache and data

### Dependencies

- PyQt6 6.4.0 or higher (GUI interface)
- httpx 0.24.0 or higher (API communication)
- rich 13.0.0 or higher (CLI formatting)
- typer 0.9.0 or higher (CLI interface)
- Other dependencies are automatically installed

### Installation Methods

#### From PyPI (Recommended)
```bash
# Install with basic dependencies
pip install pydevcheat

# Install with all optional dependencies
pip install pydevcheat[all]
```

#### From Source
```bash
# Clone repository
git clone https://github.com/elirancv/PyDevCheat.git
cd PyDevCheat

# Install all dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## 📖 Usage

### GUI Mode

Launch the graphical interface:
```bash
pydevcheat gui
```

#### Keyboard Shortcuts
- `Ctrl/Cmd + F`: Focus search
- `Esc`: Clear search
- `Up/Down`: Navigate results
- `Ctrl/Cmd + C`: Copy content
- `Tab`: Switch panels

### CLI Mode

```bash
# Basic command lookup
pydevcheat <command> [options]

# Examples
pydevcheat git commit          # Git commit examples
pydevcheat python dict        # Python dictionary guide
pydevcheat docker --source cheatsh  # Cheat.sh specific search
pydevcheat react --copy      # Copy React commands
```

### Advanced Features

```bash
# Update command sources
pydevcheat sync

# Clear cache
pydevcheat cache clear

# Show version
pydevcheat --version

# Show help
pydevcheat --help
```

## 🛠️ Development

### Project Structure
```
pydevcheat/
├── __init__.py          # Package initialization
├── gui.py              # GUI implementation
├── main.py             # CLI implementation
├── config.py           # Configuration settings
├── settings.py         # User settings management
├── utils.py            # Utility functions
└── sources/            # Command sources
    ├── tldr.py         # TLDR Pages integration
    ├── cheatsh.py      # Cheat.sh integration
    └── devhints.py     # DevHints integration
```

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt
```

### Development Tools

- **Testing**: pytest 7.0.0 or higher
- **Code Coverage**: pytest-cov 4.0.0 or higher
- **Code Formatting**: black 23.0.0 or higher
- **Linting**: flake8 6.0.0 or higher
- **Build Tools**: build 1.0.0 or higher
- **Package Publishing**: twine 4.0.0 or higher

### Development Commands

```bash
# Format code
black pydevcheat/

# Run linting
flake8 pydevcheat/

# Run tests with coverage
pytest --cov=pydevcheat tests/

# Build package
python -m build

# Upload to PyPI (maintainers only)
twine upload dist/*
```

### Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
   - Follow the code style (use black and flake8)
   - Add tests for new features
   - Update documentation as needed
4. Run tests (`pytest`)
5. Submit a pull request

#### Commit Messages

Use clear and descriptive commit messages:
```bash
# Format
<type>(<scope>): <description>

# Examples
feat(gui): add dark mode toggle
fix(cli): resolve search command crash
docs(readme): update installation instructions
```

#### Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the version numbers in:
   - `__init__.py`
   - `setup.py` (if exists)
   - Documentation references
3. The PR will be merged once you have the sign-off of a maintainer

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Eliran Cohen** - *Initial work* - [elirancv](https://github.com/elirancv)

## 🙏 Acknowledgments

- [TLDR Pages](https://github.com/tldr-pages/tldr) for command examples
- [Cheat.sh](https://github.com/chubin/cheat.sh) for the comprehensive cheat sheet engine
- [DevHints](https://devhints.io/) for quick reference guides
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [Rich](https://github.com/Textualize/rich) for beautiful CLI formatting
- [Typer](https://typer.tiangolo.com/) for CLI interface

## 🔧 Troubleshooting

### Common Issues

#### Installation Issues
- **Qt Dependencies Missing**
  ```bash
  # On Ubuntu/Debian
  sudo apt-get install python3-pyqt6 python3-pyqt6-qt6

  # On macOS
  brew install pyqt@6
  
  # On Windows
  # No additional steps required, dependencies are included in PyQt6 package
  ```

#### Source Synchronization
- **TLDR Pages Not Loading**
  ```bash
  # Force resync TLDR pages
  pydevcheat sync --force tldr
  ```
- **Cheat.sh Connection Issues**
  ```bash
  # Check connection and retry
  pydevcheat sync --retry-count 3 cheatsh
  ```

#### GUI Issues
- **Window Not Displaying Properly**
  - Try resetting the window state:
    ```bash
    pydevcheat gui --reset-layout
    ```
- **Search Not Working**
  - Clear the search cache:
    ```bash
    pydevcheat cache clear --search
    ```

## ❓ FAQ

### General Questions

**Q: How often are the command sources updated?**
A: Sources are automatically checked for updates weekly. You can manually update using `pydevcheat sync`.

**Q: Can I use PyDevCheat offline?**
A: Yes, once you've synced the sources, they're cached locally and available offline.

**Q: How can I contribute new commands?**
A: You can contribute directly to the source repositories (TLDR Pages, Cheat.sh) or submit a pull request to add custom commands.

### Technical Questions

**Q: What's the difference between TLDR and Cheat.sh sources?**
A: TLDR provides concise command examples, while Cheat.sh offers more detailed explanations and community-contributed snippets.

**Q: Does PyDevCheat support custom themes?**
A: Yes, you can customize the theme by modifying the settings. Custom theme support is planned for future releases.

**Q: Can I integrate PyDevCheat with my IDE?**
A: Currently, PyDevCheat runs as a standalone application. IDE plugins are planned for future releases.

## 🔄 Updates and Versioning

### Version History

- **0.1.0** (April 17, 2025)
  - Initial release with PyQt6-based GUI
  - Integration with TLDR Pages, Cheat.sh, and DevHints
  - Dark theme and syntax highlighting
  - Real-time search functionality
  - Cross-platform support
  - CLI interface with rich formatting

### Planned Features

- [ ] Custom theme support
- [ ] IDE plugins (VS Code, PyCharm)
- [ ] Custom snippet management
- [ ] Cloud sync for settings
- [ ] Advanced search filters
- [ ] Offline mode improvements
- [ ] Command history and favorites
- [ ] Multiple language support

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/elirancv">Eliran Cohen</a></sub>
</div> 