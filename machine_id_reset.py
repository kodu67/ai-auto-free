import json
import os
import uuid
from pathlib import Path
import platform
from datetime import datetime
import shutil
import ctypes

class MachineIDResetter:
    def __init__(self):
        self.storage_file = self._get_storage_file()

    def _get_storage_file(self):
        system = platform.system()
        if system == "Windows":
            return Path(os.getenv("APPDATA")) / "Cursor" / "User" / "globalStorage" / "storage.json"
        elif system == "Darwin":  # macOS
            return Path(os.path.expanduser("~")) / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "storage.json"
        elif system == "Linux":
            return Path(os.path.expanduser("~")) / ".config" / "Cursor" / "User" / "globalStorage" / "storage.json"
        else:
            raise OSError(f"Unsupported operating system: {system}")

    def _backup_file(self):
        if self.storage_file.exists():
            backup_path = f"{self.storage_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.storage_file, backup_path)

    def _generate_ids(self):
        return {
            "telemetry.machineId": os.urandom(32).hex(),
            "telemetry.macMachineId": os.urandom(32).hex(),
            "telemetry.devDeviceId": str(uuid.uuid4()),
        }

    def _kill_cursor_processes(self):
        try:
            if platform.system() == "Windows":
                os.system('taskkill /F /IM "Cursor.exe" 2>nul')
                os.system('taskkill /F /IM "Cursor Helper.exe" 2>nul')
            else:
                os.system('pkill -f "Cursor"')
            print("Cursor processes have been terminated.")
        except Exception as e:
            print(f"Failed to terminate Cursor processes: {e}")

    def _format_id_change(self, id_type, old_id, new_id):
        RED = '\033[91m'
        GREEN = '\033[92m'
        RESET = '\033[0m'
        STRIKE = '\033[9m'

        return (
            f"{id_type}:\n"
            f"  Old: {RED}{STRIKE}{old_id}{RESET}\n"
            f"  New: {GREEN}{new_id}{RESET}"
        )

    def reset_ids(self):
        print("Important: Before running this script, make sure to log out and completely close Cursor. If Cursor is running in the background, it may revert the reset by restoring the previous device ID.")

        self._kill_cursor_processes()

        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._backup_file()

        if not self.storage_file.exists():
            data = {}
        else:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        old_ids = {
            "telemetry.machineId": data.get("telemetry.machineId", "Not Found"),
            "telemetry.macMachineId": data.get("telemetry.macMachineId", "Not Found"),
            "telemetry.devDeviceId": data.get("telemetry.devDeviceId", "Not Found"),
        }

        new_ids = self._generate_ids()
        data.update(new_ids)

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print("🎉 Device IDs have been successfully reset. The new device IDs are: \n")
        for key, new_id in new_ids.items():
            print(self._format_id_change(key, old_ids[key], new_id))

if __name__ == "__main__":
    resetter = MachineIDResetter()
    resetter.reset_ids()
