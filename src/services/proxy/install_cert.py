import os
import shutil
from pathlib import Path
from utils.helper import Helper
from utils.locale import Locale
import time


class CertificateInstaller:
    def __init__(self):
        """Sertifika yükleyici sınıfını başlatır"""
        self.helper = Helper()
        self.locale = Locale()

    def install_certificate(self):
        """Sertifikayı işletim sistemine uygun şekilde yükler"""
        try:
            # Sertifika dosyasını kopyala
            yield self.locale.get_text("proxy.certificate.copying")
            cert_path = self._copy_certificate()
            if not cert_path:
                yield self.locale.get_text("proxy.certificate.copy_failed")
                return

            # İşletim sistemine göre sertifika yükleme
            yield self.locale.get_text("proxy.certificate.installing")
            if self.helper.is_windows():
                success = self._install_windows(cert_path)
            elif self.helper.is_macos():
                success = self._install_macos(cert_path)
            else:
                success = self._install_linux(cert_path)

            if success:
                yield self.locale.get_text("proxy.certificate.install_success")
            else:
                yield self.locale.get_text("proxy.certificate.install_failed")

        except Exception as e:
            yield self.locale.get_text("proxy.certificate.install_error").format(
                error=str(e)
            )

    def _copy_certificate(self):
        """mitmproxy sertifikasını geçici dizine kopyalar"""
        try:
            # Sertifika dosyasının konumunu bul
            cert_source = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
            
            # Sertifika dosyasının oluşturulmasını bekle (maksimum 10 saniye)
            wait_time = 0
            while not cert_source.exists() and wait_time < 10:
                time.sleep(1)
                wait_time += 1

            if not cert_source.exists():
                return None

            # Geçici dizin oluştur
            temp_dir = Path.home() / ".cursor" / "certs"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Sertifikayı kopyala
            cert_dest = temp_dir / "mitmproxy-ca-cert.pem"
            shutil.copy2(cert_source, cert_dest)

            return cert_dest

        except Exception:
            return None

    def _install_windows(self, cert_path):
        """Windows'ta sertifika yükleme"""
        try:
            # Sertifikayı Windows sertifika deposuna yükle
            cmd = f'certutil -addstore -user Root "{cert_path}"'
            result = os.system(cmd)
            return result == 0
        except:
            return False

    def _install_macos(self, cert_path):
        """MacOS'ta sertifika yükleme"""
        try:
            # Sertifikayı MacOS keychain'e yükle
            cmd = f'security add-trusted-cert -d -r trustRoot -k ~/Library/Keychains/login.keychain "{cert_path}"'
            result = os.system(cmd)
            return result == 0
        except:
            return False

    def _install_linux(self, cert_path):
        """Linux'ta sertifika yükleme"""
        try:
            # Sertifikayı sistem sertifika dizinine kopyala
            dest = "/usr/local/share/ca-certificates/mitmproxy.crt"
            shutil.copy2(cert_path, dest)

            # Sertifika deposunu güncelle
            result = os.system("update-ca-certificates")
            return result == 0
        except:
            return False
