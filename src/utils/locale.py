import json
import os
import locale
import sys


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
        try:
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

            # PyInstaller ile paketlendiğinde _MEIPASS kullan
            if getattr(sys, 'frozen', False):
                # PyInstaller ile çalışıyoruz
                base_path = sys._MEIPASS
                locale_path = os.path.join(base_path, "locales", locale_file)
            else:
                # Normal Python ile çalışıyoruz
                src_path = os.path.dirname(os.path.dirname(__file__))
                locale_path = os.path.join(src_path, "locales", locale_file)

            # Dil dosyasını yükle
            with open(locale_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

        except Exception as e:
            # Varsayılan İngilizce çevirileri yükle
            try:
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                    locale_path = os.path.join(base_path, "locales", "en.json")
                else:
                    src_path = os.path.dirname(os.path.dirname(__file__))
                    locale_path = os.path.join(src_path, "locales", "en.json")

                with open(locale_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                self.current_locale = "en"
            except Exception as e:
                print(e)
                self.translations = {}

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
