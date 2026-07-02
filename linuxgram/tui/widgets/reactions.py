#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   reaction_widget linuxgram!   #
########################

import urwid


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
        self.parent.create_task(self.parent.send_reaction(self.message, reaction), context="Send reaction")
        self.parent.close_reaction_picker()

    def keypress(self, size, key):
        if key == 'esc':
            self.parent.close_reaction_picker()
            return None
        return super().keypress(size, key)
