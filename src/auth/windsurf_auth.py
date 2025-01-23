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

    def _generate_email(self):
        """Geçici e-posta adresi oluşturur"""
        yield "[*] " + self.locale.get_text("windsurf.steps.email")

        try:
            email, _ = self.email_service.create_email()
            return email
        except Exception as e:
            yield f"{self.locale.get_text('logging.email_error')}: {e}"
            return None

    def _print_token_usage(self):
        """Token kullanım talimatlarını yazdırır"""
        yield "\n" + self.locale.get_text("windsurf.token_usage.title")
        yield self.locale.get_text("windsurf.token_usage.step1")
        yield self.locale.get_text("windsurf.token_usage.step2")
        yield self.locale.get_text("windsurf.token_usage.step3")
        yield self.locale.get_text("windsurf.token_usage.command")
        yield self.locale.get_text("windsurf.token_usage.step4")
        yield self.locale.get_text("windsurf.token_usage.step5")
        yield self.locale.get_text("windsurf.token_usage.command")

    def create_account(self):
        """Windsurf hesabı oluşturur"""
        yield "[*] " + self.locale.get_text("windsurf.progress.creating_account")
        self.firebase_token = None  # Token'ı saklamak için

        # Email oluştur
        email_generator = self._generate_email()
        try:
            while True:
                yield next(email_generator)
        except StopIteration as e:
            email = e.value
            if not email:
                return False, self.locale.get_text("windsurf.errors.email_creation")

        # Şifre oluştur
        password = self.helper.generate_password()

        browser_service = BrowserService()
        browser_generator = browser_service.init_browser()
        try:
            while True:
                yield next(browser_generator)
        except StopIteration as e:
            browser = e.value

        try:
            tab = browser.latest_tab
            tab.run_js("try { turnstile.reset() } catch(e) { }")

            # Kayıt sayfasına git
            tab.get(self.LOGIN_URL)
            time.sleep(0.5)
            tab.get(self.REGISTER_URL)

            yield "[*] " + self.locale.get_text("windsurf.progress.filling_form")
            time.sleep(random.uniform(1, 3))

            TOKEN_URL = "identitytoolkit.googleapis.com"

            # Network dinlemeyi başlat
            tab.listen.start(TOKEN_URL)

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
            handle_turnstile_generator = self.handle_turnstile(tab)
            try:
                while True:
                    yield next(handle_turnstile_generator)
            except StopIteration as e:
                if not e.value:
                    return False, self.locale.get_text("windsurf.errors.turnstile")

            # Kayıt ol butonuna tıkla
            signup_button = tab.ele("text=Sign up", timeout=10)
            if not signup_button:
                return False, self.locale.get_text("windsurf.errors.signup_button")

            # Network isteğini bekle ve token'ı al
            tab.listen.start()

            signup_button.click()

            packet = tab.listen.wait(timeout=10)
            if packet and TOKEN_URL in packet.url:
                if packet.response and packet.response.body:
                    self.firebase_token = packet.response.body.get("idToken")

            tab.listen.stop()  # Dinlemeyi durdur

            if not tab.wait.ele_displayed("@placeholder=Your first name", timeout=20):
                yield "Windsurf registration server is unavailable. Please try again later."
                yield "Retrying... (5 sec)"
                time.sleep(5)
                yield self.helper.clear_screen()
                yield from self.create_account()

            tab.get(self.PROFILE_URL)
            time.sleep(3)  # Sayfanın yüklenmesini bekle

            yield "[*] " + self.locale.get_text("windsurf.progress.getting_token")

            if self.firebase_token:
                # Token'ı panoya kopyala
                pyperclip.copy(self.firebase_token)
                yield "[*] " + self.locale.get_text("windsurf.token_copied")

                # Token kullanım talimatlarını göster
                yield from self._print_token_usage()

                account_data = {
                    "email": email,
                    "password": password,
                    "token": self.firebase_token,
                }

                yield from self.logger.log_account("Windsurf", account_data)
                yield "-REFRESH-TABLE-"

                yield "\n" + self.locale.get_text("windsurf.registration_success")
                yield "\n" + self.locale.get_text("common.account_info")
                yield "+" + "-" * 50 + "+"
                yield f"| {self.locale.get_text('common.email'):<15}: {email:<32} |"
                yield f"| {self.locale.get_text('common.password'):<15}: {password:<32} |"
                yield "+" + "-" * 50 + "+"
                yield "\n" + "+" + "-" * 70 + "+"
                yield f"| {self.locale.get_text('windsurf.token_copied'):<15} |"
                yield "+" + "-" * 70 + "+"
            else:
                yield "[!] Token not found"

        except Exception as e:
            yield f"{self.locale.get_text('logging.account_error')}: {str(e)}"
            yield "\n   " + self.locale.get_text("windsurf.registration_failed")
            yield f"   {self.locale.get_text('common.error')}: {str(e)}"

        finally:
            browser_service.quit()

    def handle_turnstile(self, tab):
        yield "[*] " + self.locale.get_text("windsurf.progress.solving_turnstile")
        try:
            while True:
                # Başarı durumunu kontrol et
                response_input = tab.ele("@name=cf-turnstile-response")
                if response_input and response_input.attr("value"):
                    yield "[*] " + self.locale.get_text(
                        "windsurf.progress.solving_turnstile_success"
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
                        yield "[*] " + self.locale.get_text(
                            "windsurf.progress.solving_turnstile"
                        )
                        time.sleep(random.uniform(1, 3))
                        iframe.click()
                        time.sleep(2)

                        # Başarı kontrolü
                        response_input = tab.ele("@name=cf-turnstile-response")
                        if response_input and response_input.attr("value"):
                            yield "[*] " + self.locale.get_text(
                                "windsurf.progress.solving_turnstile_success"
                            )
                            return True

                # Sign up butonu aktif mi kontrol et
                signup_button = tab.ele("text=Sign up")
                if signup_button and not signup_button.attr("disabled"):
                    yield "[*] " + self.locale.get_text(
                        "windsurf.progress.solving_turnstile_success"
                    )
                    return True

                time.sleep(random.uniform(1, 2))
                break

        except Exception as e:
            yield f"{self.locale.get_text('windsurf.errors.turnstile')}: {e}"
            return False
