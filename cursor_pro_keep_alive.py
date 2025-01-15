import os
import logging

os.environ["PYTHONVERBOSE"] = "0"
os.environ["PYINSTALLER_VERBOSE"] = "0"

import time
import random
from cursor_auth_manager import CursorAuthManager
from browser_utils import BrowserManager
from get_email_code import EmailVerificationHandler
from locale_manager import LocaleManager


# Sabit URL'ler
LOGIN_URL = "https://authenticator.cursor.sh"
SIGN_UP_URL = "https://authenticator.cursor.sh/sign-up"
SETTINGS_URL = "https://www.cursor.com/settings"


def handle_turnstile(tab, locale):
    print(locale["cursor"]["process"]["turnstile"]["starting"])
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
                    print(locale["cursor"]["process"]["turnstile"]["started"])
                    time.sleep(random.uniform(1, 3))
                    challenge_check.click()
                    time.sleep(2)
                    print(locale["cursor"]["process"]["turnstile"]["success"])
                    return True
            except:
                pass

            if any(
                tab.ele(selector)
                for selector in [
                    "@name=password",
                    "@data-index=0",
                    "Account Settings",
                ]
            ):
                print(locale["cursor"]["process"]["turnstile"]["success"])
                break

            time.sleep(random.uniform(1, 2))

    except Exception as e:
        print(f"{locale['cursor']['process']['turnstile']['failed']}: {e}")
        return False


def get_cursor_session_token(tab, locale, max_attempts=3, retry_interval=2):
    """
    Cursor oturum token'ını alır
    """
    print(locale["cursor"]["process"]["getting_token"])
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
                    f"{locale['cursor']['process']['token_retry']} {attempts}: {locale['cursor']['process']['token_not_found']}, {retry_interval} {locale['cursor']['process']['seconds_retry']}"
                )
                time.sleep(retry_interval)
            else:
                print(
                    f"{locale['cursor']['process']['max_attempts']} ({max_attempts})"
                )

        except Exception as e:
            print(f"{locale['cursor']['process']['token_error']}: {str(e)}")
            attempts += 1
            if attempts < max_attempts:
                print(
                    f"{locale['cursor']['process']['retry_in']} {retry_interval} {locale['cursor']['process']['seconds']}"
                )
                time.sleep(retry_interval)

    return None


def update_cursor_auth(email=None, access_token=None, refresh_token=None):
    """
    Cursor kimlik doğrulama bilgilerini günceller
    """
    auth_manager = CursorAuthManager()
    return auth_manager.update_auth(email, access_token, refresh_token)


def sign_up_account(browser, tab, email_handler, locale):
    print(locale["cursor"]["starting"])

    # Yeni e-posta adresi oluştur
    email, email_token = email_handler.create_email()
    if not email:
        print(locale["cursor"]["process"]["email_creation_failed"])
        return False

    # Rastgele şifre oluştur
    password = "".join(
        random.choices(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
            k=12,
        )
    )

    # Rastgele isim seç
    first_name = random.choice(
        [
            "Emma",
            "Liam",
            "Olivia",
            "Noah",
            "Ava",
            "William",
            "Sophia",
            "James",
            "Isabella",
            "Oliver",
        ]
    )
    last_name = random.choice(
        [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
        ]
    )

    tab.get(SIGN_UP_URL)

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
        print(f"{locale['cursor']['process']['registration_page_error']}: {e}")
        return False

    handle_turnstile(tab, locale)

    try:
        if tab.ele("@name=password"):
            tab.ele("@name=password").input(password)
            time.sleep(random.uniform(1, 3))

            tab.ele("@type=submit").click()
            print(locale["cursor"]["process"]["processing"])

    except Exception as e:
        print(f"{locale['cursor']['process']['operation_failed']}: {e}")
        return False

    time.sleep(random.uniform(1, 3))
    if tab.ele("This email is not available."):
        print(locale["cursor"]["process"]["email_unavailable"])
        return False

    handle_turnstile(tab, locale)

    while True:
        try:
            if tab.ele("Account Settings"):
                break
            if tab.ele("@data-index=0"):
                code = email_handler.get_verification_code(email)
                if not code:
                    return False

                for i, digit in enumerate(code):
                    tab.ele(f"@data-index={i}").input(digit)
                    time.sleep(random.uniform(0.1, 0.3))
                break
        except Exception as e:
            print(
                f"{locale['cursor']['process']['verification_code_error']}: {e}"
            )

    handle_turnstile(tab, locale)

    wait_time = random.randint(3, 6)
    for i in range(wait_time):
        print(
            f"{locale['cursor']['process']['waiting']} {wait_time-i} {locale['cursor']['process']['seconds']}"
        )
        time.sleep(1)

    tab.get(SETTINGS_URL)

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
                f"{locale['cursor']['process']['usage_limit']}: {total_usage}"
            )
    except Exception as e:
        print(f"{locale['cursor']['process']['usage_limit_error']}: {e}")

    print(locale["cursor"]["registration_success"])
    account_info = f"\n{locale['cursor']['account_info']}: {email}  {locale['cursor']['password']}: {password}"
    logging.info(account_info)
    time.sleep(5)
    return True


class EmailGenerator:
    def __init__(
        self,
        domain="mailto.plus",
        password="".join(
            random.choices(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
                k=12,
            )
        ),
        first_name=random.choice(
            [
                "Emma",
                "Liam",
                "Olivia",
                "Noah",
                "Ava",
                "William",
                "Sophia",
                "James",
                "Isabella",
                "Oliver",
            ]
        ),
        last_name=random.choice(
            [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Garcia",
                "Miller",
                "Davis",
                "Rodriguez",
                "Martinez",
            ]
        ),
    ):
        self.domain = domain
        self.default_password = password
        self.default_first_name = first_name
        self.default_last_name = last_name

    def generate_email(self, length=8):
        """Rastgele email adresi oluşturur"""
        random_str = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz", k=length)
        )
        timestamp = str(int(time.time()))[-6:]
        return f"{random_str}{timestamp}@{self.domain}"

    def get_account_info(self):
        """Hesap bilgilerini döndürür"""
        return {
            "email": self.generate_email(),
            "password": self.default_password,
            "first_name": self.default_first_name,
            "last_name": self.default_last_name,
        }


def main():
    locale = LocaleManager().get_locale()
    browser_manager = None
    email = None
    try:
        browser_manager = BrowserManager()
        browser = browser_manager.init_browser()

        email_handler = EmailVerificationHandler()

        tab = browser.latest_tab
        tab.run_js("try { turnstile.reset() } catch(e) { }")

        tab.get(LOGIN_URL)

        if sign_up_account(browser, tab, email_handler, locale):
            token = get_cursor_session_token(tab, locale)
            if token:
                email = email_handler.email
                update_cursor_auth(
                    email=email, access_token=token, refresh_token=token
                )
            else:
                print(locale["cursor"]["registration_failed"])

        print(locale["cursor"]["completed"])

    except Exception as e:
        print(f"{locale['common']['error']}: {str(e)}")
        import traceback

        print(str(traceback.format_exc()))
    finally:
        if browser_manager:
            browser_manager.quit()
        input(f"\n{locale['common']['press_enter']}")


if __name__ == "__main__":
    main()
