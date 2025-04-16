<div align="center">
  <img src="assets/icons/logo-256.png" alt="PyDevCheat Logo" width="256"/>
  <h1>PyDevCheat</h1>
  <p>
    <a href="https://github.com/elirancv/PyDevCheat/actions"><img src="https://github.com/elirancv/PyDevCheat/workflows/CI/badge.svg" alt="CI Status"></a>
    <a href="https://pypi.org/project/pydevcheat/"><img src="https://img.shields.io/pypi/v/pydevcheat.svg" alt="PyPI version"></a>
    <a href="https://pypi.org/project/pydevcheat/"><img src="https://img.shields.io/pypi/pyversions/pydevcheat.svg" alt="Python versions"></a>
    <a href="https://github.com/elirancv/PyDevCheat/blob/main/LICENSE"><img src="https://img.shields.io/github/license/elirancv/PyDevCheat.svg" alt="License"></a>
    <a href="https://github.com/elirancv/PyDevCheat/stargazers"><img src="https://img.shields.io/github/stars/elirancv/PyDevCheat.svg" alt="Stars"></a>
  </p>
  <p>
    <b>Your Ultimate Programming Companion for Instant Command Lookups and Code Snippets</b>
  </p>
  <br>
  <img src="assets/docs/screenshot.png" alt="PyDevCheat Screenshot" width="800"/>
</div>

## 🌟 Overview

A powerful command-line tool and GUI application for quick access to programming cheat sheets and command snippets from multiple sources. Built with Python, featuring both a modern GUI interface and an efficient CLI.

<p align="center">
  <a href="#-command-coverage">Command Coverage</a> •
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-contributing">Contributing</a>
</p>

## 📊 Command Coverage

<table>
<tr>
<td align="center"><b>TLDR Pages</b></td>
<td align="center"><b>Cheat.sh</b></td>
<td align="center"><b>DevHints</b></td>
<td align="center"><b>Total</b></td>
</tr>
<tr>
<td align="center">5,468 commands</td>
<td align="center">3,992 commands</td>
<td align="center">354 guides</td>
<td align="center"><b>9,814 commands</b></td>
</tr>
<tr>
<td>Simplified command-line examples</td>
<td>Community-driven snippets</td>
<td>Quick reference guides</td>
<td>At your fingertips!</td>
</tr>
</table>

## ✨ Features

