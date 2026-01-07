#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
# beta is linuxgram!  #
#######################
__version__ = '1.0.033-alt-test'

import asyncio
import os
import json
import sys
import importlib.util
import mimetypes
import textwrap
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient, events, functions, errors
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest
import urwid
import traceback
import subprocess

SESSION_FILE = 'linuxgram.session'
DOWNLOADS_DIR = "downloads"
CONFIG_FILE = "config.json"
CREDENTIALS_FILE = "credentials.json"
PLUGINS_DIR = "plugins"
PLUGINS_CONFIG_DIR = "plugins_config"

client = None
config = {}
loaded_plugins = []
plugin_handlers = {}

DEFAULT_THEMES = {
    "default": [
        ('header', 'white', 'black'),
        ('footer', 'white', 'black'),
        ('selected', 'white', 'dark blue'),
        ('dialog_name', 'white', ''),
        ('status', 'yellow', 'black'),
        ('title', 'bold', ''),
        ('button', 'white', ''),
        ('input', 'white', 'dark blue'),
        ('error', 'white', 'dark red'),
        ('success', 'white', 'dark green'),
        ('reaction', 'light cyan', ''),
    ],
    "dark": [
        ('header', 'white', 'dark gray'),
        ('footer', 'white', 'dark gray'),
        ('selected', 'white', 'dark magenta'),
        ('dialog_name', 'white', ''),
        ('status', 'yellow', 'dark gray'),
        ('title', 'bold', ''),
        ('button', 'white', ''),
        ('input', 'white', 'dark magenta'),
        ('error', 'white', 'dark red'),
        ('success', 'white', 'dark green'),
        ('reaction', 'light cyan', ''),
    ],
    "blue": [
        ('header', 'white', 'dark blue'),
        ('footer', 'white', 'dark blue'),
        ('selected', 'white', 'light blue'),
        ('dialog_name', 'white', ''),
        ('status', 'yellow', 'dark blue'),
        ('title', 'bold', ''),
        ('button', 'white', ''),
        ('input', 'white', 'light blue'),
        ('error', 'white', 'dark red'),
        ('success', 'white', 'dark green'),
        ('reaction', 'light cyan', ''),
    ]
}

LAYOUT_MAP = {
    'ru': {
        'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
        '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л',
        'l': 'д', ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
        ',': 'б', '.': 'ю', '/': '.',
        'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З',
        '{': 'Х', '}': 'Ъ', 'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л',
        'L': 'Д', ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь',
        '<': 'Б', '>': 'Ю', '?': ','
    },
    'en': {}
}

REVERSE_LAYOUT_MAP = {
    'ru': {v: k for k, v in LAYOUT_MAP['ru'].items()},
    'en': {}
}

def load_config():
    default_config = {
        "privacy": {"last_seen": "everybody", "read_receipts": True},
        "notifications": {"private_chats": True, "groups": True, "channels": False},
        "data": {"auto_download": {"photos": True, "videos": False, "files": False, "voice_messages": True}},
        "language": "English",
        "interface": {
            "dialogs_limit": 100,
            "messages_limit": 50,
            "show_avatars": False,
            "theme": "default",
            "keyboard_layout": "en"
        },
        "plugins": {}
    }
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_config = json.load(f)
            for key in default_config:
                if key not in loaded_config:
                    loaded_config[key] = default_config[key]
            return loaded_config
    except:
        return default_config

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_plugin_config(plugin_name, default_config=None):
    if default_config is None:
        default_config = {}
    return config.get("plugins", {}).get(plugin_name, default_config)

def save_plugin_config(plugin_name, plugin_config):
    if "plugins" not in config:
        config["plugins"] = {}
    config["plugins"][plugin_name] = plugin_config
    save_config()

def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_credentials(api_id, api_hash, phone=None):
    creds = {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone
    }
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds, f, indent=2)

def load_plugins():
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR)
        return

    loaded_plugins.clear()
    plugin_handlers.clear()

    sys.path.insert(0, PLUGINS_DIR)

    for file in os.listdir(PLUGINS_DIR):
        if file.endswith('.py') and file != '__init__.py':
            try:
                plugin_name = file[:-3]
                spec = importlib.util.spec_from_file_location(plugin_name, os.path.join(PLUGINS_DIR, file))
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
                        plugin_handlers[plugin_name] = handlers
                        print(f"✓ Plugin loaded: {plugin_info['name']} v{plugin_info['version']} by {plugin_info['author']}")
                    else:
                        print(f"⚠ Plugin {plugin_name} returned no handlers")
                else:
                    print(f"⚠ Plugin {plugin_name} has no register_hooks() function")

                loaded_plugins.append(plugin_info)

            except Exception as e:
                print(f"✗ Error loading plugin {file}: {e}")
                traceback.print_exc()

def execute_plugin_hook(hook_name, *args, **kwargs):
    results = []
    for plugin_name, handlers in plugin_handlers.items():
        if hook_name in handlers:
            try:
                result = handlers[hook_name](*args, **kwargs)
                if result is not None:
                    results.append((plugin_name, result))
            except Exception as e:
                print(f"Error executing hook '{hook_name}' in plugin {plugin_name}: {e}")
                traceback.print_exc()
    return results

class LoginWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent
        self.step = 1
        self.credentials = load_credentials()

        self.api_id_edit = urwid.Edit("API ID: ", "")
        self.api_hash_edit = urwid.Edit("API Hash: ", "")
        self.phone_edit = urwid.Edit("Phone (e.g. +79243196098): ", "")
        self.code_edit = urwid.Edit("Code: ", "")
        self.password_edit = urwid.Edit("2FA Password: ", "")

        self.next_button = urwid.Button("Next")
        urwid.connect_signal(self.next_button, 'click', self.next_step)

        self.qr_button = urwid.Button("Login with QR (Coming soon)")
        urwid.connect_signal(self.qr_button, 'click', self.qr_login)

        self.back_button = urwid.Button("Back")
        urwid.connect_signal(self.back_button, 'click', self.prev_step)

        self.cancel_button = urwid.Button("Cancel")
        urwid.connect_signal(self.cancel_button, 'click', self.cancel)

        super().__init__(urwid.Filler(urwid.Pile([]), 'top'))
        self.update_content()

    def update_content(self):
        widgets = []

        if self.step == 1:
            if self.credentials:
                self.api_id_edit.set_edit_text(str(self.credentials.get('api_id', '')))
                self.api_hash_edit.set_edit_text(self.credentials.get('api_hash', ''))

            widgets.extend([
                urwid.Text("Login to Telegram", align='center'),
                urwid.Divider(),
                urwid.Text("Step 1: Enter API credentials", align='left'),
                urwid.Text("Get API ID and Hash from https://my.telegram.org"),
                urwid.Divider(),
                self.api_id_edit,
                self.api_hash_edit,
                urwid.Divider(),
                urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.qr_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ])
            ])

        elif self.step == 2:
            if self.credentials and self.credentials.get('phone'):
                self.phone_edit.set_edit_text(self.credentials['phone'])

            widgets.extend([
                urwid.Text("Login to Telegram", align='center'),
                urwid.Divider(),
                urwid.Text("Step 2: Enter phone number", align='left'),
                self.phone_edit,
                urwid.Divider(),
                urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.back_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ])
            ])

        elif self.step == 3:
            widgets.extend([
                urwid.Text("Login to Telegram", align='center'),
                urwid.Divider(),
                urwid.Text("Step 3: Enter code", align='left'),
                urwid.Text("Code sent to your phone"),
                self.code_edit,
                urwid.Divider(),
                urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.back_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ])
            ])

        elif self.step == 4:
            widgets.extend([
                urwid.Text("Login to Telegram", align='center'),
                urwid.Divider(),
                urwid.Text("Step 4: Enter 2FA password", align='left'),
                self.password_edit,
                urwid.Divider(),
                urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.back_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ])
            ])

        self._w.original_widget = urwid.Pile(widgets)
        self.parent.refresh_ui()

    def next_step(self, button):
        if self.step == 1:
            api_id = self.api_id_edit.get_edit_text().strip()
            api_hash = self.api_hash_edit.get_edit_text().strip()

            if not api_id or not api_hash:
                self.parent.set_status("Please enter both API ID and Hash", 'error')
                return

            try:
                api_id = int(api_id)
            except ValueError:
                self.parent.set_status("API ID must be a number", 'error')
                return

            save_credentials(api_id, api_hash)
            self.parent.api_id = api_id
            self.parent.api_hash = api_hash
            self.step = 2
            self.update_content()

        elif self.step == 2:
            phone = self.phone_edit.get_edit_text().strip()
            if not phone:
                self.parent.set_status("Please enter phone number", 'error')
                return

            save_credentials(self.parent.api_id, self.parent.api_hash, phone)
            self.parent.phone = phone
            self.parent.set_status("Connecting to Telegram...", 'status')
            asyncio.get_event_loop().create_task(self.parent.async_start_login())

        elif self.step == 3:
            code = self.code_edit.get_edit_text().strip()
            if not code:
                self.parent.set_status("Please enter code", 'error')
                return

            self.parent.login_code = code
            self.parent.set_status("Signing in...", 'status')
            asyncio.get_event_loop().create_task(self.parent.async_sign_in_with_code())

        elif self.step == 4:
            password = self.password_edit.get_edit_text().strip()
            if not password:
                self.parent.set_status("Please enter password", 'error')
                return

            self.parent.login_password = password
            self.parent.set_status("Signing in with 2FA...", 'status')
            asyncio.get_event_loop().create_task(self.parent.async_sign_in_with_password())

    def prev_step(self, button):
        if self.step > 1:
            self.step -= 1
            self.update_content()

    def qr_login(self, button):
        self.parent.set_status("QR login coming soon", 'status')

    def cancel(self, button):
        self.parent.exit_app()

