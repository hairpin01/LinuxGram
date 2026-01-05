#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
# beta is linuxgram!  #
#######################
__version__ = '1.0.023'
import asyncio
import os
import json
import sys
import importlib.util
import mimetypes
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient, events, functions, errors
from telethon.tl import types
import urwid

SESSION_FILE = 'linuxgram.session'
DOWNLOADS_DIR = "downloads"
CONFIG_FILE = "config.json"
CREDENTIALS_FILE = "credentials.json"
PLUGINS_DIR = "plugins"

client = None
config = {}
loaded_plugins = []
plugin_handlers = {}

def load_config():
    default_config = {
        "privacy": {"last_seen": "everybody", "read_receipts": True},
        "notifications": {"private_chats": True, "groups": True, "channels": False},
        "data": {"auto_download": {"photos": True, "videos": False, "files": False, "voice_messages": True}},
        "language": "English",
        "interface": {"dialogs_limit": 100, "messages_limit": 50, "show_avatars": False}
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
                    plugin_handlers[plugin_name] = plugin_module.register_hooks()
                    print(f"✓ Plugin loaded: {plugin_info['name']} v{plugin_info['version']} by {plugin_info['author']}")
                else:
                    print(f"⚠ Plugin {plugin_name} has no register_hooks() function")

                loaded_plugins.append(plugin_info)

            except Exception as e:
                print(f"✗ Error loading plugin {file}: {e}")

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
    def __init__(self, message, is_selected=False, is_outgoing=False, reply_text="", sender_name=""):
        self.message = message
        self.is_selected = is_selected
        self.is_outgoing = is_outgoing
        self.reply_text = reply_text
        self.sender_name = sender_name

        self.text_widget = urwid.Text("")
        super().__init__(self.build_widget())

    def build_widget(self):
        time_str = self.message.date.strftime("%H:%M")

        if self.sender_name:
            sender_display = f"{self.sender_name}"
        else:
            sender_display = ""

        if self.message.text:
            content = self.message.text
        elif self.message.media:
            if self.message.photo:
                content = "📷 Photo"
            elif self.message.video:
                content = "🎥 Video"
            elif self.message.voice:
                content = "🎤 Voice message"
            elif self.message.document:
                content = "📄 Document"
            elif self.message.audio:
                content = "🎵 Audio"
            elif self.message.sticker:
                content = "😀 Sticker"
            else:
                content = "[Media]"
        else:
            content = "[Empty]"

        if len(content) > 60:
            content = content[:57] + "..."

        reply_indicator = ""
        if self.reply_text:
            if len(self.reply_text) > 20:
                preview = self.reply_text[:17] + "..."
            else:
                preview = self.reply_text
            reply_indicator = f" [↩ {preview}]"

        if self.is_selected:
            prefix = "> "
        else:
            prefix = "  "

        line = f"{prefix}[{time_str}] {sender_display}: {content}{reply_indicator}"

        self.text_widget.set_text(line)

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
        else:
            self.parent.filtered_dialogs = [
                dialog for dialog in self.parent.dialogs
                if dialog.name and query.lower() in dialog.name.lower()
            ]
            self.parent.set_status(f"Found {len(self.parent.filtered_dialogs)} dialogs", 'success')

        self.parent.current_dialog_index = 0
        self.parent.refresh_dialog_list()
        self.parent.close_search()

    def cancel_search(self, button):
        self.parent.filtered_dialogs = self.parent.dialogs.copy()
        self.parent.current_dialog_index = 0
        self.parent.refresh_dialog_list()
        self.parent.set_status("Search cancelled", 'status')
        self.parent.close_search()

class FileBrowserWidget(urwid.WidgetWrap):
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.current_dir = Path.home()
        self.selected_file = None

        self.header = urwid.Text("Select file to send")
        self.path_display = urwid.Text(str(self.current_dir))

        self.select_button = urwid.Button("Select")
        self.cancel_button = urwid.Button("Cancel")

        urwid.connect_signal(self.select_button, 'click', self.select_file)
        urwid.connect_signal(self.cancel_button, 'click', self.cancel)

        self.file_list = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.file_list)

        content = urwid.Pile([
            urwid.AttrMap(self.header, 'header'),
            urwid.AttrMap(self.path_display, 'title'),
            urwid.Divider(),
            urwid.AttrMap(self.listbox, 'body'),
            urwid.Divider(),
            urwid.Columns([
                ('weight', 1, urwid.AttrMap(self.select_button, 'button')),
                ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
            ])
        ])

        super().__init__(urwid.Filler(content, 'top'))
        self.load_directory()

    def load_directory(self):
        self.file_list.clear()

        if self.current_dir.parent != self.current_dir:
            item = urwid.Button(".. (Parent directory)")
            urwid.connect_signal(item, 'click', self.go_up)
            self.file_list.append(urwid.AttrMap(item, 'dialog_name'))

        try:
            for item in sorted(self.current_dir.iterdir()):
                if item.is_dir():
                    name = f"📁 {item.name}/"
                    button = urwid.Button(name)
                    urwid.connect_signal(button, 'click', self.enter_directory, item)
                else:
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
                    urwid.connect_signal(button, 'click', self.select_item, item)

                self.file_list.append(urwid.AttrMap(button, 'dialog_name'))

        except Exception as e:
            self.file_list.append(urwid.Text(f"Error: {e}", align='center'))

    def go_up(self, button):
        self.current_dir = self.current_dir.parent
        self.path_display.set_text(str(self.current_dir))
        self.load_directory()

    def enter_directory(self, button, directory):
        self.current_dir = directory
        self.path_display.set_text(str(self.current_dir))
        self.load_directory()

    def select_item(self, button, file_path):
        self.selected_file = file_path
        for i, item in enumerate(self.file_list):
            if item.original_widget == button:
                self.listbox.set_focus(i)
                break

    def select_file(self, button):
        if self.selected_file:
            self.callback(str(self.selected_file))
            self.parent.close_file_browser()
        else:
            self.parent.set_status("Please select a file first", 'error')

    def cancel(self, button):
        self.parent.close_file_browser()

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
            "Press any key to close"
        ]

        content = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text(line), 'dialog_name') for line in help_text
        ]))

        super().__init__(content)

