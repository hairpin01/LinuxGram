#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   settings_widgets linuxgram!   #
###################################

import urwid

from linuxgram.core.config import (
    get_plugin_config as _get_plugin_config,
    save_config as _save_config,
    save_plugin_config as _save_plugin_config,
)
from linuxgram.core.plugins import loaded_plugins, plugin_settings_widgets


class SettingsWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent
        self.app_config = parent.config

        self.private_chats = urwid.CheckBox("Private chats",
                                           state=self.app_config['notifications']['private_chats'])
        self.groups = urwid.CheckBox("Groups",
                                    state=self.app_config['notifications']['groups'])
        self.channels = urwid.CheckBox("Channels",
                                      state=self.app_config['notifications']['channels'])

        self.photos = urwid.CheckBox("Photos",
                                    state=self.app_config['data']['auto_download']['photos'])
        self.videos = urwid.CheckBox("Videos",
                                    state=self.app_config['data']['auto_download']['videos'])
        self.files = urwid.CheckBox("Files",
                                   state=self.app_config['data']['auto_download']['files'])
        self.voice = urwid.CheckBox("Voice messages",
                                   state=self.app_config['data']['auto_download']['voice_messages'])

        self.theme_combo = urwid.Edit("Theme (default/dark/blue): ", self.app_config.get("interface", {}).get("theme", "default"))
        self.layout_combo = urwid.Edit("Keyboard layout (en/ru): ", self.app_config.get("interface", {}).get("keyboard_layout", "en"))

        self.plugins_button = urwid.Button("Plugin Manager")
        urwid.connect_signal(self.plugins_button, 'click', self.open_plugin_manager)

        self.save_button = urwid.Button("Save")
        urwid.connect_signal(self.save_button, 'click', self.save_settings)

        self.cancel_button = urwid.Button("Cancel")
        urwid.connect_signal(self.cancel_button, 'click', self.cancel_settings)

        content = urwid.Pile([
            urwid.Text("Settings", align='center'),
            urwid.Divider(),
            urwid.Text("Notifications:", align='left'),
            self.private_chats,
            self.groups,
            self.channels,
            urwid.Divider(),
            urwid.Text("Auto-download:", align='left'),
            self.photos,
            self.videos,
            self.files,
            self.voice,
            urwid.Divider(),
            urwid.Text("Theme:", align='left'),
            self.theme_combo,
            urwid.Text("Keyboard layout:", align='left'),
            self.layout_combo,
            urwid.Divider(),
            urwid.AttrMap(self.plugins_button, 'button'),
            urwid.Divider(),
            urwid.Columns([
                ('weight', 1, urwid.AttrMap(self.save_button, 'button')),
                ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
            ])
        ])

        super().__init__(urwid.Filler(content, 'top'))

    def save_settings(self, button):
        self.app_config['notifications']['private_chats'] = self.private_chats.state
        self.app_config['notifications']['groups'] = self.groups.state
        self.app_config['notifications']['channels'] = self.channels.state

        self.app_config['data']['auto_download']['photos'] = self.photos.state
        self.app_config['data']['auto_download']['videos'] = self.videos.state
        self.app_config['data']['auto_download']['files'] = self.files.state
        self.app_config['data']['auto_download']['voice_messages'] = self.voice.state

        self.app_config['interface']['theme'] = self.theme_combo.get_edit_text().strip()
        self.app_config['interface']['keyboard_layout'] = self.layout_combo.get_edit_text().strip()

        self.parent.apply_theme(self.app_config['interface']['theme'])
        self.parent.keyboard_layout = self.app_config['interface']['keyboard_layout']

        _save_config(self.app_config)
        self.parent.close_settings()

    def cancel_settings(self, button):
        self.parent.close_settings()

    def open_plugin_manager(self, button):
        self.parent.show_plugin_manager()


