import os
import sys
import logging
import platform
from locale_manager import LocaleManager
from logo import print_logo
from elevate import elevate

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
    def __init__(self):
        self.locale_manager = LocaleManager()
        self.running = True

    def _is_admin(self):
        """Yönetici yetkilerini kontrol eder"""
        try:
            return is_admin()
        except Exception as e:
            logging.error(f"Admin kontrol hatası: {str(e)}")
            return False

    def _request_admin(self):
        """Yönetici yetkisi ister"""
        try:
            if not self._is_admin():
                elevate(graphical=False)
                sys.exit()
        except Exception as e:
            logging.error(f"Yönetici yetkileri alınamadı: {str(e)}")
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
            os.system('cls')
        else:
            os.system('clear')

    def show_main_menu(self):
        """Ana menüyü gösterir"""
        self.clear_screen()
        print_logo()
        print("\n" + self.locale_manager.get_text("menu.title"))
        print("\n" + self.locale_manager.get_text("menu.select_option"))
        print(self.locale_manager.get_text("menu.cursor"))
        print(self.locale_manager.get_text("menu.windsurf"))
        print(self.locale_manager.get_text("menu.machine_id_reset"))
        print(self.locale_manager.get_text("menu.exit"))

    def run_cursor_creator(self):
        """Cursor hesap oluşturucuyu çalıştırır"""
        try:
            from machine_id_reset import MachineIDResetter
            resetter = MachineIDResetter()
            #resetter._kill_cursor_processes()

            from cursor_pro_keep_alive import main
            self.clear_screen()
            print_logo()
            self.run_machine_id_reset(show_continue=False)
            print("\n")
            main()

        except Exception as e:
            logging.error(f"Cursor hesap oluşturucu çalıştırılamadı: {str(e)}")
            print("\n" + self.locale_manager.get_text("cursor.registration_failed"))
            input("\n" + self.locale_manager.get_text("common.press_enter"))

    def run_machine_id_reset(self, show_continue=True):
        """Machine ID sıfırlama işlemini çalıştırır"""
        self.clear_screen()
        print("\n" + self.locale_manager.get_text("machine_id_reset.starting"))

        try:
            from machine_id_reset import MachineIDResetter
            resetter = MachineIDResetter()
            success, message = resetter.reset_machine_id()

            if success:
                print("\n" + self.locale_manager.get_text("machine_id_reset.success"))
                print("\n" + self.locale_manager.get_text("machine_id_reset.changes"))
                print(message)
            else:
                print("\n" + self.locale_manager.get_text("machine_id_reset.failed"))
                print(message)

        except Exception as e:
            logging.error(f"{self.locale_manager.get_text('common.error')}: {str(e)}")
            print("\n" + self.locale_manager.get_text("machine_id_reset.failed"))
        if show_continue:
            input("\n" + self.locale_manager.get_text("common.press_enter"))

    def run_windsurf_creator(self):
        """Windsurf hesap oluşturucuyu çalıştırır"""
        self.clear_screen()
        print("\n" + self.locale_manager.get_text("windsurf.starting"))

        try:
            from windsurf_account_creator import WindsurfAccountCreator
            creator = WindsurfAccountCreator()
            success, result = creator.create_account()

            if success:
                print("\n" + self.locale_manager.get_text("windsurf.registration_success"))
                print("\n" + self.locale_manager.get_text("common.account_info"))
                print("+" + "-"*50 + "+")
                print(f"| {self.locale_manager.get_text('common.email'):<15}: {result['email']:<32} |")
                print(f"| {self.locale_manager.get_text('common.password'):<15}: {result['password']:<32} |")
                print("+" + "-"*50 + "+")
                print("\n" + "+" + "-"*70 + "+")
                print(f"| {self.locale_manager.get_text('common.token'):<15}: {result['token']:<52} |")
                print("+" + "-"*70 + "+")
            else:
                print("\n" + self.locale_manager.get_text("windsurf.registration_failed"))
                print(f"{self.locale_manager.get_text('common.error')}: {result}")

        except Exception as e:
            logging.error(f"{self.locale_manager.get_text('common.error')}: {str(e)}")
            print("\n" + self.locale_manager.get_text("windsurf.registration_failed"))

        input("\n" + self.locale_manager.get_text("common.press_enter"))

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
                input("\nInvalid choice. Press Enter to continue...")

if __name__ == "__main__":
    app = AutoFreeApp()
    if app.check_admin_rights():
        app.run()
    else:
        sys.exit(1)
