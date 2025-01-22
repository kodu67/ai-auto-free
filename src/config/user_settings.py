import os
import json
from utils.helper import Helper

class UserSettings:
    def __init__(self):
        self.helper = Helper()
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".cursor_cache")
        self.settings_file = os.path.join(self.settings_dir, "user_settings.json")
        self.imap_settings_file = os.path.join(self.settings_dir, "imap_settings.env")
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

        # IMAP ayarlar dosyası yoksa yenisini oluştur
        if not os.path.exists(self.imap_settings_file):
            self.create_imap_settings_if_not_available()


    def get_settings(self):
        """Kullanıcı ayarlarını okur"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
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
        settings = self.get_settings()
        settings["browser_visibility"] = not settings["browser_visibility"]
        return self.save_settings(settings)

    def is_browser_visible(self):
        """Tarayıcı görünürlük durumunu döndürür"""
        return self.get_value("browser_visibility")

    def create_imap_settings_if_not_available(self):
        """IMAP ayarları için varsayılan yapılandırma dosyası oluşturur"""
        try:
            config = (
                "IMAP_SERVER=imap.gmail.com  # örn: QQ Mail, Gmail\n"
                "IMAP_PORT=993               # QQ: 995, Gmail: 993\n"
                "IMAP_USER=xxxx@gmail.com    # Alıcı e-posta adresi\n"
                "IMAP_PASS=xxxxxxxxxxxxx     # E-posta yetkilendirme kodu\n"
            )

            with open(self.imap_settings_file, "w", encoding="utf-8") as f:
                f.write(config.strip())
            return True

        except Exception:
            return False

    def set_imap_email_settings(self):
        """IMAP E-mail seçenekleri için düzenleme dosyasını açar"""
        # IMAP dosyasını notepad ile aç (Windows / MacOS / Linux)
        print(f"IMAP Settings: {self.imap_settings_file}")
        if self.helper.is_windows():
            os.system(f"notepad {self.imap_settings_file}")
        elif self.helper.is_macos():
            os.system(f"open -e {self.imap_settings_file}")
        else:  # Linux ve diğer sistemler için
            editors = ["gedit", "kate", "nano", "vim"]
            for editor in editors:
                if os.system(f"which {editor}") == 0:
                    os.system(f"{editor} {self.imap_settings_file}")
                    break

    def get_imap_settings(self):
        """IMAP ayarlarını okur"""
        try:
            settings = {}
            with open(self.imap_settings_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Yorum satırını kaldır
                        line = line.split("#")[0].strip()
                        if "=" in line:
                            key, value = line.split("=", 1)
                            settings[key.strip()] = value.strip()

            return {
                "server": settings.get("IMAP_SERVER", ""),
                "port": settings.get("IMAP_PORT", ""),
                "user": settings.get("IMAP_USER", ""),
                "password": settings.get("IMAP_PASS", "")
            }
        except Exception:
            return {
                "server": "",
                "port": "",
                "user": "",
                "password": ""
            }

    def set_email_verifier(self, verifier):
        """Email doğrulayıcı tipini ayarlar"""
        settings = self.get_settings()
        settings["email_verifier"] = verifier
        return self.save_settings(settings)

    def get_email_verifier(self):
        """Email doğrulayıcı tipini döndürür"""
        return self.get_value("email_verifier")
