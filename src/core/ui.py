import customtkinter as ctk
from .app import AutoFreeApp
from config import constants
import threading
from auth.cursor_auth import CursorDatabaseManager
from src.services.proxy.proxy_service import ProxyService
from src.utils.usage import UsageChecker
import pyperclip


class MainUI(AutoFreeApp):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")

        self.window = None
        self.account_data = self.logger.get_accounts_as_list()
        self.console_output = ""
        self.cursor_enabled = True
        self.cursor_maintenance = False
        self.windsurf_enabled = True
        self.windsurf_maintenance = False
        self.processing = False
        self.selected_account = None
        self.proxy_service = ProxyService.get_instance()
        self.proxy_thread = None
        self.usage_checker = UsageChecker()

        self.imap_enabled = self.user_settings.get_email_verifier() == "imap"
        self.imap_settings = self.user_settings.get_imap_settings()

    def get_table_data(self):
        return [[account[0], account[1], account[5]] for account in self.account_data]

    def get_account_details(self, index):
        if index is None or index >= len(self.account_data):
            return None
        account = self.account_data[index]
        return {
            "service": account[0],
            "email": account[1],
            "password": account[2],
            "token": account[3],
            "usage": account[4],
            "date": account[5],
        }

    def create_settings_window(self):
        settings_window = ctk.CTkToplevel()
        settings_window.title(self.locale.get_text("settings.title"))
        settings_window.geometry("500x350")
        settings_window.resizable(False, False)

        main_frame = ctk.CTkFrame(settings_window, corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        # Browser visibility
        browser_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        browser_frame.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            browser_frame, text=self.locale.get_text("settings.browser_visibility")
        ).pack(side="left")
        browser_switch = ctk.CTkSwitch(
            browser_frame,
            text="",
            command=lambda: self.user_settings.toggle_browser_visibility(),
            width=40,
        )
        browser_switch.pack(side="right")
        browser_switch.select() if self.user_settings.is_browser_visible() else browser_switch.deselect()

        # Email verifier
        email_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        email_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(
            email_frame, text=self.locale.get_text("settings.email_verifier")
        ).pack(side="left")

        email_var = ctk.StringVar(value="imap" if self.imap_enabled else "temp")
        temp_radio = ctk.CTkRadioButton(
            email_frame,
            text="TempMail",
            variable=email_var,
            value="temp",
            command=lambda: self.user_settings.set_email_verifier("temp"),
        )
        imap_radio = ctk.CTkRadioButton(
            email_frame,
            text="IMAP",
            variable=email_var,
            value="imap",
            command=lambda: self.user_settings.set_email_verifier("imap"),
        )
        temp_radio.pack(side="right", padx=(0, 10))
        imap_radio.pack(side="right", padx=10)

        # IMAP settings
        imap_frame = ctk.CTkFrame(main_frame)
        imap_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            imap_frame,
            text=self.locale.get_text("settings.imap_settings"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=5)

        fields = [
            ("Server", "IMAP_SERVER"),
            ("User", "IMAP_USER"),
            ("Password", "IMAP_PASS"),
            ("Port", "IMAP_PORT"),
        ]

        entries = {}
        for label, key in fields:
            field_frame = ctk.CTkFrame(imap_frame, fg_color="transparent")
            field_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(field_frame, text=label, width=70).pack(side="left")
            entry = ctk.CTkEntry(field_frame, placeholder_text=label, justify="right")
            entry.pack(side="right", fill="x", expand=True)
            entry.insert(0, self.imap_settings.get(key, ""))
            if key == "IMAP_PASS":
                entry.configure(show="*")
            entries[key] = entry

        def save_imap():
            settings = {
                key: entries[key].get()
                for key in ["IMAP_SERVER", "IMAP_USER", "IMAP_PASS", "IMAP_PORT"]
            }
            if self.user_settings.set_imap_settings(settings):
                self.show_info(self.locale.get_text("settings.saved"))
            else:
                self.show_error(self.locale.get_text("settings.failed"))

        save_btn = ctk.CTkButton(
            imap_frame,
            text=self.locale.get_text("settings.save_imap"),
            command=save_imap,
            height=28,
        )
        save_btn.pack(pady=10)

        return settings_window

    def handle_settings_window(self):
        settings_window = self.create_settings_window()
        settings_window.grab_set()
        settings_window.wait_window()

    def create_layout(self):
        self.window = ctk.CTk()
        version = self.settings.get_version()
        self.window.title(f"AI Auto Free - v{version}")
        self.window.geometry("1000x605")
        self.window.resizable(False, False)
        self.window.iconbitmap("assets/icons/icon.ico")

        # Ana frame
        main_frame = ctk.CTkFrame(self.window, corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        # Üst panel
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=5)

        # Logo ve başlık
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.pack(side="left")
        title_label = ctk.CTkLabel(
            title_frame, text="AI Auto Free", font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=10)

        # Butonlar
        button_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        button_frame.pack(side="right")

        buttons = [
            (self.locale.get_text("menu.cursor"), "-CURSOR-"),
            (self.locale.get_text("menu.windsurf"), "-WINDSURF-"),
            (self.locale.get_text("menu.settings"), "-SETTINGS-"),
        ]

        def create_button_command(event_name):
            if event_name == "-SETTINGS-":
                return self.handle_settings_window
            return lambda: self.handle_button_click(event_name)

        for text, event in buttons:
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                width=100,
                height=32,
                command=create_button_command(event),
            )
            btn.pack(side="left", padx=5)

        # Proxy butonları
        proxy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        proxy_frame.pack(fill="x", padx=15, pady=5)

        self.start_proxy_button = ctk.CTkButton(
            proxy_frame,
            text=self.locale.get_text("proxy.buttons.start"),
            command=self.start_proxy,
            width=120,
        )
        self.start_proxy_button.pack(side="left", padx=5)

        self.stop_proxy_button = ctk.CTkButton(
            proxy_frame,
            text=self.locale.get_text("proxy.buttons.stop"),
            command=self.stop_proxy,
            width=120,
            state="disabled",
        )
        self.stop_proxy_button.pack(side="left", padx=5)

        # Content frame
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Sol panel
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)

        # Tablo
        self.table_frame = ctk.CTkFrame(left_frame)
        self.table_frame.pack(fill="both", expand=True, pady=(0, 5))

        headers = [
            self.locale.get_text("common.service"),
            self.locale.get_text("common.email"),
            self.locale.get_text("common.date"),
        ]

        header_frame = ctk.CTkFrame(self.table_frame, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", padx=1, pady=1)

        widths = [0.2, 0.4, 0.4]  # Sütun genişlik oranları
        for col, (header, width) in enumerate(zip(headers, widths)):
            label_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            label_frame.pack(side="left", fill="both", expand=True, padx=1)

            # E-posta ve tarih sütunları için sağa yaslı, diğerleri için sola yaslı
            anchor = "e" if col in [1, 2] else "w"
            label = ctk.CTkLabel(
                label_frame, text=header, font=ctk.CTkFont(weight="bold"), anchor=anchor
            )
            label.pack(fill="x", padx=5, pady=5)
            label_frame.configure(width=int(800 * width))

        # Tablo içeriği
        self.table_content = ctk.CTkScrollableFrame(
            self.table_frame, fg_color="transparent"
        )
        self.table_content.pack(fill="both", expand=True)
        self.update_table()

        # Detay frame
        self.detail_frame = ctk.CTkFrame(left_frame)
        self.detail_frame.pack(fill="x", pady=5)

        # Sağ panel - Konsol
        right_frame = ctk.CTkFrame(content_frame, width=300)
        right_frame.pack(side="right", fill="both", padx=(5, 0))
        right_frame.pack_propagate(False)

        self.console = ctk.CTkTextbox(right_frame, wrap="word", font=("Consolas", 11))
        self.console.pack(fill="both", expand=True, padx=1, pady=1)
        self.console.configure(state="disabled")

        # Proxy mesajları için text widget
        self.proxy_console = ctk.CTkTextbox(
            right_frame, wrap="word", font=("Consolas", 11), height=100
        )
        self.proxy_console.pack(fill="x", padx=1, pady=(10, 1))
        self.proxy_console.configure(state="disabled")

        # Alt bilgi
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=80)
        footer_frame.pack(fill="x", padx=10, pady=5)
        footer_frame.pack_propagate(False)

        # Sol taraftaki yeşil metin
        left_footer = ctk.CTkFrame(footer_frame, fg_color="transparent")
        left_footer.pack(side="left", fill="both", expand=True)

        landing_label = ctk.CTkLabel(
            left_footer,
            text=self.helper.get_landing_message(),
            wraplength=600,
            text_color="#659765",
            font=("Segoe UI", 11),
            justify="left",
            anchor="w",
        )
        landing_label.pack(fill="x", padx=5)

        # Sağ taraftaki bitcoin ve donate metinleri
        right_footer = ctk.CTkFrame(footer_frame, fg_color="transparent")
        right_footer.pack(side="right", fill="y")

        # Donate frame
        donate_frame = ctk.CTkFrame(right_footer, fg_color="transparent")
        donate_frame.pack(pady=5)

        # Donate metni
        donate_label = ctk.CTkLabel(
            donate_frame,
            text=self.locale.get_text("menu.donate").format(
                self.settings.get_bitcoin_address()["name"]
                + "\n"
                + self.settings.get_bitcoin_address()["address"]
            ),
            text_color="#D4DA8B",
            font=("Segoe UI", 11),
            justify="right",
        )
        donate_label.pack(side="left", padx=(0, 5))

        # Kopyalama butonu
        copy_btn = ctk.CTkButton(
            donate_frame,
            text=self.locale.get_text("menu.copy"),
            width=30,
            height=30,
            command=self.copy_btc,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
        )
        copy_btn.pack(side="right")

        return self.window

    def copy_btc(self):
        pyperclip.copy(self.settings.get_bitcoin_address()["address"])

    def update_table(self):
        for widget in self.table_content.winfo_children():
            widget.destroy()

        for row, data in enumerate(self.get_table_data()):
            row_frame = ctk.CTkFrame(
                self.table_content,
                fg_color=("gray95", "gray15") if row % 2 == 0 else "transparent",
                height=30,
            )
            row_frame.pack(fill="x", padx=1, pady=1)
            row_frame.pack_propagate(False)

            widths = [0.2, 0.4, 0.4]  # Sütun genişlik oranları
            for col, (value, width) in enumerate(zip(data, widths)):
                cell_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                cell_frame.pack(side="left", fill="both", expand=True, padx=1)

                # E-posta ve tarih sütunları için sağa yaslı, diğerleri için sola yaslı
                anchor = "e" if col in [1, 2] else "w"
                justify = "right" if col in [1, 2] else "left"
                label = ctk.CTkLabel(
                    cell_frame, text=value, anchor=anchor, justify=justify
                )
                label.pack(fill="x", padx=5)
                cell_frame.configure(width=int(800 * width))

                # Tıklama olayını ekle
                cell_frame.bind("<Button-1>", lambda e, r=row: self.update_details(r))
                label.bind("<Button-1>", lambda e, r=row: self.update_details(r))

    def update_details(self, index):
        details = self.get_account_details(index)
        if not details:
            return

        self.selected_account = index  # Seçili hesabı güncelle

        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        fields = [
            ("service", "common.service"),
            ("email", "common.email"),
            ("password", "common.password"),
            ("token", "common.token"),
            ("usage", "usage_stats.requests"),
            ("date", "common.date"),
        ]

        details_grid = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        details_grid.pack(fill="both", expand=True, padx=10, pady=5)

        for row, (key, label_text) in enumerate(fields):
            frame = ctk.CTkFrame(details_grid, fg_color="transparent", height=30)
            frame.pack(fill="x", pady=1)
            frame.pack_propagate(False)

            ctk.CTkLabel(
                frame,
                text=f"{self.locale.get_text(label_text)}:",
                width=100,
                anchor="e",
            ).pack(side="left", padx=5)

            entry = ctk.CTkEntry(frame, height=25)
            entry.pack(side="left", fill="x", expand=True, padx=5)

            # Eğer servis Cursor ise ve usage alanı ise, usage_checker ile limiti al
            if details["service"] == "Cursor" and key == "usage":
                usage_limit = self.usage_checker.cursor_get_usage(details["token"])
                entry.insert(0, usage_limit if usage_limit else str(details[key]))
            else:
                entry.insert(0, str(details[key]))

            entry.configure(state="readonly")

            if key == "email" and details["service"] == "Cursor":
                switch_btn = ctk.CTkButton(
                    frame,
                    text=self.locale.get_text("common.switch_account"),
                    command=lambda: self.handle_button_click("-SWITCH-ACCOUNT-"),
                    height=25,
                    width=100,
                )
                switch_btn.pack(side="right", padx=5)

    def update_console(self, text):
        ignore_list = [
            "与页面的连接已断开。",
            "没有找到元素。",
            "页面可能已关闭。",
            "无法访问页面。",
        ]

        if text in ignore_list or (
            isinstance(text, str) and any(msg in text for msg in ignore_list)
        ):
            return

        if isinstance(text, str):
            if text.startswith("-") and text.endswith("-"):
                if text == "-REFRESH-TABLE-":
                    self.account_data = self.logger.get_accounts_as_list()
                    self.update_table()
                    return

        self.console.configure(state="normal")
        self.console.insert("end", f"{text}\n")
        self.console.configure(state="disabled")
        self.console.see("end")

    def update_proxy_console(self, text):
        self.proxy_console.configure(state="normal")
        self.proxy_console.insert("end", f"{text}\n")
        self.proxy_console.configure(state="disabled")
        self.proxy_console.see("end")

    def show_info(self, message):
        info_window = ctk.CTkToplevel()
        info_window.title("Bilgi")
        info_window.geometry("800x200")

        ctk.CTkLabel(info_window, text=message).pack(pady=20)
        ctk.CTkButton(info_window, text="Tamam", command=info_window.destroy).pack()

    def show_error(self, message):
        error_window = ctk.CTkToplevel()
        error_window.title("Hata")
        error_window.geometry("300x100")

        ctk.CTkLabel(error_window, text=message, text_color="red").pack(pady=20)
        ctk.CTkButton(error_window, text="Tamam", command=error_window.destroy).pack()

    def handle_button_click(self, event):
        if event == "-CURSOR-" and not self.processing:
            self.processing = True
            self.console.configure(state="normal")
            self.console.delete("1.0", "end")
            self.console.configure(state="disabled")
            threading.Thread(target=self.handle_cursor_creation, daemon=True).start()

        elif event == "-WINDSURF-" and not self.processing:
            self.processing = True
            self.console.configure(state="normal")
            self.console.delete("1.0", "end")
            self.console.configure(state="disabled")
            threading.Thread(target=self.handle_windsurf_creation, daemon=True).start()

        elif event == "-SWITCH-ACCOUNT-":
            details = self.get_account_details(self.selected_account)
            if details and details["token"]:
                token = details["token"].split("%3A%3A")[1]
                cursor_db = CursorDatabaseManager()
                for log in cursor_db.update_auth(
                    email=details["email"], access_token=token, refresh_token=token
                ):
                    self.update_proxy_console(log)

    def handle_cursor_creation(self):
        try:
            for log in self.run_cursor_creator():
                if log == "-CLEAR-":
                    self.console.configure(state="normal")
                    self.console.delete("1.0", "end")
                    self.console.configure(state="disabled")
                else:
                    self.update_console(log)
        finally:
            self.processing = False

    def handle_windsurf_creation(self):
        try:
            for log in self.run_windsurf_creator():
                if log == "-CLEAR-":
                    self.console.configure(state="normal")
                    self.console.delete("1.0", "end")
                    self.console.configure(state="disabled")
                else:
                    self.update_console(log)
        finally:
            self.processing = False

    def check_updates(self):
        try:
            update_info = self.helper.check_updates()

            if update_info["needs_update"]:
                update_message = (
                    f"{self.locale.get_text('updates.available')}\n\n"
                    f"{self.locale.get_text('updates.message').format(update_info['latest_version'])}\n\n"
                    f"{self.locale.get_text('updates.download').format(constants.RELEASE_URL)}"
                )

                if update_info["changelog"]:
                    update_message += f"\n\n{self.locale.get_text('updates.changelog')}\n{update_info['changelog']}"

                self.show_info(update_message)

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
            self.show_error(str(e))

    def start_proxy(self):
        """Proxy'yi başlatır"""
        if not self.proxy_thread or not self.proxy_thread.is_alive():
            self.proxy_thread = threading.Thread(target=self._proxy_thread_func)
            self.proxy_thread.daemon = True
            self.proxy_thread.start()
            self.helper.kill_cursor_processes()

    def stop_proxy(self):
        """Proxy'yi durdurur"""
        if self.proxy_service.is_running():
            for status in self.proxy_service.stop_proxy():
                self.update_proxy_console(status)
            self.start_proxy_button.configure(state="normal")
            self.stop_proxy_button.configure(state="disabled")
            # Thread'i temizle
            self.proxy_thread = None

    def _proxy_thread_func(self):
        """Proxy thread fonksiyonu"""
        try:
            self.start_proxy_button.configure(state="disabled")
            for status in self.proxy_service.start_proxy():
                self.update_proxy_console(status)

            if self.proxy_service.is_running():
                self.stop_proxy_button.configure(state="normal")
            else:
                self.start_proxy_button.configure(state="normal")
        except Exception as e:
            self.update_proxy_console(f"ERR: {str(e)}")
            self.start_proxy_button.configure(state="normal")
            self.stop_proxy_button.configure(state="disabled")
            # Hata durumunda thread'i temizle
            self.proxy_thread = None

    def run(self):
        self.create_layout()
        self.check_updates()
        self.window.mainloop()
