#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   app linuxgram!   #
##################


import asyncio
import os
import mimetypes
import textwrap
from datetime import datetime
from telethon import TelegramClient, events, functions, errors
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest
import urwid

from linuxgram.core.constants import (
    CONFIG_FILE,
    CREDENTIALS_FILE,
    DEFAULT_THEMES,
    DOWNLOADS_DIR,
    PLUGINS_DIR,
    REACTION_LABELS,
    REVERSE_LAYOUT_MAP,
    SESSION_FILE,
)
from linuxgram.core.config import (
    get_plugin_config as _get_plugin_config,
    load_config as _load_config,
    save_config as _save_config,
    save_plugin_config as _save_plugin_config,
)
from linuxgram.core.credentials import (
    load_credentials as _load_credentials,
    mask_phone,
    save_credentials as _save_credentials,
)
from linuxgram.core.logging_config import configure_logging, logger
from linuxgram.core.plugins import (
    execute_plugin_command as _execute_plugin_command,
    execute_plugin_hook as _execute_plugin_hook,
    load_plugins as _load_plugins,
    loaded_plugins,
    plugin_command_handlers,
)
from linuxgram.core.models import ContactDialog
from linuxgram.core.qr import render_qr_ascii
from linuxgram.core.utils import get_peer_chat_id as _get_peer_chat_id
from linuxgram.version import __version__
from linuxgram.tui.widgets.dialogs import DialogWidget, TopicWidget
from linuxgram.tui.widgets.help import HelpWidget
from linuxgram.tui.widgets.login import LoginWidget
from linuxgram.tui.widgets.messages import MessageRow, MessageWidget
from linuxgram.tui.widgets.file_browser import FileBrowserWidget
from linuxgram.tui.widgets.reactions import ReactionPickerWidget
from linuxgram.tui.widgets.search import SearchWidget
from linuxgram.tui.widgets.settings import PluginManagerWidget, PluginSettingsWidget, SettingsWidget


client = None
config = {}


# Pure helpers/constants are now imported from linuxgram.core.*


def load_config():
    return _load_config(CONFIG_FILE)


def save_config():
    _save_config(config, CONFIG_FILE)


def get_plugin_config(plugin_name, default_config=None):
    return _get_plugin_config(config, plugin_name, default_config)


def save_plugin_config(plugin_name, plugin_config):
    _save_plugin_config(config, plugin_name, plugin_config)
    save_config()


def load_credentials():
    return _load_credentials(CREDENTIALS_FILE)


def save_credentials(api_id, api_hash, phone=None):
    _save_credentials(api_id, api_hash, phone, CREDENTIALS_FILE)


def load_plugins():
    _load_plugins(PLUGINS_DIR)


def execute_plugin_hook(hook_name, *args, **kwargs):
    return _execute_plugin_hook(hook_name, *args, **kwargs)


def execute_plugin_command(command, text, dialog, tui):
    return _execute_plugin_command(command, text, dialog, tui, config)


























# ---------------------------------------------------------------------------
# Main TUI class
# ---------------------------------------------------------------------------

