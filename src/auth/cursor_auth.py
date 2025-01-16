import sqlite3
import os
import time
import random
from utils.locale import Locale
from utils.storage import Storage
from utils.helper import Helper
from utils.logger import Logger
from services.browser_service import BrowserService
from services.email_service import EmailService


class CursorAuthManager:
    def __init__(self):
        self.locale = Locale()
        self.helper = Helper()
        self.logger = Logger()
        self.browser_service = BrowserService()
        self.browser = self.browser_service.init_browser()
        self.email_service = EmailService()

        self.LOGIN_URL = "https://authenticator.cursor.sh"
        self.SIGN_UP_URL = "https://authenticator.cursor.sh/sign-up"
        self.SETTINGS_URL = "https://www.cursor.com/settings"

        self.main()

    def handle_turnstile(self, tab):
        print(self.locale.get_text("cursor.process.turnstile.starting"))
        try:
            while True:
                try:
                    challenge_check = (
                        tab.ele("@id=cf-turnstile", timeout=2)
                        .child()
                        .shadow_root.ele("tag:iframe")
                        .ele("tag:body")
                        .sr("tag:input")
                    )

                    if challenge_check:
                        print(self.locale.get_text("cursor.process.turnstile.started"))
                        time.sleep(random.uniform(1, 3))
                        challenge_check.click()
                        time.sleep(2)
                        print(self.locale.get_text("cursor.process.turnstile.success"))
                        return True
                except Exception as e:
                    print(e)

                if any(
                    tab.ele(selector)
                    for selector in [
                        "@name=password",
                        "@data-index=0",
                        "Account Settings",
                    ]
                ):
                    print(self.locale.get_text("cursor.process.turnstile.success"))
                    break

                time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"{self.locale.get_text('cursor.process.turnstile.failed')}: {e}")
            return False

    def get_cursor_session_token(self, tab, max_attempts=3, retry_interval=2):
        """
        Cursor oturum token'ını alır
        """
        print(self.locale.get_text("cursor.process.getting_token"))
        attempts = 0

        while attempts < max_attempts:
            try:
                cookies = tab.cookies()
                for cookie in cookies:
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        raw_token = cookie["value"]  # Ham token'ı al

                        # Cache dizinini oluştur
                        cache_dir = os.path.join(
                            os.path.expanduser("~"), ".cursor_cache"
                        )
                        os.makedirs(cache_dir, exist_ok=True)

                        # Token'ı cache'e kaydet
                        cache_file = os.path.join(cache_dir, "session_token.txt")
                        with open(cache_file, "w", encoding="utf-8") as f:
                            f.write(raw_token)

                        # Split edilmiş token'ı döndür
                        return raw_token.split("%3A%3A")[1]

                attempts += 1
                if attempts < max_attempts:
                    print(
                        f"{self.locale.get_text('cursor.process.token_retry')} {attempts}: {self.locale.get_text('cursor.process.token_not_found')}, {retry_interval} {self.locale.get_text('cursor.process.seconds_retry')}"
                    )
                    time.sleep(retry_interval)
                else:
                    print(
                        f"{self.locale.get_text('cursor.process.max_attempts')} ({max_attempts})"
                    )

            except Exception as e:
                print(f"{self.locale.get_text('cursor.process.token_error')}: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    print(
                        f"{self.locale.get_text('cursor.process.retry_in')} {retry_interval} {self.locale.get_text('cursor.process.seconds')}"
                    )
                    time.sleep(retry_interval)

        return None

    def update_cursor_auth(self, email=None, access_token=None, refresh_token=None):
        """
        Cursor kimlik doğrulama bilgilerini günceller
        """
        database_manager = CursorDatabaseManager()
        return database_manager.update_auth(email, access_token, refresh_token)

    def sign_up_account(self, tab):
        print(self.locale.get_text("cursor.starting"))

        # Yeni e-posta adresi oluştur
        email, _ = self.email_service.create_email()
        if not email:
            print(self.locale.get_text("cursor.process.email_creation_failed"))
            return False

        # Rastgele şifre oluştur
        password = self.helper.generate_password()

        first_name, last_name = self.helper.get_random_name()

        tab.get(self.SIGN_UP_URL)

        try:
            if tab.ele("@name=first_name"):
                tab.actions.click("@name=first_name").input(first_name)
                time.sleep(random.uniform(1, 3))

                tab.actions.click("@name=last_name").input(last_name)
                time.sleep(random.uniform(1, 3))

                tab.actions.click("@name=email").input(email)
                time.sleep(random.uniform(1, 3))

                tab.actions.click("@type=submit")

        except Exception as e:
            print(
                f"{self.locale.get_text('cursor.process.registration_page_error')}: {e}"
            )
            return False

        self.handle_turnstile(tab)

        try:
            if tab.ele("@name=password"):
                tab.ele("@name=password").input(password)
                time.sleep(random.uniform(1, 3))

                tab.ele("@type=submit").click()
                print(self.locale.get_text("cursor.process.processing"))

        except Exception as e:
            print(f"{self.locale.get_text('cursor.process.operation_failed')}: {e}")
            return False

        time.sleep(random.uniform(1, 3))
        if tab.ele("This email is not available."):
            print(self.locale.get_text("cursor.process.email_unavailable"))
            return False

        self.handle_turnstile(tab)

        while True:
            try:
                if tab.ele("Account Settings"):
                    break
                if tab.ele("@data-index=0"):
                    code = self.email_service.get_verification_code(email)
                    if not code:
                        return False

                    for i, digit in enumerate(code):
                        tab.ele(f"@data-index={i}").input(digit)
                        time.sleep(random.uniform(0.1, 0.3))
                    break
            except Exception as e:
                print(
                    f"{self.locale.get_text('cursor.process.verification_code_error')}: {e}"
                )

        self.handle_turnstile(tab)

        wait_time = random.randint(3, 6)
        for i in range(wait_time):
            print(
                f"{self.locale.get_text('cursor.process.waiting')} {wait_time - i} {self.locale.get_text('cursor.process.seconds')}"
            )
            time.sleep(1)

        tab.get(self.SETTINGS_URL)

        try:
            usage_selector = (
                "css:div.col-span-2 > div > div > div > div > "
                "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
                "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
            )
            usage_ele = tab.ele(usage_selector)
            if usage_ele:
                usage_info = usage_ele.text
                total_usage = usage_info.split("/")[-1].strip()
                print(
                    f"{self.locale.get_text('cursor.process.usage_limit')}: {total_usage}"
                )
        except Exception as e:
            print(f"{self.locale.get_text('cursor.process.usage_limit_error')}: {e}")

        print(self.locale.get_text("cursor.registration_success"))
        account_info = f"\n{self.locale.get_text('cursor.account_info')}: {email}  {self.locale.get_text('cursor.password')}: {password}"
        time.sleep(5)
        print(account_info)
        self.logger.log_account("cursor", {"email": email, "password": password})
        return True

    def main(self):
        browser_service = None
        email = None
        try:
            tab = self.browser.latest_tab
            tab.run_js("try { turnstile.reset() } catch(e) { }")

            tab.get(self.LOGIN_URL)

            if self.sign_up_account(tab):
                token = self.get_cursor_session_token(tab)
                if token:
                    email = self.email_service.email
                    self.update_cursor_auth(
                        email=email, access_token=token, refresh_token=token
                    )
                else:
                    self.helper.press_enter()

            print(self.locale.get_text("cursor.completed"))

        except Exception as e:
            print(f"{self.locale.get_text('common.error')}: {str(e)}")

        finally:
            if browser_service:
                browser_service.quit()
            self.helper.press_enter()


