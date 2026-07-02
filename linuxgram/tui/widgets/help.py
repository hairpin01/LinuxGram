#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   help_widget linuxgram!   #
########################

import urwid


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
            "  J/K or N/P - Select next/previous message",
            "  Space/B - Page down/up messages",
            "  G/Home, Shift+G/End - First/last message",
            "  ← - Back to dialogs",
            "  Enter - Send message",
            "  R - Reply to selected message (including your own)",
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
