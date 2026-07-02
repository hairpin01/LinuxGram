#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   dialog_widgets linuxgram!   #
########################

import urwid


class DialogWidget(urwid.WidgetWrap):
    """Dialog row.  Visual highlight when focused is handled by the outer
    AttrMap(focus_map) added in refresh_dialog_list()."""

    def __init__(self, dialog, index, callback=None, member_count=None, online_count=None):
        self.dialog = dialog
        self.index = index
        self.callback = callback

        name = dialog.name or "Unknown"
        if getattr(dialog, 'unread_count', 0) > 0:
            name = f"* {name} ({dialog.unread_count})"

        info = ""
        if member_count:
            info = f" ({online_count}/{member_count})" if online_count else f" ({member_count})"

        self.button = urwid.Button(f"  {name}{info}")
        urwid.connect_signal(self.button, 'click', self.on_click)
        super().__init__(self.button)

    def on_click(self, button):
        if self.callback:
            self.callback(self.index)


class TopicWidget(urwid.WidgetWrap):
    """Topic row.  Visual highlight when focused is handled by the outer
    AttrMap(focus_map) added in refresh_topic_list()."""

    def __init__(self, topic, index, callback=None):
        self.topic = topic
        self.index = index
        self.callback = callback

        title = getattr(topic, 'title', f"Topic #{topic.id}")
        self.button = urwid.Button(f"  {title}")
        urwid.connect_signal(self.button, 'click', self.on_click)
        super().__init__(self.button)

    def on_click(self, button):
        if self.callback:
            self.callback(self.index)
