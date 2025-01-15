import os
import time
import json
import random
import requests
import pyperclip
from browser_utils import BrowserManager
from locale_manager import LocaleManager
from cursor_pro_keep_alive import handle_turnstile
from get_email_code import EmailVerificationHandler

class WindsurfAccountCreator:
    def __init__(self):
        self.register_url = "https://codeium.com/account/register"
        self.profile_url = "https://codeium.com/profile"
        self.locale_manager = LocaleManager()
        self.email_handler = EmailVerificationHandler()

        # JavaScript dosyasını yükle
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'firebase_token.js')
        with open(script_path, 'r', encoding='utf-8') as f:
            self.firebase_token_script = f.read()

    def _generate_email(self):
        """Geçici e-posta adresi oluşturur"""
        print("[*] " + self.locale_manager.get_text("windsurf.steps.email"))

        try:
            email, token = self.email_handler.create_email()
            if email and token:
                self.email_handler.email = email  # Email'i handler'a kaydet
                return email
            else:
                print(self.locale_manager.get_text("logging.email_error"))
                return None
        except Exception as e:
            print(f"{self.locale_manager.get_text('logging.email_error')}: {str(e)}")
            return None

    def _generate_password(self, length=12):
        """Güçlü bir şifre oluşturur"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))

    def _get_firebase_token(self, tab, max_attempts=3, retry_interval=2):
        """Firebase token'ını alır"""
        attempts = 0

        while attempts < max_attempts:
            try:
                # JavaScript kodunu çalıştır
                result = tab.run_js(f"{self.firebase_token_script}\nreturn getFirebaseAuthToken();")
                token_data = json.loads(result)
                return token_data.get("accessToken")

            except Exception as e:
                attempts += 1
                if attempts < max_attempts:
                    print(f"{self.locale_manager.get_text('cursor.process.token_retry')} {attempts}: "
                          f"{self.locale_manager.get_text('cursor.process.token_not_found')}, "
                          f"{retry_interval} {self.locale_manager.get_text('cursor.process.seconds_retry')}")
                    time.sleep(retry_interval)
                else:
                    print(f"{self.locale_manager.get_text('cursor.process.max_attempts')} ({max_attempts})")

        return None

    def _print_token_usage(self):
        """Token kullanım talimatlarını yazdırır"""
        print("\n" + self.locale_manager.get_text("windsurf.token_usage.title"))
        print(self.locale_manager.get_text("windsurf.token_usage.step1"))
        print(self.locale_manager.get_text("windsurf.token_usage.step2"))
        print(self.locale_manager.get_text("windsurf.token_usage.step3"))
        print(self.locale_manager.get_text("windsurf.token_usage.command"))
        print(self.locale_manager.get_text("windsurf.token_usage.step4"))
        print(self.locale_manager.get_text("windsurf.token_usage.step5"))
        print()

    def create_account(self):
        """Windsurf hesabı oluşturur"""
        print("[*] " + self.locale_manager.get_text("windsurf.progress.creating_account"))

        # Email oluştur
        email = self._generate_email()
        if not email:
            return False, self.locale_manager.get_text("windsurf.errors.email_creation")

        # Şifre oluştur
        password = self._generate_password()
        browser_manager = BrowserManager(headless=True)
        browser = browser_manager.init_browser()

        try:
            tab = browser.latest_tab

            # Kayıt sayfasına git
            tab.get(self.register_url)

            print("[*] " + self.locale_manager.get_text("windsurf.progress.filling_form"))
            # Form elementlerini doldur
            email_input = tab.ele("@type=email", timeout=10)
            if not email_input:
                return False, self.locale_manager.get_text("windsurf.errors.email_field")
            email_input.input(email)
            time.sleep(random.uniform(1, 3))  # Rastgele bekleme ekledik

            password_inputs = tab.eles("@type=password", timeout=10)
            if len(password_inputs) < 2:
                return False, self.locale_manager.get_text("windsurf.errors.password_fields")

            # İlk şifre alanı
            password_inputs[0].input(password)
            time.sleep(random.uniform(0.5, 1.5))  # Rastgele bekleme ekledik

            # İkinci şifre alanı
            password_inputs[1].input(password)
            time.sleep(random.uniform(0.5, 1.5))  # Rastgele bekleme ekledik

            # Kullanım şartları checkbox'ı
            terms_checkbox = tab.ele("@id=termsAccepted", timeout=10)
            if not terms_checkbox:
                return False, self.locale_manager.get_text("windsurf.errors.terms_checkbox")
            terms_checkbox.click()
            time.sleep(random.uniform(1, 2))  # Rastgele bekleme ekledik

            # Cloudflare Turnstile çözümü
            print("[*] " + self.locale_manager.get_text("windsurf.progress.solving_turnstile"))
            if not handle_turnstile(tab, self.locale_manager.get_locale()):
                return False, self.locale_manager.get_text("windsurf.errors.turnstile")

            # Kayıt ol butonuna tıkla
            signup_button = tab.ele("text=Sign up", timeout=10)
            if not signup_button:
                return False, self.locale_manager.get_text("windsurf.errors.signup_button")
            signup_button.click()
            time.sleep(random.uniform(2, 4))  # Rastgele bekleme ekledik

            # Profile sayfasına git ve token al
            time.sleep(3)  # Yönlendirmeyi bekle
            tab.get(self.profile_url)
            time.sleep(3)  # Sayfanın yüklenmesini bekle

            print("[*] " + self.locale_manager.get_text("windsurf.progress.getting_token"))
            token = self._get_firebase_token(tab, max_attempts=3, retry_interval=2)
            if not token:
                return False, self.locale_manager.get_text("windsurf.errors.token")

            # Token'ı panoya kopyala
            pyperclip.copy(token)
            print("[*] " + self.locale_manager.get_text("windsurf.token_copied"))

            # Token kullanım talimatlarını göster
            self._print_token_usage()

            account_info = {
                "email": email,
                "password": password,
                "token": "*** " + self.locale_manager.get_text("windsurf.token_copied") + " ***"
            }
            return True, account_info

        except Exception as e:
            print(f"{self.locale_manager.get_text('logging.account_error')}: {str(e)}")
            return False, str(e)

        finally:
            browser_manager.quit()

def handle_turnstile(tab, locale):
    print("[*] " + locale["cursor"]["process"]["turnstile"]["starting"])
    try:
        while True:
            try:
                # Shadow root içinde iframe'i ara
                turnstile_div = tab.ele("div[style*='width: 300px; height: 65px']", timeout=2)
                if turnstile_div:
                    iframe = (
                        turnstile_div
                        .child()
                        .shadow_root
                        .ele("tag:iframe")
                    )

                    if iframe:
                        print("[*] " + locale["cursor"]["process"]["turnstile"]["started"])
                        time.sleep(random.uniform(1, 3))
                        iframe.click()
                        time.sleep(2)

                        # Başarı kontrolü
                        response_input = tab.ele("@name=cf-turnstile-response")
                        if response_input and response_input.attr("value"):
                            print("[*] " + locale["cursor"]["process"]["turnstile"]["success"])
                            return True

                # Sign up butonu aktif mi kontrol et
                signup_button = tab.ele("text=Sign up")
                if signup_button and not signup_button.attr("disabled"):
                    print("[*] " + locale["cursor"]["process"]["turnstile"]["success"])
                    return True

            except Exception:
                pass

            time.sleep(random.uniform(1, 2))

    except Exception as e:
        print(f"{locale['cursor']['process']['turnstile']['failed']}: {e}")
        return False
