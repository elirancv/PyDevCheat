from rich.style import Style
from rich.theme import Theme
from PyQt6.QtGui import QFont

# UI Configuration
UI_CONFIG = {
    "font_sizes": {
        "source_header": 10,  # Source headers (TLDR Pages, Cheat.sh, etc.)
        "source_list": 9,     # Source items (commands/topics)
        "content": 10,        # Main content area
        "search": 10,         # Search box
        "title": 11          # Titles
    },
    "colors": {
        "background": "#1a1b26",
        "text": "#c4d0ff",
        "highlight": "#7aa2f7",
        "accent": "#bb9af7"
    },
    "padding": {
        "content": 10,
        "list": 5
    }
}

# Default Fonts
DEFAULT_FONT = QFont("Inter", UI_CONFIG["font_sizes"]["content"])
MONOSPACE_FONT = QFont("JetBrains Mono", UI_CONFIG["font_sizes"]["content"])

# Tree View Settings
TREE_VIEW_CONFIG = {
    "indent": 20,
    "item_height": 24
}

# Content View Settings
CONTENT_VIEW_CONFIG = {
    "line_spacing": 1.2,
    "paragraph_spacing": 1.5
}

# Rich Theme Configuration
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "command": Style(color="blue", bold=True),
    "source": Style(color="magenta", dim=True),
    "description": Style(color="white"),
})

# Source display settings
SOURCE_STYLES = {
    "title": Style(color="blue", bold=True),
    "command": Style(color="green"),
    "description": Style(color="white", dim=True),
    "example": Style(color="yellow"),
}

# Terminal output settings
TERMINAL_SETTINGS = {
    "width": 80,
    "height": 24,
    "padding": (0, 1),
    "font_size": "small",  # This will affect the display size of the sources
} 