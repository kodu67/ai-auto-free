import os
import sys
import platform
from locale_manager import LocaleManager
from logo import print_logo
from elevate import elevate
import requests
import json
import logging
from cursor_usage import CursorUsageChecker


def is_admin():
    """Yönetici yetkilerini kontrol eder"""
    try:
        if platform.system() == "Windows":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin()
        else:  # Linux/macOS
            return os.geteuid() == 0
    except:
        return False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)


class AutoFreeApp:
    def __init__(self, test_mode=False):
        checker = CursorUsageChecker()
        self.usage = checker.get_usage()
        self.locale_manager = LocaleManager()
        self.running = True
        self.test_mode = test_mode

        # Özellik durumları
        self.cursor_enabled = True
        self.cursor_maintenance = False
        self.cursor_maintenance_message = ""
        self.windsurf_enabled = True
        self.windsurf_maintenance = False
        self.windsurf_maintenance_message = ""

        # Program versiyonu
        self.current_version = self._get_version()

    def _is_admin(self):
        """Yönetici yetkilerini kontrol eder"""
        try:
            return is_admin()
        except Exception as e:
            return False

    def _request_admin(self):
        """Yönetici yetkisi ister"""
        try:
            if not self._is_admin():
                elevate(graphical=False)
                sys.exit()
        except Exception as e:
            return False
        return True

    def check_admin_rights(self):
        """Yönetici yetkilerini kontrol eder ve gerekirse ister"""
        if not self._is_admin():
            self.clear_screen()
            print_logo()
            print("\n" + self.locale_manager.get_text("admin.need_admin"))
            print(self.locale_manager.get_text("admin.requesting"))

            if not self._request_admin():
                print("\n" + self.locale_manager.get_text("admin.failed"))
                input("\n" + self.locale_manager.get_text("common.press_enter"))
                return False
        return True

    def clear_screen(self):
        """Ekranı temizler"""
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    def show_main_menu(self):
        """Ana menüyü gösterir"""
        self.clear_screen()
        print_logo()
        print("\n   " + self.locale_manager.get_text("menu.title"))

        # Cursor kullanım istatistiklerini göster
        if self.usage:
            print("-" * 30)
            print(" " + self.locale_manager.get_text("usage_stats.title"))
            for model, requests in self.usage.items():
                print(
                    f"> {model}: [{requests:,} {self.locale_manager.get_text('usage_stats.requests')}]"
                )
            print("-" * 30 + "\n")

        # Telegram grubu davetini göster
        try:
            if self.test_mode:
                settings_path = os.path.join(
                    os.path.dirname(__file__), "settings.json"
                )
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            else:
                url = "https://raw.githubusercontent.com/kodu67/ai-auto-free/refs/heads/main/settings.json"
                response = requests.get(url, timeout=5)
                settings = response.json()

            telegram_settings = settings.get("telegram", {})
            group_url = telegram_settings.get("group", "")
            if group_url:
                message_template = telegram_settings.get("message", {}).get(
                    self.locale_manager.current_locale,
                    telegram_settings["message"]["en"],  # Fallback to English
                )
                print("\n" + message_template.format(group_url))
        except Exception as e:
            pass

        print("\n" + self.locale_manager.get_text("menu.select_option"))
        print("   " + self.locale_manager.get_text("menu.cursor"))
        print("   " + self.locale_manager.get_text("menu.windsurf"))
        print("   " + self.locale_manager.get_text("menu.machine_id_reset"))
        print("   " + self.locale_manager.get_text("menu.exit"))

    def run_cursor_creator(self):
        """Cursor hesap oluşturucuyu çalıştırır"""
        if not self.cursor_enabled:
            print(
                "\n   "
                + self.locale_manager.get_text("features.disabled").format(
                    self.locale_manager.get_text("menu.cursor")
                )
            )
            input("\n   " + self.locale_manager.get_text("common.press_enter"))
            return

        if self.cursor_maintenance:
            print(f"\n   {self.cursor_maintenance_message}")
            input("\n   " + self.locale_manager.get_text("common.press_enter"))
            return

        try:
            from machine_id_reset import MachineIDResetter

            resetter = MachineIDResetter()
            # resetter._kill_cursor_processes()

            from cursor_pro_keep_alive import main

            self.clear_screen()
            print_logo()
            self.run_machine_id_reset(show_continue=False)
            print("\n")
            main()

        except Exception as e:
            print(
                "\n   "
                + self.locale_manager.get_text("cursor.registration_failed")
            )
            input("\n   " + self.locale_manager.get_text("common.press_enter"))

    def run_machine_id_reset(self, show_continue=True):
        """Machine ID sıfırlama işlemini çalıştırır"""
        self.clear_screen()
        print("\n" + self.locale_manager.get_text("machine_id_reset.starting"))

        try:
            from machine_id_reset import MachineIDResetter

            resetter = MachineIDResetter()
            success, message = resetter.reset_machine_id()

            if success:
                print(
                    "\n   "
                    + self.locale_manager.get_text("machine_id_reset.success")
                )
                print(
                    "\n   "
                    + self.locale_manager.get_text("machine_id_reset.changes")
                )
                print(message)
            else:
                print(
                    "\n   "
                    + self.locale_manager.get_text("machine_id_reset.failed")
                )
                print(message)

        except Exception as e:
            print(
                "\n" + self.locale_manager.get_text("machine_id_reset.failed")
            )
        if show_continue:
            input("\n" + self.locale_manager.get_text("common.press_enter"))

    def run_windsurf_creator(self):
        """Windsurf hesap oluşturucuyu çalıştırır"""
        if not self.windsurf_enabled:
            print(
                "\n   "
                + self.locale_manager.get_text("features.disabled").format(
                    self.locale_manager.get_text("menu.windsurf")
                )
            )
            input("\n   " + self.locale_manager.get_text("common.press_enter"))
            return

        if self.windsurf_maintenance:
            print(f"\n   {self.windsurf_maintenance_message}")
            input("\n   " + self.locale_manager.get_text("common.press_enter"))
            return

        self.clear_screen()
        print("\n   " + self.locale_manager.get_text("windsurf.starting"))

        try:
            from windsurf_account_creator import WindsurfAccountCreator

            creator = WindsurfAccountCreator()
            success, result = creator.create_account()

            if success:
                print(
                    "\n"
                    + self.locale_manager.get_text(
                        "windsurf.registration_success"
                    )
                )
                print(
                    "\n" + self.locale_manager.get_text("common.account_info")
                )
                print("+" + "-" * 50 + "+")
                print(
                    f"| {self.locale_manager.get_text('common.email'):<15}: {result['email']:<32} |"
                )
                print(
                    f"| {self.locale_manager.get_text('common.password'):<15}: {result['password']:<32} |"
                )
                print("+" + "-" * 50 + "+")
                print("\n" + "+" + "-" * 70 + "+")
                print(
                    f"| {self.locale_manager.get_text('common.token'):<15}: {result['token']:<52} |"
                )
                print("+" + "-" * 70 + "+")
            else:
                print(
                    "\n   "
                    + self.locale_manager.get_text(
                        "windsurf.registration_failed"
                    )
                )
                print(
                    f"   {self.locale_manager.get_text('common.error')}: {result}"
                )

        except Exception as e:
            print(
                "\n   "
                + self.locale_manager.get_text("windsurf.registration_failed")
            )

        input("\n" + self.locale_manager.get_text("common.press_enter"))

    def check_settings(self):
        """Uzak ayarları kontrol eder"""
        try:
            if self.test_mode:
                settings_path = os.path.join(
                    os.path.dirname(__file__), "settings.json"
                )
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            else:
                url = "https://raw.githubusercontent.com/kodu67/ai-auto-free/refs/heads/main/settings.json"
                response = requests.get(url, timeout=5)
                settings = response.json()

            # Versiyon kontrolü
            latest_version = settings.get("latest_version")
            if latest_version and latest_version != self.current_version:
                print("\n" + self.locale_manager.get_text("updates.available"))
                print(
                    self.locale_manager.get_text("updates.message").format(
                        latest_version
                    )
                )
                print(
                    self.locale_manager.get_text(
                        "updates.current_version"
                    ).format(self.current_version)
                )
                print(
                    self.locale_manager.get_text(
                        "updates.latest_version"
                    ).format(latest_version)
                )
                print(
                    self.locale_manager.get_text("updates.download").format(
                        "https://github.com/kodu67/ai-auto-free/releases/latest"
                    )
                )
                print()
                input(self.locale_manager.get_text("common.press_enter"))

            # Özellik kontrolü
            features = settings.get("features", {})

            # Cursor kontrolü
            cursor_settings = features.get("cursor", {})
            if not cursor_settings.get("enabled", True):
                self.cursor_enabled = False
            if cursor_settings.get("maintenance", False):
                self.cursor_maintenance = True
                self.cursor_maintenance_message = cursor_settings[
                    "maintenance_message"
                ][self.locale_manager.current_locale]

            # Windsurf kontrolü
            windsurf_settings = features.get("windsurf", {})
            if not windsurf_settings.get("enabled", True):
                self.windsurf_enabled = False
            if windsurf_settings.get("maintenance", False):
                self.windsurf_maintenance = True
                self.windsurf_maintenance_message = windsurf_settings[
                    "maintenance_message"
                ][self.locale_manager.current_locale]

        except Exception as e:
            pass

    def run(self):
        """Uygulamayı çalıştırır"""
        while self.running:
            self.show_main_menu()
            choice = input("\n> ")

            if choice == "1":
                self.run_cursor_creator()
            elif choice == "2":
                self.run_windsurf_creator()
            elif choice == "3":
                self.run_machine_id_reset()
            elif choice == "4":
                self.running = False
            else:
                input(
                    "\n" + self.locale_manager.get_text("menu.invalid_choice")
                )

    def _get_version(self):
        """Mevcut sürümü settings.json'dan alır"""
        try:
            if self.test_mode:
                settings_path = os.path.join(
                    os.path.dirname(__file__), "settings.json"
                )
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            else:
                url = "https://raw.githubusercontent.com/kodu67/ai-auto-free/refs/heads/main/settings.json"
                response = requests.get(url, timeout=5)
                settings = response.json()
            return settings.get("version", "1.0.0")
        except:
            return "1.0.0"  # Fallback versiyon


if __name__ == "__main__":
    # Test modu için:
    # app = AutoFreeApp(test_mode=True)

    # Normal mod için:
    app = AutoFreeApp()  # Test modunu kapattık

    if app.check_admin_rights():
        app.check_settings()  # Ayarları kontrol et
        app.run()
    else:
        sys.exit(1)
