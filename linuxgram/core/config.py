#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   config linuxgram!   #
#########################

import json

from .constants import CONFIG_FILE


def default_config() -> dict:
    """Return a fresh default LinuxGram config."""
    return {
        "privacy": {"last_seen": "everybody", "read_receipts": True},
        "notifications": {"private_chats": True, "groups": True, "channels": False},
        "data": {"auto_download": {"photos": True, "videos": False, "files": False, "voice_messages": True}},
        "language": "English",
        "interface": {
            "dialogs_limit": 100,
            "messages_limit": 50,
            "show_avatars": False,
            "theme": "mono",
            "keyboard_layout": "en",
        },
        "plugins": {},
    }


def load_config(config_file: str = CONFIG_FILE) -> dict:
    """Load config from disk, filling missing top-level keys."""
    defaults = default_config()
    try:
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
            for key in defaults:
                if key not in loaded_config:
                    loaded_config[key] = defaults[key]
            return loaded_config
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults


def save_config(config: dict, config_file: str = CONFIG_FILE) -> None:
    """Save config to disk."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def get_plugin_config(config: dict, plugin_name: str, default_config_value=None):
    """Return plugin config from the app config dict."""
    if default_config_value is None:
        default_config_value = {}
    return config.get("plugins", {}).get(plugin_name, default_config_value)


def save_plugin_config(config: dict, plugin_name: str, plugin_config) -> None:
    """Update plugin config inside the app config dict."""
    if "plugins" not in config:
        config["plugins"] = {}
    config["plugins"][plugin_name] = plugin_config


class ConfigManager:
    """Compatibility wrapper for config helpers during migration."""

    default_config = staticmethod(default_config)
    load_config = staticmethod(load_config)
    save_config = staticmethod(save_config)
    get_plugin_config = staticmethod(get_plugin_config)
    save_plugin_config = staticmethod(save_plugin_config)


__all__ = [
    'ConfigManager',
    'default_config',
    'load_config',
    'save_config',
    'get_plugin_config',
    'save_plugin_config',
]
