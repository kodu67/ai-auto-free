import os
import sys

# Proje kök dizinini al ve src klasörünü Python path'ine ekle
if getattr(sys, 'frozen', False):
    # PyInstaller ile paketlenmiş
    BASE_DIR = sys._MEIPASS
else:
    # Normal Python çalışma zamanı
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# src klasörünü Python path'ine ekle
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

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
