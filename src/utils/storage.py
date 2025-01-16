import os
from pathlib import Path
from .helper import Helper


class Storage:
    def __init__(self):
        self.helper = Helper()

    def cursor_global_storage_path(self):
        # :: Windows
        if self.helper.is_windows():
            appdata = os.getenv("APPDATA")
            return os.path.join(appdata, "Cursor", "User", "globalStorage")
        # :: MacOS
        elif self.helper.is_macos():
            home = str(Path.home())
            return os.path.join(
                home,
                "Library",
                "Application Support",
                "Cursor",
                "User",
                "globalStorage",
            )
        # :: Linux
        else:
            home = str(Path.home())
            return os.path.join(home, ".config", "Cursor", "User", "globalStorage")

    def cursor_storage_json_path(self):
        return os.path.join(self.cursor_global_storage_path(), "storage.json")

    def cursor_storage_json_exist(self):
        return os.path.exists(self.cursor_storage_json_path())

    def cursor_db_path(self):
        return os.path.join(self.cursor_global_storage_path(), "state.vscdb")

    def cursor_db_exist(self):
        return os.path.exists(self.cursor_db_path())
