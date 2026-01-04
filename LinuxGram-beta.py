#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
# beta is linuxgram!  #
#######################
__version__ = '1.0.013'
import asyncio
import os
import json
import re
import sys
import importlib.util
from datetime import datetime
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
    """Загружает учетные данные из файла"""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_credentials(api_id, api_hash, phone=None):
    """Сохраняет учетные данные в файл"""
    creds = {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone
    }
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds, f, indent=2)

def load_plugins():
    """Улучшенная система загрузки плагинов"""
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

                # Регистрация хуков
                if hasattr(plugin_module, 'register_hooks'):
                    plugin_handlers[plugin_name] = plugin_module.register_hooks()
                    print(f"✓ Plugin loaded: {plugin_info['name']} v{plugin_info['version']} by {plugin_info['author']}")
                else:
                    print(f"⚠ Plugin {plugin_name} has no register_hooks() function")

                loaded_plugins.append(plugin_info)

            except Exception as e:
                print(f"✗ Error loading plugin {file}: {e}")

def execute_plugin_hook(hook_name, *args, **kwargs):
    """Выполнение хука во всех плагинах"""
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
    """Виджет для входа в систему"""
    def __init__(self, parent):
        self.parent = parent
        self.step = 1  # 1: API, 2: Номер, 3: Код, 4: Пароль 2FA, 5: QR
        self.credentials = load_credentials()

        self.api_id_edit = urwid.Edit("API ID: ", "")
        self.api_hash_edit = urwid.Edit("API Hash: ", "")
        self.phone_edit = urwid.Edit("Phone (e.g. +1234567890): ", "")
        self.code_edit = urwid.Edit("Code: ", "")
        self.password_edit = urwid.Edit("2FA Password: ", "")

        self.next_button = urwid.Button("Next")
        urwid.connect_signal(self.next_button, 'click', self.next_step)

        self.qr_button = urwid.Button("Login with QR")
        urwid.connect_signal(self.qr_button, 'click', self.login_with_qr)

        self.cancel_button = urwid.Button("Cancel")
        urwid.connect_signal(self.cancel_button, 'click', self.cancel)

        self.content = urwid.Pile([])
        self.update_content()

        super().__init__(urwid.Filler(self.content, 'top'))

    def update_content(self):
        self.content.contents.clear()

        if self.step == 1:
            if self.credentials:
                self.api_id_edit.set_edit_text(str(self.credentials.get('api_id', '')))
                self.api_hash_edit.set_edit_text(self.credentials.get('api_hash', ''))

            self.content.contents.extend([
                (urwid.Text("Login to Telegram", align='center'), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Text("Step 1: Enter API credentials", align='left'), ('pack', None)),
                (urwid.Text("Get API ID and Hash from https://my.telegram.org"), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (self.api_id_edit, ('pack', None)),
                (self.api_hash_edit, ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.qr_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ]), ('pack', None))
            ])

        elif self.step == 2:
            if self.credentials and self.credentials.get('phone'):
                self.phone_edit.set_edit_text(self.credentials['phone'])

            self.content.contents.extend([
                (urwid.Text("Login to Telegram", align='center'), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Text("Step 2: Enter phone number", align='left'), ('pack', None)),
                (self.phone_edit, ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ]), ('pack', None))
            ])

        elif self.step == 3:
            self.content.contents.extend([
                (urwid.Text("Login to Telegram", align='center'), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Text("Step 3: Enter code", align='left'), ('pack', None)),
                (urwid.Text("Code sent to your phone"), ('pack', None)),
                (self.code_edit, ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ]), ('pack', None))
            ])

        elif self.step == 4:
            self.content.contents.extend([
                (urwid.Text("Login to Telegram", align='center'), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Text("Step 4: Enter 2FA password", align='left'), ('pack', None)),
                (self.password_edit, ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ]), ('pack', None))
            ])

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

        elif self.step == 2:
            phone = self.phone_edit.get_edit_text().strip()
            if not phone:
                self.parent.set_status("Please enter phone number", 'error')
                return

            save_credentials(self.parent.api_id, self.parent.api_hash, phone)
            self.parent.phone = phone
            self.parent.loop.create_task(self.parent.start_login())
            return

        elif self.step == 3:
            code = self.code_edit.get_edit_text().strip()
            if not code:
                self.parent.set_status("Please enter code", 'error')
                return

            self.parent.login_code = code
            self.parent.loop.create_task(self.parent.continue_login())
            return

        elif self.step == 4:
            password = self.password_edit.get_edit_text().strip()
            if not password:
                self.parent.set_status("Please enter password", 'error')
                return

            self.parent.login_password = password
            self.parent.loop.create_task(self.parent.continue_login())
            return

        self.update_content()
        self.parent.urwid_loop.draw_screen()

    def login_with_qr(self, button):
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
        self.parent.loop.create_task(self.parent.login_with_qr())

    def cancel(self, button):
        self.parent.exit_app()

