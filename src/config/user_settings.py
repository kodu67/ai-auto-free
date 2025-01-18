import os
import json

class UserSettings:
    def __init__(self):
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".cursor_cache")
        self.settings_file = os.path.join(self.settings_dir, "user_settings.json")
        self.default_settings = {
            "browser_visibility": False  # Varsayılan olarak tarayıcı görünür olacak
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
        except Exception:
            return self.default_settings

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
        settings = self.get_settings()
        settings["browser_visibility"] = not settings["browser_visibility"]
        return self.save_settings(settings)

    def is_browser_visible(self):
        """Tarayıcı görünürlük durumunu döndürür"""
        return self.get_settings().get("browser_visibility", self.default_settings["browser_visibility"])
