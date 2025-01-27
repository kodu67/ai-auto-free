import os
import winreg
import atexit
import subprocess
import threading
from pathlib import Path
from utils.helper import Helper
from utils.locale import Locale
from config.constants import TEST_MODE

class ProxyManager:
    def __init__(self):
        self.original_proxy_settings = {}
        self.proxy_port = 8080
        self.proxy_process = None
        self.helper = Helper()
        self.locale = Locale()

    def _find_available_port(self, start_port=8080, max_attempts=10):
        """Kullanılabilir bir port bulur"""
        import socket

        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue
        raise Exception("Not available port")

    def setup_proxy(self):
        """Proxy ayarlarını sisteme uygular"""
        if self.helper.is_windows():
            yield from self._setup_windows_proxy()
        elif self.helper.is_macos():
            yield from self._setup_macos_proxy()
        else:
            yield from self._setup_linux_proxy()

        # Çıkışta eski ayarlara dönme
        atexit.register(self.restore_proxy_settings)

    def _setup_windows_proxy(self):
        """Windows proxy ayarlarını yapar"""
        try:
            yield self.locale.get_text("proxy.setup.windows.configuring")

            # Internet Settings kayıt defteri anahtarı
            internet_settings = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_ALL_ACCESS,
            )

            # Mevcut ayarları kaydet
            try:
                proxy_enable = winreg.QueryValueEx(internet_settings, "ProxyEnable")[0]
                proxy_server = winreg.QueryValueEx(internet_settings, "ProxyServer")[0]
                self.original_proxy_settings = {
                    "ProxyEnable": proxy_enable,
                    "ProxyServer": proxy_server,
                }
                yield self.locale.get_text("proxy.setup.windows.saved_settings")
            except WindowsError:
                self.original_proxy_settings = {
                    "ProxyEnable": 0,
                    "ProxyServer": "",
                }

            # Yeni proxy ayarlarını uygula
            winreg.SetValueEx(
                internet_settings,
                "ProxyEnable",
                0,
                winreg.REG_DWORD,
                1,
            )
            winreg.SetValueEx(
                internet_settings,
                "ProxyServer",
                0,
                winreg.REG_SZ,
                f"127.0.0.1:{self.proxy_port}",
            )
            yield self.locale.get_text("proxy.setup.windows.applied_settings")

            # Internet Explorer ayarlarını güncelle
            yield self.locale.get_text("proxy.setup.windows.updating")
            import ctypes

            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_REFRESH = 37
            ctypes.windll.Wininet.InternetSetOptionW(
                0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0
            )
            ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
            yield self.locale.get_text("proxy.setup.windows.updated")

            winreg.CloseKey(internet_settings)
        except Exception as e:
            raise Exception(str(e))

    def _setup_macos_proxy(self):
        """MacOS proxy ayarlarını yapar"""
        yield self.locale.get_text("proxy.setup.macos.configuring")

        # Mevcut ayarları kaydet
        self.original_proxy_settings["http"] = os.popen(
            "networksetup -getwebproxy Wi-Fi"
        ).read()
        self.original_proxy_settings["https"] = os.popen(
            "networksetup -getsecurewebproxy Wi-Fi"
        ).read()
        yield self.locale.get_text("proxy.setup.macos.saved_settings")

        # Yeni proxy ayarlarını uygula
        os.system(f"networksetup -setwebproxy Wi-Fi 127.0.0.1 {self.proxy_port}")
        os.system(f"networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 {self.proxy_port}")
        yield self.locale.get_text("proxy.setup.macos.applied_settings")

    def _setup_linux_proxy(self):
        """Linux proxy ayarlarını yapar"""
        yield self.locale.get_text("proxy.setup.linux.configuring")
        # Mevcut ayarları kaydet
        self.original_proxy_settings["http_proxy"] = os.environ.get("http_proxy", "")
        self.original_proxy_settings["https_proxy"] = os.environ.get("https_proxy", "")
        yield self.locale.get_text("proxy.setup.linux.saved_settings")

        # Yeni proxy ayarlarını uygula
        proxy_url = f"http://127.0.0.1:{self.proxy_port}"
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        yield self.locale.get_text("proxy.setup.linux.applied_settings")

    def restore_proxy_settings(self):
        """Proxy ayarlarını eski haline getirir"""
        try:
            yield self.locale.get_text("proxy.restore.starting")
            if self.proxy_process:
                self.proxy_process.terminate()
                self.proxy_process = None
            yield self.locale.get_text("proxy.restore.success")
        except Exception as e:
            yield self.locale.get_text("proxy.restore.error").format(error=str(e))

    def stop(self):
        """Proxy'yi durdurur"""
        try:
            if self.proxy_process:
                # Process'i sonlandır
                self.proxy_process.terminate()
                try:
                    # En fazla 5 saniye bekle
                    self.proxy_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Hala kapanmadıysa zorla kapat
                    self.proxy_process.kill()
                    self.proxy_process.wait()

                # Process'i temizle
                self.proxy_process = None

            # Windows'ta proxy ayarlarını eski haline getir
            if self.helper.is_windows():
                internet_settings = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                    0,
                    winreg.KEY_WRITE,
                )
                
                # Orijinal ayarları geri yükle
                if self.original_proxy_settings:
                    winreg.SetValueEx(
                        internet_settings,
                        "ProxyEnable",
                        0,
                        winreg.REG_DWORD,
                        self.original_proxy_settings.get("ProxyEnable", 0)
                    )
                    winreg.SetValueEx(
                        internet_settings,
                        "ProxyServer",
                        0,
                        winreg.REG_SZ,
                        self.original_proxy_settings.get("ProxyServer", "")
                    )
                else:
                    # Orijinal ayarlar yoksa tamamen kapat
                    winreg.SetValueEx(
                        internet_settings,
                        "ProxyEnable",
                        0,
                        winreg.REG_DWORD,
                        0
                    )
                    winreg.SetValueEx(
                        internet_settings,
                        "ProxyServer",
                        0,
                        winreg.REG_SZ,
                        ""
                    )

                winreg.CloseKey(internet_settings)

                # Internet Options'ı güncelle
                import ctypes
                INTERNET_OPTION_REFRESH = 37
                INTERNET_OPTION_SETTINGS_CHANGED = 39
                internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
                internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
                internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)

            # MacOS için proxy ayarlarını geri yükle
            elif self.helper.is_macos():
                os.system("networksetup -setwebproxystate Wi-Fi off")
                os.system("networksetup -setsecurewebproxystate Wi-Fi off")

            # Linux için proxy ayarlarını geri yükle
            else:
                if "http_proxy" in os.environ:
                    del os.environ["http_proxy"]
                if "https_proxy" in os.environ:
                    del os.environ["https_proxy"]

        except Exception as e:
            print(f"Error stopping proxy: {str(e)}")
            raise

    def start(self, status_callback=None, mitmproxy_path=None):
        """Proxy'yi başlatır ve durumu bildirir"""
        try:
            if status_callback:
                status_callback(self.locale.get_text("proxy.start.starting"))

            # mitmproxy'nin yüklü olup olmadığını kontrol et
            try:
                import mitmproxy
            except ImportError:
                raise Exception("pip install mitmproxy")

            # Kullanılabilir bir port bul
            self.proxy_port = self._find_available_port()

            # Script dosyasının yolunu al
            script_path = str(Path(__file__).parent / "cursor_interceptor.py")

            # mitmdump yolunu belirle
            if self.helper.is_windows():
                mitmdump_path = os.path.join(mitmproxy_path, "mitmdump.exe")
            else:
                mitmdump_path = "mitmdump"

            # mitmproxy komut satırı argümanlarını hazırla
            args = [
                mitmdump_path,
                "--listen-host",
                "127.0.0.1",
                "--listen-port",
                str(self.proxy_port),
                "--ssl-insecure",
                "--set",
                "console_eventlog_verbosity=info",
                "-s",
                script_path,
            ]

            # Proxy'yi ayrı bir process olarak başlat
            try:
                # Environment değişkenlerini hazırla
                env = os.environ.copy()

                # src klasörünü Python yoluna ekle
                src_path = str(Path(__file__).parent.parent.parent)
                if "PYTHONPATH" in env:
                    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
                else:
                    env["PYTHONPATH"] = src_path

                self.proxy_process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if self.helper.is_windows() else 0,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env=env,
                )
            except FileNotFoundError:
                raise Exception("mitmdump not found")

            # Process'in başlaması ve sertifika dosyalarının oluşturulması için bekle
            import time
            time.sleep(3)  # Bekleme süresini 3 saniyeye çıkardık

            if self.proxy_process.poll() is not None:
                error = self.proxy_process.stderr.read()
                stdout = self.proxy_process.stdout.read()
                error_msg = f"STDERR: {error}\nSTDOUT: {stdout}"
                raise Exception(error_msg)

            # Proxy ayarlarını yapılandır
            yield from self.setup_proxy()

            # Başarılı başlatma mesajı
            if status_callback:
                status_callback(self.locale.get_text("proxy.start.success"))

            # Çıktıları okumak için thread'ler başlat
            def read_output(pipe, prefix):
                for line in pipe:
                    if status_callback and line.strip():
                        status_callback(f"{prefix}: {line.strip()}")

            threading.Thread(
                target=read_output,
                args=(
                    self.proxy_process.stdout,
                    self.locale.get_text("proxy.start.info"),
                ),
                daemon=True,
            ).start()

            threading.Thread(
                target=read_output,
                args=(
                    self.proxy_process.stderr,
                    self.locale.get_text("proxy.start.error"),
                ),
                daemon=True,
            ).start()

            return True

        except Exception as e:
            if status_callback:
                status_callback(
                    self.locale.get_text("proxy.start.error").format(error=str(e))
                )
            if self.proxy_process:
                self.proxy_process.terminate()
                self.proxy_process = None
            raise