class MessageWidget(urwid.WidgetWrap):
    def __init__(self, message, is_selected=False, is_outgoing=False, reply_text="", sender_name="", reactions=None):
        self.message = message
        self.is_selected = is_selected
        self.is_outgoing = is_outgoing
        self.reply_text = reply_text
        self.sender_name = sender_name
        self.reactions = reactions or {}

        self.text_widget = urwid.Text("")
        super().__init__(self.build_widget())

    def build_widget(self):
        time_str = self.message.date.strftime("%H:%M")

        if self.sender_name:
            sender_display = f"{self.sender_name}"
        else:
            sender_display = ""

        content_lines = []
        if self.message.text:
            wrapped_text = textwrap.wrap(self.message.text, width=80)
            if len(wrapped_text) > 3:
                content = wrapped_text[0] + " ..."
            else:
                content = " ".join(wrapped_text)
            content_lines.append(content)

        media_type = None
        if self.message.media:
            if self.message.photo:
                media_type = "📷 Photo"
            elif self.message.video:
                media_type = "🎥 Video"
            elif self.message.voice:
                media_type = "🎤 Voice message"
            elif self.message.document:
                media_type = "📄 Document"
            elif self.message.audio:
                media_type = "🎵 Audio"
            elif self.message.sticker:
                media_type = "😀 Sticker"
            else:
                media_type = "[Media]"

            if media_type:
                content_lines.append(media_type)

        if not content_lines:
            content_lines.append("[Empty]")

        content = " | ".join(content_lines)
        if len(content) > 120:
            content = content[:117] + "..."

        reply_indicator = ""
        if self.reply_text:
            if len(self.reply_text) > 30:
                preview = self.reply_text[:27] + "..."
            else:
                preview = self.reply_text
            reply_indicator = f" [↩ {preview}]"

        if self.is_selected:
            prefix = "> "
        else:
            prefix = "  "

        line = f"{prefix}[{time_str}] {sender_display}: {content}{reply_indicator}"

        reaction_text = ""
        if self.reactions:
            reactions_display = []
            for emoji, count in self.reactions.items():
                if count > 1:
                    reactions_display.append(f"{emoji} {count}")
                else:
                    reactions_display.append(emoji)
            if reactions_display:
                reaction_text = "\n  " + " ".join(reactions_display)

        self.text_widget.set_text(line + reaction_text)

        if self.is_selected:
            return urwid.AttrMap(self.text_widget, 'selected')
        else:
            return self.text_widget

class DialogWidget(urwid.WidgetWrap):
    def __init__(self, dialog, index, is_selected=False, callback=None, member_count=None, online_count=None):
        self.dialog = dialog
        self.index = index
        self.is_selected = is_selected
        self.callback = callback
        self.member_count = member_count
        self.online_count = online_count

        name = dialog.name or "Unknown"
        if getattr(dialog, 'unread_count', 0) > 0:
            name = f"* {name} ({dialog.unread_count})"

        info = ""
        if self.member_count:
            if self.online_count:
                info = f" ({self.online_count}/{self.member_count})"
            else:
                info = f" ({self.member_count})"

        if self.is_selected:
            prefix = "> "
        else:
            prefix = "  "

        text = f"{prefix}{name}{info}"

        self.button = urwid.Button(text)
        urwid.connect_signal(self.button, 'click', self.on_click)

        if self.is_selected:
            wrapped_button = urwid.AttrMap(self.button, 'selected')
        else:
            wrapped_button = self.button

        super().__init__(wrapped_button)

    def on_click(self, button):
        if self.callback:
            self.callback(self.index)

class SettingsWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent

        self.private_chats = urwid.CheckBox("Private chats",
                                           state=config['notifications']['private_chats'])
        self.groups = urwid.CheckBox("Groups",
                                    state=config['notifications']['groups'])
        self.channels = urwid.CheckBox("Channels",
                                      state=config['notifications']['channels'])

        self.photos = urwid.CheckBox("Photos",
                                    state=config['data']['auto_download']['photos'])
        self.videos = urwid.CheckBox("Videos",
                                    state=config['data']['auto_download']['videos'])
        self.files = urwid.CheckBox("Files",
                                   state=config['data']['auto_download']['files'])
        self.voice = urwid.CheckBox("Voice messages",
                                   state=config['data']['auto_download']['voice_messages'])

        self.theme_combo = urwid.Edit("Theme (default/dark/blue): ", config.get("interface", {}).get("theme", "default"))
        self.layout_combo = urwid.Edit("Keyboard layout (en/ru): ", config.get("interface", {}).get("keyboard_layout", "en"))

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
            urwid.Columns([
                ('weight', 1, urwid.AttrMap(self.save_button, 'button')),
                ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
            ])
        ])

        super().__init__(urwid.Filler(content, 'top'))

    def save_settings(self, button):
        config['notifications']['private_chats'] = self.private_chats.state
        config['notifications']['groups'] = self.groups.state
        config['notifications']['channels'] = self.channels.state

        config['data']['auto_download']['photos'] = self.photos.state
        config['data']['auto_download']['videos'] = self.videos.state
        config['data']['auto_download']['files'] = self.files.state
        config['data']['auto_download']['voice_messages'] = self.voice.state

        config['interface']['theme'] = self.theme_combo.get_edit_text().strip()
        config['interface']['keyboard_layout'] = self.layout_combo.get_edit_text().strip()

        self.parent.apply_theme(config['interface']['theme'])
        self.parent.keyboard_layout = config['interface']['keyboard_layout']

        save_config()
        self.parent.close_settings()

    def cancel_settings(self, button):
        self.parent.close_settings()

class SearchWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent
        self.search_edit = urwid.Edit("Search: ", "")
        self.search_button = urwid.Button("Search")
        self.cancel_button = urwid.Button("Cancel")

        urwid.connect_signal(self.search_button, 'click', self.do_search)
        urwid.connect_signal(self.cancel_button, 'click', self.cancel_search)

        content = urwid.Pile([
            urwid.Text("Search Dialogs", align='center'),
            urwid.Divider(),
            self.search_edit,
            urwid.Divider(),
            urwid.Columns([
                ('weight', 1, urwid.AttrMap(self.search_button, 'button')),
                ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
            ])
        ])

        super().__init__(urwid.Filler(content, 'top'))

    def do_search(self, button):
        query = self.search_edit.get_edit_text().strip()
        if not query:
            self.parent.filtered_dialogs = self.parent.dialogs.copy()
            self.parent.set_status("Search cleared", 'status')
            self.parent.close_search()
        else:
            filtered = []
            for dialog in self.parent.dialogs:
                if dialog.name and query.lower() in dialog.name.lower():
                    filtered.append(dialog)

            if not filtered:
                self.parent.set_status(f"No dialogs found for '{query}'", 'error')
                self.parent.filtered_dialogs = self.parent.dialogs.copy()
            else:
                self.parent.filtered_dialogs = filtered
                self.parent.set_status(f"Found {len(filtered)} dialogs", 'success')

            self.parent.close_search()

        self.parent.current_dialog_index = 0
        self.parent.refresh_dialog_list()
        self.parent.refresh_ui()

    def cancel_search(self, button):
        self.parent.filtered_dialogs = self.parent.dialogs.copy()
        self.parent.current_dialog_index = 0
        self.parent.refresh_dialog_list()
        self.parent.set_status("Search cancelled", 'status')
        self.parent.close_search()
        self.parent.refresh_ui()

class ReactionPickerWidget(urwid.WidgetWrap):
    def __init__(self, parent, message):
        self.parent = parent
        self.message = message

        self.reactions = ['👍', '👎', '❤️', '🔥', '🥰', '👏', '😁', '🤔', '🤯', '😱', '🤬', '😢', '🎉', '🤩', '🤮', '💩', '🙏', '👌', '🕊', '🤡', '🥱', '🥴', '😍', '🐳', '❤️‍🔥', '🌚', '🌭', '💯', '🤣', '⚡️', '🍌', '🏆', '💔', '🤨', '😐', '🍓', '🍾', '💋', '🖕', '😈', '😴', '😭', '🤓', '👻', '👨‍💻', '👀', '🎃', '🙈', '😇', '😨', '🤝', '✍️', '🤗', '🫡', '🎅', '🎄', '☃️', '💅', '🤪', '🗿', '🆒', '💘', '🙉', '🦄', '😘', '💊', '🙊', '😎', '👾', '🤷‍♂️', '🤷', '🤷‍♀️', '😡']

        self.list_walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.list_walker)

        header = urwid.Text("Select reaction (Esc to close)", align='center')
        footer = urwid.Text("Press Esc to cancel", align='center')

        frame = urwid.Frame(
            header=urwid.AttrMap(header, 'header'),
            body=urwid.AttrMap(self.listbox, 'body'),
            footer=urwid.AttrMap(footer, 'footer')
        )

        super().__init__(frame)
        self.load_reactions()

    def load_reactions(self):
        self.list_walker.clear()
        for reaction in self.reactions:
            button = urwid.Button(reaction)
            urwid.connect_signal(button, 'click', lambda button, r=reaction: self.select_reaction(r))
            self.list_walker.append(urwid.AttrMap(button, 'dialog_name'))

    def select_reaction(self, reaction):
        self.parent.loop.create_task(self.parent.send_reaction(self.message, reaction))
        self.parent.close_reaction_picker()

    def keypress(self, size, key):
        if key == 'esc':
            self.parent.close_reaction_picker()
            return None
        return super().keypress(size, key)

class FileBrowserWidget(urwid.WidgetWrap):
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.current_dir = Path.home()
        self.selected_file = None

        self.header = urwid.Text("Select file to send (Esc to close)")
        self.path_display = urwid.Text(str(self.current_dir))

        self.select_button = urwid.Button("Select")
        self.cancel_button = urwid.Button("Cancel")

        urwid.connect_signal(self.select_button, 'click', self.select_file)
        urwid.connect_signal(self.cancel_button, 'click', self.cancel)

        self.file_list = urwid.SimpleFocusListWalker([])

        header_widget = urwid.Pile([
            urwid.AttrMap(self.header, 'header'),
            urwid.AttrMap(self.path_display, 'title'),
            urwid.Divider()
        ])

        footer_widget = urwid.Pile([
            urwid.Divider(),
            urwid.Columns([
                ('weight', 1, urwid.AttrMap(self.select_button, 'button')),
                ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
            ])
        ])

        self.listbox = urwid.ListBox(self.file_list)
        body_widget = urwid.AttrMap(self.listbox, 'body')

        content = urwid.Frame(
            header=header_widget,
            body=body_widget,
            footer=footer_widget
        )

        super().__init__(content)
        self.load_directory()

    def load_directory(self):
        self.file_list.clear()

        if self.current_dir.parent != self.current_dir:
            item = urwid.Button(".. (Parent directory)")
            urwid.connect_signal(item, 'click', self.go_up)
            self.file_list.append(urwid.AttrMap(item, 'dialog_name'))

        try:
            dirs = []
            files = []

            for item in self.current_dir.iterdir():
                if not item.name.startswith('.'):
                    if item.is_dir():
                        dirs.append(item)
                    else:
                        files.append(item)

            dirs.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())

            for item in dirs:
                name = f"📁 {item.name}/"
                button = urwid.Button(name)
                urwid.connect_signal(button, 'click', lambda button, path=item: self.enter_directory(path))
                self.file_list.append(urwid.AttrMap(button, 'dialog_name'))

            for item in files:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024*1024:
                    size_str = f"{size/1024:.1f} KB"
                elif size < 1024*1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                else:
                    size_str = f"{size/(1024*1024*1024):.1f} GB"

                name = f"📄 {item.name} ({size_str})"
                button = urwid.Button(name)
                urwid.connect_signal(button, 'click', lambda button, path=item: self.select_item(path))
                self.file_list.append(urwid.AttrMap(button, 'dialog_name'))

        except Exception as e:
            self.file_list.append(urwid.Text(f"Error: {e}", align='center'))

        self.parent.refresh_ui()

    def go_up(self, button):
        self.current_dir = self.current_dir.parent
        self.path_display.set_text(str(self.current_dir))
        self.load_directory()

    def enter_directory(self, directory):
        self.current_dir = directory
        self.path_display.set_text(str(self.current_dir))
        self.load_directory()

    def select_item(self, file_path):
        self.selected_file = file_path
        self.parent.refresh_ui()

    def select_file(self, button):
        if self.selected_file:
            self.parent.file_to_send = str(self.selected_file)
            self.parent.show_input("Caption (optional): ", self.parent.send_file_with_caption)
            self.parent.close_file_browser()
        else:
            self.parent.set_status("Please select a file first", 'error')
            self.parent.refresh_ui()

    def cancel(self, button):
        self.parent.close_file_browser()

    def keypress(self, size, key):
        if key == 'esc':
            self.parent.close_file_browser()
            return None
        return super().keypress(size, key)

class HelpWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent

        help_text = [
            "Keyboard shortcuts:",
            "",
            "DIALOGS MODE:",
            "  ↑↓, PgUp/PgDn, Home/End - Navigate",
            "  Enter - Open selected dialog",
            "  C - Search dialogs",
            "  P - Search contacts",
            "  S - Settings",
            "  L - Reload plugins",
            "  Q - Quit",
            "",
            "CHAT MODE:",
            "  ↑↓, PgUp/PgDn, Home/End - Navigate messages",
            "  ← - Back to dialogs",
            "  Enter - Send message",
            "  R - Reply to message",
            "  F - Send file",
            "  D - Download media",
            "  / - Search messages",
            "  E - Edit message",
            "  Delete - Delete message",
            "  T - Add reaction",
            "  S - Settings",
            "",
            "SEARCH:",
            "  Esc - Cancel search",
            "  Enter - Execute search",
            "",
            "FILE BROWSER:",
            "  ↑↓ - Navigate files",
            "  Enter - Select folder/file",
            "  Esc - Cancel",
            "",
            "REACTIONS:",
            "  T - Open reaction picker",
            "  Esc - Close reaction picker",
            "",
            "INPUT MODE:",
            "  Enter - Send",
            "  Esc - Cancel",
            "",
            "Press any key to close"
        ]

        content = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text(line), 'dialog_name') for line in help_text
        ]))

        super().__init__(content)

