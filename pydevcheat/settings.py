import json
import os
from pathlib import Path
from typing import Dict, Any
from .config import UI_CONFIG


class SettingsManager:
    def __init__(self):
        self.config_dir = Path.home() / ".pydevcheat"
        self.config_file = self.config_dir / "settings.json"
        self.settings = {
            "font_sizes": {
                "source_header": 10,
                "source_list": 9,
                "content": 10,
                "search": 10,
                "title": 11,
            },
            "ui": {"style": "dark", "animations": True, "smooth_scrolling": True},
        }
        self.load_settings()

    def load_settings(self):
        """Load settings from file or use defaults."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    saved_settings = json.load(f)
                    # Update settings while preserving defaults for missing values
                    if "font_sizes" in saved_settings:
                        self.settings["font_sizes"].update(saved_settings["font_sizes"])
                    if "ui" in saved_settings:
                        self.settings["ui"].update(saved_settings["ui"])
            else:
                # Ensure defaults are saved on first run
                self.ensure_defaults()
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Reset to defaults if there's an error
            self.ensure_defaults()

    def ensure_defaults(self):
        """Ensure default settings are set and saved."""
        # Set the exact default values we want
        self.settings["font_sizes"] = {
            "source_header": 10,
            "source_list": 9,
            "content": 10,
            "search": 10,
            "title": 11,
        }
        self.settings["ui"] = {"style": "dark", "animations": True, "smooth_scrolling": True}
        self.save_settings()

    def save_settings(self):
        """Save current settings to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_font_sizes(self) -> Dict[str, int]:
        """Get current font sizes."""
        return self.settings["font_sizes"]

    def update_font_sizes(self, new_sizes: Dict[str, int]):
        """Update font sizes and save to file."""
        self.settings["font_sizes"] = new_sizes
        self.save_settings()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        return self.settings.get(key, default)


# Global settings instance
settings_manager = SettingsManager()