class CursorDatabaseManager:
    def __init__(self):
        self.locale = Locale()
        self.storage = Storage()

        self.db_path = self.storage.cursor_db_path()

    def update_auth(self, email=None, access_token=None, refresh_token=None):
        """
        Cursor kimlik doğrulama bilgilerini günceller
        :param email: Yeni e-posta adresi
        :param access_token: Yeni erişim anahtarı
        :param refresh_token: Yeni yenileme anahtarı
        :return: bool Güncellemenin başarılı olup olmadığı
        """
        updates = []
        updates.append(("cursorAuth/cachedSignUpType", "Auth_0"))

        if email is not None:
            updates.append(("cursorAuth/cachedEmail", email))
        if access_token is not None:
            updates.append(("cursorAuth/accessToken", access_token))
        if refresh_token is not None:
            updates.append(("cursorAuth/refreshToken", refresh_token))

        if not updates:
            print(self.locale.get_text("cursor.auth.no_update_values"))
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for key, value in updates:
                check_query = "SELECT COUNT(*) FROM itemTable WHERE key = ?"
                cursor.execute(check_query, (key,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO itemTable (key, value) VALUES (?, ?)"
                    cursor.execute(insert_query, (key, value))
                else:
                    update_query = "UPDATE itemTable SET value = ? WHERE key = ?"
                    cursor.execute(update_query, (value, key))

                if cursor.rowcount > 0:
                    print(
                        self.locale.get_text("cursor.auth.update_success").format(
                            key.split("/")[-1]
                        )
                    )
                else:
                    print(
                        self.locale.get_text("cursor.auth.update_failed").format(
                            key.split("/")[-1]
                        )
                    )

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"{self.locale.get_text('cursor.auth.db_error')}: {str(e)}")
            return False
        except Exception as e:
            print(f"{self.locale.get_text('cursor.auth.error')}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