class MessageWidget(urwid.WidgetWrap):
    def __init__(self, message, is_selected=False, is_outgoing=False, reply_text="", sender_name=""):
        self.message = message
        self.is_selected = is_selected
        self.is_outgoing = is_outgoing
        self.reply_text = reply_text
        self.sender_name = sender_name
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

        widget = urwid.Text(line)

        if self.is_selected:
            widget = urwid.AttrMap(widget, 'selected')

        return widget

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

        if self.is_selected:
            wrapped_button = urwid.AttrMap(self.button, 'selected')
        else:
            wrapped_button = urwid.AttrMap(self.button, 'dialog_name')

        urwid.connect_signal(self.button, 'click', self.on_click)
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
        execute_plugin_hook('config_saved', config)
        self.parent.close_settings()

    def cancel_settings(self, button):
        self.parent.close_settings()

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
            "Press any key to close"
        ]

        content = urwid.ListBox(urwid.SimpleListWalker([
            urwid.AttrMap(urwid.Text(line), 'dialog_name') for line in help_text
        ]))

        super().__init__(content)

class LinuxGramTUI:
    def __init__(self, loop):
        self.loop = loop
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
        self.show_help = False
        self.member_count = None
        self.online_count = None
        self.dialogs_loaded = False

        # Атрибуты для входа
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.login_code = None
        self.login_password = None
        self.qr_login = False
        self.need_password = False
        self.logged_in = False
        self.login_widget = None

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

        self._status_handle = None

        self.dialog_list = urwid.SimpleListWalker([])
        self.dialog_listbox = urwid.ListBox(self.dialog_list)

        self.message_list = urwid.SimpleListWalker([])
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

    def run(self):
        load_plugins()
        execute_plugin_hook('init', self)

        # Проверяем наличие сессии
        if not os.path.exists(SESSION_FILE):
            self.show_login_screen()
        else:
            self.urwid_loop = urwid.MainLoop(
                self.frame,
                self.palette,
                unhandled_input=self.handle_keypress,
                event_loop=urwid.AsyncioEventLoop(loop=self.loop),
                handle_mouse=True
            )
            self.loop.create_task(self.start_client())
            self.urwid_loop.run()

    def show_login_screen(self):
        """Показать экран входа"""
        self.login_widget = LoginWidget(self)
        self.frame.body = self.login_widget
        self.header.set_text("Login to Telegram")
        self.frame.footer = urwid.AttrMap(urwid.Text("Press Ctrl+Q to exit"), 'footer')

        self.urwid_loop = urwid.MainLoop(
            self.frame,
            self.palette,
            unhandled_input=self.handle_login_keypress,
            event_loop=urwid.AsyncioEventLoop(loop=self.loop),
            handle_mouse=True
        )
        self.urwid_loop.run()

    async def start_login(self):
        """Начать процесс входа"""
        try:
            global client
            client = TelegramClient(SESSION_FILE, self.api_id, self.api_hash)

            if not self.qr_login:
                await client.connect()
                sent_code = await client.send_code_request(self.phone)
                self.set_status("Code sent to your phone. Enter it above.", 'success')
                self.login_widget.step = 3
                self.login_widget.update_content()
                self.urwid_loop.draw_screen()
            else:
                await client.connect()
                await client.sign_in(self.phone)
                qr_login = await client.qr_login()
                self.set_status("Scan QR code with Telegram app", 'success')
                await qr_login.wait()
                await client.start()
                self.login_successful()

        except errors.PhoneNumberInvalidError:
            self.set_status("Invalid phone number", 'error')
        except errors.PhoneCodeInvalidError:
            self.set_status("Invalid code", 'error')
        except errors.SessionPasswordNeededError:
            self.need_password = True
            self.login_widget.step = 4
            self.login_widget.update_content()
            self.set_status("2FA password required", 'success')
            self.urwid_loop.draw_screen()
        except Exception as e:
            self.set_status(f"Login error: {e}", 'error')

    async def continue_login(self):
        """Продолжить вход после получения кода/пароля"""
        try:
            if self.need_password:
                await client.sign_in(password=self.login_password)
            else:
                await client.sign_in(self.phone, self.login_code)

            await client.start()
            self.login_successful()

        except errors.PhoneCodeInvalidError:
            self.set_status("Invalid code", 'error')
        except errors.PasswordHashInvalidError:
            self.set_status("Invalid password", 'error')
        except Exception as e:
            self.set_status(f"Login error: {e}", 'error')

    async def login_with_qr(self):
        """Вход через QR-код"""
        self.qr_login = True
        await self.start_login()

    def login_successful(self):
        """Успешный вход"""
        self.logged_in = True
        self.set_status("Login successful! Loading dialogs...", 'success')

        # Переключаемся на основной интерфейс
        self.urwid_loop.widget = self.frame
        self.urwid_loop.unhandled_input = self.handle_keypress
        self.header.set_text("Dialogs")
        self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')

        # Запускаем клиент
        self.loop.create_task(self.start_client())

        self.urwid_loop.draw_screen()

    async def start_client(self):
        global client

        # Если клиент еще не создан (при обычном входе)
        if client is None:
            creds = load_credentials()
            if not creds:
                self.set_status("No credentials found. Please login.", 'error')
                return

            self.api_id = creds.get('api_id')
            self.api_hash = creds.get('api_hash')
            client = TelegramClient(SESSION_FILE, self.api_id, self.api_hash)

        try:
            if not client.is_connected():
                await client.connect()

            if not await client.is_user_authorized():
                self.set_status("Not authorized. Please login again.", 'error')
                self.show_login_screen()
                return

            execute_plugin_hook('client_started', client)

            client.add_event_handler(self.handler_new_message, events.NewMessage)
            client.add_event_handler(self.handler_message_edited, events.MessageEdited)
            client.add_event_handler(self.handler_message_deleted, events.MessageDeleted)

            # Загружаем диалоги
            await self.load_dialogs()

        except Exception as e:
            self.set_status(f"Connection error: {e}", 'error')
            # Если ошибка авторизации, показываем экран входа
            if "auth" in str(e).lower() or "401" in str(e):
                self.show_login_screen()

    async def load_dialogs(self):
        try:
            if not client or not client.is_connected():
                self.set_status("Waiting for connection...", 'status')
                return

            limit = config.get("interface", {}).get("dialogs_limit", 100)
            self.dialogs = await client.get_dialogs(limit=limit)
            self.filtered_dialogs = self.dialogs.copy()

            # Параллельная загрузка информации о чатах
            tasks = []
            for dialog in self.dialogs:
                if isinstance(dialog.entity, (types.Channel, types.Chat)):
                    tasks.append(self.load_chat_info(dialog))
                else:
                    # Для личных диалогов устанавливаем None
                    dialog.member_count = None
                    dialog.online_count = None

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.refresh_dialog_list()
            self.dialogs_loaded = True
            self.set_status(f"Loaded {len(self.dialogs)} dialogs", 'success')
            execute_plugin_hook('dialogs_loaded', self.dialogs)
        except Exception as e:
            self.set_status(f"Error loading dialogs: {e}", 'error')
            # Пробуем снова через 5 секунд
            await asyncio.sleep(5)
            self.loop.create_task(self.load_dialogs())

    async def load_chat_info(self, dialog):
        """Асинхронная загрузка информации о чате"""
        try:
            if isinstance(dialog.entity, types.Channel):
                full_chat = await client(functions.channels.GetFullChannelRequest(channel=dialog.entity))
            elif isinstance(dialog.entity, types.Chat):
                full_chat = await client(functions.messages.GetFullChatRequest(chat_id=dialog.entity.id))
            else:
                return

            dialog.member_count = getattr(full_chat.full_chat, 'participants_count', 0)
            dialog.online_count = getattr(full_chat.full_chat, 'online_count', 0)
        except Exception as e:
            dialog.member_count = 0
            dialog.online_count = 0

    async def load_messages(self, dialog):
        try:
            self.current_dialog = dialog
            limit = config.get("interface", {}).get("messages_limit", 50)

            self.messages = await client.get_messages(dialog.entity, limit=limit)
            self.messages.reverse()
            self.message_widgets = []

            messages_dict = {msg.id: msg for msg in self.messages}
            for msg in self.messages:
                msg.sender_name = await self.get_sender_name(msg)

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
            execute_plugin_hook('messages_loaded', dialog, self.messages)

            if self.messages:
                self.message_listbox.focus_position = len(self.messages) - 1
                self.current_message_index = len(self.messages) - 1
                self.refresh_message_list()

        except Exception as e:
            self.set_status(f"Error: {e}", 'error')

    async def get_sender_name(self, msg):
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

    def select_dialog(self, index):
        if not self.filtered_dialogs or index >= len(self.filtered_dialogs):
            return

        self.current_dialog_index = index
        self.refresh_dialog_list()
        self.loop.create_task(self.load_messages(self.filtered_dialogs[index]))

    def clear_status(self):
        self.footer_status.set_text("")
        self.footer_status_am.set_attr_map({None: 'footer'})
        if self.urwid_loop:
            self.urwid_loop.draw_screen()

    def set_status(self, text, style="status", timeout=3):
        self.footer_status.set_text(f" {text} ")
        if style == 'error':
            self.footer_status_am.set_attr_map({None: 'error'})
        elif style == 'success':
            self.footer_status_am.set_attr_map({None: 'success'})
        else:
            self.footer_status_am.set_attr_map({None: style if style else 'footer'})

        if self._status_handle:
            self._status_handle.cancel()
            self._status_handle = None

        if timeout and self.loop:
            self._status_handle = self.loop.call_later(timeout, self.clear_status)

        if self.urwid_loop:
            self.urwid_loop.draw_screen()

    def show_input(self, prompt, callback):
        self.input_mode = True
        self.input_prompt = prompt
        self.input_callback = callback
        self.input_edit.set_caption(prompt)
        self.input_edit.set_edit_text("")
        self.frame.footer = self.input_widget
        self.urwid_loop.draw_screen()

    def hide_input(self):
        self.input_mode = False
        self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')
        self.input_callback = None
        self.urwid_loop.draw_screen()

    async def send_message(self, text):
        if not text.strip():
            self.set_status("Message is empty", 'error')
            return

        # Проверяем, является ли текст командой плагина
        if text.startswith('/'):
            command = text[1:].split()[0] if ' ' in text else text[1:]
            args = text.split()[1:] if ' ' in text else []

            # Ищем команду в плагинах
            for result in execute_plugin_hook('command', command, args, self):
                if result:
                    return

            # Глобальные команды плагинов
            if '_global' in plugin_handlers and 'commands' in plugin_handlers['_global']:
                if command in plugin_handlers['_global']['commands']:
                    handler = plugin_handlers['_global']['commands'][command]
                    try:
                        await handler(args, self) if asyncio.iscoroutinefunction(handler) else handler(args, self)
                        return
                    except Exception as e:
                        self.set_status(f"Command error: {e}", 'error')
                        return

        try:
            if self.reply_to_message:
                await client.send_message(self.current_dialog.entity, text, reply_to=self.reply_to_message.id)
                self.reply_to_message = None
                self.reply_mode = False
            elif self.edit_message:
                await client.edit_message(self.current_dialog.entity, self.edit_message, text)
                self.edit_message = None
                self.edit_mode = False
                self.set_status("Message edited", 'success')
            else:
                await client.send_message(self.current_dialog.entity, text)

            await self.load_messages(self.current_dialog)
            if not self.edit_message:
                self.set_status("Message sent", 'success')

            execute_plugin_hook('message_sent', self.current_dialog.entity, text)

        except Exception as e:
            self.set_status(f"Error: {e}", 'error')

    async def send_file(self, file_path):
        if not os.path.exists(file_path):
            self.set_status("File not found", 'error')
            return

        try:
            if self.reply_to_message:
                await client.send_file(self.current_dialog.entity, file_path, reply_to=self.reply_to_message.id)
                self.reply_to_message = None
                self.reply_mode = False
            elif self.edit_message:
                self.set_status("Cannot edit message with file", 'error')
                return
            else:
                await client.send_file(self.current_dialog.entity, file_path)

            await self.load_messages(self.current_dialog)
            self.set_status("File sent", 'success')
            execute_plugin_hook('file_sent', self.current_dialog.entity, file_path)
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')

    async def download_media(self):
        if not self.messages or self.current_message_index >= len(self.messages):
            self.set_status("No message selected", 'error')
            return

        msg = self.messages[self.current_message_index]
        if not msg.media and not msg.file:
            self.set_status("No media in this message", 'error')
            return

        try:
            dialog_dir = os.path.join(DOWNLOADS_DIR, self.current_dialog.name.replace("/", "_"))
            os.makedirs(dialog_dir, exist_ok=True)

            if msg.file and msg.file.name:
                file_name = msg.file.name
            else:
                media_type = "file"
                ext = ".bin"
                if msg.photo:
                    media_type = "photo"
                    ext = ".jpg"
                elif msg.video:
                    media_type = "video"
                    ext = ".mp4"
                elif msg.voice:
                    media_type = "voice"
                    ext = ".ogg"
                date_str = msg.date.strftime("%Y%m%d_%H%M%S")
                file_name = f"{media_type}_{date_str}{ext}"

            file_path = os.path.join(dialog_dir, file_name)
            await msg.download_media(file=file_path)

            self.set_status(f"Downloaded: {file_name}", 'success')
            execute_plugin_hook('media_downloaded', file_path)
        except Exception as e:
            self.set_status(f"Download error: {e}", 'error')

    async def search_messages(self, query):
        try:
            results = await client.get_messages(self.current_dialog.entity, search=query, limit=20)
            if results:
                self.search_results = list(reversed(results))
                self.messages = self.search_results

                messages_dict = {msg.id: msg for msg in self.messages}
                for msg in self.messages:
                    msg.sender_name = await self.get_sender_name(msg)

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
                self.header.set_text(f"Search: '{query}'")
                self.set_status(f"Found {len(results)} messages", 'success')

                if self.messages:
                    self.message_listbox.focus_position = 0
                    self.current_message_index = 0
                    self.refresh_message_list()
            else:
                self.set_status("No results found", 'error')
        except Exception as e:
            self.set_status(f"Search error: {e}", 'error')

    async def search_contacts(self, query):
        try:
            if query.startswith('@'):
                query = query[1:]

            result = await client(functions.contacts.ResolveUsernameRequest(username=query))
            if result.users:
                self.set_status(f"Found user: {result.users[0].first_name}", 'success')
            elif result.chats:
                self.set_status(f"Found chat: {result.chats[0].title}", 'success')
            else:
                self.set_status("Not found", 'error')
        except Exception as e:
            self.set_status(f"Search error: {e}", 'error')

    async def search_dialogs(self, query):
        if not query.strip():
            self.filtered_dialogs = self.dialogs.copy()
        else:
            self.filtered_dialogs = [
                d for d in self.dialogs
                if query.lower() in d.name.lower()
            ]

        self.current_dialog_index = 0
        self.refresh_dialog_list()
        self.set_status(f"Found {len(self.filtered_dialogs)} dialogs", 'success')

    def refresh_dialog_list(self):
        self.dialog_list.clear()

        if not self.filtered_dialogs:
            self.dialog_list.append(urwid.Text("No dialogs found", align='center'))
            return

        for i, dialog in enumerate(self.filtered_dialogs):
            # Используем getattr для безопасного получения атрибутов
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

        if self.urwid_loop:
            self.urwid_loop.draw_screen()

    def refresh_message_list(self):
        self.message_list.clear()
        self.message_widgets.clear()

        if not self.messages:
            self.message_list.append(urwid.Text("No messages", align='center'))
            return

        for i, msg in enumerate(self.messages):
            reply_text = getattr(msg, 'reply_text', "")
            sender_name = getattr(msg, 'sender_name', "")

            widget = MessageWidget(
                msg,
                is_selected=(i == self.current_message_index),
                is_outgoing=msg.out,
                reply_text=reply_text,
                sender_name=sender_name
            )
            self.message_list.append(widget)
            self.message_widgets.append(widget)

        if self.urwid_loop:
            self.urwid_loop.draw_screen()

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

    def handle_login_keypress(self, key):
        """Обработка клавиш на экране входа"""
        if isinstance(key, str):
            if key.lower() == 'q':
                self.exit_app()
        elif isinstance(key, tuple):
            # Ctrl+Q для выхода
            if len(key) == 2 and key[0] == 'ctrl' and key[1].lower() == 'q':
                self.exit_app()

    def handle_keypress(self, key):
        if self.input_mode:
            self.handle_input_key(key)
            return

        if self.in_settings:
            if key == 'esc':
                self.close_settings()
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

        if key in ('l', 'L'):
            load_plugins()
            self.set_status("Plugins reloaded", 'success')
            return

        if isinstance(key, tuple) and len(key) >= 2 and key[0] == 'mouse press':
            button = key[1]
            if button == 1:
                if self.view_mode == "dialogs":
                    try:
                        focus_pos = self.dialog_listbox.focus_position
                        if 0 <= focus_pos < len(self.filtered_dialogs):
                            self.select_dialog(focus_pos)
                    except (IndexError, AttributeError):
                        pass
                elif self.view_mode == "messages":
                    try:
                        focus_pos = self.message_listbox.focus_position
                        if 0 <= focus_pos < len(self.messages):
                            self.current_message_index = focus_pos
                            self.refresh_message_list()
                    except (IndexError, AttributeError):
                        pass
                return
            elif button in (4, 5):
                if self.view_mode == "dialogs" and self.filtered_dialogs:
                    if button == 4:
                        self.current_dialog_index = max(0, self.current_dialog_index - 1)
                    else:
                        self.current_dialog_index = min(len(self.filtered_dialogs) - 1, self.current_dialog_index + 1)
                    self.refresh_dialog_list()
                    self.dialog_listbox.focus_position = self.current_dialog_index
                elif self.view_mode == "messages" and self.messages:
                    if button == 4:
                        self.current_message_index = max(0, self.current_message_index - 1)
                    else:
                        self.current_message_index = min(len(self.messages) - 1, self.current_message_index + 1)
                    self.refresh_message_list()
                    self.message_listbox.focus_position = self.current_message_index
                return

        if self.view_mode == "dialogs":
            if not self.filtered_dialogs:
                return

            if key == 'up' and self.current_dialog_index > 0:
                self.current_dialog_index -= 1
                self.refresh_dialog_list()
                self.dialog_listbox.focus_position = self.current_dialog_index
            elif key == 'down' and self.current_dialog_index < len(self.filtered_dialogs) - 1:
                self.current_dialog_index += 1
                self.refresh_dialog_list()
                self.dialog_listbox.focus_position = self.current_dialog_index
            elif key == 'page up':
                self.current_dialog_index = max(0, self.current_dialog_index - 10)
                self.refresh_dialog_list()
                self.dialog_listbox.focus_position = self.current_dialog_index
            elif key == 'page down':
                self.current_dialog_index = min(len(self.filtered_dialogs) - 1, self.current_dialog_index + 10)
                self.refresh_dialog_list()
                self.dialog_listbox.focus_position = self.current_dialog_index
            elif key == 'home':
                self.current_dialog_index = 0
                self.refresh_dialog_list()
                self.dialog_listbox.focus_position = 0
            elif key == 'end':
                self.current_dialog_index = len(self.filtered_dialogs) - 1
                self.refresh_dialog_list()
                self.dialog_listbox.focus_position = self.current_dialog_index
            elif key == 'enter':
                if self.filtered_dialogs:
                    self.select_dialog(self.current_dialog_index)
            elif key == 'c' or key == 'C':
                self.show_input("Search dialogs: ", self.search_dialogs)
            elif key == 'p' or key == 'P':
                self.show_input("Search contacts (@username): ", self.search_contacts)
            elif key == 's' or key == 'S':
                self.show_settings()

        elif self.view_mode == "messages":
            if not self.messages:
                return

            if key == 'up' and self.current_message_index > 0:
                self.current_message_index -= 1
                self.refresh_message_list()
                self.message_listbox.focus_position = self.current_message_index
            elif key == 'down' and self.current_message_index < len(self.messages) - 1:
                self.current_message_index += 1
                self.refresh_message_list()
                self.message_listbox.focus_position = self.current_message_index
            elif key == 'page up':
                self.current_message_index = max(0, self.current_message_index - 10)
                self.refresh_message_list()
                self.message_listbox.focus_position = self.current_message_index
            elif key == 'page down':
                self.current_message_index = min(len(self.messages) - 1, self.current_message_index + 10)
                self.refresh_message_list()
                self.message_listbox.focus_position = self.current_message_index
            elif key == 'home':
                self.current_message_index = 0
                self.refresh_message_list()
                self.message_listbox.focus_position = 0
            elif key == 'end':
                self.current_message_index = len(self.messages) - 1
                self.refresh_message_list()
                self.message_listbox.focus_position = self.current_message_index
            elif key == 'left':
                self.view_mode = "dialogs"
                self.current_message_index = 0
                self.header.set_text("Dialogs")
                self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
                self.set_status("Back to dialogs")
            elif key == 'enter':
                if self.reply_mode and self.current_message_index < len(self.messages):
                    self.reply_to_message = self.messages[self.current_message_index]
                    self.reply_mode = False
                    self.set_status(f"Selected message {self.current_message_index + 1} for reply. Now type your message or send file.")
                elif self.edit_mode and self.current_message_index < len(self.messages):
                    msg = self.messages[self.current_message_index]
                    if msg.out:
                        self.edit_message = msg
                        self.edit_mode = False
                        self.show_input(f"Edit message {self.current_message_index + 1}: ", self.send_message)
                        self.set_status(f"Editing message {self.current_message_index + 1}")
                    else:
                        self.set_status("Can only edit your own messages", 'error')
                        self.edit_mode = False
                else:
                    self.show_input("Message: ", self.send_message)
            elif key == 'r' or key == 'R':
                if self.messages:
                    self.reply_mode = True
                    self.set_status(f"Select message to reply (use arrows, press Enter to select)")
            elif key == 'e' or key == 'E':
                if self.messages:
                    self.edit_mode = True
                    self.set_status(f"Select your message to edit (use arrows, press Enter to select)")
            elif key == 'f' or key == 'F':
                if self.reply_mode:
                    if self.current_message_index < len(self.messages):
                        self.reply_to_message = self.messages[self.current_message_index]
                        self.reply_mode = False
                        self.show_input("File path: ", self.send_file)
                        self.set_status(f"Selected message {self.current_message_index + 1} for reply. Now send file.")
                else:
                    self.show_input("File path: ", self.send_file)
            elif key == 'd' or key == 'D':
                self.loop.create_task(self.download_media())
            elif key == '/':
                self.show_input("Search messages: ", self.search_messages)
            elif key == 's' or key == 'S':
                self.show_settings()
            elif key == 'esc':
                if self.reply_mode:
                    self.reply_mode = False
                    self.set_status("Reply mode cancelled")
                elif self.edit_mode:
                    self.edit_mode = False
                    self.set_status("Edit mode cancelled")

    def show_settings(self):
        self.in_settings = True
        self.settings_widget = SettingsWidget(self)
        self.frame.body = self.settings_widget
        if self.urwid_loop:
            self.urwid_loop.draw_screen()

    def close_settings(self):
        self.in_settings = False
        if self.view_mode == "dialogs":
            self.frame.body = urwid.AttrMap(self.dialog_listbox, 'body')
        else:
            self.frame.body = urwid.AttrMap(self.message_listbox, 'body')
        if self.urwid_loop:
            self.urwid_loop.draw_screen()

    def exit_app(self):
        """Выход из приложения"""
        if client and client.is_connected():
            self.loop.create_task(client.disconnect())
        raise urwid.ExitMainLoop()

    async def handler_new_message(self, event):
        execute_plugin_hook('new_message', event)

        if event.is_private and not event.message.out:
            if config.get("notifications", {}).get("private_chats", True):
                sender = await event.get_sender()
                sender_name = sender.first_name if sender else "Unknown"
                self.set_status(f"New message from {sender_name}", 'success')

                if self.view_mode == "dialogs":
                    await self.load_dialogs()
                elif self.view_mode == "messages" and self.current_dialog and event.chat_id == self.current_dialog.entity.id:
                    await self.load_messages(self.current_dialog)

    async def handler_message_edited(self, event):
        execute_plugin_hook('message_edited', event)

        if self.view_mode == "messages" and self.current_dialog and event.chat_id == self.current_dialog.entity.id:
            await self.load_messages(self.current_dialog)

    async def handler_message_deleted(self, event):
        execute_plugin_hook('message_deleted', event)

        if self.view_mode == "messages" and self.current_dialog and event.chat_id == self.current_dialog.entity.id:
            await self.load_messages(self.current_dialog)

def main():
    global config
    config = load_config()

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tui = LinuxGramTUI(loop)
    tui.run()

if __name__ == '__main__':
    main()
