import os
import sys

# Proje kök dizinini al ve src klasörünü Python path'ine ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from core.app import AutoFreeApp


def main():
    try:
        app = AutoFreeApp()
        if app.check_admin_rights():
            app.check_settings()
            app.run()
        else:
            sys.exit(1)
    except SystemExit:
        # Yönetici yetkileriyle yeniden başlatıldığında
        pass


if __name__ == "__main__":
    main()