class TopicWidget(urwid.WidgetWrap):
    def __init__(self, topic, index, is_selected=False, callback=None):
        self.topic = topic
        self.index = index
        self.is_selected = is_selected
        self.callback = callback

        title = getattr(topic, 'title', f"Topic #{topic.id}")

        if self.is_selected:
            prefix = "> "
        else:
            prefix = "  "

        text = f"{prefix}{title}"

        self.button = urwid.Button(text)
        urwid.connect_signal(self.button, 'click', self.on_click)

        if self.is_selected:
            wrapped_button = urwid.AttrMap(self.button, 'selected')
        else:
            wrapped_button = self.button

        super().__init__(wrapped_button)

    def on_click(self, button):
        if self.callback:
            self.callback(self.index)

class LinuxGramTUI:
    def __init__(self):
        theme_name = config.get("interface", {}).get("theme", "default")
        self.palette = DEFAULT_THEMES.get(theme_name, DEFAULT_THEMES["default"])
        self.keyboard_layout = config.get("interface", {}).get("keyboard_layout", "en")

        self.dialogs = []
        self.filtered_dialogs = []
        self.messages = []
        self.message_widgets = []
        self.topics = []
        self.topic_widgets = []
        self.current_dialog_index = 0
        self.current_message_index = 0
        self.current_topic_index = 0
        self.current_dialog = None
        self.current_topic = None
        self.input_mode = False
        self.input_buffer = ""
        self.input_prompt = ""
        self.input_callback = None
        self.reply_to_message = None
        self.edit_message = None
        self.reply_mode = False
        self.edit_mode = False
        self.search_results = None
        self.view_mode = "dialogs"
        self.status_msg = "Starting..."
        self.search_query = ""
        self.in_settings = False
        self.in_search = False
        self.in_file_browser = False
        self.in_reaction_picker = False
        self.show_help = False
        self.member_count = None
        self.online_count = None
        self.dialogs_loaded = False
        self.reaction_picker_timeout = False
        self.file_browser_timeout = False

        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.login_code = None
        self.login_password = None
        self.logged_in = False
        self.login_widget = None

        self.client = None
        self.loop = None
        self.typing_status = False
        self.file_to_send = None
        self.files_to_send = []

        self.title = urwid.Text(f"LinuxGram Beta v{__version__}", align='center')
        self.header = urwid.Text("Dialogs")

        self.footer_help_text = "Enter... | H: help | L: reload plugins"
        self.footer_help = urwid.Text(self.footer_help_text)

        self.footer_status = urwid.Text("")
        self.footer_status_am = urwid.AttrMap(self.footer_status, 'footer')

        self.full_help_text = (
            "Q: Quit | ↑↓: Select | Enter: Open | ←: Back | R: Reply | "
            "F: File | D: Download | /: Search | S: Settings | C: Search | E: Edit | L: Plugins | T: Reaction | Delete: Delete"
        )
        self.full_help = urwid.Text(self.full_help_text)

        self.footer_widget = urwid.Pile([
            urwid.AttrMap(self.footer_help, 'footer'),
            self.footer_status_am
        ])

        self.full_help_widget = urwid.Pile([
            urwid.AttrMap(self.full_help, 'footer'),
            self.footer_status_am
        ])

        self.dialog_list = urwid.SimpleFocusListWalker([])
        self.dialog_listbox = urwid.ListBox(self.dialog_list)

        self.topic_list = urwid.SimpleFocusListWalker([])
        self.topic_listbox = urwid.ListBox(self.topic_list)

        self.message_list = urwid.SimpleFocusListWalker([])
        self.message_listbox = urwid.ListBox(self.message_list)

        self.input_edit = urwid.Edit(multiline=False)
        self.input_widget = urwid.AttrMap(self.input_edit, 'input')

        self.help_widget = HelpWidget(self)

        self.frame = urwid.Frame(
            body=urwid.AttrMap(self.dialog_listbox, 'body'),
            header=urwid.AttrMap(urwid.Pile([
                urwid.AttrMap(self.title, 'title'),
                urwid.AttrMap(self.header, 'header')
            ]), ''),
            footer=urwid.AttrMap(self.footer_widget, 'footer')
        )

        self.urwid_loop = None

        # Создаем папку для конфигурации плагинов
        if not os.path.exists(PLUGINS_CONFIG_DIR):
            os.makedirs(PLUGINS_CONFIG_DIR)

        # Инициализация плагинов
        load_plugins()
        execute_plugin_hook('on_tui_init', self)

    def setup_ui(self):
        self.urwid_loop = urwid.MainLoop(
            self.frame,
            self.palette,
            unhandled_input=self.handle_keypress,
            event_loop=urwid.AsyncioEventLoop(loop=self.loop)
        )

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.setup_ui()

        if not os.path.exists(SESSION_FILE):
            self.show_login_screen()
        else:
            self.loop.create_task(self.init_client())

        try:
            self.urwid_loop.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.exit_app()

    def refresh_ui(self):
        if self.urwid_loop:
            try:
                self.urwid_loop.draw_screen()
            except:
                pass

    def show_login_screen(self):
        self.login_widget = LoginWidget(self)
        self.frame.body = self.login_widget
        self.header.set_text("Login to Telegram")
        self.refresh_ui()

    async def init_client(self):
        try:
            creds = load_credentials()
            if not creds:
                self.show_login_screen()
                return

            self.api_id = creds.get('api_id')
            self.api_hash = creds.get('api_hash')

            if not self.client:
                self.client = TelegramClient(
                    SESSION_FILE,
                    self.api_id,
                    self.api_hash,
                    loop=self.loop
                )

            await self.client.start()

            if not await self.client.is_user_authorized():
                self.show_login_screen()
                return

            if not self.client.list_event_handlers():
                self.client.add_event_handler(self.handler_new_message, events.NewMessage)
                self.client.add_event_handler(self.handler_message_edited, events.MessageEdited)
                self.client.add_event_handler(self.handler_message_deleted, events.MessageDeleted)

            execute_plugin_hook('on_client_ready', self.client)

            self.loop.create_task(self.load_dialogs_async())

        except Exception as e:
            print(f"Client init error: {e}")
            traceback.print_exc()
            self.show_login_screen()

    async def async_start_login(self):
        try:
            if not self.client:
                self.client = TelegramClient(
                    SESSION_FILE,
                    self.api_id,
                    self.api_hash,
                    loop=self.loop
                )

            await self.client.connect()
            await self.client.send_code_request(self.phone)

            self.login_widget.step = 3
            self.login_widget.update_content()
            self.set_status("Code sent to your phone. Enter it above.", 'success')

        except errors.PhoneNumberInvalidError:
            self.set_status("Invalid phone number", 'error')
            self.login_widget.step = 2
            self.login_widget.update_content()
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"Login error: {e}")
            traceback.print_exc()

    async def async_sign_in_with_code(self):
        try:
            await self.client.sign_in(self.phone, self.login_code)
            await self.login_successful()

        except errors.SessionPasswordNeededError:
            self.set_status("2FA password required", 'success')
            self.login_widget.step = 4
            self.login_widget.update_content()
        except errors.PhoneCodeInvalidError:
            self.set_status("Invalid code", 'error')
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"Sign in error: {e}")
            traceback.print_exc()

    async def async_sign_in_with_password(self):
        try:
            password = await self.client(functions.account.GetPasswordRequest())
            await self.client.sign_in(password=self.login_password)
            await self.login_successful()

        except errors.PasswordHashInvalidError:
            self.set_status("Invalid password", 'error')
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"2FA error: {e}")
            traceback.print_exc()

    async def login_successful(self):
        self.logged_in = True
        self.set_status("Login successful! Loading dialogs...", 'success')

        save_credentials(self.api_id, self.api_hash, self.phone)

        await self.init_client()

    async def load_dialogs_async(self):
        try:
            if not self.client or not self.client.is_connected():
                self.set_status("Waiting for connection...", 'status')
                return

            self.set_status("Loading dialogs...", 'status')

            limit = config.get("interface", {}).get("dialogs_limit", 100)
            self.dialogs = await self.client.get_dialogs(limit=limit)
            self.filtered_dialogs = self.dialogs.copy()

            self.refresh_dialog_list()
            self.dialogs_loaded = True
            self.set_status(f"Loaded {len(self.dialogs)} dialogs", 'success')

            self.loop.create_task(self.load_dialogs_details())

        except Exception as e:
            self.set_status(f"Error loading dialogs: {e}", 'error')
            print(f"Dialogs error: {e}")
            traceback.print_exc()

    async def load_dialogs_details(self):
        if not self.dialogs:
            return

        for dialog in self.dialogs:
            try:
                if isinstance(dialog.entity, (types.Channel, types.Chat)):
                    await asyncio.sleep(0.1)

                    if isinstance(dialog.entity, types.Channel):
                        full_chat = await self.client(
                            functions.channels.GetFullChannelRequest(channel=dialog.entity)
                        )
                    else:
                        full_chat = await self.client(
                            functions.messages.GetFullChatRequest(chat_id=dialog.entity.id)
                        )

                    dialog.member_count = getattr(full_chat.full_chat, 'participants_count', 0)
                    dialog.online_count = getattr(full_chat.full_chat, 'online_count', 0)

                    self.refresh_dialog_list()

            except Exception:
                continue

    async def load_topics(self, dialog):
        try:
            self.set_status("Loading topics...", 'status')

            try:
                if hasattr(self.client, 'get_forum_topics'):
                    result = await self.client.get_forum_topics(dialog.entity, limit=50)
                    if hasattr(result, 'topics'):
                        self.topics = result.topics
                    else:
                        self.topics = result
                else:
                    self.set_status("Telethon version doesn't support forum topics", 'error')
                    self.topics = []

            except Exception as e:
                self.set_status(f"Topics API Error: {str(e)}", 'error')
                with open("debug_log.txt", "a") as f:
                    f.write(f"Topic error: {e}\n")
                self.topics = []

            for topic in self.topics:
                topic.id = int(topic.id)
                topic.title = getattr(topic, 'title', f"Topic #{topic.id}")

            self.topic_widgets = []
            self.refresh_topic_list()

            self.view_mode = "topics"
            self.header.set_text(f"Topics: {dialog.name}")
            self.frame.body = urwid.AttrMap(self.topic_listbox, 'body')

            if self.topics:
                self.current_topic_index = 0
                self.topic_list.set_focus(0)
                self.set_status(f"Loaded {len(self.topics)} topics", 'success')
            else:
                if not self.topics and getattr(dialog.entity, 'forum', False):
                     self.set_status("No topics found or API error", 'error')
                else:
                     self.set_status("No topics found. Press Enter to open general chat.", 'status')

        except Exception as e:
            self.set_status(f"Error loading topics wrapper: {e}", 'error')
            self.topics = []
            await self.load_messages(dialog, keep_position=False, focus_on_bottom=True)

    def refresh_topic_list(self):
        self.topic_list.clear()
        self.topic_widgets.clear()

        if not self.topics:
            self.topic_list.append(urwid.Text("No topics found. Press Enter to open general chat or ← to go back.", align='center'))
            self.refresh_ui()
            return

        for i, topic in enumerate(self.topics):
            widget = TopicWidget(
                topic,
                i,
                i == self.current_topic_index,
                callback=self.select_topic
            )
            self.topic_list.append(widget)
            self.topic_widgets.append(widget)

        if self.topic_list:
            self.topic_list.set_focus(self.current_topic_index)

        self.refresh_ui()

    async def load_messages(self, dialog, topic=None, keep_position=False, focus_on_bottom=False):
        try:
            old_focus_position = None
            old_message_id = None

            if keep_position and self.messages and self.current_message_index < len(self.messages):
                old_focus_position = self.current_message_index
                old_message_id = self.messages[old_focus_position].id

            self.current_dialog = dialog
            self.current_topic = topic
            limit = config.get("interface", {}).get("messages_limit", 50)

            self.set_status("Loading messages...", 'status')

            if topic:
                try:
                    messages = await self.client.get_messages(
                        dialog.entity,
                        limit=limit,
                        reply_to=int(topic.id)
                    )
                except Exception as e:
                    self.set_status(f"Error fetching topic msgs: {e}", 'error')
                    messages = []
            else:
                messages = await self.client.get_messages(dialog.entity, limit=limit)

            self.messages = list(reversed(messages))
            self.message_widgets = []

            messages_dict = {msg.id: msg for msg in self.messages}

            for msg in self.messages:
                msg.sender_name = await self.get_sender_name_async(msg)

                if hasattr(msg, 'reply_to') and msg.reply_to and hasattr(msg.reply_to, 'reply_to_msg_id'):
                    reply_id = msg.reply_to.reply_to_msg_id
                    if reply_id in messages_dict:
                        reply_msg = messages_dict[reply_id]
                        if reply_msg.text:
                            if len(reply_msg.text) > 40:
                                msg.reply_text = reply_msg.text[:37] + "..."
                            else:
                                msg.reply_text = reply_msg.text
                        else:
                            msg.reply_text = "[Media]"

                if hasattr(msg, 'reactions') and msg.reactions:
                    reactions_dict = {}
                    for reaction in msg.reactions.results:
                        if hasattr(reaction.reaction, 'emoticon'):
                            emoji = reaction.reaction.emoticon
                            count = reaction.count
                            reactions_dict[emoji] = count
                    msg.reactions_dict = reactions_dict

            self.refresh_message_list()

            self.view_mode = "messages"

            header_text = f"Chat: {dialog.name}"
            if topic:
                header_text = f"Topic: {getattr(topic, 'title', f'#{topic.id}')} - {dialog.name}"
            if hasattr(dialog, 'member_count') and dialog.member_count:
                if hasattr(dialog, 'online_count') and dialog.online_count:
                    header_text += f" ({dialog.online_count}/{dialog.member_count})"
                else:
                    header_text += f" ({dialog.member_count})"

            self.header.set_text(header_text)
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')

            self.set_status(f"Loaded {len(self.messages)} messages", 'success')

            if self.messages:
                if focus_on_bottom:
                    self.current_message_index = len(self.messages) - 1
                    self.message_list.set_focus(self.current_message_index)
                elif keep_position and old_message_id:
                    for i, msg in enumerate(self.messages):
                        if msg.id == old_message_id:
                            self.current_message_index = i
                            self.message_list.set_focus(i)
                            break
                    else:
                        self.current_message_index = len(self.messages) - 1
                        self.message_list.set_focus(self.current_message_index)
                else:
                    self.current_message_index = len(self.messages) - 1
                    self.message_list.set_focus(self.current_message_index)

                self.refresh_message_list()

        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"Messages error: {e}")
            traceback.print_exc()

    async def get_sender_name_async(self, msg):
        try:
            sender = await msg.get_sender()
            if isinstance(sender, types.User):
                name = sender.first_name or ""
                if sender.last_name:
                    name += f" {sender.last_name}"
                return name.strip() or "User"
            elif isinstance(sender, (types.Channel, types.Chat)):
                return sender.title or "Channel"
            return "Unknown"
        except:
            return "Unknown"

    def get_sender_name(self, msg):
        return getattr(msg, 'sender_name', "Unknown")

    def select_dialog(self, index):
        if not self.filtered_dialogs or index >= len(self.filtered_dialogs):
            return

        dialog = self.filtered_dialogs[index]
        if not hasattr(dialog, 'entity'):
            self.set_status("Cannot open this dialog", 'error')
            self.refresh_ui()
            return

        self.current_dialog_index = index
        self.refresh_dialog_list()

        if hasattr(dialog.entity, 'forum') and dialog.entity.forum:
            self.loop.create_task(self.load_topics(dialog))
        else:
            self.loop.create_task(self.load_messages(dialog, keep_position=False, focus_on_bottom=True))

    def select_topic(self, index):
        if not self.topics or index >= len(self.topics):
            self.loop.create_task(self.load_messages(self.current_dialog, keep_position=False, focus_on_bottom=True))
            return

        topic = self.topics[index]
        self.current_topic_index = index
        self.refresh_topic_list()

        self.loop.create_task(self.load_messages(self.current_dialog, topic=topic, keep_position=False, focus_on_bottom=True))

    def refresh_dialog_list(self):
        self.dialog_list.clear()

        if not self.filtered_dialogs:
            self.dialog_list.append(urwid.Text("No dialogs found", align='center'))
            self.refresh_ui()
            return

        for i, dialog in enumerate(self.filtered_dialogs):
            member_count = getattr(dialog, 'member_count', None)
            online_count = getattr(dialog, 'online_count', None)

            widget = DialogWidget(
                dialog,
                i,
                i == self.current_dialog_index,
                callback=self.select_dialog,
                member_count=member_count,
                online_count=online_count
            )
            self.dialog_list.append(widget)

        if self.dialog_list:
            self.dialog_list.set_focus(self.current_dialog_index)

        self.refresh_ui()

    def refresh_message_list(self):
        self.message_list.clear()
        self.message_widgets.clear()

        if not self.messages:
            self.message_list.append(urwid.Text("No messages", align='center'))
            self.refresh_ui()
            return

        for i, msg in enumerate(self.messages):
            reply_text = getattr(msg, 'reply_text', "")
            sender_name = self.get_sender_name(msg)
            reactions = getattr(msg, 'reactions_dict', {})

            widget = MessageWidget(
                msg,
                is_selected=(i == self.current_message_index),
                is_outgoing=msg.out,
                reply_text=reply_text,
                sender_name=sender_name,
                reactions=reactions
            )
            self.message_list.append(widget)
            self.message_widgets.append(widget)

        if self.message_list:
            self.message_list.set_focus(self.current_message_index)

        self.refresh_ui()

    def set_status(self, text, style="status"):
        self.footer_status.set_text(f" {text} ")
        if style == 'error':
            self.footer_status_am.set_attr_map({None: 'error'})
        elif style == 'success':
            self.footer_status_am.set_attr_map({None: 'success'})
        else:
            self.footer_status_am.set_attr_map({None: style if style else 'footer'})

        self.refresh_ui()

    def show_input(self, prompt, callback):
        async def start_typing():
            try:
                await self.client(functions.messages.SetTypingRequest(
                    peer=self.current_dialog.entity,
                    action=types.SendMessageTypingAction()
                ))
            except Exception as e:
                print(f"Typing error: {e}")
                traceback.print_exc()

        if self.current_dialog:
            self.loop.create_task(start_typing())

        self.input_mode = True
        self.input_prompt = prompt
        self.input_callback = callback
        self.input_edit.set_caption(prompt)
        self.input_edit.set_edit_text("")
        self.input_edit.set_edit_pos(0)
        self.frame.footer = self.input_widget
        self.refresh_ui()

    def hide_input(self):
        async def stop_typing():
            try:
                await self.client(functions.messages.SetTypingRequest(
                    peer=self.current_dialog.entity,
                    action=types.SendMessageCancelAction()
                ))
            except Exception as e:
                print(f"Stop typing error: {e}")
                traceback.print_exc()

        if self.current_dialog:
            self.loop.create_task(stop_typing())

        self.input_mode = False
        self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')
        self.input_callback = None
        self.refresh_ui()

    def convert_key_for_layout(self, key):
        if isinstance(key, str) and len(key) == 1:
            layout = self.keyboard_layout
            if layout == 'ru' and key in REVERSE_LAYOUT_MAP['ru']:
                return REVERSE_LAYOUT_MAP['ru'][key]
        return key

    def handle_input_key(self, key):
        if key == 'enter':
            text = self.input_edit.get_edit_text()

            # Обработка плагинами перед отправкой
            plugin_results = execute_plugin_hook('process_message_before_send', text, self.current_dialog, self)
            for _, new_text in plugin_results:
                if new_text is not None:
                    text = new_text

            cb = self.input_callback
            self.hide_input()

            if cb:
                self.loop.create_task(cb(text))
            return True
        elif key == 'esc':
            self.hide_input()
            self.set_status("Input cancelled")
            return True
        return False

    async def send_message(self, text):
        if not text.strip() and not self.edit_message:
            self.set_status("Message is empty", 'error')
            return

        async def send_typing():
            try:
                await self.client(functions.messages.SetTypingRequest(
                    peer=self.current_dialog.entity,
                    action=types.SendMessageTypingAction()
                ))
                await asyncio.sleep(0.5)
            except:
                pass

        self.loop.create_task(send_typing())

        try:
            if self.reply_to_message:
                await self.client.send_message(
                    self.current_dialog.entity,
                    text,
                    reply_to=self.reply_to_message.id
                )
                self.reply_to_message = None
                self.reply_mode = False
                self.set_status("Reply sent", 'success')
            elif self.edit_message:
                await self.client.edit_message(self.current_dialog.entity, self.edit_message, text)
                self.edit_message = None
                self.edit_mode = False
                self.set_status("Message edited", 'success')
            else:
                await self.client.send_message(self.current_dialog.entity, text)
                self.set_status("Message sent", 'success')

            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=True)
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"Send message error: {e}")
            traceback.print_exc()

    async def send_file_with_caption(self, caption):
        if not self.file_to_send:
            self.set_status("No file selected", 'error')
            return

        async def send_typing():
            try:
                await self.client(functions.messages.SetTypingRequest(
                    peer=self.current_dialog.entity,
                    action=types.SendMessageTypingAction()
                ))
                await asyncio.sleep(0.5)
            except:
                pass

        self.loop.create_task(send_typing())

        try:
            file_size = os.path.getsize(self.file_to_send)

            mime_type, _ = mimetypes.guess_type(self.file_to_send)

            if mime_type and mime_type.startswith('image/'):
                self.set_status(f"Sending photo: {os.path.basename(self.file_to_send)}...", 'status')
                await self.client.send_file(self.current_dialog.entity, self.file_to_send, caption=caption)
            elif mime_type and mime_type.startswith('video/'):
                self.set_status(f"Sending video: {os.path.basename(self.file_to_send)}...", 'status')
                await self.client.send_file(self.current_dialog.entity, self.file_to_send, supports_streaming=True, caption=caption)
            else:
                self.set_status(f"Sending file: {os.path.basename(self.file_to_send)}...", 'status')
                await self.client.send_file(self.current_dialog.entity, self.file_to_send, caption=caption)

            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=True)
            self.set_status(f"File sent: {os.path.basename(self.file_to_send)}", 'success')
            self.file_to_send = None
            self.files_to_send = []

        except Exception as e:
            self.set_status(f"Error sending file: {e}", 'error')
            print(f"Send file error: {e}")
            traceback.print_exc()

    async def download_media(self, message):
        if not message or not message.media:
            self.set_status("No media in this message", 'error')
            return

        try:
            self.set_status("Downloading media...", 'status')

            os.makedirs(DOWNLOADS_DIR, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if message.photo:
                ext = ".jpg"
                file_type = "photo"
            elif message.video:
                ext = ".mp4"
                file_type = "video"
            elif message.document:
                if hasattr(message.document, 'attributes'):
                    for attr in message.document.attributes:
                        if isinstance(attr, types.DocumentAttributeFilename):
                            ext = os.path.splitext(attr.file_name)[1]
                            break
                    else:
                        ext = ".bin"
                else:
                    ext = ".bin"
                file_type = "document"
            elif message.voice:
                ext = ".ogg"
                file_type = "voice message"
            elif message.audio:
                ext = ".mp3"
                file_type = "audio"
            else:
                ext = ".bin"
                file_type = "media"

            filename = f"{file_type}_{timestamp}{ext}"
            file_path = os.path.join(DOWNLOADS_DIR, filename)

            await self.client.download_media(message.media, file_path)

            self.set_status(f"Downloaded: {filename}", 'success')

        except Exception as e:
            self.set_status(f"Download error: {e}", 'error')
            print(f"Download error: {e}")
            traceback.print_exc()

    async def delete_message(self, message):
        try:
            if not message.out:
                self.set_status("You can only delete your own messages", 'error')
                return

            await self.client(DeleteMessagesRequest(
                id=[message.id],
                revoke=True
            ))

            self.set_status("Message deleted", 'success')
            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=False)

        except Exception as e:
            self.set_status(f"Error deleting message: {e}", 'error')
            print(f"Delete message error: {e}")
            traceback.print_exc()

    async def send_reaction(self, message, reaction):
        try:
            await self.client(SendReactionRequest(
                peer=self.current_dialog.entity,
                msg_id=message.id,
                reaction=[types.ReactionEmoji(emoticon=reaction)]
            ))
            self.set_status(f"Reaction {reaction} sent", 'success')
            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=False)
        except Exception as e:
            self.set_status(f"Error sending reaction: {e}", 'error')
            print(f"Reaction error: {e}")
            traceback.print_exc()

    def show_reaction_picker(self, message):
        self.in_reaction_picker = True
        self.reaction_picker = ReactionPickerWidget(self, message)
        self.frame.body = self.reaction_picker
        self.refresh_ui()

    def close_reaction_picker(self):
        self.in_reaction_picker = False
        if self.view_mode == "dialogs":
            self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        elif self.view_mode == "topics":
            self.frame.body = urwid.AttrMap(self.topic_listbox, 'body')
        else:
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')
        self.refresh_ui()

    async def search_messages(self, query):
        if not query or not query.strip():
            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=False, focus_on_bottom=True)
            self.set_status("Search cleared", 'status')
            return

        try:
            search_results = await self.client.get_messages(
                self.current_dialog.entity,
                search=query.strip(),
                limit=config.get("interface", {}).get("messages_limit", 50)
            )

            if not search_results:
                self.set_status(f"No messages found for '{query}'", 'error')
                return

            self.messages = list(reversed(search_results))
            self.message_widgets = []

            messages_dict = {msg.id: msg for msg in self.messages}
            for msg in self.messages:
                msg.sender_name = await self.get_sender_name_async(msg)

                if hasattr(msg, 'reply_to') and msg.reply_to and hasattr(msg.reply_to, 'reply_to_msg_id'):
                    reply_id = msg.reply_to.reply_to_msg_id
                    if reply_id in messages_dict:
                        reply_msg = messages_dict[reply_id]
                        if reply_msg.text:
                            if len(reply_msg.text) > 40:
                                msg.reply_text = reply_msg.text[:37] + "..."
                            else:
                                msg.reply_text = reply_msg.text
                        else:
                            msg.reply_text = "[Media]"

            self.refresh_message_list()
            self.set_status(f"Found {len(self.messages)} messages for '{query}'", 'success')

            if self.messages:
                self.current_message_index = len(self.messages) - 1
                self.message_list.set_focus(self.current_message_index)
                self.refresh_message_list()

        except Exception as e:
            self.set_status(f"Search error: {e}", 'error')
            print(f"Search error: {e}")
            traceback.print_exc()

    async def search_contacts(self, query):
        if not query or not query.strip():
            self.set_status("Enter contact name to search", 'error')
            return

        try:
            from telethon.tl.functions.contacts import GetContactsRequest

            contacts_result = await self.client(GetContactsRequest(hash=0))
            contacts = contacts_result.users if hasattr(contacts_result, 'users') else []

            if not contacts:
                self.set_status("No contacts found", 'status')
                return

            filtered_contacts = []
            query_lower = query.strip().lower()

            for contact in contacts:
                if isinstance(contact, types.User):
                    name = (contact.first_name or "") + " " + (contact.last_name or "")
                    name = name.strip()
                    if query_lower in name.lower():
                        filtered_contacts.append(contact)

            if not filtered_contacts:
                self.set_status(f"No contacts found for '{query}'", 'error')
                return

            class TempDialog:
                pass

            temp_dialogs = []
            for contact in filtered_contacts:
                temp_dialog = TempDialog()
                temp_dialog.entity = contact
                temp_dialog.name = f"{contact.first_name} {contact.last_name or ''}".strip()
                temp_dialog.unread_count = 0
                temp_dialog.member_count = None
                temp_dialog.online_count = None
                temp_dialogs.append(temp_dialog)

            self.filtered_dialogs = temp_dialogs
            self.current_dialog_index = 0
            self.refresh_dialog_list()
            self.set_status(f"Found {len(temp_dialogs)} contacts", 'success')

        except Exception as e:
            self.set_status(f"Contact search error: {e}", 'error')
            print(f"Contact search error: {e}")
            traceback.print_exc()

    def show_search(self):
        self.in_search = True
        self.search_widget = SearchWidget(self)
        self.frame.body = self.search_widget
        self.refresh_ui()

    def close_search(self):
        self.in_search = False
        self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        self.refresh_ui()

    def show_file_browser(self):
        self.in_file_browser = True
        self.file_browser = FileBrowserWidget(self, self.send_file_with_caption)
        self.frame.body = self.file_browser
        self.refresh_ui()

    def close_file_browser(self):
        self.in_file_browser = False
        if self.view_mode == "dialogs":
            self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        elif self.view_mode == "topics":
            self.frame.body = urwid.AttrMap(self.topic_listbox, 'body')
        else:
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')
        self.refresh_ui()

    def handle_keypress(self, key):
        if not self.input_mode and isinstance(key, str) and len(key) == 1:
            key = self.convert_key_for_layout(key)

        if self.input_mode:
            if self.handle_input_key(key):
                return
            else:
                return

        if self.in_settings:
            if key == 'esc':
                self.close_settings()
            return

        if self.in_search:
            if key == 'esc':
                self.close_search()
                return
            return

        if self.in_file_browser:
            if key == 'esc':
                self.close_file_browser()
                self.set_status("File browser closed", 'status')
                return
            return

        if self.in_reaction_picker:
            if key == 'esc':
                self.close_reaction_picker()
                self.set_status("Reaction picker closed", 'status')
                return
            return

        if self.show_help:
            self.show_help = False
            if self.view_mode == "dialogs":
                self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
            elif self.view_mode == "topics":
                self.frame.body = urwid.AttrMap(self.topic_listbox, 'body')
            else:
                self.frame.body = urwid.AttrMap(self.message_listbox, 'body')
            self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')
            self.refresh_ui()
            return

        if key in ('q', 'Q'):
            self.exit_app()
            return

        if key in ('h', 'H'):
            if not self.show_help:
                self.show_help = True
                self.frame.body = self.help_widget
                self.refresh_ui()
                return

        if self.view_mode == "dialogs":
            if not self.filtered_dialogs:
                return

            if key == 'up' and self.current_dialog_index > 0:
                self.current_dialog_index -= 1
                self.refresh_dialog_list()
            elif key == 'down' and self.current_dialog_index < len(self.filtered_dialogs) - 1:
                self.current_dialog_index += 1
                self.refresh_dialog_list()
            elif key == 'enter':
                if self.filtered_dialogs:
                    self.select_dialog(self.current_dialog_index)
            elif key in ('s', 'S'):
                self.show_settings()
            elif key in ('c', 'C'):
                self.show_search()
            elif key in ('p', 'P'):
                self.show_input("Search contacts: ", self.search_contacts)
            elif key in ('l', 'L'):
                load_plugins()
                execute_plugin_hook('on_tui_init', self)
                self.set_status("Plugins reloaded", 'success')

        elif self.view_mode == "topics":
            if key == 'up' and self.current_topic_index > 0:
                self.current_topic_index -= 1
                self.refresh_topic_list()
            elif key == 'down' and self.current_topic_index < len(self.topics) - 1:
                self.current_topic_index += 1
                self.refresh_topic_list()
            elif key == 'enter':
                self.select_topic(self.current_topic_index)
            elif key == 'left':
                self.view_mode = "dialogs"
                self.current_topic_index = 0
                self.header.set_text("Dialogs")
                self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
                self.set_status("Back to dialogs")

        elif self.view_mode == "messages":
            if not self.messages:
                return

            if key == 'up' and self.current_message_index > 0:
                self.current_message_index -= 1
                self.refresh_message_list()
            elif key == 'down' and self.current_message_index < len(self.messages) - 1:
                self.current_message_index += 1
                self.refresh_message_list()
            elif key == 'left':
                if self.current_topic:
                    self.view_mode = "topics"
                    self.current_message_index = 0
                    self.header.set_text(f"Topics: {self.current_dialog.name}")
                    self.frame.body = urwid.AttrMap(self.topic_listbox, 'body')
                    self.set_status("Back to topics")
                else:
                    self.view_mode = "dialogs"
                    self.current_message_index = 0
                    self.header.set_text("Dialogs")
                    self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
                    self.set_status("Back to dialogs")
            elif key == 'enter':
                self.show_input("Message: ", self.send_message)
            elif key in ('r', 'R'):
                if self.messages and self.current_message_index < len(self.messages):
                    message = self.messages[self.current_message_index]
                    if not message.out:
                        self.reply_to_message = message
                        self.reply_mode = True
                        self.set_status(f"Replying to message from {self.get_sender_name(message)}", 'status')
                        self.show_input("Reply: ", self.send_message)
                    else:
                        self.set_status("You can't reply to your own messages", 'error')
            elif key in ('e', 'E'):
                if self.messages and self.current_message_index < len(self.messages):
                    message = self.messages[self.current_message_index]
                    if message.out:
                        self.edit_message = message
                        self.edit_mode = True
                        self.set_status(f"Editing message: {message.text[:50] if message.text else '[Media]'}", 'status')
                        self.show_input("Edit message: ", self.send_message)
                    else:
                        self.set_status("You can only edit your own messages", 'error')
            elif key == 'delete':
                if self.messages and self.current_message_index < len(self.messages):
                    message = self.messages[self.current_message_index]
                    self.loop.create_task(self.delete_message(message))
            elif key in ('s', 'S'):
                self.show_settings()
            elif key in ('/', '?'):
                self.show_input("Search messages: ", self.search_messages)
            elif key in ('d', 'D'):
                if self.messages and self.current_message_index < len(self.messages):
                    message = self.messages[self.current_message_index]
                    if message.media:
                        self.loop.create_task(self.download_media(message))
                    else:
                        self.set_status("No media in this message", 'error')
            elif key in ('f', 'F'):
                self.show_file_browser()
            elif key in ('t', 'T'):
                if self.messages and self.current_message_index < len(self.messages):
                    message = self.messages[self.current_message_index]
                    self.show_reaction_picker(message)
            elif key == 'esc':
                if self.reply_mode:
                    self.reply_mode = False
                    self.reply_to_message = None
                    self.set_status("Reply mode cancelled")
                elif self.edit_mode:
                    self.edit_mode = False
                    self.edit_message = None
                    self.set_status("Edit mode cancelled")

    def show_settings(self):
        self.in_settings = True
        self.settings_widget = SettingsWidget(self)
        self.frame.body = self.settings_widget
        self.refresh_ui()

    def close_settings(self):
        self.in_settings = False
        if self.view_mode == "dialogs":
            self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        elif self.view_mode == "topics":
            self.frame.body = urwid.AttrMap(self.topic_listbox, 'body')
        else:
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')
        self.refresh_ui()

    def apply_theme(self, theme_name):
        if theme_name in DEFAULT_THEMES:
            self.palette = DEFAULT_THEMES[theme_name]
            if self.urwid_loop:
                self.urwid_loop.screen.register_palette(self.palette)
                self.title.set_text(f"LinuxGram Beta")
                self.refresh_ui()

    def exit_app(self):
        if self.urwid_loop:
            try:
                self.urwid_loop.stop()
            except:
                pass

        if self.client and self.client.is_connected():
            async def disconnect():
                try:
                    await self.client.disconnect()
                except:
                    pass

            try:
                if self.loop and self.loop.is_running():
                    self.loop.run_until_complete(disconnect())
            except:
                pass

    async def handler_new_message(self, event):
        try:
            chat_id = None
            if hasattr(event.message.peer_id, 'channel_id'):
                chat_id = event.message.peer_id.channel_id
            elif hasattr(event.message.peer_id, 'chat_id'):
                chat_id = event.message.peer_id.chat_id
            elif hasattr(event.message.peer_id, 'user_id'):
                chat_id = event.message.peer_id.user_id

            if event.is_private and not event.message.out:
                if config.get("notifications", {}).get("private_chats", True):
                    sender = await event.get_sender()
                    sender_name = sender.first_name if sender else "Unknown"
                    self.set_status(f"New message from {sender_name}", 'success')

            if self.view_mode == "dialogs":
                self.loop.create_task(self.load_dialogs_async())
            elif self.view_mode == "messages" and self.current_dialog:
                try:
                    current_chat_id = None
                    if hasattr(self.current_dialog.entity, 'id'):
                        current_chat_id = self.current_dialog.entity.id

                    if chat_id == current_chat_id:
                        at_bottom = self.current_message_index == len(self.messages) - 1 if self.messages else True
                        await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=at_bottom)
                except:
                    pass
        except Exception as e:
            print(f"Error in new message handler: {e}")
            traceback.print_exc()

    async def handler_message_edited(self, event):
        try:
            chat_id = None
            if hasattr(event.message.peer_id, 'channel_id'):
                chat_id = event.message.peer_id.channel_id
            elif hasattr(event.message.peer_id, 'chat_id'):
                chat_id = event.message.peer_id.chat_id
            elif hasattr(event.message.peer_id, 'user_id'):
                chat_id = event.message.peer_id.user_id

            if self.view_mode == "messages" and self.current_dialog:
                try:
                    current_chat_id = None
                    if hasattr(self.current_dialog.entity, 'id'):
                        current_chat_id = self.current_dialog.entity.id

                    if chat_id == current_chat_id:
                        at_bottom = self.current_message_index == len(self.messages) - 1 if self.messages else True
                        await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=at_bottom)
                except:
                    pass
        except Exception as e:
            print(f"Error in edited message handler: {e}")
            traceback.print_exc()

    async def handler_message_deleted(self, event):
        try:
            chat_ids = []
            for chat_id in event.deleted_ids:
                chat_ids.append(chat_id)

            if self.view_mode == "messages" and self.current_dialog:
                try:
                    current_chat_id = None
                    if hasattr(self.current_dialog.entity, 'id'):
                        current_chat_id = self.current_dialog.entity.id

                    if current_chat_id in chat_ids:
                        at_bottom = self.current_message_index == len(self.messages) - 1 if self.messages else True
                        await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=at_bottom)
                except:
                    pass
        except Exception as e:
            print(f"Error in deleted message handler: {e}")
            traceback.print_exc()

def main():
    global config
    config = load_config()

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    tui = LinuxGramTUI()

    try:
        tui.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        tui.exit_app()

if __name__ == '__main__':
    main()
