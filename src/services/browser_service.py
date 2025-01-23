from DrissionPage import ChromiumOptions, Chromium
import sys
import os
from utils.helper import Helper
from config import constants
from config.user_settings import UserSettings


class BrowserService:
    def __init__(self):
        self.user_settings = UserSettings()
        self.browser = None
        # Test modunda değilse veya kullanıcı görünmez mod seçtiyse headless olsun
        self.headless = not self.user_settings.is_browser_visible()
        self.helper = Helper()

    def init_browser(self):
        """Tarayıcıyı başlatır"""
        co_generator = self._get_browser_options()
        try:
            while True:
                yield next(co_generator)
        except StopIteration as e:
            co = e.value
            self.browser = Chromium(co)
            return self.browser

    def _get_browser_options(self):
        """Tarayıcı ayarlarını yapılandırır"""
        co = ChromiumOptions()

        co.set_argument("--lang=en-US")  # Dili İngilizce'ye ayarla
        co.set_pref("intl.accept_languages", "en-US")

        try:
            extension_path_generator = self._get_extension_path()
            while True:
                yield next(extension_path_generator)
        except StopIteration as e:
            if e.value:
                co.add_extension(e.value)
        except Exception as e:
            yield f"Chrome extension loading error: {e}"


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
        try:
            if getattr(sys, 'frozen', False):
                # PyInstaller ile paketlenmiş
                base_path = sys._MEIPASS
                extension_path = os.path.join(base_path, "scripts", "turnstilePatch")
            else:
                # Normal Python çalışma zamanı
                extension_path = os.path.join(
                    self.helper.get_src_path(), "scripts", "turnstilePatch"
                )

            if not os.path.exists(extension_path):
                raise FileNotFoundError(f"Extension directory not found: {extension_path}")

            # Dizin içeriğini kontrol et
            if not os.path.exists(os.path.join(extension_path, "manifest.json")):
                raise FileNotFoundError(f"manifest.json not found in extension directory")

            return extension_path

        except Exception as e:
            yield f"Extension path error: {str(e)}"
            return None

    def quit(self):
        """Tarayıcıyı kapatır"""
        if self.browser:
            self.browser.quit()