class LinuxGramTUI:
    def __init__(self):
        self.palette = [
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
        ]

        self.dialogs = []
        self.filtered_dialogs = []
        self.messages = []
        self.message_widgets = []
        self.current_dialog_index = 0
        self.current_message_index = 0
        self.current_dialog = None
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
        self.show_help = False
        self.member_count = None
        self.online_count = None
        self.dialogs_loaded = False

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

        self.title = urwid.Text(f"LinuxGram Beta v{__version__}", align='center')
        self.header = urwid.Text("Dialogs")

        self.footer_help_text = "Enter... | H: help | L: reload plugins"
        self.footer_help = urwid.Text(self.footer_help_text)

        self.footer_status = urwid.Text("")
        self.footer_status_am = urwid.AttrMap(self.footer_status, 'footer')

        self.full_help_text = (
            "Q: Quit | ↑↓: Select | Enter: Open | ←: Back | R: Reply | "
            "F: File | D: Download | /: Search | S: Settings | C: Search | E: Edit | L: Plugins"
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

        self.message_list = urwid.SimpleFocusListWalker([])
        self.message_listbox = urwid.ListBox(self.message_list)

        self.input_edit = urwid.Edit("")
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

    def setup_ui(self):
        self.urwid_loop = urwid.MainLoop(
            self.frame,
            self.palette,
            unhandled_input=self.handle_keypress,
            event_loop=urwid.AsyncioEventLoop(loop=self.loop),
            handle_mouse=True
        )

    def start(self):
        load_plugins()

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
            self.exit_app()

    def show_login_screen(self):
        self.login_widget = LoginWidget(self)
        self.frame.body = self.login_widget
        self.header.set_text("Login to Telegram")

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

            self.loop.create_task(self.load_dialogs_async())

        except Exception as e:
            print(f"Client init error: {e}")
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

    async def load_messages(self, dialog):
        try:
            self.current_dialog = dialog
            limit = config.get("interface", {}).get("messages_limit", 50)

            self.set_status("Loading messages...", 'status')
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

            self.refresh_message_list()

            self.view_mode = "messages"

            header_text = f"Chat: {dialog.name}"
            if hasattr(dialog, 'member_count') and dialog.member_count:
                if hasattr(dialog, 'online_count') and dialog.online_count:
                    header_text += f" ({dialog.online_count}/{dialog.member_count})"
                else:
                    header_text += f" ({dialog.member_count})"

            self.header.set_text(header_text)
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')

            self.set_status(f"Loaded {len(self.messages)} messages", 'success')

            if self.messages:
                self.current_message_index = len(self.messages) - 1
                self.message_list.set_focus(self.current_message_index)
                self.refresh_message_list()

        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"Messages error: {e}")

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
            return

        self.current_dialog_index = index
        self.refresh_dialog_list()

        self.loop.create_task(self.load_messages(dialog))

    def refresh_dialog_list(self):
        self.dialog_list.clear()

        if not self.filtered_dialogs:
            self.dialog_list.append(urwid.Text("No dialogs found", align='center'))
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

        if self.filtered_dialogs:
            self.dialog_list.set_focus(self.current_dialog_index)

    def refresh_message_list(self):
        self.message_list.clear()
        self.message_widgets.clear()

        if not self.messages:
            self.message_list.append(urwid.Text("No messages", align='center'))
            return

        for i, msg in enumerate(self.messages):
            reply_text = getattr(msg, 'reply_text', "")
            sender_name = self.get_sender_name(msg)

            widget = MessageWidget(
                msg,
                is_selected=(i == self.current_message_index),
                is_outgoing=msg.out,
                reply_text=reply_text,
                sender_name=sender_name
            )
            self.message_list.append(widget)
            self.message_widgets.append(widget)

        if self.messages:
            self.message_list.set_focus(self.current_message_index)

    def set_status(self, text, style="status"):
        self.footer_status.set_text(f" {text} ")
        if style == 'error':
            self.footer_status_am.set_attr_map({None: 'error'})
        elif style == 'success':
            self.footer_status_am.set_attr_map({None: 'success'})
        else:
            self.footer_status_am.set_attr_map({None: style if style else 'footer'})

    def show_input(self, prompt, callback):
        self.input_mode = True
        self.input_prompt = prompt
        self.input_callback = callback
        self.input_edit.set_caption(prompt)
        self.input_edit.set_edit_text("")
        self.frame.footer = self.input_widget

    def hide_input(self):
        self.input_mode = False
        self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')
        self.input_callback = None

    def handle_input_key(self, key):
        if key == 'enter':
            text = self.input_edit.get_edit_text()
            cb = self.input_callback
            self.hide_input()

            if cb:
                self.loop.create_task(cb(text))

        elif key == 'esc':
            self.hide_input()
            self.set_status("Input cancelled")

    async def send_message(self, text):
        if not text.strip():
            self.set_status("Message is empty", 'error')
            return

        try:
            if self.reply_to_message:
                await self.client.send_message(self.current_dialog.entity, text, reply_to=self.reply_to_message.id)
                self.reply_to_message = None
                self.reply_mode = False
            elif self.edit_message:
                await self.client.edit_message(self.current_dialog.entity, self.edit_message, text)
                self.edit_message = None
                self.edit_mode = False
                self.set_status("Message edited", 'success')
            else:
                await self.client.send_message(self.current_dialog.entity, text)

            await self.load_messages(self.current_dialog)
            if not self.edit_message:
                self.set_status("Message sent", 'success')
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')
            print(f"Send message error: {e}")

    async def send_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            self.set_status(f"File not found: {file_path}", 'error')
            return

        try:
            file_size = os.path.getsize(file_path)

            mime_type, _ = mimetypes.guess_type(file_path)

            if mime_type and mime_type.startswith('image/'):
                self.set_status(f"Sending photo: {os.path.basename(file_path)}...", 'status')
                await self.client.send_file(self.current_dialog.entity, file_path, caption="")
            elif mime_type and mime_type.startswith('video/'):
                self.set_status(f"Sending video: {os.path.basename(file_path)}...", 'status')
                await self.client.send_file(self.current_dialog.entity, file_path, supports_streaming=True)
            else:
                self.set_status(f"Sending file: {os.path.basename(file_path)}...", 'status')
                await self.client.send_file(self.current_dialog.entity, file_path)

            await self.load_messages(self.current_dialog)
            self.set_status(f"File sent: {os.path.basename(file_path)}", 'success')

        except Exception as e:
            self.set_status(f"Error sending file: {e}", 'error')
            print(f"Send file error: {e}")

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

    async def search_messages(self, query):
        if not query or not query.strip():
            await self.load_messages(self.current_dialog)
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

    async def search_contacts(self, query):
        if not query or not query.strip():
            self.set_status("Enter contact name to search", 'error')
            return

        try:
            contacts = await self.client.get_contacts()
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

    def show_search(self):
        self.in_search = True
        self.search_widget = SearchWidget(self)
        self.frame.body = self.search_widget

    def close_search(self):
        self.in_search = False
        self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')

    def show_file_browser(self):
        self.in_file_browser = True
        self.file_browser = FileBrowserWidget(self, self.send_file)
        self.frame.body = self.file_browser

    def close_file_browser(self):
        self.in_file_browser = False
        if self.view_mode == "dialogs":
            self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        else:
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')

    def handle_keypress(self, key):
        if isinstance(key, tuple):
            event, button, col, row = key
            if event == 'mouse press':
                if button == 4:
                    if self.view_mode == "dialogs":
                        if self.current_dialog_index > 0:
                            self.current_dialog_index -= 1
                            self.refresh_dialog_list()
                    elif self.view_mode == "messages":
                        if self.current_message_index > 0:
                            self.current_message_index -= 1
                            self.refresh_message_list()
                    return
                elif button == 5:
                    if self.view_mode == "dialogs":
                        if self.current_dialog_index < len(self.filtered_dialogs) - 1:
                            self.current_dialog_index += 1
                            self.refresh_dialog_list()
                    elif self.view_mode == "messages":
                        if self.current_message_index < len(self.messages) - 1:
                            self.current_message_index += 1
                            self.refresh_message_list()
                    return

        if self.input_mode:
            self.handle_input_key(key)
            return

        if self.in_settings:
            if key == 'esc':
                self.close_settings()
            return

        if self.in_search:
            if key == 'esc':
                self.search_widget.cancel_search(None)
            return

        if self.in_file_browser:
            if key == 'esc':
                self.close_file_browser()
                self.set_status("File browser closed", 'status')
            return

        if self.show_help:
            self.show_help = False
            if self.view_mode == "dialogs":
                self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
            else:
                self.frame.body = urwid.AttrMap(self.message_listbox, 'body')
            self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')
            return

        if key in ('q', 'Q'):
            self.exit_app()

        if key in ('h', 'H'):
            if not self.show_help:
                self.show_help = True
                self.frame.body = self.help_widget
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
            elif key == 's' or key == 'S':
                self.show_settings()
            elif key == 'c' or key == 'C':
                self.show_search()
            elif key == 'p' or key == 'P':
                self.show_input("Search contacts: ", self.search_contacts)
            elif key == 'l' or key == 'L':
                load_plugins()
                self.set_status("Plugins reloaded", 'success')

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
                self.view_mode = "dialogs"
                self.current_message_index = 0
                self.header.set_text("Dialogs")
                self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
                self.set_status("Back to dialogs")
            elif key == 'enter':
                self.show_input("Message: ", self.send_message)
            elif key == 'r' or key == 'R':
                if self.messages:
                    self.reply_mode = True
                    self.set_status("Select message to reply (use arrows, press Enter to select)")
            elif key == 's' or key == 'S':
                self.show_settings()
            elif key == '/' or key == '?':
                self.show_input("Search messages: ", self.search_messages)
            elif key == 'd' or key == 'D':
                if self.messages and self.current_message_index < len(self.messages):
                    message = self.messages[self.current_message_index]
                    if message.media:
                        self.loop.create_task(self.download_media(message))
                    else:
                        self.set_status("No media in this message", 'error')
            elif key == 'f' or key == 'F':
                self.show_file_browser()
            elif key == 'esc':
                if self.reply_mode:
                    self.reply_mode = False
                    self.set_status("Reply mode cancelled")

    def show_settings(self):
        self.in_settings = True
        self.settings_widget = SettingsWidget(self)
        self.frame.body = self.settings_widget

    def close_settings(self):
        self.in_settings = False
        if self.view_mode == "dialogs":
            self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        else:
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')

    def exit_app(self):
        if self.urwid_loop:
            raise urwid.ExitMainLoop()

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
            if event.is_private and not event.message.out:
                if config.get("notifications", {}).get("private_chats", True):
                    sender = await event.get_sender()
                    sender_name = sender.first_name if sender else "Unknown"
                    self.set_status(f"New message from {sender_name}", 'success')

                    if self.view_mode == "dialogs":
                        self.loop.create_task(self.load_dialogs_async())
                    elif self.view_mode == "messages" and self.current_dialog:
                        try:
                            if event.chat_id == self.current_dialog.entity.id:
                                await self.load_messages(self.current_dialog)
                        except:
                            pass
        except Exception as e:
            print(f"Error in new message handler: {e}")

    async def handler_message_edited(self, event):
        try:
            if self.view_mode == "messages" and self.current_dialog:
                if event.chat_id == self.current_dialog.entity.id:
                    await self.load_messages(self.current_dialog)
        except:
            pass

    async def handler_message_deleted(self, event):
        try:
            if self.view_mode == "messages" and self.current_dialog:
                if event.chat_id == self.current_dialog.entity.id:
                    await self.load_messages(self.current_dialog)
        except:
            pass

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