class PluginSettingsWidget(urwid.WidgetWrap):
    def __init__(self, parent, plugin_name, plugin_info):
        self.parent = parent
        self.app_config = parent.config
        self.plugin_name = plugin_name
        self.plugin_info = plugin_info

        self.enabled = self.app_config.get("plugins", {}).get(plugin_name, {}).get('enabled', True)

        self.enable_button = urwid.Button("[X] Enabled" if self.enabled else "[ ] Enabled")
        self.configure_button = urwid.Button("Configure")
        self.back_button = urwid.Button("Back")

        urwid.connect_signal(self.enable_button, 'click', self.toggle_enabled)
        urwid.connect_signal(self.configure_button, 'click', self.configure)
        urwid.connect_signal(self.back_button, 'click', self.back)

        content = urwid.Pile([
            urwid.Text(f"Plugin: {plugin_info.get('name', plugin_name)}", align='center'),
            urwid.Divider(),
            urwid.Text(f"Version: {plugin_info.get('version', '1.0')}"),
            urwid.Text(f"Author: {plugin_info.get('author', 'Unknown')}"),
            urwid.Divider(),
            urwid.Text(f"Description: {plugin_info.get('description', '')}"),
            urwid.Divider(),
            urwid.AttrMap(self.enable_button, 'button'),
            urwid.AttrMap(self.configure_button, 'button'),
            urwid.Divider(),
            urwid.AttrMap(self.back_button, 'button')
        ])

        super().__init__(urwid.Filler(content, 'top'))

    def toggle_enabled(self, button):
        self.enabled = not self.enabled
        button.set_label("[X] Enabled" if self.enabled else "[ ] Enabled")

        if "plugins" not in self.app_config:
            self.app_config["plugins"] = {}
        if self.plugin_name not in self.app_config["plugins"]:
            self.app_config["plugins"][self.plugin_name] = {}
        self.app_config["plugins"][self.plugin_name]['enabled'] = self.enabled
        _save_config(self.app_config)

        self.parent.set_status("Plugin " + ("enabled" if self.enabled else "disabled"), 'success')

    def configure(self, button):
        if self.plugin_name in plugin_settings_widgets:
            widget_creator = plugin_settings_widgets[self.plugin_name]
            plugin_config = _get_plugin_config(self.app_config, self.plugin_name, {})

            # FIX: renamed from save_plugin_config to avoid shadowing the module-level function,
            # which caused an infinite recursive call when invoked with two arguments.
            def _on_save(new_config):
                new_config['enabled'] = self.enabled
                _save_plugin_config(self.app_config, self.plugin_name, new_config)
                _save_config(self.app_config)
                self.parent.show_plugin_settings(self.plugin_name)

            widget = widget_creator(self.parent, plugin_config, _on_save)
            self.parent.frame.body = widget
            self.parent.in_plugin_settings = True
            self.parent.current_plugin_settings = self.plugin_name
        else:
            self.parent.set_status("No configuration available for this plugin", 'error')

    def back(self, button):
        self.parent.show_plugin_manager()


class PluginManagerWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent
        self.app_config = parent.config
        self.plugin_list = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.plugin_list)

        self.back_button = urwid.Button("Back to Settings")
        urwid.connect_signal(self.back_button, 'click', self.back)

        header = urwid.Pile([
            urwid.Text("Plugin Manager", align='center'),
            urwid.Divider()
        ])

        footer = urwid.Pile([
            urwid.Divider(),
            urwid.AttrMap(self.back_button, 'button')
        ])

        content = urwid.Frame(
            header=header,
            body=urwid.AttrMap(self.listbox, 'body'),
            footer=footer
        )

        super().__init__(content)
        self.load_plugins()

    def load_plugins(self):
        self.plugin_list.clear()

        if not loaded_plugins:
            self.plugin_list.append(urwid.Text("No plugins loaded", align='center'))
            return

        for plugin_info in loaded_plugins:
            plugin_name = plugin_info['name']
            enabled = self.app_config.get("plugins", {}).get(plugin_name, {}).get('enabled', True)
            status = "✓" if enabled else "✗"

            button = urwid.Button(f"{status} {plugin_name} v{plugin_info['version']}")
            urwid.connect_signal(button, 'click', lambda button, p=plugin_name, i=plugin_info: self.open_plugin(p, i))
            self.plugin_list.append(urwid.AttrMap(button, 'dialog_name'))

        self.parent.refresh_ui()

    def open_plugin(self, plugin_name, plugin_info):
        self.parent.show_plugin_settings(plugin_name, plugin_info)

    def back(self, button):
        self.parent.close_plugin_manager()

    def keypress(self, size, key):
        if key == 'esc':
            self.parent.close_plugin_manager()
            return None
        return super().keypress(size, key)
