import os
import random
import platform
from .locale import Locale
from config.settings import Settings


class Helper:
    def __init__(self):
        self.locale = Locale()
        self.settings = Settings()
        self.system = platform.system()

    def print_logo(self):
        """Logo yazdırır"""
        print(f"""
    ╔═╗╦  ╔═╗╦ ╦╔╦╗╔═╗  ╔═╗╦═╗╔═╗╔═╗
    ╠═╣║  ╠═╣║ ║ ║ ║ ║  ╠╣ ╠╦╝║╣ ║╣
    ╩ ╩╩  ╩ ╩╩═╩ ╩ ╚═╝  ╩  ╩╚═╚═╝╚═╝ v{self.settings.get_version()} - {self.system}
        """)

    def is_windows(self):
        return self.system == "Windows"

    def is_macos(self):
        return self.system == "Darwin"

    def is_linux(self):
        return self.system == "Linux"

    def clear_screen(self):
        """Ekranı temizler"""
        return "-CLEAR-"

    def get_bitcoin(self):
        """Bitcoin bağış bilgisini gösterir"""
        btc = self.settings.get_bitcoin_address()
        return self.locale.get_text("bitcoin").format("(" + btc["name"] + ")\n " + btc["address"])

    def show_repo(self):
        """Repo adresini gösterir"""
        return self.settings.get_repo_address()

    def get_landing_message(self):
        """Giriş mesajını gösterir"""
        landing_message = self.settings.get_settings_json().get("message", {}).get(
                self.locale.current_locale, ""
            )
        return landing_message

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

    def check_updates(self):
        """Güncellemeleri kontrol eder ve güncelleme bilgilerini döndürür"""
        try:
            settings_json = self.settings.get_settings_json()
            current_version = self.settings.get_version()
            latest_version = settings_json.get("latest_version")
            update_info = {
                "needs_update": False,
                "latest_version": latest_version,
                "changelog": "",
                "features": {
                    "cursor": {"enabled": True, "maintenance": False, "message": ""},
                    "windsurf": {"enabled": True, "maintenance": False, "message": ""}
                }
            }

            # Versiyon kontrolü
            if latest_version and current_version:
                # Versiyon numaralarını parçalara ayır
                current_parts = [int(x) for x in current_version.split('.')]
                latest_parts = [int(x) for x in latest_version.split('.')]

                # Eksik parçaları 0 ile doldur
                while len(current_parts) < 3:
                    current_parts.append(0)
                while len(latest_parts) < 3:
                    latest_parts.append(0)

                # Versiyon karşılaştırması
                for i in range(3):
                    if latest_parts[i] > current_parts[i]:
                        update_info["needs_update"] = True
                        update_info["changelog"] = (
                            settings_json.get("changelog", {})
                            .get(latest_version, {})
                            .get(self.locale.current_locale, "")
                        )
                        break
                    elif latest_parts[i] < current_parts[i]:
                        break

            # Özellik kontrolü
            features = settings_json.get("features", {})

            # Cursor kontrolü
            cursor_settings = features.get("cursor", {})
            if not cursor_settings.get("enabled", True):
                update_info["features"]["cursor"]["enabled"] = False
            if cursor_settings.get("maintenance", False):
                update_info["features"]["cursor"]["maintenance"] = True
                update_info["features"]["cursor"]["message"] = cursor_settings["maintenance_message"][self.locale.current_locale]

            # Windsurf kontrolü
            windsurf_settings = features.get("windsurf", {})
            if not windsurf_settings.get("enabled", True):
                update_info["features"]["windsurf"]["enabled"] = False
            if windsurf_settings.get("maintenance", False):
                update_info["features"]["windsurf"]["maintenance"] = True
                update_info["features"]["windsurf"]["message"] = windsurf_settings["maintenance_message"][self.locale.current_locale]

            return update_info

        except Exception as e:
            raise Exception(f"Update Check Error: {str(e)}")
