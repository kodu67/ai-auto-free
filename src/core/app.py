from utils.locale import Locale
from utils.helper import Helper
from utils.usage import UsageChecker
from utils.logger import Logger
from config.settings import Settings
from config import constants
from config.user_settings import UserSettings

class AutoFreeApp:
    def __init__(self):
        self.locale = Locale()
        self.helper = Helper()
        self.usage_checker = UsageChecker()
        self.settings = Settings()
        self.user_settings = UserSettings()
        self.logger = Logger()

    def check_admin_rights(self):
        """Yönetici yetkilerini kontrol eder ve gerekirse ister"""
        if not self.helper.is_admin():
            self.helper.show_main()
            print("\n" + self.locale.get_text("admin.need_admin"))

            if not self.helper.is_admin():
                input("\n" + self.locale.get_text("common.press_enter"))
                return False
        return True

    def run_cursor_creator(self):
        """Cursor hesap oluşturucuyu çalıştırır"""
        try:
            from auth.cursor_auth import CursorAuthManager

            yield from self._run_machine_id_reset()
            yield "\n"
            cursor_auth = CursorAuthManager()
            yield from cursor_auth.create_cursor_account()

        except Exception as e:
            yield self.locale.get_text('cursor.registration_failed')
            yield str(e)

    def _run_machine_id_reset(self):
        """Machine ID sıfırlama işlemini çalıştırır"""
        yield self.locale.get_text("machine_id_reset.starting")

        try:
            from auth.machine_id import CursorMachineIDResetter

            cursor_machine_id = CursorMachineIDResetter()
            success, message = cursor_machine_id.reset_machine_id()
            if success:
                yield self.locale.get_text('machine_id_reset.success')
                yield self.locale.get_text('machine_id_reset.changes')
                yield message
            else:
                yield self.locale.get_text('machine_id_reset.failed')
                yield message

        except Exception as e:
            yield self.locale.get_text('machine_id_reset.failed')
            yield str(e)

    def run_windsurf_creator(self):
        """Windsurf hesap oluşturucuyu çalıştırır"""

        yield self.locale.get_text("windsurf.starting")

        from auth.windsurf_auth import WindsurfAuthManager
        windsurf_auth = WindsurfAuthManager()
        yield from windsurf_auth.create_account()
