from DrissionPage import ChromiumOptions, Chromium
import sys
import os
import logging


class BrowserManager:
    def __init__(self, headless=True):
        self.browser = None
        self.headless = headless  # Varsayılan olarak True

    def init_browser(self):
        """Tarayıcıyı başlatır"""
        co = self._get_browser_options()
        self.browser = Chromium(co)
        return self.browser

    def _get_browser_options(self):
        """Tarayıcı ayarlarını yapılandırır"""
        co = ChromiumOptions()
        try:
            extension_path = self._get_extension_path()
            co.add_extension(extension_path)
        except FileNotFoundError as e:
            logging.warning(f"Uyarı: {e}")

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
        else:
            pass

        # Mac sistemleri için özel ayarlar
        if sys.platform == "darwin":
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")

        return co

    def _get_extension_path(self):
        """Eklenti yolunu alır"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "turnstilePatch")

        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"Eklenti bulunamadı: {extension_path}")

        return extension_path

    def quit(self):
        """Tarayıcıyı kapatır"""
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
