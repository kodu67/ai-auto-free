import os
import random
import platform
from .locale import Locale
from config.settings import Settings
from rich.panel import Panel
from rich.console import Console


class Helper:
    def __init__(self):
        self.locale = Locale()
        self.settings = Settings()

    def print_logo(self):
        """Logo yazdırır"""
        print(f"""
    ╔═╗╦  ╔═╗╦ ╦╔╦╗╔═╗  ╔═╗╦═╗╔═╗╔═╗
    ╠═╣║  ╠═╣║ ║ ║ ║ ║  ╠╣ ╠╦╝║╣ ║╣
    ╩ ╩╩  ╩ ╩╩═╩ ╩ ╚═╝  ╚  ╩╚═╚═╝╚═╝ v{self.settings.get_version()}
        """)

    def is_windows(self):
        return os.name == "nt"

    def is_macos(self):
        return os.name == "posix" and "darwin" in os.uname().sysname.lower()

    def is_linux(self):
        return not self.is_windows() and not self.is_macos()

    def clear_screen(self):
        """Ekranı temizler"""
        if self.is_windows():
            os.system("cls")
        else:
            os.system("clear")

    def show_bitcoin(self):
        """Bitcoin bağış bilgisini gösterir"""
        btc = self.settings.get_bitcoin_address()
        console = Console()
        console.print(Panel.fit(self.locale.get_text("bitcoin").format("(" + btc["name"] + ")\n " + btc["address"]),
            title="💰 Donate",
            border_style="yellow",
        ))

    def show_repo(self):
        """Repo adresini gösterir"""
        return self.settings.get_repo_address()

    def show_landing_message(self):
        """Giriş mesajını gösterir"""
        landing_message = self.settings.get_settings_json().get("message", {}).get(
                self.locale.current_locale, ""
            )
        if landing_message:
            print(f" {landing_message}")

    def show_main(self):
        """Ana menüyü gösterir"""
        self.clear_screen()
        self.print_logo()

    def press_enter(self):
        return input("\n   " + self.locale.get_text("common.press_enter"))

    def kill_cursor_processes(self):
        try:
            if self.is_windows():
                import subprocess

                subprocess.run(
                    ["taskkill", "/F", "/IM", "Cursor.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                os.system("pkill -f Cursor")
        except Exception:
            pass

    def get_random_name(self):
        """Rastgele bir isim döndürür"""
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]
        return random.choice(first_names), random.choice(last_names)

    def generate_password(self, length=12):
        """Güçlü bir şifre oluşturur"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    def get_src_path(self):
        return os.path.dirname(os.path.dirname(__file__))

    def is_admin(self):
        """Yönetici yetkilerini kontrol eder"""
        try:
            if platform.system() == "Windows":
                import ctypes

                return ctypes.windll.shell32.IsUserAnAdmin()
            else:  # Linux/macOS
                return os.geteuid() == 0
        except Exception as e:
            raise e
