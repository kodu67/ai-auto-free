from DrissionPage import ChromiumOptions, Chromium
import sys
import os
import logging


class BrowserManager:
    def __init__(self, headless=True):
        self.browser = None
        self.headless = headless  

    def init_browser(self):
        """Tarayıcıyı başlatır"""
        try:
            co = self._get_browser_options()
            self.browser = Chromium(co)
            return self.browser
        except Exception as e:
            logging.error(f"Tarayıcı başlatılırken hata oluştu: {e}")
            raise

    def _get_browser_options(self):
        """Tarayıcı ayarlarını yapılandırır"""
        co = ChromiumOptions()

        user_data_dir = os.path.join(
            os.path.expanduser("~"), ".cursor_browser_data"
        )
        co.set_pref("user_data_dir", user_data_dir)

        try:
            extension_path = self._get_extension_path()
            co.add_extension(extension_path)
        except FileNotFoundError as e:
            logging.error(f"Eklenti yüklenirken hata oluştu: {e}")

        co.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.6723.92 Safari/537.36"
        )
        co.set_pref("credentials_enable_service", False)
        co.set_argument("--hide-crash-restore-bubble")
        co.auto_port()

        # Headless mod ayarı
        if self.headless:
            co.set_argument("--headless=new")

        if sys.platform in ["darwin", "linux"]:
            co.set_argument("--no-sandbox")
            co.set_argument(
                "--disable-gpu"
            )  

        return co

    def _get_extension_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        extension_path = os.path.join(current_dir, "turnstilePatch")
        if not os.path.exists(extension_path):
            raise FileNotFoundError(
                f"Eklenti dizini bulunamadı: {extension_path}"
            )
        return extension_path

    def quit(self):
        try:
            if self.browser:
                self.browser.quit()
        except Exception as e:
            logging.error(f"Tarayıcı kapatılırken hata oluştu: {e}")
