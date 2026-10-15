"""
Settings management for turkce-otoduzeltici.
Handles loading and saving user preferences in JSON format.
"""
import json
import os
from pathlib import Path

# Default settings
DEFAULTS = {
    "hotkey": "alt+q",
    "startup_toggle": False,
    "sound_toggle": True,
    "theme": "dark",
    "slang_expansion": True,
    "elongation_cleanup": True,
    "contextual_correction": True,
    "ai_provider": "auto",
    "gemini_api_key": "",
    "gemini_model": "gemini-3.5-flash-lite",
    "nvidia_api_key": "",
    "ai_model": "stepfun-ai/step-5-preview",
    "use_ai_in_tray": True,
}

def get_config_dir():
    """Return the path to the application configuration directory."""
    # Use APPDATA on Windows, fallback to home directory
    appdata = os.getenv('APPDATA')
    if appdata:
        config_dir = Path(appdata) / "turkce-otoduzeltici"
    else:
        config_dir = Path.home() / ".config" / "turkce-otoduzeltici"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_settings_path():
    """Return the full path to the settings JSON file."""
    return get_config_dir() / "settings.json"

def load_settings():
    """Load settings from JSON file, falling back to defaults."""
    settings_path = get_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Ensure all default keys are present
                for key, value in DEFAULTS.items():
                    settings.setdefault(key, value)
                return settings
        except (json.JSONDecodeError, OSError):
            # If file is corrupted or unreadable, return defaults
            return DEFAULTS.copy()
    else:
        return DEFAULTS.copy()

def save_settings(settings):
    """Save settings to JSON file."""
    settings_path = get_settings_path()
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except OSError:
        return False

def reset_to_defaults():
    """Reset settings to defaults and save."""
    defaults = DEFAULTS.copy()
    save_settings(defaults)
    return defaults