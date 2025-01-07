import os
import sys
import json
import uuid
import random
import string
import logging
import platform
import ctypes
from pathlib import Path

class MachineIDResetter:
    def __init__(self):
        self.storage_path = self._get_storage_path()
        self.logger = logging.getLogger(__name__)

    def _get_storage_path(self):
        """Cursor'un storage.json dosyasının yolunu alır"""
        if platform.system() == "Windows":
            appdata = os.getenv("APPDATA")
            return os.path.join(appdata, "Cursor", "User", "globalStorage", "storage.json")
        else:  # macOS
            home = str(Path.home())
            return os.path.join(home, "Library", "Application Support", "Cursor", "User", "globalStorage", "storage.json")

    def _is_admin(self):
        """Yönetici yetkilerini kontrol eder"""
        try:
            if platform.system() == "Windows":
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False

    def _generate_machine_id(self):
        """Yeni bir makine kimliği oluşturur"""
        return str(uuid.uuid4())

    def _generate_device_id(self):
        """Yeni bir cihaz kimliği oluşturur"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(32))

    def _generate_mac_machine_id(self):
        """macOS için yeni bir makine kimliği oluşturur"""
        return str(uuid.uuid4())

    def _generate_sqm_id(self):
        """Yeni bir SQM kimliği oluşturur"""
        return str(uuid.uuid4())

    def _read_config(self):
        """Mevcut yapılandırmayı okur"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Yapılandırma okunamadı: {str(e)}")
        return {}

    def _save_config(self, config):
        """Yapılandırmayı kaydeder"""
        try:
            # Dosya izinlerini kontrol et
            if os.path.exists(self.storage_path):
                if not os.access(self.storage_path, os.W_OK):
                    self.logger.error(f"Dosya yazma izni yok: {self.storage_path}")
                    return False

            # Dizin yolunun var olduğundan emin ol
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            # Dosyaya yazmayı dene
            with open(self.storage_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Yazma işlemini doğrula
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    written_config = json.load(f)
                if written_config == config:
                    self.logger.info("Yapılandırma başarıyla kaydedildi")
                    return True
                else:
                    self.logger.error("Yapılandırma doğrulama başarısız")
                    return False
            else:
                self.logger.error("Dosya oluşturulamadı")
                return False

        except PermissionError as e:
            self.logger.error(f"Yetki hatası: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Yapılandırma kaydedilemedi: {str(e)}")
            return False

    def _format_id_change(self, id_type, old_id, new_id):
        """ID değişikliğini formatlar"""
        # ANSI renk kodları
        RED = '\033[91m'
        GREEN = '\033[92m'
        RESET = '\033[0m'
        STRIKE = '\033[9m'

        return (
            f"{id_type}:\n"
            f"  Eski: {RED}{STRIKE}{old_id}{RESET}\n"
            f"  Yeni: {GREEN}{new_id}{RESET}"
        )

    def reset_machine_id(self):
        """Makine kimliğini sıfırlar"""
        if not self._is_admin():
            return False, "Bu işlem için yönetici yetkileri gerekiyor."

        # Cursor'u kapat
        self._kill_cursor_processes()

        # Mevcut yapılandırmayı oku
        old_config = self._read_config()
        new_config = old_config.copy()

        # Yeni kimlikleri oluştur ve değişiklikleri kaydet
        changes = []

        # Machine ID
        old_machine_id = old_config.get("telemetry.machineId", "Bulunamadı")
        new_machine_id = self._generate_machine_id()
        new_config["telemetry.machineId"] = new_machine_id
        changes.append(self._format_id_change("Machine ID", old_machine_id, new_machine_id))

        # Device ID
        old_device_id = old_config.get("telemetry.devDeviceId", "Bulunamadı")
        new_device_id = self._generate_device_id()
        new_config["telemetry.devDeviceId"] = new_device_id
        changes.append(self._format_id_change("Device ID", old_device_id, new_device_id))

        # Mac Machine ID
        old_mac_id = old_config.get("telemetry.macMachineId", "Bulunamadı")
        new_mac_id = self._generate_mac_machine_id()
        new_config["telemetry.macMachineId"] = new_mac_id
        changes.append(self._format_id_change("Mac Machine ID", old_mac_id, new_mac_id))

        # SQM ID'yi koru veya yeni oluştur
        if "telemetry.sqmId" not in new_config:
            new_config["telemetry.sqmId"] = self._generate_sqm_id()

        # Yapılandırmayı kaydet
        if self._save_config(new_config):
            return True, "\n\n".join(changes)
        else:
            return False, "Makine kimliği sıfırlanamadı."

    def _kill_cursor_processes(self):
        """Cursor işlemlerini sonlandırır"""
        try:
            if platform.system() == "Windows":
                os.system('taskkill /F /IM "Cursor.exe" 2>nul')
                os.system('taskkill /F /IM "Cursor Helper.exe" 2>nul')
            else:
                os.system('pkill -f "Cursor"')
            return True
        except:
            return False
