import os
import sys

# src klasörünü Python path'ine ekle
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

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
