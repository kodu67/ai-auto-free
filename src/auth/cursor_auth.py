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
        self.account_data = {}

        self.email_service = EmailService()
        self.LOGIN_URL = "https://authenticator.cursor.sh"
        self.SIGN_UP_URL = "https://authenticator.cursor.sh/sign-up"
        self.SETTINGS_URL = "https://www.cursor.com/settings"

    def _generate_browser(self):
        browser_generator = self.browser_service.init_browser()
        try:
            while True:
                yield next(browser_generator)
        except StopIteration as e:
            self.browser = e.value

    def handle_turnstile(self, tab):
        yield self.locale.get_text("cursor.process.turnstile.starting")
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
                        yield self.locale.get_text("cursor.process.turnstile.started")
                        time.sleep(random.uniform(1, 3))
                        challenge_check.click()
                        time.sleep(2)
                        yield self.locale.get_text("cursor.process.turnstile.success")
                        return True
                except Exception as e:
                    yield e

                if any(
                    tab.ele(selector)
                    for selector in [
                        "@name=password",
                        "@data-index=0",
                        "Account Settings",
                    ]
                ):
                    yield self.locale.get_text("cursor.process.turnstile.success")
                    break

                time.sleep(random.uniform(1, 2))

        except Exception as e:
            yield f"{self.locale.get_text('cursor.process.turnstile.failed')}: {e}"
            return False

    def get_cursor_session_token(self, tab, max_attempts=3, retry_interval=2):
        """
        Cursor oturum token'ını alır
        """
        yield self.locale.get_text("cursor.process.getting_token")
        attempts = 0

        while attempts < max_attempts:
            try:
                cookies = tab.cookies()
                for cookie in cookies:
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        raw_token = cookie["value"]  # Ham token'ı al

                        # Split edilmiş token'ı döndür
                        return raw_token, raw_token.split("%3A%3A")[1]

                attempts += 1
                if attempts < max_attempts:
                    yield f"{self.locale.get_text('cursor.process.token_retry')} {attempts}: {self.locale.get_text('cursor.process.token_not_found')}, {retry_interval} {self.locale.get_text('cursor.process.seconds_retry')}"
                    time.sleep(retry_interval)
                else:
                    yield f"{self.locale.get_text('cursor.process.max_attempts')} ({max_attempts})"

            except Exception as e:
                yield f"{self.locale.get_text('cursor.process.token_error')}: {str(e)}"
                attempts += 1
                if attempts < max_attempts:
                    yield f"{self.locale.get_text('cursor.process.retry_in')} {retry_interval} {self.locale.get_text('cursor.process.seconds')}"
                    time.sleep(retry_interval)

        return None

    def update_cursor_auth(self, email=None, access_token=None, refresh_token=None):
        """
        Cursor kimlik doğrulama bilgilerini günceller
        """
        database_manager = CursorDatabaseManager()
        yield from database_manager.update_auth(email, access_token, refresh_token)

    def sign_up_account(self, tab):
        yield self.locale.get_text("cursor.starting")

        # Yeni e-posta adresi oluştur
        email, _ = self.email_service.create_email()
        if not email:
            yield self.locale.get_text("cursor.process.email_creation_failed")
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
            yield f"{self.locale.get_text('cursor.process.registration_page_error')}: {e}"
            return False

        yield from self.handle_turnstile(tab)

        try:
            if tab.ele("@name=password"):
                tab.ele("@name=password").input(password)
                time.sleep(random.uniform(1, 3))

                tab.ele("@type=submit").click()
                yield self.locale.get_text("cursor.process.processing")

        except Exception as e:
            yield f"{self.locale.get_text('cursor.process.operation_failed')}: {e}"
            return False

        time.sleep(random.uniform(1, 3))
        if tab.ele("This email is not available."):
            yield self.locale.get_text("cursor.process.email_unavailable")
            return False

        yield from self.handle_turnstile(tab)

        code = None
        while True:
            try:
                if tab.ele("Account Settings"):
                    break
                if tab.ele("@data-index=0"):
                    code_generator = self.email_service.get_verification_code(email)
                    code = None
                    while True:
                        try:
                            message = next(code_generator)
                            yield message
                        except StopIteration as e:
                            code = e.value
                            break

                    if code:
                        for i, digit in enumerate(code):
                            tab.ele(f"@data-index={i}").input(digit)
                            time.sleep(random.uniform(0.3, 0.6))

                        time.sleep(1)
                    break
            except Exception as e:
                yield f"{self.locale.get_text('cursor.process.verification_code_error')}: {e}"

        yield from self.handle_turnstile(tab)

        wait_time = random.randint(3, 6)
        for i in range(wait_time):
            yield self.locale.get_text('cursor.process.waiting') + " " + str(wait_time - i) + " " + self.locale.get_text('cursor.process.seconds')
            time.sleep(1)

        tab.get(self.SETTINGS_URL)
        time.sleep(1)
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
                yield f"{self.locale.get_text('cursor.process.usage_limit')}: {total_usage}"
        except Exception as e:
            yield f"{self.locale.get_text('cursor.process.usage_limit_error')}: {e}"

        yield self.locale.get_text("cursor.registration_success")
        account_info = f"\n{self.locale.get_text('cursor.account_info')}: {email}  {self.locale.get_text('cursor.password')}: {password}"
        time.sleep(5)
        yield account_info
        self.account_data = {
            "email": email,
            "password": password,
        }
        return True

    def create_cursor_account(self):
        browser_service = None
        email = None
        try:
            yield from self._generate_browser()
            tab = self.browser.latest_tab
            tab.run_js("try { turnstile.reset() } catch(e) { }")

            tab.get(self.LOGIN_URL)

            signup_generator = self.sign_up_account(tab)
            while True:
                try:
                    yield next(signup_generator)
                except StopIteration as e:
                    if e.value:
                        session_token_generator = self.get_cursor_session_token(tab)
                        while True:
                            try:
                                yield next(session_token_generator)
                            except StopIteration as e:
                                raw_token, token = e.value
                                if token:
                                    email = self.email_service.email
                                    yield from self.update_cursor_auth(
                                        email=email, access_token=token, refresh_token=token
                                    )
                                    self.account_data["token"] = raw_token
                                    yield from self.logger.log_account("Cursor", self.account_data)
                                    yield "-REFRESH-TABLE-"
                                break
                        break


            yield self.locale.get_text("cursor.completed")

        except Exception as e:
            yield f"{self.locale.get_text('common.error')}: {str(e)}"

        finally:
            if browser_service:
                browser_service.quit()


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
            yield self.locale.get_text("cursor.auth.no_update_values")
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
                    yield self.locale.get_text("cursor.auth.update_success").format(
                            key.split("/")[-1]
                        )
                else:
                    yield self.locale.get_text("cursor.auth.update_failed").format(
                            key.split("/")[-1]
                        )

            conn.commit()
            return True

        except sqlite3.Error as e:
            yield f"{self.locale.get_text('cursor.auth.db_error')}: {str(e)}"
            return False
        except Exception as e:
            yield f"{self.locale.get_text('cursor.auth.error')}: {str(e)}"
            return False
        finally:
            if conn:
                conn.close()
