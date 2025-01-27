import os
from pathlib import Path
from .proxy_manager import ProxyManager
from utils.helper import Helper
from utils.locale import Locale


class ProxyService:
    _instance = None
    _proxy_manager = None
    _is_running = False
    _status_callback = None
    _locale = None
    _helper = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ProxyService()
        return cls._instance

    def __init__(self):
        if ProxyService._instance is not None:
            raise Exception(
                "Use ProxyService.get_instance() instead of direct instantiation."
            )
        ProxyService._instance = self
        self._locale = Locale()
        self._helper = Helper()

    def set_status_callback(self, callback):
        """UI'a durum mesajı göndermek için callback fonksiyonu ayarlar"""
        self._status_callback = callback

    def _send_status(self, message):
        """Durum mesajını callback üzerinden gönderir"""
        if self._status_callback:
            self._status_callback(message)

    def start_proxy(self):
        """Proxy'yi başlatır ve durumu yield eder"""
        if self._is_running:
            yield self._locale.get_text("proxy.already_running")
            return

        try:
            yield self._locale.get_text("proxy.checking_certificate")
            if not self.is_certificate_installed():
                yield self._locale.get_text("proxy.certificate_not_installed")
                instructions = self.get_cert_install_instructions()
                yield instructions
                return

            # Yeni bir proxy manager oluştur
            self._proxy_manager = ProxyManager()

            # Proxy'yi başlat
            for status in self._proxy_manager.start(self.proxy_status_handler):
                yield status

            self._is_running = True
        except Exception as e:
            error_msg = self._locale.get_text("proxy.start.error").format(error=str(e))
            yield error_msg
            self._is_running = False
            if self._proxy_manager:
                self._proxy_manager.stop()  # Hata durumunda process'i temizle
                self._proxy_manager = None

    def stop_proxy(self):
        """Proxy'yi durdurur ve durumu yield eder"""
        if not self._is_running:
            yield self._locale.get_text("proxy.already_stopped")
            return

        try:
            yield self._locale.get_text("proxy.stop.stopping")

            if self._proxy_manager:
                # Önce proxy process'ini durdur
                self._proxy_manager.stop()

                # Sonra sistem ayarlarını geri yükle
                for status in self._proxy_manager.restore_proxy_settings():
                    yield status

                self._proxy_manager = None

            self._is_running = False
            yield self._locale.get_text("proxy.stop.success")
        except Exception as e:
            error_msg = self._locale.get_text("proxy.stop.error").format(error=str(e))
            yield error_msg
            self._is_running = False  # Hata durumunda da false yap

    def is_running(self):
        """Proxy'nin çalışıp çalışmadığını kontrol eder"""
        return self._is_running

    def is_certificate_installed(self):
        """mitmproxy sertifikasının yüklü olup olmadığını kontrol eder"""
        try:
            if self._helper.is_windows():
                return self._is_cert_installed_windows()
            elif self._helper.is_macos():
                return self._is_cert_installed_macos()
            else:
                return self._is_cert_installed_linux()
        except Exception:
            return False

    def _is_cert_installed_windows(self):
        """Windows'ta sertifikanın yüklü olup olmadığını kontrol eder"""
        try:
            cmd = 'certutil -store -user Root "mitmproxy"'
            result = os.popen(cmd).read()
            return "mitmproxy" in result
        except:
            return False

    def _is_cert_installed_macos(self):
        """MacOS'ta sertifikanın yüklü olup olmadığını kontrol eder"""
        try:
            cmd = 'security find-certificate -c "mitmproxy"'
            result = os.popen(cmd).read()
            return "mitmproxy" in result
        except:
            return False

    def _is_cert_installed_linux(self):
        """Linux'ta sertifikanın yüklü olup olmadığını kontrol eder"""
        cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
        return cert_path.exists()

    def get_cert_install_instructions(self):
        """Sertifika yükleme talimatlarını döndürür"""
        if self._helper.is_windows():
            return self._locale.get_text("proxy.certificate.windows_instructions")
        elif self._helper.is_macos():
            return self._locale.get_text("proxy.certificate.macos_instructions")
        else:
            return self._locale.get_text("proxy.certificate.linux_instructions")

    def proxy_status_handler(self, message):
        if self._status_callback:
            self._status_callback(message)
        yield message
