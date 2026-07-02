#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   login_widget linuxgram!   #
##############################

import urwid

from linuxgram.core.credentials import load_credentials, save_credentials


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

        self.qr_button = urwid.Button("Login with QR")
        urwid.connect_signal(self.qr_button, 'click', self.qr_login)

        self.qr_refresh_button = urwid.Button("Refresh QR")
        urwid.connect_signal(self.qr_refresh_button, 'click', self.refresh_qr)

        self.back_button = urwid.Button("Back")
        urwid.connect_signal(self.back_button, 'click', self.prev_step)

        self.resend_button = urwid.Button("Resend SMS")
        urwid.connect_signal(self.resend_button, 'click', self.resend_code)

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
                urwid.Text("Code request sent. Check Telegram app first; SMS/call may take a minute."),
                self.code_edit,
                urwid.Divider(),
                urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.next_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.resend_button, 'button')),
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

        elif self.step == 5:
            qr_ascii = self.parent.qr_ascii or "Preparing QR code..."
            qr_url = self.parent.qr_url
            qr_status = self.parent.qr_status or "Open Telegram on your phone and scan this code."
            widgets.extend([
                urwid.Text("Login to Telegram", align='center'),
                urwid.Divider(),
                urwid.Text("QR login", align='left'),
                urwid.Text("Telegram app: Settings → Devices → Link Desktop Device"),
                urwid.Divider(),
                urwid.Text(qr_ascii, align='center'),
                urwid.Divider(),
                urwid.Text(qr_status),
                urwid.Text(f"URL fallback: {qr_url}" if qr_url else "URL fallback will appear here."),
                urwid.Divider(),
                urwid.Columns([
                    ('weight', 1, urwid.AttrMap(self.qr_refresh_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.back_button, 'button')),
                    ('weight', 1, urwid.AttrMap(self.cancel_button, 'button'))
                ])
            ])

        self._w.original_widget = urwid.Pile(widgets)
        self.parent.refresh_ui()

    def _save_api_credentials_from_form(self):
        api_id = self.api_id_edit.get_edit_text().strip()
        api_hash = self.api_hash_edit.get_edit_text().strip()

        if not api_id or not api_hash:
            self.parent.set_status("Please enter both API ID and Hash", 'error')
            return False

        try:
            api_id = int(api_id)
        except ValueError:
            self.parent.set_status("API ID must be a number", 'error')
            return False

        save_credentials(api_id, api_hash)
        self.parent.api_id = api_id
        self.parent.api_hash = api_hash
        return True

    def next_step(self, button):
        if self.step == 1:
            if not self._save_api_credentials_from_form():
                return
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
            self.parent.create_task(self.parent.async_start_login(), context="Start login")

        elif self.step == 3:
            code = self.code_edit.get_edit_text().strip()
            if not code:
                self.parent.set_status("Please enter code", 'error')
                return

            self.parent.login_code = code
            self.parent.set_status("Signing in...", 'status')
            self.parent.create_task(self.parent.async_sign_in_with_code(), context="Sign in with code")

        elif self.step == 4:
            password = self.password_edit.get_edit_text().strip()
            if not password:
                self.parent.set_status("Please enter password", 'error')
                return

            self.parent.login_password = password
            self.parent.set_status("Signing in with 2FA...", 'status')
            self.parent.create_task(self.parent.async_sign_in_with_password(), context="Sign in with password")

    def prev_step(self, button):
        if self.step == 5:
            self.parent.cancel_qr_login()
            self.step = 1
            self.update_content()
        elif self.step > 1:
            self.step -= 1
            self.update_content()

    def qr_login(self, button):
        if not self._save_api_credentials_from_form():
            return
        self.step = 5
        self.parent.qr_url = ""
        self.parent.qr_ascii = "Preparing QR code..."
        self.parent.qr_status = "Preparing QR login..."
        self.update_content()
        self.parent.start_qr_login()

    def refresh_qr(self, button):
        if self.step != 5:
            return
        self.parent.qr_ascii = "Refreshing QR code..."
        self.parent.qr_status = "Refreshing QR login..."
        self.update_content()
        self.parent.start_qr_login()

    def resend_code(self, button):
        if self.step != 3:
            return
        self.parent.set_status("Requesting a new SMS login code...", 'status')
        self.parent.create_task(self.parent.async_start_login(force_sms=True), context="Resend SMS login code")

    def cancel(self, button):
        self.parent.cancel_qr_login()
        self.parent.exit_app()
