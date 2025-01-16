import os
import time
import json
import random
import pyperclip
from services.browser_service import BrowserService
from services.email_service import EmailService
from utils.locale import Locale
from utils.helper import Helper
from utils.logger import Logger


class WindsurfAuthManager:
    def __init__(self):
        self.LOGIN_URL = "https://codeium.com/account/login"
        self.REGISTER_URL = "https://codeium.com/account/register"
        self.PROFILE_URL = "https://codeium.com/profile"
        self.locale = Locale()
        self.helper = Helper()
        self.logger = Logger()
        self.email_service = EmailService()

        # JavaScript dosyasını yükle
        script_path = os.path.join(
            self.helper.get_src_path(), "scripts", "firebase_token.js"
        )
        with open(script_path, "r", encoding="utf-8") as f:
            self.firebase_token_script = f.read()

        self.create_account()

    def _generate_email(self):
        """Geçici e-posta adresi oluşturur"""
        print("[*] " + self.locale.get_text("windsurf.steps.email"))

        try:
            email, _ = self.email_service.create_email()
            if email:
                self.email_service.email = email
                return email
            else:
                print(self.locale.get_text("logging.email_error"))
                return None
        except Exception as e:
            print(f"{self.locale.get_text('logging.email_error')}: {str(e)}")
            return None

    def _get_firebase_token(self, tab, max_attempts=3, retry_interval=2):
        """Firebase token'ını alır"""
        attempts = 0

        while attempts < max_attempts:
            try:
                # JavaScript kodunu çalıştır
                result = tab.run_js(
                    f"{self.firebase_token_script}\nreturn getFirebaseAuthToken();"
                )
                token_data = json.loads(result)
                return token_data.get("accessToken")

            except Exception:
                attempts += 1
                if attempts < max_attempts:
                    print(
                        f"{self.locale.get_text('cursor.process.token_retry')} {attempts}: "
                        f"{self.locale.get_text('cursor.process.token_not_found')}, "
                        f"{retry_interval} {self.locale.get_text('cursor.process.seconds_retry')}"
                    )
                    time.sleep(retry_interval)
                else:
                    print(
                        f"{self.locale.get_text('cursor.process.max_attempts')} ({max_attempts})"
                    )

        return None

    def _print_token_usage(self):
        """Token kullanım talimatlarını yazdırır"""
        print("\n" + self.locale.get_text("windsurf.token_usage.title"))
        print(self.locale.get_text("windsurf.token_usage.step1"))
        print(self.locale.get_text("windsurf.token_usage.step2"))
        print(self.locale.get_text("windsurf.token_usage.step3"))
        print(self.locale.get_text("windsurf.token_usage.command"))
        print(self.locale.get_text("windsurf.token_usage.step4"))
        print(self.locale.get_text("windsurf.token_usage.step5"))
        print()

    def create_account(self):
        """Windsurf hesabı oluşturur"""
        print("[*] " + self.locale.get_text("windsurf.progress.creating_account"))

        # Email oluştur
        email = self._generate_email()
        if not email:
            return False, self.locale.get_text("windsurf.errors.email_creation")

        # Şifre oluştur
        password = self.helper.generate_password()

        browser_service = BrowserService()
        browser = browser_service.init_browser()

        try:
            tab = browser.latest_tab
            tab.run_js("try { turnstile.reset() } catch(e) { }")

            # Kayıt sayfasına git
            tab.get(self.LOGIN_URL)

            time.sleep(0.5)

            tab.get(self.REGISTER_URL)

            print("[*] " + self.locale.get_text("windsurf.progress.filling_form"))

            time.sleep(random.uniform(1, 3))

            # Form elementlerini doldur
            email_input = tab.ele("@type=email", timeout=10)
            if not email_input:
                return False, self.locale.get_text("windsurf.errors.email_field")
            tab.actions.click("@type=email").input(email)
            time.sleep(random.uniform(1, 3))

            password_inputs = tab.eles("@type=password", timeout=10)
            if len(password_inputs) < 2:
                return False, self.locale.get_text("windsurf.errors.password_fields")
            time.sleep(random.uniform(1, 3))

            # İlk şifre alanı
            tab.actions.click(password_inputs[0]).input(password)
            time.sleep(random.uniform(0.5, 1.5))

            # İkinci şifre alanı
            tab.actions.click(password_inputs[1]).input(password)
            time.sleep(random.uniform(0.5, 1.5))

            # Kullanım şartları checkbox'ı
            terms_checkbox = tab.ele("@id=termsAccepted", timeout=10)
            if not terms_checkbox:
                return False, self.locale.get_text("windsurf.errors.terms_checkbox")
            terms_checkbox.click()
            time.sleep(random.uniform(1, 2))

            # Cloudflare Turnstile çözümü
            if not self.handle_turnstile(tab):
                return False, self.locale.get_text("windsurf.errors.turnstile")

            # Kayıt ol butonuna tıkla
            signup_button = tab.ele("text=Sign up", timeout=10)
            if not signup_button:
                return False, self.locale.get_text("windsurf.errors.signup_button")
            signup_button.click()
            if not tab.wait.ele_displayed("@placeholder=Your first name", timeout=30):
                time.sleep(6)

            tab.get(self.PROFILE_URL)
            time.sleep(3)  # Sayfanın yüklenmesini bekle

            print("[*] " + self.locale.get_text("windsurf.progress.getting_token"))
            token = self._get_firebase_token(tab, max_attempts=3, retry_interval=3)
            if not token:
                return False, self.locale.get_text("windsurf.errors.token")

            # Token'ı panoya kopyala
            pyperclip.copy(token)
            print("[*] " + self.locale.get_text("windsurf.token_copied"))

            # Token kullanım talimatlarını göster
            self._print_token_usage()

            account_data = {"email": email, "password": password, "token": token}

            self.logger.log_account("windsurf", account_data)

            print("\n" + self.locale.get_text("windsurf.registration_success"))
            print("\n" + self.locale.get_text("common.account_info"))
            print("+" + "-" * 50 + "+")
            print(f"| {self.locale.get_text('common.email'):<15}: {email:<32} |")
            print(f"| {self.locale.get_text('common.password'):<15}: {password:<32} |")
            print("+" + "-" * 50 + "+")
            print("\n" + "+" + "-" * 70 + "+")
            print(f"| {self.locale.get_text('windsurf.token_copied'):<15} |")
            print("+" + "-" * 70 + "+")

        except Exception as e:
            print(f"{self.locale.get_text('logging.account_error')}: {str(e)}")
            print("\n   " + self.locale.get_text("windsurf.registration_failed"))
            print(f"   {self.locale.get_text('common.error')}: {account_data}")

        finally:
            self.helper.press_enter()
            browser_service.quit()

    def handle_turnstile(self, tab):
        print("[*] " + self.locale.get_text("windsurf.progress.solving_turnstile"))
        try:
            while True:
                # Başarı durumunu kontrol et
                response_input = tab.ele("@name=cf-turnstile-response")
                if response_input and response_input.attr("value"):
                    print(
                        "[*] "
                        + self.locale.get_text(
                            "windsurf.progress.solving_turnstile_success"
                        )
                    )
                    return True

                # Shadow root içinde iframe'i ara
                turnstile_div = tab.ele(
                    "div[style*='width: 300px; height: 65px']", timeout=2
                )

                if turnstile_div:
                    iframe = turnstile_div.child().shadow_root.ele("tag:iframe")

                    if iframe:
                        time.sleep(3)
                        print(
                            "[*] "
                            + self.locale.get_text(
                                "windsurf.progress.solving_turnstile"
                            )
                        )
                        time.sleep(random.uniform(1, 3))
                        iframe.click()
                        time.sleep(2)

                        # Başarı kontrolü
                        response_input = tab.ele("@name=cf-turnstile-response")
                        if response_input and response_input.attr("value"):
                            print(
                                "[*] "
                                + self.locale.get_text(
                                    "windsurf.progress.solving_turnstile_success"
                                )
                            )
                            return True

                # Sign up butonu aktif mi kontrol et
                signup_button = tab.ele("text=Sign up")
                if signup_button and not signup_button.attr("disabled"):
                    print(
                        "[*] "
                        + self.locale.get_text(
                            "windsurf.progress.solving_turnstile_success"
                        )
                    )
                    return True

                time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"{self.locale.get_text('windsurf.errors.turnstile')}: {e}")
            return False
