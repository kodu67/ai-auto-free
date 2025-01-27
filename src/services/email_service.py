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
        self.mail_api_url = "https://api.internal.temp-mail.io/api/v3"
        self.locale = Locale()
        self.email = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Accept": "application/json",
            "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/json;charset=utf-8",
            "Application-Name": "web",
            "Application-Version": "2.4.2",
            "Origin": "https://temp-mail.io",
            "Referer": "https://temp-mail.io/",
        }
        self.user_settings = UserSettings()

    def create_email(self):
        """Yeni bir geçici e-posta adresi oluşturur"""
        from utils.logger import Logger

        logger = Logger()

        def is_email_used(email):
            """Email'in daha önce kullanılıp kullanılmadığını kontrol eder"""
            accounts = logger.get_accounts()
            return any(account["email"] == email for account in accounts)

        while True:
            email, token = self._generate_email()
            if not is_email_used(email):
                self.email = email
                return email, token

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

        # Diğer durumlarda temp-mail API'sini kullan
        try:
            data = {"min_name_length": 10, "max_name_length": 10}

            response = requests.post(
                f"{self.mail_api_url}/email/new", headers=self.headers, json=data
            )

            if response.status_code == 200:
                result = response.json()
                self.email = result.get("email")
                return self.email, result.get("token")
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
        """API üzerinden doğrulama kodunu alır"""
        for _ in range(max_attempts):
            response = requests.get(
                f"{self.mail_api_url}/email/{email}/messages", headers=self.headers
            )

            if response.status_code == 200:
                messages = response.json()
                if messages:
                    message = messages[0]
                    body_text = message.get("body_text", "")

                    # Satır satır kontrol
                    for line in body_text.split("\n"):
                        line = line.strip()
                        # Sadece rakamlardan oluşan 6 haneli kodları ara
                        if line.isdigit() and len(line) == 6:
                            yield f"{self.locale.get_text('cursor.verification_code')}: {line}"
                            return line

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
                search_criteria = (
                    f'(UNSEEN FROM "no-reply@cursor.sh" SINCE "{one_minute_ago}")'
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