class LinuxGramTUI:
    def __init__(self):
        self.config = config
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
        self.input_prompt = ""
        self.input_callback = None
        self.reply_to_message = None
        self.edit_message = None
        self.reply_mode = False
        self.edit_mode = False
        self.view_mode = "dialogs"
        self.status_msg = "Starting..."
        self.in_settings = False
        self.in_search = False
        self.in_file_browser = False
        self.in_reaction_picker = False
        self.in_plugin_manager = False
        self.in_plugin_settings = False
        self.current_plugin_settings = None
        self.show_help = False
        self._help_previous_body = None
        self._help_previous_footer = None
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
        self.qr_task = None
        self.qr_url = ""
        self.qr_ascii = ""
        self.qr_status = ""

        self.client = None
        self.loop = None
        self.file_to_send = None

        self.title = urwid.Text(f"LinuxGram Beta {__version__}", align='center')
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

        self.dialog_indicators = []
        self.topic_indicators = []
        self.message_indicators = []

        self.input_edit = urwid.Edit(multiline=False)
        self.input_widget = urwid.AttrMap(self.input_edit, 'input')

        self.help_widget = HelpWidget(self)

        self.empty_chat = urwid.Filler(urwid.Text("Выберите диалог слева", align='center'), 'middle')

        self.frame = urwid.Frame(
            body=urwid.AttrMap(self.dialog_listbox, 'body'),
            header=urwid.AttrMap(urwid.Pile([
                urwid.AttrMap(self.title, 'title'),
                urwid.AttrMap(self.header, 'header')
            ]), ''),
            footer=urwid.AttrMap(self.footer_widget, 'footer')
        )

        self.urwid_loop = None
        self._ui_running = False
        self._notification_widget = None
        self._notification_token = None

        load_plugins()
        execute_plugin_hook('on_tui_init', self)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _restore_body(self) -> None:
        """Restore the frame body to match the current view."""
        self._update_main_view()

    def open_help(self) -> None:
        """Show help and remember the current panel for exact restoration."""
        if self.show_help:
            return
        self._help_previous_body = self.frame.body
        self._help_previous_footer = self.frame.footer
        self.show_help = True
        self.frame.body = self.help_widget
        self.refresh_ui()

    def close_help(self) -> None:
        """Close help and restore the panel that opened it."""
        if not self.show_help:
            return
        self.show_help = False
        if self._help_previous_body is not None:
            self.frame.body = self._help_previous_body
        else:
            self._restore_body()
        if self._help_previous_footer is not None:
            self.frame.footer = self._help_previous_footer
        self._help_previous_body = None
        self._help_previous_footer = None
        self.refresh_ui()

    def _update_main_view(self):
        """Compose the two-column layout: dialogs on the left, content on the right."""
        left = urwid.AttrMap(self.dialog_listbox, 'body')

        if self.view_mode == "topics":
            right_widget = self.topic_listbox if self.topics else urwid.Filler(urwid.Text("Темы не найдены", align='center'), 'middle')
            focus_col = 1
        elif self.view_mode == "messages":
            right_widget = self.message_listbox if self.messages else self.empty_chat
            focus_col = 1
        else:
            right_widget = self.empty_chat
            focus_col = 0

        right = urwid.AttrMap(right_widget, 'body')
        self.main_columns = urwid.Columns([('weight', 1, left), ('weight', 2, right)], dividechars=1, focus_column=focus_col)
        self.frame.body = self.main_columns

    def _get_listbox_focus(self, listbox) -> int:
        """Return the current focused position in a ListBox, or 0 on error."""
        try:
            return listbox.focus_position
        except Exception:
            return 0

    def _get_dialog_key(self, dialog):
        entity = getattr(dialog, 'entity', None)
        if entity is not None and hasattr(entity, 'id'):
            return (type(entity).__name__, entity.id)
        return getattr(dialog, 'id', None) or getattr(dialog, 'name', None)

    def _sync_dialog_focus(self) -> int:
        if self.filtered_dialogs:
            self.current_dialog_index = min(
                self._get_listbox_focus(self.dialog_listbox),
                len(self.filtered_dialogs) - 1,
            )
        return self.current_dialog_index

    def _sync_topic_focus(self) -> int:
        if self.topics:
            self.current_topic_index = min(
                self._get_listbox_focus(self.topic_listbox),
                len(self.topics) - 1,
            )
        return self.current_topic_index

    def _sync_message_focus(self) -> int:
        if self.messages:
            self.current_message_index = min(
                self._get_listbox_focus(self.message_listbox),
                len(self.messages) - 1,
            )
        return self.current_message_index

    def _is_message_focus_at_bottom(self) -> bool:
        if not self.messages:
            return True
        return self._sync_message_focus() >= len(self.messages) - 1

    def _set_message_focus(self, index: int, *, update_status: bool = True) -> None:
        if not self.messages:
            return
        target = max(0, min(index, len(self.messages) - 1))
        self.current_message_index = target
        self.message_list.set_focus(target)
        self._update_message_focus()
        if update_status:
            self.set_status(f"Selected message {target + 1}/{len(self.messages)}", 'status')
        else:
            self.refresh_ui()

    def _move_message_focus(self, *, delta: int = 0, absolute: int | None = None, update_status: bool = True) -> None:
        if not self.messages:
            return
        if absolute is None:
            target = self._sync_message_focus() + delta
        else:
            target = absolute
        self._set_message_focus(target, update_status=update_status)

    def create_task(self, coro, *, context="background task"):
        """Schedule a coroutine and report unexpected async exceptions."""
        task = self.loop.create_task(coro)
        task.add_done_callback(lambda done_task: self._handle_task_result(done_task, context))
        logger.trace("Scheduled %s", context)
        return task

    def _handle_task_result(self, task, context: str) -> None:
        if task.cancelled():
            logger.debug("Cancelled %s", context)
            return
        try:
            task.result()
        except Exception as exc:
            self.report_exception(context, exc)

    def _handle_loop_exception(self, loop, context):
        exc = context.get('exception')
        message = context.get('message', 'Event loop error')
        if exc:
            self.report_exception(message, exc)
        else:
            logger.error("%s", message)
            self.show_notification(message, style='error')

    def report_exception(self, context: str, exc: BaseException, *, notify: bool = True) -> None:
        """Log an exception with traceback and show a compact visible error."""
        logger.error("%s: %s", context, exc, exc_info=(type(exc), exc, exc.__traceback__))
        if notify:
            self.show_notification(f"{context}: {exc}", style='error')
        self.set_status(f"{context}: {exc}", 'error')

    def show_notification(self, text: str, *, style: str = 'notification', timeout: float = 5.0) -> None:
        """Show a temporary notification in the top-right corner."""
        logger.debug("Notification [%s]: %s", style, text)
        message = textwrap.shorten(str(text).replace('\n', ' '), width=78, placeholder='...')
        box = urwid.LineBox(urwid.Padding(urwid.Text(message), left=1, right=1))
        notification = urwid.AttrMap(box, style)
        self._notification_widget = urwid.Overlay(
            notification,
            self.frame,
            align='right',
            width=('relative', 45),
            valign='top',
            height='pack',
            min_width=24,
            left=0,
            right=1,
            top=1,
            bottom=0,
        )
        token = object()
        self._notification_token = token
        if self.urwid_loop:
            self.urwid_loop.widget = self._notification_widget
            self.refresh_ui()
            if self.loop:
                self.loop.call_later(timeout, self.clear_notification, token)

    def clear_notification(self, token=None) -> None:
        if token is not None and token is not self._notification_token:
            return
        if self.urwid_loop and getattr(self.urwid_loop, 'widget', None) is getattr(self, '_notification_widget', None):
            self.urwid_loop.widget = self.frame
            self.refresh_ui()
        self._notification_widget = None
        self._notification_token = None

    async def _enrich_messages(self, messages: list) -> None:
        """Populate sender_name, reply_text, and reactions_dict on each message."""
        messages_by_id = {msg.id: msg for msg in messages}
        for msg in messages:
            msg.sender_name = await self.get_sender_name_async(msg)

            reply_to = getattr(msg, 'reply_to', None)
            if reply_to and hasattr(reply_to, 'reply_to_msg_id'):
                reply_msg = messages_by_id.get(reply_to.reply_to_msg_id)
                if reply_msg:
                    text = reply_msg.text
                    if text:
                        msg.reply_text = (text[:37] + "...") if len(text) > 40 else text
                    else:
                        msg.reply_text = "[Media]"

            raw_reactions = getattr(msg, 'reactions', None)
            if raw_reactions:
                msg.reactions_dict = {
                    REACTION_LABELS.get(r.reaction.emoticon, r.reaction.emoticon): r.count
                    for r in raw_reactions.results
                    if hasattr(r.reaction, 'emoticon')
                }

    # ------------------------------------------------------------------
    # Setup / start
    # ------------------------------------------------------------------

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
        self.loop.set_exception_handler(self._handle_loop_exception)

        self.setup_ui()

        if not os.path.exists(SESSION_FILE):
            self.show_login_screen()
        else:
            self.create_task(self.init_client(), context="Client init")

        try:
            self._ui_running = True
            self.urwid_loop.run()
        except KeyboardInterrupt:
            pass
        finally:
            self._ui_running = False
            self.exit_app()

    def refresh_ui(self):
        if self.urwid_loop and self._ui_running:
            try:
                logger.trace("Refreshing UI")
                self.urwid_loop.draw_screen()
            except RuntimeError as exc:
                logger.trace("UI refresh skipped: %s", exc)
            except Exception as exc:
                logger.debug("UI refresh failed: %s", exc, exc_info=exc)

    def show_login_screen(self):
        self.login_widget = LoginWidget(self)
        self.frame.body = self.login_widget
        self.header.set_text("Login to Telegram")
        self.refresh_ui()

    # ------------------------------------------------------------------
    # Client initialisation and login
    # ------------------------------------------------------------------

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

            await self.client.connect()
            self._set_login_protection_mode()

            if not await self.client.is_user_authorized():
                logger.warning("Stored Telegram session is not authorized; showing login screen")
                self.set_status("Session expired or invalid. Please login again.", 'error')
                self.show_login_screen()
                return

            if not self.client.list_event_handlers():
                self.client.add_event_handler(self.handler_new_message, events.NewMessage)
                self.client.add_event_handler(self.handler_message_edited, events.MessageEdited)
                self.client.add_event_handler(self.handler_message_deleted, events.MessageDeleted)

            execute_plugin_hook('on_client_ready', self.client)

            self.create_task(self.load_dialogs_async(), context="Load dialogs")

        except Exception as e:
            self.report_exception("Client init error", e)
            self.show_login_screen()

    async def _ensure_login_client(self):
        if not self.client:
            self.client = TelegramClient(
                SESSION_FILE,
                self.api_id,
                self.api_hash,
                loop=self.loop
            )
        await self.client.connect()
        self._set_login_protection_mode()
        return self.client

    def _get_protection_mode(self) -> str | None:
        if not self.client:
            return None
        try:
            return getattr(self.client, 'protection_mode', None)
        except Exception as exc:
            logger.debug("Unable to read protection mode: %s", exc)
            return None

    def _set_protection_mode(self, mode: str) -> bool:
        if not self.client or not hasattr(self.client, 'set_protection_mode'):
            return False
        try:
            current_mode = self._get_protection_mode()
            if current_mode == mode:
                return True
            self.client.set_protection_mode(mode)
            logger.info("Telethon protection mode changed: %s -> %s", current_mode, mode)
            return True
        except Exception as exc:
            logger.warning("Unable to set Telethon protection mode to %s: %s", mode, exc)
            return False

    def _set_login_protection_mode(self) -> None:
        """Allow login/registration requests under Telethon-MCUB protection."""
        self._set_protection_mode('safe')

    def _restore_post_login_protection_mode(self) -> None:
        """Keep protection enabled after registration/login."""
        self._set_protection_mode('safe')

    def start_qr_login(self):
        self.cancel_qr_login(clear=False)
        self.qr_url = ""
        self.qr_ascii = "Preparing QR code..."
        self.qr_status = "Connecting to Telegram..."
        if self.login_widget:
            self.login_widget.update_content()
        self.set_status("Preparing QR login...", 'status')
        self.qr_task = self.create_task(self.async_qr_login(), context="QR login")

    def cancel_qr_login(self, *, clear: bool = True):
        task = self.qr_task
        self.qr_task = None
        if task and not task.done():
            task.cancel()
            logger.debug("QR login task cancelled")
        if clear:
            self.qr_url = ""
            self.qr_ascii = ""
            self.qr_status = ""

    async def async_qr_login(self):
        current_task = asyncio.current_task()
        try:
            await self._ensure_login_client()
            while self.qr_task is current_task:
                qr_login = await self.client.qr_login()
                self.qr_url = qr_login.url
                self.qr_ascii = render_qr_ascii(qr_login.url)
                self.qr_status = "Scan the QR code in Telegram. It will refresh automatically if it expires."
                logger.info("QR login code generated; expires at %s", getattr(qr_login, 'expires', None))
                if self.login_widget and self.login_widget.step == 5:
                    self.login_widget.update_content()
                self.set_status("QR login ready. Scan it with Telegram.", 'success')

                try:
                    await qr_login.wait()
                except asyncio.TimeoutError:
                    if self.qr_task is not current_task:
                        return
                    self.qr_status = "QR code expired. Refreshing..."
                    self.qr_ascii = "Refreshing QR code..."
                    if self.login_widget and self.login_widget.step == 5:
                        self.login_widget.update_content()
                    continue

                if self.qr_task is current_task:
                    self.qr_task = None
                await self.login_successful()
                return

        except errors.SessionPasswordNeededError:
            if self.qr_task is current_task:
                self.qr_task = None
            self.set_status("2FA password required after QR scan", 'success')
            if self.login_widget:
                self.login_widget.step = 4
                self.login_widget.update_content()
        except asyncio.CancelledError:
            logger.debug("QR login cancelled")
            raise
        except Exception as e:
            if self.qr_task is current_task:
                self.qr_task = None
            self.report_exception("QR login error", e)

    async def async_start_login(self, *, force_sms: bool = False):
        try:
            await self._ensure_login_client()
            sent_code = await self.client.send_code_request(self.phone, force_sms=force_sms)
            code_type = getattr(getattr(sent_code, 'type', None), '__class__', type(None)).__name__
            logger.info(
                "Login code requested for phone %s via %s (force_sms=%s)",
                mask_phone(self.phone),
                code_type,
                force_sms,
            )

            self.login_widget.step = 3
            self.login_widget.update_content()
            self.set_status("Code requested. Check Telegram app first; SMS/call can take a minute.", 'success')

        except errors.PhoneNumberInvalidError:
            self.set_status("Invalid phone number", 'error')
            self.login_widget.step = 2
            self.login_widget.update_content()
        except errors.FloodWaitError as e:
            seconds = getattr(e, 'seconds', 0)
            self.set_status(f"Too many code requests. Try again in {seconds} seconds.", 'error')
            logger.warning("Telegram flood wait while requesting login code for %s: %s seconds", mask_phone(self.phone), seconds)
            self.show_notification(f"Too many code requests. Wait {seconds}s before retrying.", style='error')
        except Exception as e:
            self.report_exception("Login error", e)

    async def async_sign_in_with_code(self):
        try:
            self._set_login_protection_mode()
            await self.client.sign_in(self.phone, self.login_code)
            await self.login_successful()

        except errors.SessionPasswordNeededError:
            self.set_status("2FA password required", 'success')
            self.login_widget.step = 4
            self.login_widget.update_content()
        except errors.PhoneCodeInvalidError:
            self.set_status("Invalid code", 'error')
        except Exception as e:
            self.report_exception("Sign in error", e)

    async def async_sign_in_with_password(self):
        try:
            self._set_login_protection_mode()
            await self.client(functions.account.GetPasswordRequest())
            await self.client.sign_in(password=self.login_password)
            await self.login_successful()

        except errors.PasswordHashInvalidError:
            self.set_status("Invalid password", 'error')
        except Exception as e:
            self.report_exception("2FA error", e)

    async def login_successful(self):
        self.logged_in = True
        self._restore_post_login_protection_mode()
        self.set_status("Login successful! Loading dialogs...", 'success')
        save_credentials(self.api_id, self.api_hash, self.phone)
        await self.init_client()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    async def load_dialogs_async(self):
        try:
            if not self.client or not self.client.is_connected():
                self.set_status("Waiting for connection...", 'status')
                return

            self.set_status("Loading dialogs...", 'status')

            focused_dialog_key = None
            if self.filtered_dialogs:
                focus = self._sync_dialog_focus()
                if 0 <= focus < len(self.filtered_dialogs):
                    focused_dialog_key = self._get_dialog_key(self.filtered_dialogs[focus])

            limit = config.get("interface", {}).get("dialogs_limit", 100)
            self.dialogs = await self.client.get_dialogs(limit=limit)
            self.filtered_dialogs = self.dialogs.copy()

            if focused_dialog_key is not None:
                for i, dialog in enumerate(self.filtered_dialogs):
                    if self._get_dialog_key(dialog) == focused_dialog_key:
                        self.current_dialog_index = i
                        break
                else:
                    self.current_dialog_index = min(self.current_dialog_index, max(0, len(self.filtered_dialogs) - 1))

            self.refresh_dialog_list()
            self.dialogs_loaded = True
            self.set_status(f"Loaded {len(self.dialogs)} dialogs", 'success')

            self.create_task(self.load_dialogs_details(), context="Load dialog details")

        except Exception as e:
            self.report_exception("Error loading dialogs", e)

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

    # ------------------------------------------------------------------
    # Topics
    # ------------------------------------------------------------------

    async def load_topics(self, dialog):
        # Must be set before select_topic -> load_messages can reference it.
        self.current_dialog = dialog
        try:
            self.set_status("Loading topics...", 'status')

            try:
                from telethon.tl.functions.messages import GetForumTopicsRequest
                from telethon.tl.types import ForumTopic as TLForumTopic

                # Paginate until we have all topics (or hit a reasonable cap).
                all_topics = []
                offset_date = 0
                offset_id = 0
                offset_topic = 0
                PAGE = 100
                CAP = 500

                while len(all_topics) < CAP:
                    result = await self.client(GetForumTopicsRequest(
                        peer=dialog.entity,
                        offset_date=offset_date,
                        offset_id=offset_id,
                        offset_topic=offset_topic,
                        limit=PAGE,
                        q="",
                    ))
                    page = [t for t in result.topics if isinstance(t, TLForumTopic)]
                    all_topics.extend(page)

                    if len(page) < PAGE:
                        break  # last page

                    # Advance cursors from the last item
                    last = page[-1]
                    offset_date = last.date
                    offset_id = getattr(last, 'top_message', 0)
                    offset_topic = last.id

                self.topics = all_topics

            except Exception as e:
                self.report_exception("Topics error", e)
                self.topics = []

            for topic in self.topics:
                topic.id = int(topic.id)
                topic.title = getattr(topic, 'title', f"Topic #{topic.id}")

            self.topic_widgets = []
            self.refresh_topic_list()

            self.view_mode = "topics"
            self.header.set_text(f"Topics: {dialog.name or getattr(dialog.entity, 'title', None) or 'Unknown'}")
            self._update_main_view()

            if self.topics:
                self.current_topic_index = 0
                self.topic_list.set_focus(0)
                self.set_status(f"Loaded {len(self.topics)} topics", 'success')
            elif getattr(dialog.entity, 'forum', False):
                self.set_status("No topics found or API error", 'error')
            else:
                self.set_status("No topics found. Press Enter to open general chat.", 'status')

        except Exception as e:
            self.report_exception("Error loading topics wrapper", e)
            self.topics = []
            await self.load_messages(dialog, keep_position=False, focus_on_bottom=True)

    def refresh_topic_list(self):
        self.topic_list.clear()
        self.topic_widgets.clear()
        self.topic_indicators.clear()

        if not self.topics:
            self.topic_list.append(urwid.Text("No topics found. Press Enter to open general chat or ← to go back.", align='center'))
            self.refresh_ui()
            return

        for i, topic in enumerate(self.topics):
            indicator = urwid.Text("  ")
            self.topic_indicators.append(indicator)
            widget = TopicWidget(topic, i, callback=self.select_topic)
            row = urwid.Columns([('fixed', 2, indicator), widget], dividechars=0)
            self.topic_list.append(row)
            self.topic_widgets.append(widget)

        focus = min(self.current_topic_index, len(self.topic_list) - 1)
        self.topic_list.set_focus(max(0, focus))
        self.topic_list.set_focus_changed_callback(lambda _: self._update_topic_focus())
        self._update_topic_focus()
        self.refresh_ui()

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def load_messages(self, dialog, topic=None, keep_position=False, focus_on_bottom=False):
        try:
            old_message_id = None
            if keep_position and self.messages and self.current_message_index < len(self.messages):
                old_message_id = self.messages[self.current_message_index].id

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

            await self._enrich_messages(self.messages)

            self.view_mode = "messages"

            dialog_name = dialog.name or getattr(dialog.entity, 'title', None) or getattr(dialog.entity, 'first_name', None) or "Unknown"
            header_text = f"Chat: {dialog_name}"
            if topic:
                header_text = f"Topic: {getattr(topic, 'title', f'#{topic.id}')} - {dialog_name}"
            if getattr(dialog, 'member_count', None):
                online = getattr(dialog, 'online_count', None)
                header_text += f" ({online}/{dialog.member_count})" if online else f" ({dialog.member_count})"

            self.header.set_text(header_text)
            self._update_main_view()
            self.set_status(f"Loaded {len(self.messages)} messages", 'success')

            if self.messages:
                if focus_on_bottom:
                    self.current_message_index = len(self.messages) - 1
                elif keep_position and old_message_id:
                    for i, msg in enumerate(self.messages):
                        if msg.id == old_message_id:
                            self.current_message_index = i
                            break
                    else:
                        self.current_message_index = len(self.messages) - 1
                else:
                    self.current_message_index = len(self.messages) - 1

                self.message_list.set_focus(self.current_message_index)
                self.refresh_message_list()
            else:
                self.refresh_message_list()

        except Exception as e:
            self.report_exception("Messages error", e)

    async def get_sender_name_async(self, msg) -> str:
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
        except Exception:
            return "Unknown"

    def get_sender_name(self, msg) -> str:
        return getattr(msg, 'sender_name', "Unknown")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def select_dialog(self, index):
        if not self.filtered_dialogs or index >= len(self.filtered_dialogs):
            return

        dialog = self.filtered_dialogs[index]
        if not hasattr(dialog, 'entity'):
            self.set_status("Cannot open this dialog", 'error')
            self.refresh_ui()
            return

        self.current_dialog_index = index
        # ListBox already shows the focused item as highlighted via focus_map;
        # no need to rebuild the list just to change selection.

        if hasattr(dialog.entity, 'forum') and dialog.entity.forum:
            self.create_task(self.load_topics(dialog), context="Load topics")
        else:
            self.create_task(self.load_messages(dialog, keep_position=False, focus_on_bottom=True), context="Load messages")

    def select_topic(self, index):
        if not self.topics or index >= len(self.topics):
            self.create_task(self.load_messages(self.current_dialog, keep_position=False, focus_on_bottom=True), context="Load messages")
            return

        self.current_topic_index = index
        self.create_task(self.load_messages(self.current_dialog, topic=self.topics[index], keep_position=False, focus_on_bottom=True), context="Load topic messages")

    def refresh_dialog_list(self):
        self.dialog_list.clear()
        self.dialog_indicators.clear()

        if not self.filtered_dialogs:
            self.dialog_list.append(urwid.Text("No dialogs found", align='center'))
            self.refresh_ui()
            return

        for i, dialog in enumerate(self.filtered_dialogs):
            indicator = urwid.Text("  ")
            self.dialog_indicators.append(indicator)
            widget = DialogWidget(
                dialog, i,
                callback=self.select_dialog,
                member_count=getattr(dialog, 'member_count', None),
                online_count=getattr(dialog, 'online_count', None)
            )
            row = urwid.Columns([('fixed', 2, indicator), widget], dividechars=0)
            self.dialog_list.append(row)

        focus = min(self.current_dialog_index, len(self.dialog_list) - 1)
        self.dialog_list.set_focus(max(0, focus))
        self.dialog_list.set_focus_changed_callback(lambda _: self._update_dialog_focus())
        self._update_dialog_focus()
        self.refresh_ui()

    def refresh_message_list(self):
        self.message_list.clear()
        self.message_widgets.clear()
        self.message_indicators.clear()

        if not self.messages:
            self.message_list.append(urwid.Text("No messages", align='center'))
            self.refresh_ui()
            return

        for i, msg in enumerate(self.messages):
            indicator = urwid.Text("  ")
            self.message_indicators.append(indicator)
            widget = MessageWidget(
                msg,
                reply_text=getattr(msg, 'reply_text', ""),
                sender_name=self.get_sender_name(msg),
                reactions=getattr(msg, 'reactions_dict', {})
            )
            row = MessageRow(self, i, indicator, widget)
            self.message_list.append(row)
            self.message_widgets.append(widget)

        focus = min(self.current_message_index, len(self.message_list) - 1)
        self.message_list.set_focus(max(0, focus))
        self.message_list.set_focus_changed_callback(lambda _: self._update_message_focus())
        self._update_message_focus()
        self.refresh_ui()

    def _update_dialog_focus(self):
        if not self.dialog_indicators:
            return
        focus = self._sync_dialog_focus()
        for i, indicator in enumerate(self.dialog_indicators):
            indicator.set_text("> " if i == focus else "  ")

    def _update_topic_focus(self):
        if not self.topic_indicators:
            return
        focus = self._sync_topic_focus()
        for i, indicator in enumerate(self.topic_indicators):
            indicator.set_text("> " if i == focus else "  ")

    def _update_message_focus(self):
        if not self.message_indicators:
            return
        focus = self._sync_message_focus()
        for i, indicator in enumerate(self.message_indicators):
            indicator.set_text("> " if i == focus else "  ")

    # ------------------------------------------------------------------
    # Status / input
    # ------------------------------------------------------------------

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
                self.report_exception("Typing indicator error", e, notify=False)

        if self.current_dialog:
            self.create_task(start_typing(), context="Start typing indicator")

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
                self.report_exception("Stop typing indicator error", e, notify=False)

        if self.current_dialog:
            self.create_task(stop_typing(), context="Stop typing indicator")

        self.input_mode = False
        self.frame.footer = urwid.AttrMap(self.footer_widget, 'footer')
        self.input_callback = None
        self.refresh_ui()

    def convert_key_for_layout(self, key):
        if isinstance(key, str) and len(key) == 1:
            if self.keyboard_layout == 'ru' and key in REVERSE_LAYOUT_MAP['ru']:
                return REVERSE_LAYOUT_MAP['ru'][key]
        return key

    def handle_input_key(self, key) -> bool:
        if key == 'enter':
            text = self.input_edit.get_edit_text()

            words = text.split()
            if words and words[0] in plugin_command_handlers:
                result = execute_plugin_command(words[0], text, self.current_dialog, self)
                if result is not None:
                    text = result

            plugin_results = execute_plugin_hook('process_message_before_send', text, self.current_dialog, self)
            for _, new_text in plugin_results:
                if new_text is not None:
                    text = new_text

            cb = self.input_callback
            self.hide_input()

            if cb:
                self.create_task(cb(text), context="Input callback")
            return True
        elif key == 'esc':
            self.hide_input()
            self.set_status("Input cancelled")
            return True
        return False

    # ------------------------------------------------------------------
    # Messaging actions
    # ------------------------------------------------------------------

    async def send_message(self, text):
        if not text.strip() and not self.edit_message:
            self.set_status("Message is empty", 'error')
            return

        # In forum topics every outgoing message must carry reply_to=topic.id
        # so Telegram routes it into the correct thread.
        topic_id = self.current_topic.id if self.current_topic else None

        async def send_typing():
            try:
                await self.client(functions.messages.SetTypingRequest(
                    peer=self.current_dialog.entity,
                    action=types.SendMessageTypingAction(),
                    **({'top_msg_id': topic_id} if topic_id else {})
                ))
                await asyncio.sleep(0.5)
            except Exception:
                pass

        self.create_task(send_typing(), context="Send typing indicator")

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
                await self.client.send_message(
                    self.current_dialog.entity,
                    text,
                    reply_to=topic_id  # None → General; int → correct topic thread
                )
                self.set_status("Message sent", 'success')

            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=True)
        except Exception as e:
            self.report_exception("Send message error", e)

    async def send_file_with_caption(self, caption):
        if not self.file_to_send:
            self.set_status("No file selected", 'error')
            return

        topic_id = self.current_topic.id if self.current_topic else None

        async def send_typing():
            try:
                await self.client(functions.messages.SetTypingRequest(
                    peer=self.current_dialog.entity,
                    action=types.SendMessageTypingAction(),
                    **({'top_msg_id': topic_id} if topic_id else {})
                ))
                await asyncio.sleep(0.5)
            except Exception:
                pass

        self.create_task(send_typing(), context="Send typing indicator")

        try:
            mime_type, _ = mimetypes.guess_type(self.file_to_send)
            basename = os.path.basename(self.file_to_send)

            if mime_type and mime_type.startswith('image/'):
                self.set_status(f"Sending photo: {basename}...", 'status')
                await self.client.send_file(self.current_dialog.entity, self.file_to_send, caption=caption, reply_to=topic_id)
            elif mime_type and mime_type.startswith('video/'):
                self.set_status(f"Sending video: {basename}...", 'status')
                await self.client.send_file(self.current_dialog.entity, self.file_to_send, supports_streaming=True, caption=caption, reply_to=topic_id)
            else:
                self.set_status(f"Sending file: {basename}...", 'status')
                await self.client.send_file(self.current_dialog.entity, self.file_to_send, caption=caption, reply_to=topic_id)

            await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=True)
            self.set_status(f"File sent: {basename}", 'success')
            self.file_to_send = None

        except Exception as e:
            self.report_exception("Error sending file", e)

    async def download_media(self, message):
        if not message or not message.media:
            self.set_status("No media in this message", 'error')
            return

        try:
            self.set_status("Downloading media...", 'status')

            os.makedirs(DOWNLOADS_DIR, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if message.photo:
                ext, file_type = ".jpg", "photo"
            elif message.video:
                ext, file_type = ".mp4", "video"
            elif message.document:
                ext = ".bin"
                file_type = "document"
                if hasattr(message.document, 'attributes'):
                    for attr in message.document.attributes:
                        if isinstance(attr, types.DocumentAttributeFilename):
                            ext = os.path.splitext(attr.file_name)[1]
                            break
            elif message.voice:
                ext, file_type = ".ogg", "voice message"
            elif message.audio:
                ext, file_type = ".mp3", "audio"
            else:
                ext, file_type = ".bin", "media"

            filename = f"{file_type}_{timestamp}{ext}"
            file_path = os.path.join(DOWNLOADS_DIR, filename)

            await self.client.download_media(message.media, file_path)
            self.set_status(f"Downloaded: {filename}", 'success')

        except Exception as e:
            self.report_exception("Download error", e)

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
            self.report_exception("Error deleting message", e)

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
            self.report_exception("Error sending reaction", e)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

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

            await self._enrich_messages(self.messages)

            if self.messages:
                self.current_message_index = len(self.messages) - 1
                self.refresh_message_list()

            self.set_status(f"Found {len(self.messages)} messages for '{query}'", 'success')

        except Exception as e:
            self.report_exception("Search error", e)

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

            query_lower = query.strip().lower()
            filtered_contacts = []
            for contact in contacts:
                if isinstance(contact, types.User):
                    name = ((contact.first_name or "") + " " + (contact.last_name or "")).strip()
                    if query_lower in name.lower():
                        filtered_contacts.append(contact)

            if not filtered_contacts:
                self.set_status(f"No contacts found for '{query}'", 'error')
                return

            self.filtered_dialogs = [
                ContactDialog(
                    entity=c,
                    name=((c.first_name or "") + " " + (c.last_name or "")).strip()
                )
                for c in filtered_contacts
            ]
            self.current_dialog_index = 0
            self.refresh_dialog_list()
            self.set_status(f"Found {len(self.filtered_dialogs)} contacts", 'success')

        except Exception as e:
            self.report_exception("Contact search error", e)

    # ------------------------------------------------------------------
    # Panel/overlay management
    # ------------------------------------------------------------------

    def show_settings(self):
        self.in_settings = True
        self.settings_widget = SettingsWidget(self)
        self.frame.body = self.settings_widget
        self.refresh_ui()

    def close_settings(self):
        self.in_settings = False
        self._restore_body()
        self.refresh_ui()

    def show_search(self):
        self.in_search = True
        self.search_widget = SearchWidget(self)
        self.frame.body = self.search_widget
        self.refresh_ui()

    def close_search(self):
        self.in_search = False
        self._restore_body()
        self.refresh_ui()

    def show_file_browser(self):
        self.in_file_browser = True
        self.file_browser = FileBrowserWidget(self, self.send_file_with_caption)
        self.frame.body = self.file_browser
        self.refresh_ui()

    def close_file_browser(self):
        self.in_file_browser = False
        self._restore_body()
        self.refresh_ui()

    def show_reaction_picker(self, message):
        self.in_reaction_picker = True
        self.reaction_picker = ReactionPickerWidget(self, message)
        self.frame.body = self.reaction_picker
        self.refresh_ui()

    def close_reaction_picker(self):
        self.in_reaction_picker = False
        self._restore_body()
        self.refresh_ui()

    def show_plugin_manager(self):
        self.in_plugin_manager = True
        self.plugin_manager = PluginManagerWidget(self)
        self.frame.body = self.plugin_manager
        self.refresh_ui()

    def close_plugin_manager(self):
        self.in_plugin_manager = False
        self.in_plugin_settings = False
        self.view_mode = "dialogs"
        self.header.set_text("Dialogs")
        self._restore_body()
        self.refresh_ui()

    def show_plugin_settings(self, plugin_name, plugin_info=None):
        if plugin_info is None:
            for p in loaded_plugins:
                if p['name'] == plugin_name:
                    plugin_info = p
                    break

        if plugin_info:
            self.in_plugin_settings = True
            self.current_plugin_settings = plugin_name
            widget = PluginSettingsWidget(self, plugin_name, plugin_info)
            self.frame.body = widget
            self.refresh_ui()
        else:
            self.set_status(f"Plugin {plugin_name} not found", 'error')
            self.show_plugin_manager()

    def apply_theme(self, theme_name):
        if theme_name in DEFAULT_THEMES:
            self.palette = DEFAULT_THEMES[theme_name]
            if self.urwid_loop:
                self.urwid_loop.screen.register_palette(self.palette)
                self.title.set_text("LinuxGram Beta")
                self.refresh_ui()

    # ------------------------------------------------------------------
    # Keyboard handler
    # ------------------------------------------------------------------

    def handle_keypress(self, key):
        if not self.input_mode and isinstance(key, str) and len(key) == 1:
            key = self.convert_key_for_layout(key)

        if self.input_mode:
            self.handle_input_key(key)
            return

        if self.in_settings:
            if key == 'esc':
                self.close_settings()
            return

        if self.in_search:
            if key == 'esc':
                self.close_search()
            return

        if self.in_file_browser:
            if key == 'esc':
                self.close_file_browser()
                self.set_status("File browser closed", 'status')
            return

        if self.in_reaction_picker:
            if key == 'esc':
                self.close_reaction_picker()
                self.set_status("Reaction picker closed", 'status')
            return

        if self.in_plugin_manager or self.in_plugin_settings:
            return

        if self.show_help:
            self.close_help()
            return

        if key in ('q', 'Q'):
            self.exit_app()
            return

        if key in ('h', 'H'):
            self.open_help()
            return

        # ----------------------------------------------------------------
        # Dialog / Topic / Message navigation
        #
        # up / down / page up / page down / home / end are handled natively
        # by urwid's ListBox (both for Button-based and selectable-widget
        # lists).  Those keys are consumed inside the widget tree and never
        # reach unhandled_input.  We only need to handle action keys here
        # and read the current focused position from the ListBox when we do.
        # ----------------------------------------------------------------

        if self.view_mode == "dialogs":
            if not self.filtered_dialogs:
                return

            if key == 'enter':
                idx = self._get_listbox_focus(self.dialog_listbox)
                self.select_dialog(idx)
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
            if key == 'enter':
                idx = self._get_listbox_focus(self.topic_listbox)
                self.select_topic(idx)
            elif key == 'left':
                self.view_mode = "dialogs"
                self.current_topic_index = 0
                self.header.set_text("Dialogs")
                self._update_main_view()
                self.set_status("Back to dialogs")

        elif self.view_mode == "messages":
            if not self.messages:
                return

            # Read current focused message once; used by all action branches.
            msg_idx = self._get_listbox_focus(self.message_listbox)
            # Keep internal index in sync so keep_position logic stays correct.
            if 0 <= msg_idx < len(self.messages):
                self.current_message_index = msg_idx

            if key in ('j', 'down', 'n', 'о', 'т'):
                self._move_message_focus(delta=1)
                return
            elif key in ('k', 'up', 'p', 'л', 'з'):
                self._move_message_focus(delta=-1)
                return
            elif key in ('page down', ' ', 'space'):
                self._move_message_focus(delta=10)
                return
            elif key in ('page up', 'b', 'и'):
                self._move_message_focus(delta=-10)
                return
            elif key in ('home', 'g', 'п'):
                self._move_message_focus(absolute=0)
                return
            elif key in ('end', 'G', 'П'):
                self._move_message_focus(absolute=len(self.messages) - 1)
                return

            if key == 'left':
                if self.current_topic:
                    self.view_mode = "topics"
                    self.current_message_index = 0
                    self.header.set_text(f"Topics: {self.current_dialog.name or getattr(self.current_dialog.entity, 'title', None) or 'Unknown'}")
                    self._update_main_view()
                    self.set_status("Back to topics")
                else:
                    self.view_mode = "dialogs"
                    self.current_message_index = 0
                    self.header.set_text("Dialogs")
                    self._update_main_view()
                    self.set_status("Back to dialogs")
            elif key == 'enter':
                self.show_input("Message: ", self.send_message)
            elif key in ('r', 'R'):
                if 0 <= msg_idx < len(self.messages):
                    message = self.messages[msg_idx]
                    self.reply_to_message = message
                    self.reply_mode = True
                    self.set_status(f"Replying to message from {self.get_sender_name(message)}", 'status')
                    self.show_input("Reply: ", self.send_message)
            elif key in ('e', 'E'):
                if 0 <= msg_idx < len(self.messages):
                    message = self.messages[msg_idx]
                    if message.out:
                        self.edit_message = message
                        self.edit_mode = True
                        self.set_status(f"Editing message: {message.text[:50] if message.text else '[Media]'}", 'status')
                        self.show_input("Edit message: ", self.send_message)
                    else:
                        self.set_status("You can only edit your own messages", 'error')
            elif key == 'delete':
                if 0 <= msg_idx < len(self.messages):
                    self.create_task(self.delete_message(self.messages[msg_idx]), context="Delete message")
            elif key in ('s', 'S'):
                self.show_settings()
            elif key in ('/', '?'):
                self.show_input("Search messages: ", self.search_messages)
            elif key in ('d', 'D'):
                if 0 <= msg_idx < len(self.messages):
                    message = self.messages[msg_idx]
                    if message.media:
                        self.create_task(self.download_media(message), context="Download media")
                    else:
                        self.set_status("No media in this message", 'error')
            elif key in ('f', 'F'):
                self.show_file_browser()
            elif key in ('t', 'T'):
                if 0 <= msg_idx < len(self.messages):
                    self.show_reaction_picker(self.messages[msg_idx])
            elif key == 'esc':
                if self.reply_mode:
                    self.reply_mode = False
                    self.reply_to_message = None
                    self.set_status("Reply mode cancelled")
                elif self.edit_mode:
                    self.edit_mode = False
                    self.edit_message = None
                    self.set_status("Edit mode cancelled")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def exit_app(self):
        self.cancel_qr_login()

        if self.urwid_loop:
            try:
                self.urwid_loop.stop()
            except Exception:
                pass

        if self.client and self.client.is_connected():
            async def disconnect():
                try:
                    await self.client.disconnect()
                except Exception:
                    pass

            if self.loop:
                try:
                    # FIX: previously guarded by `is_running()` which is False
                    # after urwid stops, so disconnect was silently skipped.
                    if self.loop.is_running():
                        self.create_task(disconnect(), context="Disconnect client")
                    else:
                        self.loop.run_until_complete(disconnect())
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Telegram event handlers
    # ------------------------------------------------------------------

    async def handler_new_message(self, event):
        try:
            chat_id = _get_peer_chat_id(event.message.peer_id)

            if event.is_private and not event.message.out:
                if config.get("notifications", {}).get("private_chats", True):
                    sender = await event.get_sender()
                    sender_name = sender.first_name if sender else "Unknown"
                    self.set_status(f"New message from {sender_name}", 'success')

            if self.view_mode == "dialogs":
                self._sync_dialog_focus()
                self.create_task(self.load_dialogs_async(), context="Load dialogs")
            elif self.view_mode == "messages" and self.current_dialog:
                try:
                    current_chat_id = getattr(self.current_dialog.entity, 'id', None)
                    if chat_id == current_chat_id:
                        at_bottom = self._is_message_focus_at_bottom()
                        await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=at_bottom)
                except Exception:
                    pass
        except Exception as e:
            self.report_exception("New message handler error", e)

    async def handler_message_edited(self, event):
        try:
            chat_id = _get_peer_chat_id(event.message.peer_id)

            if self.view_mode == "messages" and self.current_dialog:
                try:
                    current_chat_id = getattr(self.current_dialog.entity, 'id', None)
                    if chat_id == current_chat_id:
                        at_bottom = self._is_message_focus_at_bottom()
                        await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=at_bottom)
                except Exception:
                    pass
        except Exception as e:
            self.report_exception("Edited message handler error", e)

    async def handler_message_deleted(self, event):
        try:
            # FIX: was an explicit append-loop; list() is equivalent and cleaner.
            deleted_ids = list(event.deleted_ids)

            if self.view_mode == "messages" and self.current_dialog:
                try:
                    current_chat_id = getattr(self.current_dialog.entity, 'id', None)
                    if current_chat_id in deleted_ids:
                        at_bottom = self._is_message_focus_at_bottom()
                        await self.load_messages(self.current_dialog, topic=self.current_topic, keep_position=True, focus_on_bottom=at_bottom)
                except Exception:
                    pass
        except Exception as e:
            self.report_exception("Deleted message handler error", e)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    global config
    configure_logging()
    config = load_config()

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    logger.info("LinuxGram %s started", __version__)

    tui = LinuxGramTUI()

    try:
        tui.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as exc:
        logger.exception("Fatal application error: %s", exc)
        raise
    finally:
        tui.exit_app()


if __name__ == '__main__':
    main()
