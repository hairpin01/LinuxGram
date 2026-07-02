#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   file_browser linuxgram!   #
########################

from pathlib import Path

import urwid

from linuxgram.core.utils import format_file_size


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
                name = f"{item.name}/"
                button = urwid.Button(name)
                urwid.connect_signal(button, 'click', lambda button, path=item: self.enter_directory(path))
                self.file_list.append(urwid.AttrMap(button, 'dialog_name'))

            for item in files:
                size_str = format_file_size(item.stat().st_size)
                name = f"{item.name} ({size_str})"
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
