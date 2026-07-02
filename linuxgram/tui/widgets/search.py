#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   search_widget linuxgram!   #
########################

import urwid


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
            filtered = [d for d in self.parent.dialogs if d.name and query.lower() in d.name.lower()]

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
