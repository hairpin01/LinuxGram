
#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
# beta is linuxgram!  #
#######################

import asyncio
import os
import json
import mimetypes
import re
import random
from datetime import datetime
from telethon import TelegramClient, events, functions
from telethon.tl import types
import urwid

API_ID = 12345678
API_HASH = 'API_HASH'
SESSION_FILE = 'linuxgram.session'
DOWNLOADS_DIR = "downloads"
CONFIG_FILE = "config.json"

client = None
config = {}

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

class MessageWidget(urwid.WidgetWrap):
    def __init__(self, message, is_selected=False, is_outgoing=False, reply_text=""):
        self.message = message
        self.is_selected = is_selected
        self.is_outgoing = is_outgoing
        self.reply_text = reply_text
        super().__init__(self.build_widget())

    def build_widget(self):
        lines = []

        # Reply info
        if self.reply_text:
            if len(self.reply_text) > 40:
                preview = self.reply_text[:37] + "..."
            else:
                preview = self.reply_text
            reply_text = f"↩ ({preview})"
            lines.append(urwid.AttrMap(urwid.Text(reply_text), 'reply'))

        # Message content
        if self.message.text:
            content = self.message.text
        elif self.message.media:
            if self.message.photo:
                content = "📷 Photo"
            elif self.message.video:
                content = "🎬 Video"
            elif self.message.voice:
                content = "🎤 Voice message"
            elif self.message.document:
                content = "📄 Document"
            else:
                content = "[Media]"
        else:
            content = "[Empty]"

        # Truncate long messages
        if len(content) > 80:
            content = content[:77] + "..."

        # Time
        time_str = self.message.date.strftime("%H:%M")
        time_text = f" [{time_str}]"

        # Build content with time
        content_widget = urwid.Columns([
            (len(content), urwid.Text(content)),
            ('pack', urwid.Text(time_text))
        ])

        lines.append(content_widget)

        # Build pile
        widget = urwid.Pile(lines)

        # Apply selection style
        if self.is_selected:
            widget = urwid.AttrMap(widget, 'selected')
        elif self.is_outgoing:
            widget = urwid.AttrMap(widget, 'my_message')

        return widget

class DialogWidget(urwid.WidgetWrap):
    def __init__(self, dialog, index, is_selected=False, callback=None):
        self.dialog = dialog
        self.index = index
        self.is_selected = is_selected
        self.callback = callback

        # Create button with dialog info
        dialog_type = ""
        if isinstance(self.dialog.entity, types.Channel):
            if getattr(self.dialog.entity, 'megagroup', False):
                dialog_type = "👥 "
            else:
                dialog_type = "📢 "
        elif isinstance(self.dialog.entity, types.Chat):
            dialog_type = "👥 "
        else:
            dialog_type = "👤 "

        name = self.dialog.name
        if self.dialog.unread_count > 0:
            name = f"● {name} ({self.dialog.unread_count})"

        self.button = urwid.Button(dialog_type + name)
        urwid.connect_signal(self.button, 'click', self.on_click)

        # Apply styling
        if self.is_selected:
            widget = urwid.AttrMap(self.button, 'selected')
        else:
            widget = urwid.AttrMap(self.button, 'dialog_name')

        super().__init__(widget)

    def on_click(self, button):
        if self.callback:
            self.callback(self.index)

