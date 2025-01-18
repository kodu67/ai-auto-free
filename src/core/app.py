from utils.locale import Locale
from utils.helper import Helper
from utils.usage import UsageChecker
from config.settings import Settings
from config import constants
from config.user_settings import UserSettings


class AutoFreeApp:
    def __init__(self):
        self.helper = Helper()
        self.usage_checker = UsageChecker()
        self.cursor_usage = self.usage_checker.cursor_get_usage()
        self.locale = Locale()
        self.settings = Settings()
        self.user_settings = UserSettings()
        self.running = True

        # Özellik durumları
        self.cursor_enabled = True
        self.cursor_maintenance = False
        self.cursor_maintenance_message = ""
        self.windsurf_enabled = True
        self.windsurf_maintenance = False
        self.windsurf_maintenance_message = ""

    def check_admin_rights(self):
        """Yönetici yetkilerini kontrol eder ve gerekirse ister"""
        if not self.helper.is_admin():
            self.helper.show_main()
            print("\n" + self.locale.get_text("admin.need_admin"))

            if not self.helper.is_admin():
                input("\n" + self.locale.get_text("common.press_enter"))
                return False
        return True

    def show_main_menu(self):
        """Ana menüyü gösterir"""
        self.helper.show_main()

        # Cursor kullanım istatistiklerini göster
        if self.cursor_usage:
            print("- Cursor " + "-" * 10)
            for model, requests in self.cursor_usage.items():
                print(
                    f" > {model}: {requests}"
                )
            print("-" * 19 + "\n")

        # Giriş mesajını göster
        try:
            self.helper.show_landing_message()
            self.helper.show_repo()
            print("")
            self.helper.show_bitcoin()

        except Exception as e:
            print(e)

        print("\n " + self.locale.get_text("menu.select_option"))
        print("   " + self.locale.get_text("menu.cursor"))
        print("   " + self.locale.get_text("menu.windsurf"))
        print("   " + self.locale.get_text("menu.machine_id_reset"))
        print("   " + self.locale.get_text("menu.settings"))
        print("   " + self.locale.get_text("menu.exit"))

    def run_cursor_creator(self):
        """Cursor hesap oluşturucuyu çalıştırır"""
        if not self.cursor_enabled:
            print(
                "\n   "
                + self.locale.get_text("features.disabled").format(
                    self.locale.get_text("menu.cursor")
                )
            )

            if self.cursor_maintenance:
                print(f"\n   {self.cursor_maintenance_message}")

            self.helper.press_enter()
            return

        try:
            from auth.machine_id import CursorMachineIDResetter

            resetter = CursorMachineIDResetter()
            resetter.reset_machine_id()

            from auth.cursor_auth import CursorAuthManager

            self.helper.show_main()
            self.run_machine_id_reset(show_continue=False)
            print("\n")
            CursorAuthManager()

        except Exception as e:
            print(
                "\n   "
                + self.locale.get_text("cursor.registration_failed")
                + "\n"
                + str(e)
            )
            self.helper.press_enter()

    def run_machine_id_reset(self, show_continue=True):
        """Machine ID sıfırlama işlemini çalıştırır"""
        self.helper.clear_screen()
        print("\n" + self.locale.get_text("machine_id_reset.starting"))

        try:
            from auth.machine_id import CursorMachineIDResetter

            cursor_machine_id = CursorMachineIDResetter()
            success, message = cursor_machine_id.reset_machine_id()

            if success:
                print("\n   " + self.locale.get_text("machine_id_reset.success"))
                print("\n   " + self.locale.get_text("machine_id_reset.changes"))
                print(message)
            else:
                print("\n   " + self.locale.get_text("machine_id_reset.failed"))
                print(message)

        except Exception as e:
            print(
                "\n" + self.locale.get_text("machine_id_reset.failed") + "\n" + str(e)
            )

        if show_continue:
            self.helper.press_enter()

    def run_windsurf_creator(self):
        """Windsurf hesap oluşturucuyu çalıştırır"""
        if not self.windsurf_enabled:
            print(
                "\n   "
                + self.locale.get_text("features.disabled").format(
                    self.locale.get_text("menu.windsurf")
                )
            )
            self.helper.press_enter()
            return

        if self.windsurf_maintenance:
            print(f"\n   {self.windsurf_maintenance_message}")
            self.helper.press_enter()
            return

        self.helper.clear_screen()
        print("\n   " + self.locale.get_text("windsurf.starting"))

        from auth.windsurf_auth import WindsurfAuthManager

        WindsurfAuthManager()

    def check_settings(self):
        """Uzak ayarları kontrol eder"""
        try:
            settings = self.settings.get_settings_json()
            current_version = self.settings.get_version()
            # Versiyon kontrolü
            latest_version = settings.get("latest_version")
            if latest_version and int(latest_version) > int(current_version):
                print("\n" + self.locale.get_text("updates.available"))
                print(self.locale.get_text("updates.message").format(latest_version))
                print(
                    self.locale.get_text("updates.download").format(
                        constants.RELEASE_URL
                    )
                )
                changelog = (
                    settings.get("changelog", {})
                    .get(latest_version, {})
                    .get(self.locale.current_locale, "")
                )
                if changelog:
                    print(":: " + changelog)

                self.helper.press_enter()

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
                ][self.locale.current_locale]

            # Windsurf kontrolü
            windsurf_settings = features.get("windsurf", {})
            if not windsurf_settings.get("enabled", True):
                self.windsurf_enabled = False
            if windsurf_settings.get("maintenance", False):
                self.windsurf_maintenance = True
                self.windsurf_maintenance_message = windsurf_settings[
                    "maintenance_message"
                ][self.locale.current_locale]

        except Exception as e:
            print(e)

    def show_settings_menu(self):
        """Ayarlar menüsünü gösterir"""
        while True:
            self.helper.show_main()
            print("\n " + self.locale.get_text("settings.title"))

            # Tarayıcı görünürlüğü ayarı
            current_visibility = self.user_settings.is_browser_visible()
            print("\n   1. " + self.locale.get_text("settings.browser_visibility"))
            print(f"      {self.locale.get_text('settings.current_value')}: " +
                  f"[{self.locale.get_text('settings.yes') if current_visibility else self.locale.get_text('settings.no')}]")

            print("\n   2. " + self.locale.get_text("menu.back"))

            choice = input("\n > ")

            if choice == "1":
                print("\n   " + self.locale.get_text("settings.select_option"))
                option = input("   > ").strip().lower()

                if option in ['y', 'yes', 'e', 'evet']:
                    if not current_visibility:
                        self.user_settings.toggle_browser_visibility()
                    print("\n   " + self.locale.get_text("settings.saved"))
                    self.helper.press_enter()
                elif option in ['n', 'no', 'h', 'hayır']:
                    if current_visibility:
                        self.user_settings.toggle_browser_visibility()
                    print("\n   " + self.locale.get_text("settings.saved"))
                    self.helper.press_enter()
                else:
                    input("\n" + self.locale.get_text("menu.invalid_choice"))

            elif choice == "2":
                break
            else:
                input("\n" + self.locale.get_text("menu.invalid_choice"))

    def run(self):
        """Uygulamayı çalıştırır"""
        while self.running:
            self.show_main_menu()
            choice = input("\n > ")

            if choice == "1":
                self.run_cursor_creator()
            elif choice == "2":
                self.run_windsurf_creator()
            elif choice == "3":
                self.run_machine_id_reset()
            elif choice == "4":
                self.show_settings_menu()
            elif choice == "5":
                self.running = False
            else:
                input("\n" + self.locale.get_text("menu.invalid_choice"))
