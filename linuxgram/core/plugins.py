#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   plugins linuxgram!   #
##########################

import importlib.util
import os
import sys

from .constants import PLUGINS_DIR
from .logging_config import logger

loaded_plugins = []
plugin_handlers = {}
plugin_command_handlers = {}
plugin_settings_widgets = {}


def load_plugins(plugins_dir: str = PLUGINS_DIR) -> None:
    """Load plugin modules from the plugins directory into the shared registry."""
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)
        return

    loaded_plugins.clear()
    plugin_handlers.clear()
    plugin_command_handlers.clear()
    plugin_settings_widgets.clear()

    if plugins_dir not in sys.path:
        sys.path.insert(0, plugins_dir)

    for file in os.listdir(plugins_dir):
        if not file.endswith('.py') or file == '__init__.py':
            continue

        try:
            plugin_name = file[:-3]
            path = os.path.join(plugins_dir, file)
            spec = importlib.util.spec_from_file_location(plugin_name, path)
            if spec is None or spec.loader is None:
                logger.warning("Plugin %s cannot be loaded: invalid module spec", file)
                continue
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)

            plugin_info = getattr(plugin_module, 'PLUGIN_INFO', {})
            plugin_info['name'] = plugin_info.get('name', plugin_name)
            plugin_info['version'] = plugin_info.get('version', '1.0')
            plugin_info['author'] = plugin_info.get('author', 'Unknown')
            plugin_info['description'] = plugin_info.get('description', '')
            plugin_info['module'] = plugin_module
            plugin_info['file'] = file

            if hasattr(plugin_module, 'register_hooks'):
                handlers = plugin_module.register_hooks()
                if handlers:
                    if 'hooks' in handlers:
                        plugin_handlers[plugin_name] = handlers['hooks']
                    if 'commands' in handlers:
                        for command, handler in handlers['commands'].items():
                            plugin_command_handlers[command] = (plugin_name, handler)
                    if 'settings_widget' in handlers:
                        plugin_settings_widgets[plugin_name] = handlers['settings_widget']

                    logger.info(
                        "Plugin loaded: %s v%s by %s",
                        plugin_info['name'],
                        plugin_info['version'],
                        plugin_info['author'],
                    )
                else:
                    logger.warning("Plugin %s returned no handlers", plugin_name)
            else:
                logger.warning("Plugin %s has no register_hooks() function", plugin_name)

            loaded_plugins.append(plugin_info)

        except Exception as e:
            logger.exception("Error loading plugin %s: %s", file, e)


def execute_plugin_hook(hook_name, *args, **kwargs):
    """Execute registered plugin hook handlers."""
    results = []
    for plugin_name, handlers in plugin_handlers.items():
        if hook_name in handlers:
            try:
                result = handlers[hook_name](*args, **kwargs)
                if result is not None:
                    results.append((plugin_name, result))
            except Exception as e:
                logger.exception("Error executing hook '%s' in plugin %s: %s", hook_name, plugin_name, e)
    return results


def execute_plugin_command(command, text, dialog, tui, app_config):
    """Execute a registered plugin command if enabled."""
    if command in plugin_command_handlers:
        plugin_name, handler = plugin_command_handlers[command]
        plugin_config = app_config.get("plugins", {}).get(plugin_name, {})
        if not plugin_config.get('enabled', True):
            return None

        try:
            return handler(text, dialog, tui)
        except Exception as e:
            logger.exception("Error executing command '%s' in plugin %s: %s", command, plugin_name, e)
    return None


class PluginRegistry:
    """Compatibility wrapper around the module-level plugin registry."""

    loaded_plugins = loaded_plugins
    plugin_handlers = plugin_handlers
    plugin_command_handlers = plugin_command_handlers
    plugin_settings_widgets = plugin_settings_widgets
    load_plugins = staticmethod(load_plugins)
    execute_plugin_hook = staticmethod(execute_plugin_hook)
    execute_plugin_command = staticmethod(execute_plugin_command)


__all__ = [
    'PluginRegistry',
    'loaded_plugins',
    'plugin_handlers',
    'plugin_command_handlers',
    'plugin_settings_widgets',
    'load_plugins',
    'execute_plugin_hook',
    'execute_plugin_command',
]
