from DrissionPage import ChromiumOptions, Chromium
import sys
import os
from utils.helper import Helper
from config import constants


class BrowserService:
    def __init__(self):
        self.browser = None
        self.headless = not constants.TEST_MODE
        self.helper = Helper()

    def init_browser(self):
        """Tarayıcıyı başlatır"""
        co = self._get_browser_options()
        self.browser = Chromium(co)
        return self.browser

    def _get_browser_options(self):
        """Tarayıcı ayarlarını yapılandırır"""
        co = ChromiumOptions()

        co.set_argument("--lang=en-US")  # Dili İngilizce'ye ayarla
        co.set_pref("intl.accept_languages", "en-US")

        try:
            extension_path = self._get_extension_path()
            co.add_extension(extension_path)
        except FileNotFoundError as e:
            print(f"Chrome extension loading error: {e}")

        co.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.6723.92 Safari/537.36"
        )
        co.set_pref("credentials_enable_service", False)
        co.set_argument("--hide-crash-restore-bubble")
        co.auto_port()

        # Headless (tarayıcı görünürlüğü) mod ayarı
        if self.headless:
            co.set_argument("--headless=new")

        # Mac ve Linux sistemlerinde performans için özel ayarlar
        if sys.platform in ["darwin", "linux"]:
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")

        return co

    def _get_extension_path(self):
        """Turnstile Patch eklentisinin yolunu döndürür"""
        extension_path = os.path.join(
            self.helper.get_src_path(), "scripts/turnstilePatch"
        )
        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"Extension directory not found: {extension_path}")
        return extension_path

    def quit(self):
        """Tarayıcıyı kapatır"""
        if self.browser:
            self.browser.quit()
