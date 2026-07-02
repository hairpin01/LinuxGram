#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   message_widgets linuxgram!   #
########################

import textwrap

import urwid


class MessageWidget(urwid.WidgetWrap):
    """A single message row.

    Selectable so that ListBox can move focus between messages natively
    (up/down/pgup/pgdn/home/end are handled by the ListBox; all other keys
    are returned unhandled so they bubble up to unhandled_input).
    Visual selection highlight is provided by the outer AttrMap focus_map
    added in refresh_message_list(), not here.
    """

    def __init__(self, message, reply_text="", sender_name="", reactions=None, index=None, on_select=None):
        self.message = message
        self.reply_text = reply_text
        self.sender_name = sender_name
        self.reactions = reactions or {}
        self.index = index
        self.on_select = on_select

        self.text_widget = urwid.Text("")
        super().__init__(self._build())

    def selectable(self):
        return False

    def keypress(self, size, key):
        # Return every key so the ListBox can scroll, and action keys
        # bubble further up to unhandled_input.
        return key

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press' and button == 1 and self.on_select is not None and self.index is not None:
            self.on_select(self.index)
            return True
        return False

    def _build(self):
        time_str = self.message.date.strftime("%H:%M")

        content_lines = []
        if self.message.text:
            wrapped_text = textwrap.wrap(self.message.text, width=80)
            content = (wrapped_text[0] + " ...") if len(wrapped_text) > 3 else " ".join(wrapped_text)
            content_lines.append(content)

        if self.message.media:
            if self.message.photo:
                media_type = "PHOTO"
            elif self.message.video:
                media_type = "VIDEO"
            elif self.message.voice:
                media_type = "VOICE"
            elif self.message.document:
                media_type = "DOCUMENT"
            elif self.message.audio:
                media_type = "AUDIO"
            elif self.message.sticker:
                media_type = "STICKER"
            else:
                media_type = "MEDIA"
            content_lines.append(media_type)

        if not content_lines:
            content_lines.append("[Empty]")

        content = " | ".join(content_lines)
        if len(content) > 120:
            content = content[:117] + "..."

        reply_indicator = ""
        if self.reply_text:
            preview = self.reply_text[:27] + "..." if len(self.reply_text) > 30 else self.reply_text
            reply_indicator = f" [↩ {preview}]"

        line = f"[{time_str}] {self.sender_name}: {content}{reply_indicator}"

        if self.reactions:
            reactions_display = []
            for label, count in self.reactions.items():
                reactions_display.append(f"{label} x{count}" if count > 1 else label)
            line += "\n  " + " ".join(reactions_display)

        self.text_widget.set_text(line)
        return self.text_widget


class MessageRow(urwid.WidgetWrap):
    """Selectable message row with exact mouse/keyboard focus handling."""

    def __init__(self, parent, index, indicator, widget):
        self.parent = parent
        self.index = index
        super().__init__(urwid.Columns([('fixed', 2, indicator), widget], dividechars=0))

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key == 'up':
            self.parent._move_message_focus(delta=-1, update_status=False)
            return None
        if key == 'down':
            self.parent._move_message_focus(delta=1, update_status=False)
            return None
        if key == 'page up':
            self.parent._move_message_focus(delta=-10)
            return None
        if key == 'page down':
            self.parent._move_message_focus(delta=10)
            return None
        if key == 'home':
            self.parent._move_message_focus(absolute=0)
            return None
        if key == 'end':
            self.parent._move_message_focus(absolute=len(self.parent.messages) - 1)
            return None
        return key

    def mouse_event(self, size, event, button, col, row, focus):
        if event != 'mouse press':
            return False
        if button == 1:
            self.parent._set_message_focus(self.index)
            return True
        if button == 4:
            self.parent._move_message_focus(delta=-3, update_status=False)
            return True
        if button == 5:
            self.parent._move_message_focus(delta=3, update_status=False)
            return True
        return False
