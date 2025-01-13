import json
import os
import locale

class LocaleManager:
    def __init__(self):
        self.current_locale = None
        self.translations = {}
        self._load_locale()

    def _load_locale(self):
        """Sistem diline göre uygun dil dosyasını yükler"""
        try:
            # Sistem dilini al
            system_locale = locale.getdefaultlocale()[0]
            lang_code = system_locale.split('_')[0] if system_locale else 'en'

            # Desteklenen diller
            supported_locales = {
                'en': 'en.json',
                'tr': 'tr.json',
                'zh': 'zh.json',
                'ru': 'ru.json',
                'az': 'az.json'
            }

            # Eğer sistem dili desteklenmiyorsa varsayılan olarak İngilizce kullan
            locale_file = supported_locales.get(lang_code, 'en.json')
            self.current_locale = lang_code

            # Dil dosyasını yükle
            locale_path = os.path.join(os.path.dirname(__file__), 'locales', locale_file)
            with open(locale_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

        except Exception as e:
            # Hata durumunda varsayılan İngilizce metinleri kullan
            self.current_locale = 'en'
            self.translations = self._get_default_translations()

    def _get_default_translations(self):
        """Varsayılan İngilizce metinleri döndürür"""
        return {
            "menu": {
                "title": "Cursor Auto Free",
                "select_option": "Please select an option:",
                "cursor": "1. Cursor Account Creator",
                "windsurf": "2. Windsurf (Coming Soon)",
                "settings": "3. Settings",
                "exit": "4. Exit"
            }
        }

    def get_text(self, key_path):
        """
        Verilen anahtar yoluna göre metni döndürür
        Örnek: get_text("menu.title")
        """
        try:
            keys = key_path.split('.')
            value = self.translations
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return f"[Missing: {key_path}]"

    def get_locale(self):
        """
        Mevcut dil çevirilerini döndürür
        """
        return self.translations
