import PySimpleGUI as sg
import json
from datetime import datetime
from .app import AutoFreeApp
from config import constants
import threading
from auth.cursor_auth import CursorDatabaseManager

class MainUI(AutoFreeApp):
    def __init__(self):
        super().__init__()
        sg.theme('LightGrey1')
        self.window = None
        self.account_data = self.logger.get_accounts_as_list()
        self.console_output = ""
        self.cursor_enabled = True
        self.cursor_maintenance = False
        self.windsurf_enabled = True
        self.windsurf_maintenance = False
        self.processing = False
        self.selected_account = None

        self.imap_enabled = self.user_settings.get_email_verifier() == "imap"
        self.imap_settings = self.user_settings.get_imap_settings()

    def get_table_data(self):
        """Tablo için sadece servis, email ve tarih bilgilerini döndürür"""
        return [[account[0], account[1], account[5]] for account in self.account_data]

    def get_account_details(self, index):
        """Seçilen hesabın tüm detaylarını döndürür"""
        if index is None or index >= len(self.account_data):
            return None
        account = self.account_data[index]
        return {
            'service': account[0],
            'email': account[1],
            'password': account[2],
            'token': account[3],
            'usage': account[4],
            'date': account[5]
        }

    def create_settings_window(self):
        """Ayarlar penceresini oluşturur"""
        layout = [
            [sg.Frame(self.locale.get_text('settings.title'), [
                [sg.Text(self.locale.get_text('settings.browser_visibility')),
                 sg.Checkbox(self.locale.get_text('settings.enabled'), key='-BROWSER_VISIBLE-', default=self.user_settings.is_browser_visible(), enable_events=True)],
                [sg.Text(self.locale.get_text('settings.email_verifier')),
                 sg.Radio("TempMail", 'EMAIL', key='-EMAIL_TEMP-', default=not self.imap_enabled, enable_events=True),
                 sg.Radio("IMAP", 'EMAIL', key='-EMAIL_IMAP-', default=self.imap_enabled, enable_events=True)],
                [sg.pin(sg.Frame(self.locale.get_text('settings.imap_settings'), [
                    [sg.Text("Server"), sg.Input(key='-IMAP_SERVER-', size=(35,1), default_text=self.imap_settings.get("IMAP_SERVER", ""))],
                    [sg.Text("User"), sg.Input(key='-IMAP_USER-', size=(35,1), default_text=self.imap_settings.get("IMAP_USER", ""))],
                    [sg.Text("Password"), sg.Input(key='-IMAP_PASS-', password_char='*', size=(35,1), default_text=self.imap_settings.get("IMAP_PASS", ""))],
                    [sg.Text("Port"), sg.Input(key='-IMAP_PORT-', size=(35,1), default_text=self.imap_settings.get("IMAP_PORT", ""))],
                    [sg.Button(self.locale.get_text('settings.save_imap'), key='-SAVE_IMAP-')]
                ], key='-IMAP_FRAME-', visible=self.imap_enabled))]
            ])],
        ]
        return sg.Window(self.locale.get_text('settings.title'), layout, modal=True, finalize=True)

    def handle_settings_window(self):
        """Ayarlar penceresini yönetir"""
        settings_window = self.create_settings_window()
        while True:
            event, values = settings_window.read()

            if event in (sg.WIN_CLOSED, '-SETTINGS_CLOSE-'):
                break

            if event == '-EMAIL_IMAP-':
                self.imap_enabled = True
                settings_window['-IMAP_FRAME-'].update(visible=True)
                self.user_settings.set_email_verifier("imap")

            if event == '-EMAIL_TEMP-':
                self.imap_enabled = False
                settings_window['-IMAP_FRAME-'].update(visible=False)
                self.user_settings.set_email_verifier("temp")

            if event == '-SAVE_IMAP-':
                self.imap_settings = {
                    'IMAP_SERVER': values['-IMAP_SERVER-'],
                    'IMAP_USER': values['-IMAP_USER-'],
                    'IMAP_PASS': values['-IMAP_PASS-'],
                    'IMAP_PORT': values['-IMAP_PORT-']
                }
                if (self.user_settings.set_imap_settings(self.imap_settings)):
                    sg.popup(self.locale.get_text('settings.saved'), title='OK')
                else:
                    sg.popup(self.locale.get_text('settings.failed'), title='Error')

            if event == '-BROWSER_VISIBLE-':
                if self.user_settings.toggle_browser_visibility():
                    settings_window['-BROWSER_VISIBLE-'].update(self.user_settings.is_browser_visible())

        settings_window.close()
        del settings_window

    def create_layout(self):
        # Tablo başlıkları
        headers = [
            self.locale.get_text('common.service'),
            self.locale.get_text('common.email'),
            self.locale.get_text('common.date')
        ]

        # Sol panel - Ana içerik
        left_content = [
            [sg.Text('AI Auto Free', font=('Helvetica', 20), justification='center')],
            [
                sg.Button(self.locale.get_text('menu.cursor'), size=(20,1), key='-CURSOR-'),
                sg.Button(self.locale.get_text('menu.windsurf'), size=(20,1), key='-WINDSURF-'),
                sg.Button(self.locale.get_text('menu.settings'), size=(10,1), key='-SETTINGS-')
            ],
            [sg.HorizontalSeparator()],
            [sg.Table(
                values=self.get_table_data(),
                headings=headers,
                auto_size_columns=False,
                justification='left',
                num_rows=8,
                key='-TABLE-',
                enable_events=True,
                col_widths=[15, 35, 15]
            )],
            [sg.HorizontalSeparator()],
            [sg.Frame(self.locale.get_text('common.account_info'), [
                [sg.Text(f"{self.locale.get_text('common.service')}:", size=(10,1)),
                 sg.Input(key='-DETAIL-SERVICE-', size=(70,1), readonly=True)],
                [sg.Text(f"{self.locale.get_text('common.email')}:", size=(10,1)),
                 sg.Input(key='-DETAIL-EMAIL-', size=(55,1), readonly=True),
                 sg.Button(self.locale.get_text('common.switch_account'), key='-SWITCH-ACCOUNT-', visible=False)],
                [sg.Text(f"{self.locale.get_text('common.password')}:", size=(10,1)),
                 sg.Input(key='-DETAIL-PASSWORD-', size=(70,1), readonly=True)],
                [sg.Text(f"{self.locale.get_text('common.token')}:", size=(10,1)),
                 sg.Input(key='-DETAIL-TOKEN-', size=(70,1), readonly=True)],
                [sg.Text(f"{self.locale.get_text('usage_stats.requests')}:", size=(10,1)),
                 sg.Input(key='-DETAIL-USAGE-', size=(70,1), readonly=True)],
                [sg.Text(f"{self.locale.get_text('common.date')}:", size=(10,1)),
                 sg.Input(key='-DETAIL-DATE-', size=(70,1), readonly=True)]
            ], key='-DETAIL-FRAME-', visible=False, expand_x=True)],
            [sg.Text(self.helper.get_landing_message(), key='-LANDING-MESSAGE-', size=(80, None), visible=True, expand_x=True, text_color='#467246')],
            [sg.Input(self.locale.get_text("menu.donate").format(self.settings.get_bitcoin_address()["name"] + ": " + self.settings.get_bitcoin_address()["address"]), size=(80, 1), visible=True, readonly=True, text_color='#471E45', border_width=0)]
        ]

        # Sağ panel - Konsol
        right_panel = [
            [sg.Multiline(
                size=(50, 30),
                key='-CONSOLE-',
                disabled=True,
                autoscroll=True,
                reroute_stdout=True,
                reroute_stderr=True,
                background_color='black',
                text_color='white',
                visible=False
            )]
        ]

        # Ana layout
        layout = [
            [
                sg.Column(left_content, vertical_alignment='top', expand_x=True),
                sg.VSeparator(),
                sg.Column(right_panel, vertical_alignment='top', key='-RIGHT_PANEL-')
            ]
        ]

        return layout

    def update_console(self, text):
        """Konsola yeni metin ekler"""
        # Çince hata mesajlarını ve diğer gereksiz mesajları filtrele
        ignore_list = [
            "与页面的连接已断开。", # Sayfa bağlantısı kesildi
            "没有找到元素。", # Eleman bulunamadı
            "页面可能已关闭。", # Sayfa kapanmış olabilir
            "无法访问页面。" # Sayfaya erişilemiyor
        ]

        if text in ignore_list or (isinstance(text, str) and any(msg in text for msg in ignore_list)):
            return

        if isinstance(text, str):
            if text.startswith("-") and text.endswith("-"):
                if text == "-REFRESH-TABLE-":
                    self.account_data = self.logger.get_accounts_as_list()
                    self.window['-TABLE-'].update(values=self.get_table_data())
                    return

        self.console_output += f"{text}\n"
        self.window['-CONSOLE-'].update(self.console_output)

    def update_details(self, index):
        """Detay panelini günceller"""
        details = self.get_account_details(index)
        if details:
            self.window['-DETAIL-FRAME-'].update(visible=True)
            self.window['-DETAIL-SERVICE-'].update(details['service'])
            self.window['-DETAIL-EMAIL-'].update(details['email'])
            self.window['-DETAIL-PASSWORD-'].update(details['password'])
            self.window['-DETAIL-TOKEN-'].update(details['token'])
            self.window['-DETAIL-USAGE-'].update(details['usage'])
            self.window['-DETAIL-DATE-'].update(details['date'])

            # Cursor hesabı için geçiş butonu göster/gizle
            if details['service'] == "Cursor":
                self.window['-SWITCH-ACCOUNT-'].update(visible=True)
            else:
                self.window['-SWITCH-ACCOUNT-'].update(visible=False)
        else:
            self.window['-DETAIL-FRAME-'].update(visible=False)

    def clear_console(self):
        """Konsolu temizler"""
        self.console_output = ""
        self.window['-CONSOLE-'].update(self.console_output)

    def update_usage(self, index):
        """Seçilen hesabın usage bilgisini günceller"""
        if index is None or index >= len(self.account_data):
            return

        account = self.account_data[index]
        token = account[3]  # token 3. indexte

        if account[0] == "Cursor" and token:  # service "Cursor" ise ve token varsa
            usage = self.usage_checker.cursor_get_usage(token)
            self.account_data[index][4] = usage  # usage bilgisini 4. indexte güncelle

    def run(self):
        self.window = sg.Window(self.locale.get_text('menu.title'), self.create_layout(), finalize=True)
        self.check_updates()

        while True:
            event, values = self.window.read(timeout=100)

            if event == sg.WIN_CLOSED:
                break

            if event == '-TABLE-':
                if len(values['-TABLE-']) > 0:
                    self.selected_account = values['-TABLE-'][0]
                    self.update_usage(self.selected_account)  # Önce usage'ı güncelle
                    self.update_details(self.selected_account)  # Sonra detayları göster

            if event == '-SETTINGS-':
                self.handle_settings_window()

            if event == '-CURSOR-' and not self.processing:
                self.processing = True
                self.window['-CONSOLE-'].update(visible=True)
                threading.Thread(target=self.handle_cursor_creation, daemon=True).start()

            if event == '-WINDSURF-' and not self.processing:
                self.processing = True
                self.window['-CONSOLE-'].update(visible=True)
                threading.Thread(target=self.handle_windsurf_creation, daemon=True).start()

            if event == '-SWITCH-ACCOUNT-':
                details = self.get_account_details(self.selected_account)
                if details and details['token']:
                    token = details['token'].split("%3A%3A")[1]
                    cursor_db = CursorDatabaseManager()
                    cursor_db.update_auth(
                        email=details['email'],
                        access_token=token,
                        refresh_token=token
                    )
                    sg.popup(self.locale.get_text('common.switch_account_success'), title='Cursor')

        self.window.close()

    def handle_cursor_creation(self):
        try:
            self.clear_console()
            for log in self.run_cursor_creator():
                if log == "-CLEAR-":
                    self.clear_console()
                else:
                    self.update_console(log)
        finally:
            self.processing = False

    def handle_windsurf_creation(self):
        try:
            self.clear_console()
            for log in self.run_windsurf_creator():
                if log == "-CLEAR-":
                    self.clear_console()
                else:
                    self.update_console(log)
        finally:
            self.processing = False

    def check_updates(self):
        """Güncellemeleri kontrol eder ve güncelleme diyaloğunu gösterir"""
        try:
            update_info = self.helper.check_updates()

            # Güncelleme kontrolü
            if update_info["needs_update"]:
                update_message = (
                    f"{self.locale.get_text('updates.available')}\n\n"
                    f"{self.locale.get_text('updates.message').format(update_info['latest_version'])}\n\n"
                    f"{self.locale.get_text('updates.download').format(constants.RELEASE_URL)}"
                )

                if update_info["changelog"]:
                    update_message += f"\n\n{self.locale.get_text('updates.changelog')}\n{update_info['changelog']}"

                sg.popup_scrolled(
                    update_message,
                    title=self.locale.get_text('updates.title'),
                    size=(60, 10)
                )

            # Özellik durumlarını güncelle
            cursor_feature = update_info["features"]["cursor"]
            self.cursor_enabled = cursor_feature["enabled"]
            self.cursor_maintenance = cursor_feature["maintenance"]
            if cursor_feature["maintenance"]:
                self.cursor_maintenance_message = cursor_feature["message"]

            windsurf_feature = update_info["features"]["windsurf"]
            self.windsurf_enabled = windsurf_feature["enabled"]
            self.windsurf_maintenance = windsurf_feature["maintenance"]
            if windsurf_feature["maintenance"]:
                self.windsurf_maintenance_message = windsurf_feature["message"]

        except Exception as e:
            sg.popup_error(str(e))
