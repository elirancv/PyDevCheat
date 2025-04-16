# 🧠 PyDevCheat - Your CLI Programming Companion

<div align="center">
  <img src="assets/icons/logo-256.png" alt="PyDevCheat Logo" width="256"/>
  <br>
  <p>
    <a href="https://pypi.org/project/pydevcheat/"><img src="https://img.shields.io/pypi/v/pydevcheat.svg" alt="PyPI version"></a>
    <a href="https://pypi.org/project/pydevcheat/"><img src="https://img.shields.io/pypi/pyversions/pydevcheat.svg" alt="Python versions"></a>
    <a href="https://github.com/elirancv/PyDevCheat/actions"><img src="https://github.com/elirancv/PyDevCheat/workflows/CI/badge.svg" alt="CI Status"></a>
    <a href="https://codecov.io/gh/elirancv/PyDevCheat"><img src="https://codecov.io/gh/elirancv/PyDevCheat/branch/main/graph/badge.svg" alt="Code Coverage"></a>
    <a href="https://github.com/elirancv/PyDevCheat/blob/main/LICENSE"><img src="https://img.shields.io/github/license/elirancv/PyDevCheat.svg" alt="License"></a>
    <a href="https://github.com/elirancv/PyDevCheat/stargazers"><img src="https://img.shields.io/github/stars/elirancv/PyDevCheat.svg" alt="Stars"></a>
  </p>
</div>

A powerful programming companion that combines a modern desktop application and CLI tool for instant access to commands, snippets, and cheat sheets. Built with Python and Qt, featuring both a sleek GUI and an efficient command-line interface.

<div align="center">
  <img src="docs/screenshot.png" alt="PyDevCheat Screenshot" width="800"/>
</div>

## ✨ Features

- 🖥️ **Dual Interface**:
  - Modern desktop application with dark theme
  - Fast command-line interface for terminal lovers
- 🔍 **Instant Search**: Real-time filtering across multiple command sources
- 📚 **Multiple Sources**:
  - TLDR Pages (5,400+ commands)
  - Cheat.sh (3,900+ snippets)
  - DevHints (350+ reference guides)
- 🎨 **Modern UI**:
  - Sleek dark theme with carefully crafted color palette
  - Responsive and fluid interface
  - Professional IDE-style design
- ⚡ **Performance**:
  - Asynchronous loading of sources
  - Efficient search filtering
  - Smart caching system
- 🛠️ **Developer Tools**:
  - Command syntax highlighting
  - Copy-to-clipboard functionality
  - Source synchronization
- ⌨️ **Keyboard Shortcuts**:
  - `Ctrl/Cmd + F`: Focus search
  - `Esc`: Clear search
  - `Up/Down`: Navigate results

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/elirancv/PyDevCheat.git
cd PyDevCheat
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
# Launch desktop interface
python -m pydevcheat

# Or use CLI
python -m pydevcheat cli git commit
```

## 📦 Dependencies

Core Dependencies:
- **PyQt6**: Modern GUI framework
- **qt-material**: Material design styling
- **httpx**: Async HTTP client for API requests
- **rich**: Terminal output formatting
- **typer**: CLI interface creation
- **markdown2**: Markdown parsing
- **pygments**: Syntax highlighting
- **beautifulsoup4**: HTML/XML parsing
- **pyperclip**: Clipboard operations
- **pyyaml**: YAML file handling

Development Dependencies:
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **build**: Package building
- **twine**: Package publishing

## 🎯 Usage

### Desktop Interface

1. **First Launch**:
   - Click the sync button (↻) to download command databases
   - Wait for initial synchronization to complete

2. **Finding Commands**:
   - Type in the search box to filter commands (`Ctrl/Cmd + F`)
   - Use specific terms for better results
   - Navigate results with arrow keys (`↑`/`↓`)
   - Press `Enter` to view details
   - Press `Esc` to clear search

3. **Browsing Sources**:
   - Expand source categories in the sidebar
   - Click on commands to view details
   - Use `Ctrl/Cmd + C` to copy selected command
   - Right-click for additional options

4. **Keeping Updated**:
   - Use the sync button to update command databases
   - Click refresh (⟳) to reload the current view
   - Check the status bar for sync progress

### Command Line Interface

```bash
# Basic command search (defaults to TLDR)
pydevcheat git commit
pydevcheat python "list comprehension"

# Specify source
pydevcheat --source cheatsh docker run
pydevcheat --source devhints javascript

# Copy to clipboard
pydevcheat git commit --copy

# Sync command databases
pydevcheat sync

# Show help
pydevcheat --help
```

## 🏗️ Project Structure

```
pydevcheat/
├── __init__.py
├── gui.py           # Desktop GUI implementation
├── cli.py           # Command-line interface
├── sources/
│   ├── __init__.py
│   ├── tldr.py      # TLDR Pages integration
│   ├── cheatsh.py   # Cheat.sh API client
│   └── devhints.py  # DevHints parser
├── utils/
│   ├── __init__.py
│   ├── cache.py     # Caching system
│   └── syntax.py    # Syntax highlighting
└── resources/
    └── styles/      # UI themes and styles
```

## 🎨 Color Scheme

The application uses a carefully crafted dark theme:

- **Background**: Rich dark blue (#1a1f2e)
- **Sidebar**: Light blue-gray (#212739)
- **Text**: Bright blue-white (#c4d0ff)
- **Accents**: 
  - Primary: Vibrant blue (#7aa2f7)
  - Secondary: Soft purple (#bb9af7)
- **Interactive**:
  - Hover: Rich navy (#3b4366)
  - Selection: Deep navy (#2d3452)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [TLDR Pages](https://tldr.sh/) for their excellent command documentation
- [Cheat.sh](https://cheat.sh/) for their comprehensive API
- [DevHints](https://devhints.io/) for their quick reference guides
- The Qt team for their amazing framework

---

Made with ❤️ by [Eliran](https://github.com/elirancv) 