import os
import json
import uuid
import random
import string
from utils.storage import Storage
from utils.helper import Helper


class CursorMachineIDResetter:
    def __init__(self):
        self.storage = Storage()
        self.helper = Helper()
        self.cursor_storage_json_path = self.storage.cursor_storage_json_path()

    def _generate_machine_id(self):
        return str(uuid.uuid4())

    def _generate_device_id(self):
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(32))

    def _generate_mac_machine_id(self):
        return str(uuid.uuid4())

    def _generate_sqm_id(self):
        return str(uuid.uuid4())

    def _read_config(self):
        try:
            if self.storage.cursor_storage_json_exist():
                with open(self.cursor_storage_json_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Config read error: {str(e)}")
        return {}

    def _save_config(self, config):
        try:
            with open(self.cursor_storage_json_path, "w") as f:
                json.dump(config, f, indent=2)
                return True

        except PermissionError as e:
            print(f"Permission error: {str(e)}")
            return False
        except Exception as e:
            print(f"Config save error: {str(e)}")
            return False

    def _format_id_change(self, id_type, old_id, new_id):
        RED = "\033[91m"
        GREEN = "\033[92m"
        RESET = "\033[0m"
        STRIKE = "\033[9m"

        return (
            f"{id_type}:\n"
            f"  - : {RED}{STRIKE}{old_id}{RESET}\n"
            f"  + : {GREEN}{new_id}{RESET}"
        )

    def reset_machine_id(self):
        self.helper.kill_cursor_processes()

        old_config = self._read_config()
        new_config = old_config.copy()

        changes = []

        old_machine_id = old_config.get("telemetry.machineId", "Bulunamadı")
        new_machine_id = self._generate_machine_id()
        new_config["telemetry.machineId"] = new_machine_id
        changes.append(
            self._format_id_change("Machine ID", old_machine_id, new_machine_id)
        )

        old_device_id = old_config.get("telemetry.devDeviceId", "Bulunamadı")
        new_device_id = self._generate_device_id()
        new_config["telemetry.devDeviceId"] = new_device_id
        changes.append(
            self._format_id_change("Device ID", old_device_id, new_device_id)
        )

        old_mac_id = old_config.get("telemetry.macMachineId", "Bulunamadı")
        new_mac_id = self._generate_mac_machine_id()
        new_config["telemetry.macMachineId"] = new_mac_id
        changes.append(self._format_id_change("Mac Machine ID", old_mac_id, new_mac_id))

        if "telemetry.sqmId" not in new_config:
            new_config["telemetry.sqmId"] = self._generate_sqm_id()

        if self._save_config(new_config):
            return True, "\n\n".join(changes)
        else:
            return False, "Not changed"