class SettingsWidget(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent

        # Create checkboxes
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

        # Create save and cancel buttons
        self.save_button = urwid.Button("Save")
        urwid.connect_signal(self.save_button, 'click', self.save_settings)

        self.cancel_button = urwid.Button("Cancel")
        urwid.connect_signal(self.cancel_button, 'click', self.cancel_settings)

        # Layout
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

class LinuxGramTUI:
    def __init__(self, loop):
        self.loop = loop
        self.palette = [
            ('header', 'white', 'dark magenta'),  # Изменен с dark blue на dark magenta
            ('footer', 'white', 'dark gray'),
            ('selected', 'white', 'dark magenta'),  # Изменен с light gray на dark magenta
            ('unread', 'yellow,bold', ''),
            ('my_message', 'light green', ''),
            ('their_message', 'white', ''),
            ('reply', 'light cyan', ''),
            ('error', 'light red', ''),
            ('success', 'light green', ''),
            ('input', 'white', 'dark cyan'),
            ('dialog_name', 'white', ''),
            ('preview', 'light gray', ''),
            ('status', 'yellow', 'dark magenta'),  # Изменен с dark blue на dark magenta
            ('title', 'bold', ''),
            ('loading', 'yellow', 'dark magenta'),  # Изменен с dark blue на dark magenta
            ('search_highlight', 'black', 'yellow'),
            ('button', 'white', 'dark magenta'),  # Изменен с dark blue на dark magenta
            ('button_focus', 'black', 'light gray'),
        ]

        self.dialogs = []
        self.filtered_dialogs = []
        self.messages = []
        self.current_dialog_index = 0
        self.current_message_index = 0
        self.current_dialog = None
        self.input_mode = False
        self.input_buffer = ""
        self.input_prompt = ""
        self.input_callback = None
        self.reply_to_message = None
        self.search_results = None
        self.view_mode = "dialogs"
        self.status_msg = "Starting..."
        self.search_query = ""
        self.in_settings = False

        self.title = urwid.Text("LinuxGram", align='center')
        self.header = urwid.Text("Dialogs")

        self.footer_help_text = (
            "Q: Quit | ↑↓/PgUp/PgDn: Select | Enter: Open/Message | ←: Back | R: Reply | "
            "F: File | D: Download | /: Search | S: Settings | C: Search chats"
        )
        self.footer_help = urwid.Text(self.footer_help_text)

        self.footer_status = urwid.Text("")
        self.footer_status_am = urwid.AttrMap(self.footer_status, 'footer')

        self.footer_widget = urwid.Pile([
            urwid.AttrMap(self.footer_help, 'footer'),
            self.footer_status_am
        ])

        self._status_handle = None

        self.dialog_list = urwid.SimpleListWalker([])
        self.dialog_listbox = urwid.ListBox(self.dialog_list)

        self.message_list = urwid.SimpleListWalker([])
        self.message_listbox = urwid.ListBox(self.message_list)

        self.input_edit = urwid.Edit("")
        self.input_widget = urwid.AttrMap(self.input_edit, 'input')

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
        self.urwid_loop = urwid.MainLoop(
            self.frame,
            self.palette,
            unhandled_input=self.handle_keypress,
            event_loop=urwid.AsyncioEventLoop(loop=self.loop),
            handle_mouse=True
        )
        self.loop.create_task(self.start_client())
        self.urwid_loop.run()

    async def start_client(self):
        global client
        client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        await client.start()
        client.add_event_handler(self.handler_new_message, events.NewMessage)
        client.add_event_handler(self.handler_message_edited, events.MessageEdited)
        client.add_event_handler(self.handler_message_deleted, events.MessageDeleted)
        await self.load_dialogs()

    async def load_dialogs(self):
        try:
            limit = config.get("interface", {}).get("dialogs_limit", 100)
            self.dialogs = await client.get_dialogs(limit=limit)
            self.filtered_dialogs = self.dialogs.copy()
            self.refresh_dialog_list()
            self.set_status(f"Loaded {len(self.dialogs)} dialogs", 'success')
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')

    async def load_messages(self, dialog):
        try:
            self.current_dialog = dialog
            limit = config.get("interface", {}).get("messages_limit", 50)

            # Сохраняем текущую позицию прокрутки
            if self.view_mode == "messages" and self.current_dialog == dialog:
                focus_widget, focus_idx = self.message_listbox.get_focus()
                if focus_idx is not None:
                    # Сохраняем относительную позицию
                    self.scroll_position = focus_idx
                else:
                    self.scroll_position = len(self.messages) - 1

            self.messages = await client.get_messages(dialog.entity, limit=limit)
            self.messages.reverse()

            # Получаем текст ответов для сообщений
            messages_dict = {msg.id: msg for msg in self.messages}
            for msg in self.messages:
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
            self.header.set_text(f"Chat: {dialog.name}")
            self.set_status(f"Loaded {len(self.messages)} messages", 'success')

            # Восстанавливаем позицию прокрутки
            if hasattr(self, 'scroll_position') and self.scroll_position < len(self.messages):
                self.current_message_index = min(self.scroll_position, len(self.messages) - 1)
                self.refresh_message_list()
                self.message_listbox.set_focus(self.current_message_index)
        except Exception as e:
            self.set_status(f"Error: {e}", 'error')

    def select_dialog(self, index):
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

        try:
            # Сохраняем позицию перед отправкой
            focus_widget, focus_idx = self.message_listbox.get_focus()
            current_focus = focus_idx if focus_idx is not None else len(self.messages) - 1

            if self.reply_to_message:
                await client.send_message(self.current_dialog.entity, text, reply_to=self.reply_to_message.id)
                self.reply_to_message = None
            else:
                await client.send_message(self.current_dialog.entity, text)

            # Обновляем сообщения без индикатора загрузки
            await self.load_messages(self.current_dialog)
            self.set_status("Message sent", 'success')

        except Exception as e:
            self.set_status(f"Error: {e}", 'error')

    async def send_file(self, file_path):
        if not os.path.exists(file_path):
            self.set_status("File not found", 'error')
            return

        try:
            # Сохраняем позицию перед отправкой
            focus_widget, focus_idx = self.message_listbox.get_focus()
            current_focus = focus_idx if focus_idx is not None else len(self.messages) - 1

            await client.send_file(self.current_dialog.entity, file_path)
            await self.load_messages(self.current_dialog)
            self.set_status("File sent", 'success')
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
        except Exception as e:
            self.set_status(f"Download error: {e}", 'error')

    async def search_messages(self, query):
        try:
            # Сохраняем текущую позицию
            focus_widget, focus_idx = self.message_listbox.get_focus()
            current_focus = focus_idx if focus_idx is not None else 0

            results = await client.get_messages(self.current_dialog.entity, search=query, limit=20)
            if results:
                self.search_results = list(reversed(results))
                self.messages = self.search_results

                # Получаем текст ответов для найденных сообщений
                messages_dict = {msg.id: msg for msg in self.messages}
                for msg in self.messages:
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

                # Восстанавливаем позицию
                self.message_listbox.set_focus(0)
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

        for i, dialog in enumerate(self.filtered_dialogs):
            widget = DialogWidget(
                dialog,
                i,
                i == self.current_dialog_index,
                callback=self.select_dialog
            )
            self.dialog_list.append(widget)

        if self.urwid_loop:
            self.urwid_loop.draw_screen()

    def refresh_message_list(self):
        self.message_list.clear()

        for i, msg in enumerate(self.messages):
            reply_text = getattr(msg, 'reply_text', "")
            widget = MessageWidget(
                msg,
                is_selected=(i == self.current_message_index),
                is_outgoing=msg.out,
                reply_text=reply_text
            )
            self.message_list.append(widget)

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

    def handle_keypress(self, key):
        if self.input_mode:
            self.handle_input_key(key)
            return

        if self.in_settings:
            if key == 'esc':
                self.close_settings()
            return

        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if isinstance(key, tuple) and len(key) >= 2 and key[0] == 'mouse press':
            button = key[1]
            pos = key[2] if len(key) > 2 else 0
            if button == 1:  # Left click
                if self.view_mode == "dialogs" and self.filtered_dialogs:
                    dialog_index = min(pos, len(self.filtered_dialogs) - 1)
                    if 0 <= dialog_index < len(self.filtered_dialogs):
                        self.select_dialog(dialog_index)
                elif self.view_mode == "messages" and self.messages:
                    message_index = min(pos // 2, len(self.messages) - 1)
                    if 0 <= message_index < len(self.messages):
                        self.current_message_index = message_index
                        self.refresh_message_list()
                        self.message_listbox.set_focus(self.current_message_index)
            elif button in (4, 5) and self.urwid_loop:
                direction = 'up' if button == 4 else 'down'
                cols, rows = self.urwid_loop.screen.get_cols_rows()
                try:
                    self.frame.body.keypress((cols, rows), direction)
                except Exception:
                    pass
                return

        if self.view_mode == "dialogs":
            if key == 'up' and self.current_dialog_index > 0:
                self.current_dialog_index -= 1
                self.refresh_dialog_list()
            elif key == 'down' and self.current_dialog_index < len(self.filtered_dialogs) - 1:
                self.current_dialog_index += 1
                self.refresh_dialog_list()
            elif key == 'page up':
                self.current_dialog_index = max(0, self.current_dialog_index - 10)
                self.refresh_dialog_list()
            elif key == 'page down':
                self.current_dialog_index = min(len(self.filtered_dialogs) - 1, self.current_dialog_index + 10)
                self.refresh_dialog_list()
            elif key == 'enter':
                if self.filtered_dialogs:
                    self.select_dialog(self.current_dialog_index)
            elif key == 'home':
                self.current_dialog_index = 0
                self.refresh_dialog_list()
                self.dialog_listbox.set_focus(0)
            elif key == 'end':
                self.current_dialog_index = len(self.filtered_dialogs) - 1
                self.refresh_dialog_list()
                self.dialog_listbox.set_focus(self.current_dialog_index)
            elif key == 'c' or key == 'C':
                self.show_input("Search dialogs: ", self.search_dialogs)
            elif key == 'p' or key == 'P':
                self.show_input("Search contacts (@username): ", self.search_contacts)
            elif key == 's' or key == 'S':
                self.show_settings()

        elif self.view_mode == "messages":
            if key == 'up' and self.current_message_index > 0:
                self.current_message_index -= 1
                self.refresh_message_list()
                self.message_listbox.set_focus(self.current_message_index)
            elif key == 'down' and self.current_message_index < len(self.messages) - 1:
                self.current_message_index += 1
                self.refresh_message_list()
                self.message_listbox.set_focus(self.current_message_index)
            elif key == 'page up':
                self.current_message_index = max(0, self.current_message_index - 10)
                self.refresh_message_list()
                self.message_listbox.set_focus(self.current_message_index)
            elif key == 'page down':
                self.current_message_index = min(len(self.messages) - 1, self.current_message_index + 10)
                self.refresh_message_list()
                self.message_listbox.set_focus(self.current_message_index)
            elif key == 'home':
                self.current_message_index = 0
                self.refresh_message_list()
                self.message_listbox.set_focus(0)
            elif key == 'end':
                self.current_message_index = len(self.messages) - 1
                self.refresh_message_list()
                self.message_listbox.set_focus(self.current_message_index)
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
                    self.reply_to_message = self.messages[self.current_message_index]
                    reply_text = ""
                    if hasattr(self.reply_to_message, 'text') and self.reply_to_message.text:
                        if len(self.reply_to_message.text) > 40:
                            reply_text = self.reply_to_message.text[:37] + "..."
                        else:
                            reply_text = self.reply_to_message.text
                    self.show_input(f"Reply: ", self.send_message)
                    self.set_status(f"Replying to message")
            elif key == 'f' or key == 'F':
                self.show_input("File path: ", self.send_file)
            elif key == 'd' or key == 'D':
                self.loop.create_task(self.download_media())
            elif key == '/':
                self.show_input("Search messages: ", self.search_messages)
            elif key == 's' or key == 'S':
                self.show_settings()

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

    async def handler_new_message(self, event):
        if event.is_private and not event.message.out:
            if config.get("notifications", {}).get("private_chats", True):
                sender = await event.get_sender()
                sender_name = sender.first_name if sender else "Unknown"
                self.set_status(f"New message from {sender_name}", 'success')

                # Update dialog list if open
                if self.view_mode == "dialogs":
                    await self.load_dialogs()
                # Update messages if in the same chat
                elif self.view_mode == "messages" and self.current_dialog and event.chat_id == self.current_dialog.entity.id:
                    await self.load_messages(self.current_dialog)

    async def handler_message_edited(self, event):
        if self.view_mode == "messages" and self.current_dialog and event.chat_id == self.current_dialog.entity.id:
            await self.load_messages(self.current_dialog)

    async def handler_message_deleted(self, event):
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
