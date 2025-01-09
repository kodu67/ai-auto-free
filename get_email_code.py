import requests
import time
from locale_manager import LocaleManager

class EmailVerificationHandler:
    def __init__(self, mail_api_url="https://api.internal.temp-mail.io/api/v3"):
        self.mail_api_url = mail_api_url
        self.locale = LocaleManager().get_locale()
        self.email = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Content-Type': 'application/json;charset=utf-8',
            'Application-Name': 'web',
            'Application-Version': '2.4.2',
            'Origin': 'https://temp-mail.io',
            'Referer': 'https://temp-mail.io/'
        }

    def create_email(self):
        """Yeni bir geçici e-posta adresi oluşturur"""
        try:
            data = {
                "min_name_length": 10,
                "max_name_length": 10
            }

            response = requests.post(
                f"{self.mail_api_url}/email/new",
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                self.email = result.get("email")
                return self.email, result.get("token")
            return None, None

        except Exception:
            return None, None

    def get_verification_code(self, email, max_attempts=30, delay=2):
        """E-posta adresine gelen doğrulama kodunu alır"""
        print(self.locale["email"]["processing"])

        try:
            for attempt in range(max_attempts):
                response = requests.get(
                    f"{self.mail_api_url}/email/{email}/messages",
                    headers=self.headers
                )

                if response.status_code == 200:
                    messages = response.json()
                    if messages:
                        message = messages[0]
                        body_text = message.get("body_text", "")

                        # Satır satır kontrol
                        for line in body_text.split('\n'):
                            line = line.strip()
                            # Sadece rakamlardan oluşan 6 haneli kodları ara
                            if line.isdigit() and len(line) == 6:
                                print(f"{self.locale['cursor']['verification_code']}: {line}")
                                return line

                time.sleep(delay)

            print(self.locale["email"]["verification_failed"])
            return None

        except Exception:
            print(self.locale["email"]["execution_failed"])
            return None
