import os
import json
from utils.helper import Helper

class UserSettings:
    def __init__(self):
        self.helper = Helper()
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".cursor_cache")
        self.settings_file = os.path.join(self.settings_dir, "user_settings.json")
        self.default_settings = {
            "browser_visibility": False,  # Varsayılan olarak tarayıcı görünür olacak
            "email_verifier": "temp", # temp | imap
        }

        # Ayarlar dizini yoksa oluştur
        if not os.path.exists(self.settings_dir):
            os.makedirs(self.settings_dir)

        # Ayarlar dosyası yoksa varsayılan ayarları kaydet
        if not os.path.exists(self.settings_file):
            self.save_settings(self.default_settings)

    def get_settings(self):
        """Kullanıcı ayarlarını okur"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return self.default_settings

    def get_value(self, setting_key):
        """Spesifik bir ayarın değerini döndürür"""
        return self.get_settings().get(setting_key, self.default_settings[setting_key])

    def save_settings(self, settings):
        """Kullanıcı ayarlarını kaydeder"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception:
            return False

    def toggle_browser_visibility(self):
        """Tarayıcı görünürlüğünü değiştirir"""
        try:
            settings = self.get_settings()
            current_visibility = settings.get("browser_visibility", False)
            settings["browser_visibility"] = not current_visibility
            success = self.save_settings(settings)
            if success:
                return True
            return False
        except Exception:
            return False

    def is_browser_visible(self):
        """Tarayıcı görünürlük durumunu döndürür"""
        return self.get_value("browser_visibility")

    def get_imap_settings(self):
        """IMAP ayarlarını okur"""

        return self.get_settings().get("imap_settings", {
            "IMAP_SERVER": "imap.gmail.com",
            "IMAP_PORT": "993",
            "IMAP_USER": "xxxx@gmail.com",
            "IMAP_PASS": ""
        })

    def set_imap_settings(self, imap_settings):
        """IMAP ayarlarını ayarlar"""
        try:
            settings = self.get_settings()
            settings["imap_settings"] = imap_settings
            self.save_settings(settings)
            return True
        except Exception:
            return False

    def set_email_verifier(self, verifier):
        """Email doğrulayıcı tipini ayarlar"""
        settings = self.get_settings()
        settings["email_verifier"] = verifier
        self.save_settings(settings)

    def get_email_verifier(self):
        """Email doğrulayıcı tipini döndürür"""
        return self.get_value("email_verifier")
