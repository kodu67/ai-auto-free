import json
import os
import locale


class Locale:
    def __init__(self):
        self.current_locale = None
        self.translations = {}
        self._load_locale()

    def get_lang_code(self):
        """Sistem dilini alir"""
        system_locale = locale.getdefaultlocale()[0]
        lang_code = system_locale.split("_")[0] if system_locale else "en"
        return lang_code

    def _load_locale(self):
        """Sistem diline göre uygun dil dosyasını yükler"""

        # Sistem dilini al
        lang_code = self.get_lang_code()

        # Desteklenen diller
        supported_locales = {
            "en": "en.json",
            "tr": "tr.json",
            "zh": "zh.json",
            "ru": "ru.json",
            "az": "az.json",
        }

        # Eğer sistem dili desteklenmiyorsa varsayılan olarak İngilizce kullan
        locale_file = supported_locales.get(lang_code, "en.json")
        self.current_locale = lang_code

        # Dil dosyasını yükle
        src_path = os.path.dirname(os.path.dirname(__file__))
        locale_path = os.path.join(src_path, "locales", locale_file)
        with open(locale_path, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

    def get_text(self, key_path):
        """
        Verilen anahtar yoluna göre metni döndürür
        Örnek: get_text("menu.title")
        """
        try:
            keys = key_path.split(".")
            value = self.translations
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return f"[Missing Translation: {key_path}]"

    def get_locale(self):
        """
        Mevcut dil çevirilerini döndürür
        """
        return self.translations
