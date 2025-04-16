# PyDevCheat

<div align="center">
  <img src="assets/icons/logo-256.png" alt="PyDevCheat Logo" width="128"/>
  
  [![Build Status](https://img.shields.io/github/workflow/status/elirancv/PyDevCheat/CI?style=flat-square)](https://github.com/elirancv/PyDevCheat/actions)
  [![License](https://img.shields.io/github/license/elirancv/PyDevCheat?style=flat-square)](LICENSE)
  [![Python versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square)](https://pypi.org/project/pydevcheat/)
  [![Version](https://img.shields.io/badge/version-0.1.0-brightgreen?style=flat-square)](https://pypi.org/project/pydevcheat/)
</div>

## Overview

PyDevCheat is a modern cheat sheet application that provides instant access to programming commands and snippets through both GUI and CLI interfaces. It combines multiple sources into one seamless experience:

- [TLDR Pages](https://github.com/tldr-pages/tldr) - Community-driven command examples
- [Cheat.sh](https://github.com/chubin/cheat.sh) - Comprehensive cheat sheet engine
- [DevHints](https://devhints.io/) - Quick reference guides

<div align="center">
  <img src="assets/docs/screenshot.png" alt="PyDevCheat Screenshot" width="800"/>
</div>

## Features

- 🔍 Real-time search across all sources
- 🌙 Modern dark theme with syntax highlighting
- 💻 Both GUI and CLI interfaces
- 📱 Cross-platform support
- 🔄 Offline mode with local caching

## Installation

### Prerequisites

- Python 3.8 or higher
- Git

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/elirancv/PyDevCheat.git
cd PyDevCheat
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

### Platform-Specific Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install python3-pyqt6 python3-pyqt6-qt6
```

#### macOS
```bash
brew install pyqt@6
```

#### Windows
No additional steps required - dependencies are included in PyQt6 package.

## Quick Start

### GUI Mode
```bash
pydevcheat gui
```

### CLI Mode
```bash
# Get cheat sheet for a command
pydevcheat cheat git commit

# Sync sources for offline use
pydevcheat sync
```

## Keyboard Shortcuts

- `Ctrl/Cmd + F`: Focus search
- `Esc`: Clear search
- `Ctrl/Cmd + C`: Copy content

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TLDR Pages](https://github.com/tldr-pages/tldr)
- [Cheat.sh](https://github.com/chubin/cheat.sh)
- [DevHints](https://devhints.io/) 