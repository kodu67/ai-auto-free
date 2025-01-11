import os
import time
import json
import random
import logging
import requests
import pyperclip
from browser_utils import BrowserManager
from locale_manager import LocaleManager
from cursor_pro_keep_alive import handle_turnstile

class WindsurfAccountCreator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.register_url = "https://codeium.com/account/register"
        self.profile_url = "https://codeium.com/profile"
        self.locale_manager = LocaleManager()

    def _generate_email(self):
        """Geçici e-posta adresi oluşturur"""
        # Rastgele harfler ve sayılardan oluşan kullanıcı adı
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        username = ''.join(random.choice(chars) for _ in range(10))

        # Rastgele domain seçimi
        domains = ["gmail.com", "outlook.com"]
        domain = random.choice(domains)

        email = f"{username}@{domain}"
        return email

    def _generate_password(self, length=12):
        """Güçlü bir şifre oluşturur"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))

    def _get_firebase_token(self, tab):
        """Firebase token'ını alır"""
        js_code = """
        function getFirebaseAuthToken() {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open("firebaseLocalStorageDb");

                request.onerror = (event) => {
                    reject(JSON.stringify({
                        error: "IndexedDB açılırken hata",
                        details: event.target.error
                    }));
                };

                request.onsuccess = (event) => {
                    const db = event.target.result;
                    const transaction = db.transaction(["firebaseLocalStorage"], "readonly");
                    const objectStore = transaction.objectStore("firebaseLocalStorage");

                    const getAllRequest = objectStore.getAll();

                    getAllRequest.onsuccess = (event) => {
                        const items = event.target.result;
                        const authData = items.find(item =>
                            item.fbase_key.startsWith("firebase:authUser:")
                        );

                        if (authData && authData.value) {
                            const tokenData = {
                                apiKey: authData.value.apiKey,
                                accessToken: authData.value.stsTokenManager.accessToken,
                                refreshToken: authData.value.stsTokenManager.refreshToken,
                                expirationTime: authData.value.stsTokenManager.expirationTime
                            };
                            resolve(JSON.stringify(tokenData, null, 2));
                        } else {
                            reject(JSON.stringify({
                                error: "Auth verisi bulunamadı"
                            }));
                        }
                    };

                    getAllRequest.onerror = (event) => {
                        reject(JSON.stringify({
                            error: "Veri alınırken hata",
                            details: event.target.error
                        }));
                    };
                };
            });
        }
        return getFirebaseAuthToken();
        """
        try:
            result = tab.run_js(js_code)
            token_data = json.loads(result)
            return token_data.get("accessToken")
        except Exception as e:
            self.logger.error(f"{self.locale_manager.get_text('logging.token_error')}: {str(e)}")
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

        email = self._generate_email()
        if not email:
            return False, self.locale_manager.get_text("windsurf.errors.email_creation")

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

            password_inputs = tab.eles("@type=password", timeout=10)
            if len(password_inputs) < 2:
                return False, self.locale_manager.get_text("windsurf.errors.password_fields")
            password_inputs[0].input(password)  # Şifre
            password_inputs[1].input(password)  # Şifre tekrarı

            # Kullanım şartları checkbox'ı
            terms_checkbox = tab.ele("@id=termsAccepted", timeout=10)
            if not terms_checkbox:
                return False, self.locale_manager.get_text("windsurf.errors.terms_checkbox")
            terms_checkbox.click()

            # Cloudflare Turnstile çözümü
            print("[*] " + self.locale_manager.get_text("windsurf.progress.solving_turnstile"))
            if not handle_turnstile(tab, self.locale_manager.get_locale()):
                return False, self.locale_manager.get_text("windsurf.errors.turnstile")

            # Kayıt ol butonuna tıkla
            signup_button = tab.ele("text=Sign up", timeout=10)
            if not signup_button:
                return False, self.locale_manager.get_text("windsurf.errors.signup_button")
            signup_button.click()

            # Profile sayfasına git ve token al
            time.sleep(3)  # Yönlendirmeyi bekle
            tab.get(self.profile_url)
            time.sleep(3)  # Sayfanın yüklenmesini bekle

            print("[*] " + self.locale_manager.get_text("windsurf.progress.getting_token"))
            token = self._get_firebase_token(tab)
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
            self.logger.error(f"{self.locale_manager.get_text('logging.account_error')}: {str(e)}")
            return False, str(e)

        finally:
            browser_manager.quit()

def handle_turnstile(tab, locale):
    print(locale["cursor"]["process"]["turnstile"]["starting"])
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
                        print(locale["cursor"]["process"]["turnstile"]["started"])
                        time.sleep(random.uniform(1, 3))
                        iframe.click()
                        time.sleep(2)

                        # Başarı kontrolü
                        response_input = tab.ele("@name=cf-turnstile-response")
                        if response_input and response_input.attr("value"):
                            print(locale["cursor"]["process"]["turnstile"]["success"])
                            return True

                # Sign up butonu aktif mi kontrol et
                signup_button = tab.ele("text=Sign up")
                if signup_button and not signup_button.attr("disabled"):
                    print(locale["cursor"]["process"]["turnstile"]["success"])
                    return True

            except Exception:
                pass

            time.sleep(random.uniform(1, 2))

    except Exception as e:
        print(f"{locale['cursor']['process']['turnstile']['failed']}: {e}")
        return False
