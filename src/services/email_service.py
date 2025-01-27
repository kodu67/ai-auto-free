import requests
import time
import imaplib
from email import message_from_bytes
import random
from utils.locale import Locale
from config.user_settings import UserSettings
from datetime import datetime, timedelta


class EmailService:
    def __init__(self):
        self.mail_api_url = "https://tempmail.so/us/api"
        self.locale = Locale()
        self.email = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Content-Type": "application/json",
            "Sec-Ch-Ua-Platform": "Windows",
            "X-Inbox-Lifespan": "600",
            "Sec-Ch-Ua": "Chromium;v=131, Not_A Brand;v=24",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://tempmail.so/",
        }
        self.user_settings = UserSettings()
        self.session_cookie = None
        self.tm_session = None

    def create_email(self):
        """Yeni bir geçici e-posta adresi oluşturur"""
        from utils.logger import Logger

        logger = Logger()
        accounts = logger.get_accounts()

        def is_email_used(email):
            """Email'in daha önce kullanılıp kullanılmadığını kontrol eder"""
            return any(account["email"] == email for account in accounts)

        while True:
            email, token = self._generate_email()
            if not is_email_used(email):
                self.email = email
                return email, token

    def _process_cookie(self, set_cookie):
        """Set-Cookie header'ından tm_session cookie'sini ayıklar"""
        if not set_cookie:
            return None

        try:
            tm_sessions = set_cookie.split("tm_session=")
            if len(tm_sessions) > 2:
                cookie_value = tm_sessions[-1]
            elif len(tm_sessions) == 2:
                cookie_value = tm_sessions[1]
            else:
                cookie_value = tm_sessions[0].split(";")[0]

            return cookie_value.split(";")[0]
        except Exception:
            return None

    def _update_headers_with_cookie(self):
        """Headers'ı cookie ile günceller"""
        if self.tm_session and "Cookie" not in self.headers:
            self.headers = self.headers | {"Cookie": f"tm_session={self.tm_session}"}

    def _generate_email(self):
        """Yeni bir email adresi oluşturur"""
        # IMAP kullanılıyorsa IMAP ayarlarından e-posta oluştur
        if self.user_settings.get_email_verifier() == "imap":
            imap_settings = self.user_settings.get_imap_settings()
            email_parts = imap_settings["IMAP_USER"].split("@")

            # Gmail.com'u bazen googlemail.com'a çevir
            domain = email_parts[1]
            is_gmail = domain == "gmail.com"
            if is_gmail and random.random() < 0.5:
                domain = "googlemail.com"

            # Username'in harfleri arasına nokta ekle
            username = email_parts[0]
            if not is_gmail:
                username_chars = list(username)
                num_dots = random.randint(1, len(username) - 1)
                dot_positions = random.sample(range(1, len(username)), num_dots)

                for pos in sorted(dot_positions, reverse=True):
                    username_chars.insert(pos, ".")

                new_username = "".join(username_chars)
                return f"{new_username}@{domain}", None
            return f"{username}@{domain}", None

        # Diğer durumlarda tempmail.so API'sini kullan
        try:
            response = requests.get(f"{self.mail_api_url}/inbox", headers=self.headers)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 and result.get("message") == "Success":
                    data = result.get("data", {})
                    self.email = data.get("name")

                    # Set-Cookie header'ından tm_session değerini al
                    set_cookie = response.headers.get("Set-Cookie", "")
                    cookie_value = self._process_cookie(set_cookie)

                    if cookie_value:
                        self.tm_session = cookie_value
                        self._update_headers_with_cookie()

                    return self.email, None
            return None, None

        except Exception as e:
            raise e

    def get_verification_code(self, email, max_attempts=20, delay=2):
        """E-posta adresine gelen doğrulama kodunu alır"""
        yield self.locale.get_text("email.processing")

        try:
            if self.user_settings.get_email_verifier() == "imap":
                imap_generator = self._get_verification_code_imap(
                    email, max_attempts, delay
                )
                while True:
                    try:
                        yield next(imap_generator)
                    except StopIteration as e:
                        return e.value
            else:
                api_generator = self._get_verification_code_api(
                    email, max_attempts, delay
                )
                while True:
                    try:
                        yield next(api_generator)
                    except StopIteration as e:
                        return e.value

        except Exception as e:
            yield self.locale.get_text("email.execution_failed") + " - " + str(e)
            return None

    def _get_verification_code_api(self, email, max_attempts, delay):
        """API için doğrulama kodunu alır"""
        import re

        for _ in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.mail_api_url}/inbox", headers=self.headers
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0 and result.get("message") == "Success":
                        data = result.get("data", {})
                        inbox = data.get("inbox", [])

                        if inbox:
                            for message in inbox:
                                text_body = message.get("textBody", "")

                                # Regex ile 6 haneli kodu ara
                                code_match = re.search(r"\b(\d{6})\b", text_body)
                                if code_match:
                                    verification_code = code_match.group(1)
                                    yield f"{self.locale.get_text('cursor.verification_code')}: {verification_code}"
                                    return verification_code

                time.sleep(delay)

            except Exception as e:
                yield f"API error: {str(e)}"
                time.sleep(delay)

        yield self.locale.get_text("email.verification_failed")
        return None

    def _get_verification_code_imap(self, email, max_attempts, delay):
        """IMAP üzerinden doğrulama kodunu alır"""
        imap_settings = self.user_settings.get_imap_settings()

        for attempt in range(max_attempts):
            try:
                yield self.locale.get_text("email.imap_connecting").format(
                    imap_settings["IMAP_SERVER"]
                )
                imap = imaplib.IMAP4_SSL(
                    imap_settings["IMAP_SERVER"], int(imap_settings["IMAP_PORT"])
                )
                imap.login(imap_settings["IMAP_USER"], imap_settings["IMAP_PASS"])
                yield self.locale.get_text("email.imap_login_success")
                imap.select("INBOX")

                # Son 1 dakika içinde gelen okunmamış mesajları ara
                one_minute_ago = (datetime.now() - timedelta(minutes=1)).strftime(
                    "%d-%b-%Y"
                )

                _, messages = imap.search(
                    None,
                    "UNSEEN",
                    f'(FROM "no-reply@cursor.sh" SINCE "{one_minute_ago}")',
                )
                message_nums = messages[0].split()

                if not message_nums:
                    yield self.locale.get_text("email.imap_new_mail_waiting").format(
                        attempt + 1, max_attempts
                    )
                    imap.close()
                    imap.logout()
                    time.sleep(delay)
                    continue

                # En son gelen mesajı al (listeden son eleman)
                latest_email_id = message_nums[-1]
                _, msg_data = imap.fetch(latest_email_id, "(RFC822)")
                email_body = message_from_bytes(msg_data[0][1])

                body_text = ""
                if email_body.is_multipart():
                    for part in email_body.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            try:
                                content = part.get_payload(decode=True).decode()
                                body_text += content + "\n"
                            except Exception as e:
                                yield self.locale.get_text(
                                    "email.imap_content_read_error"
                                ).format(str(e))
                                continue
                else:
                    body_text = email_body.get_payload(decode=True).decode()

                import re

                codes = re.findall(r"\b\d{6}\b", body_text)

                if codes:
                    code = codes[0]
                    yield f"{self.locale.get_text('cursor.verification_code')}: {code}"

                    # Mesajı sil
                    imap.store(latest_email_id, "+FLAGS", "\\Deleted")
                    imap.expunge()

                    imap.close()
                    imap.logout()
                    return code

                imap.close()
                imap.logout()
                time.sleep(delay)

            except Exception as e:
                yield self.locale.get_text("email.imap_error").format(str(e))
                return None

        yield self.locale.get_text("email.verification_failed")
        return None