### Core Features
- 🔍 **Multi-Source Search**:
  - [TLDR Pages](https://tldr.sh/) - Community-driven command examples
  - [Cheat.sh](https://cheat.sh/) - Comprehensive programming cheat sheets
  - [DevHints](https://devhints.io/) - Quick reference guides
- 🎯 **Rich Terminal Output**:
  - Syntax highlighting for commands
  - Formatted tables with descriptions
  - Cyberpunk-style borders and styling
- 💾 **Smart Caching**:
  - Local cache for faster repeated searches
  - Automatic cache updates
  - Offline mode support

### GUI Features
- 🖥️ **Modern Interface**:
  - Dark theme with carefully crafted color palette
  - Syntax highlighting for code snippets
  - Real-time search filtering
  - Tree-based command browsing
  - Status bar with command counts
  - Collapsible sidebar categories
- 🔄 **Source Management**:
  - One-click source synchronization
  - Progress tracking for downloads
  - Error handling and recovery
- 📋 **Content Display**:
  - Formatted command documentation
  - Syntax-highlighted code examples
  - Copy-to-clipboard functionality
- ⌨️ **Keyboard Shortcuts**:
  - `Ctrl/Cmd + F` - Focus search
  - `Esc` - Clear search
  - `Up/Down` - Navigate results
  - Right-click menu for additional options

### CLI Features
- 🎨 **Rich Output Formatting**:
  - Colorized command syntax
  - Structured command descriptions
  - Clear section separation
- 🔧 **Advanced Options**:
  - Source selection (`--source`)
  - Debug mode (`--debug`)
  - Clipboard integration (`--copy`)
- 🔄 **Sync Command**:
  - Offline database updates
  - Multi-source synchronization
  - Progress tracking

## 🎨 Color Scheme

<table>
<tr>
<td align="center"><b>Element</b></td>
<td align="center"><b>Color</b></td>
<td align="center"><b>Hex</b></td>
</tr>
<tr>
<td>Background</td>
<td><div style="background-color: #1a1f2e; color: white; padding: 4px;">Rich dark blue</div></td>
<td><code>#1a1f2e</code></td>
</tr>
<tr>
<td>Sidebar</td>
<td><div style="background-color: #212739; color: white; padding: 4px;">Light blue-gray</div></td>
<td><code>#212739</code></td>
</tr>
<tr>
<td>Text</td>
<td><div style="background-color: #c4d0ff; color: black; padding: 4px;">Bright blue-white</div></td>
<td><code>#c4d0ff</code></td>
</tr>
<tr>
<td>Primary Accent</td>
<td><div style="background-color: #7aa2f7; color: black; padding: 4px;">Vibrant blue</div></td>
<td><code>#7aa2f7</code></td>
</tr>
<tr>
<td>Secondary Accent</td>
<td><div style="background-color: #bb9af7; color: black; padding: 4px;">Soft purple</div></td>
<td><code>#bb9af7</code></td>
</tr>
</table>

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/elirancv/PyDevCheat.git
cd PyDevCheat

# Install dependencies
pip install -r requirements.txt

# For development dependencies
pip install -r requirements-dev.txt
```

## 📖 Usage

### Command Line Interface

```bash
# Basic search (defaults to TLDR)
pydevcheat git commit
pydevcheat python for loop

# Specify source
pydevcheat docker --source cheatsh
pydevcheat npm --source devhints

# Copy to clipboard
pydevcheat git push --copy

# Enable debug mode
pydevcheat npm install --debug

# Sync sources for offline use
pydevcheat sync

# Launch GUI
pydevcheat gui
```

### GUI Mode

Launch the graphical interface with:
```bash
pydevcheat gui
```

<details>
<summary>🖥️ GUI Features</summary>

- Tree-based command browsing with 9,814+ commands
- Real-time search filtering with instant results
- Syntax-highlighted content display
- One-click source synchronization
- Copy-to-clipboard functionality
- Category-based navigation:
  - Programming Languages
  - Development Tools
  - System Commands
  - Frameworks & Libraries

</details>

<details>
<summary>🔍 Search Tips</summary>

- Use specific terms for better results
  - Example: `python list comprehension`
  - Example: `git commit amend`
- Browse categories in the sidebar
- Right-click items to expand/collapse sections
- Press Enter to search across all sources
- Click any command for detailed usage

</details>

<details>
<summary>⌨️ Keyboard Shortcuts</summary>

- `Ctrl/Cmd + F` - Focus search
- `Esc` - Clear search
- `Up/Down` - Navigate results
- Right-click menu for additional options

</details>

## 🏗️ Project Structure

```
PyDevCheat/
├── pydevcheat/
│   ├── __init__.py
│   ├── main.py          # CLI entry point and core functionality
│   ├── gui.py          # GUI implementation with Qt
│   └── sources/
│       ├── __init__.py
│       ├── tldr.py     # TLDR pages source with local caching
│       ├── cheatsh.py  # Cheat.sh API integration
│       └── devhints.py # DevHints parser and cache
├── tests/              # Test suite
├── requirements.txt    # Production dependencies
├── requirements-dev.txt # Development dependencies
└── setup.py           # Package configuration
```

## 🔧 Configuration

<details>
<summary>Configuration Details</summary>

The tool stores its data in:
- Windows: `%USERPROFILE%\.pydevcheat\`
- Linux/macOS: `~/.pydevcheat/`

Directory structure:
- `cache/` - Search results cache
- `tldr-pages/` - Local TLDR pages repository
- `cheatsh/` - Cheat.sh cached content
- `devhints/` - DevHints cached content

</details>

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [TLDR Pages](https://tldr.sh/) for their excellent command documentation
- [Cheat.sh](https://cheat.sh/) for their comprehensive cheat sheets
- [DevHints](https://devhints.io/) for their developer-friendly hints
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Qt-Material](https://github.com/UN-GCPDS/qt-material) for Material Design styling

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/elirancv">Eliran</a>
</div> 