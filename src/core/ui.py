import PySimpleGUI as sg
import json
from datetime import datetime

class MainUI:
    def __init__(self, locale, helper, settings, user_settings):
        sg.theme('LightGrey1')
        self.window = None
        self.account_data = []
        self.locale = locale
        self.helper = helper
        self.settings = settings
        self.user_settings = user_settings
        self.console_output = ""

    def create_layout(self):
        # Tablo başlıkları
        headers = ['İsim', 'Email', 'Şifre', 'Token', 'Limit', 'Oluşturma Tarihi']

        # Sol panel - Ana içerik
        left_panel = [
            [sg.Text('AI Auto Free', font=('Helvetica', 20), justification='center')],
            [
                sg.Button(self.locale.get_text('menu.cursor'), size=(20,1), key='-CURSOR-'),
                sg.Button(self.locale.get_text('menu.windsurf'), size=(20,1), key='-WINDSURF-')
            ],
            [sg.HorizontalSeparator()],
            [sg.Table(
                values=self.account_data,
                headings=headers,
                auto_size_columns=True,
                justification='left',
                num_rows=10,
                key='-TABLE-',
                enable_events=True
            )],
            [sg.HorizontalSeparator()],
            [sg.Frame('Ayarlar', [
                [sg.Text('Tarayıcı Görünürlüğü:'),
                 sg.Radio('Etkin', 'BROWSER', key='-BROWSER_VISIBLE-', default=True),
                 sg.Radio('Gizli', 'BROWSER', key='-BROWSER_HIDDEN-')],
                [sg.Text('Email Doğrulama:'),
                 sg.Radio('TempMail', 'EMAIL', key='-EMAIL_TEMP-', default=True, enable_events=True),
                 sg.Radio('IMAP', 'EMAIL', key='-EMAIL_IMAP-', enable_events=True)],
                [sg.pin(sg.Frame('IMAP Ayarları', [
                    [sg.Text('IMAP Sunucu:'), sg.Input(key='-IMAP_SERVER-', size=(45,1))],
                    [sg.Text('Email:'), sg.Input(key='-IMAP_EMAIL-', size=(45,1))],
                    [sg.Text('Şifre:'), sg.Input(key='-IMAP_PASSWORD-', password_char='*', size=(45,1))],
                    [sg.Text('Port:'), sg.Input(key='-IMAP_PORT-', size=(45,1))],
                    [sg.Button('IMAP Ayarlarını Kaydet', key='-SAVE_IMAP-')]
                ], key='-IMAP_FRAME-', visible=False))]
            ])],

        ]

        # Sağ panel - Konsol
        right_panel = [
            [sg.Multiline(
                size=(50, 22),
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
                sg.Column(left_panel, vertical_alignment='top'),
                sg.VSeparator(),
                sg.Column(right_panel, vertical_alignment='top', key='-RIGHT_PANEL-', visible=False)
            ]
        ]

        return layout

    def update_console(self, text):
        """Konsola yeni metin ekler"""
        self.console_output += f"{text}\n"
        self.window['-CONSOLE-'].update(self.console_output)

    def run(self):
        self.window = sg.Window('AI Auto Free', self.create_layout(), finalize=True)

        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                break

            if event == '-CURSOR-':
                self.window['-RIGHT_PANEL-'].update(visible=True)
                self.window['-CONSOLE-'].update(visible=True)
                self.update_console("Cursor hesabı oluşturuluyor...")
                self.update_console("1. Tarayıcı başlatılıyor")
                self.update_console("2. Kayıt sayfası açılıyor")
                self.update_console("3. Bilgiler dolduruluyor")
                # Cursor hesabı oluşturma işlemi
                new_account = ['Cursor', 'test@mail.com', '123456', 'token123', '25/150', datetime.now().strftime("%Y-%m-%d %H:%M")]
                self.account_data.append(new_account)
                self.window['-TABLE-'].update(values=self.account_data)
                self.update_console("4. Hesap başarıyla oluşturuldu!")

            if event == '-WINDSURF-':
                self.window['-RIGHT_PANEL-'].update(visible=True)
                self.window['-CONSOLE-'].update(visible=True)
                self.update_console("Windsurf hesabı oluşturuluyor...")
                self.update_console("1. Tarayıcı başlatılıyor")
                self.update_console("2. Kayıt sayfası açılıyor")
                self.update_console("3. Bilgiler dolduruluyor")
                # Windsurf hesabı oluşturma işlemi
                new_account = ['Windsurf', 'test2@mail.com', '654321', 'token456', '15/100', datetime.now().strftime("%Y-%m-%d %H:%M")]
                self.account_data.append(new_account)
                self.window['-TABLE-'].update(values=self.account_data)
                self.update_console("4. Hesap başarıyla oluşturuldu!")

            if event == '-EMAIL_IMAP-':
                self.window['-IMAP_FRAME-'].update(visible=True)

            if event == '-EMAIL_TEMP-':
                self.window['-IMAP_FRAME-'].update(visible=False)

            if event == '-SAVE_IMAP-':
                # IMAP ayarlarını kaydetme işlemi
                imap_settings = {
                    'server': values['-IMAP_SERVER-'],
                    'email': values['-IMAP_EMAIL-'],
                    'password': values['-IMAP_PASSWORD-'],
                    'port': values['-IMAP_PORT-']
                }
                sg.popup('IMAP ayarları kaydedildi!', title='Başarılı')

        self.window.close()
