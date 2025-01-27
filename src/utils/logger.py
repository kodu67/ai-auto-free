from datetime import datetime
from config.user_settings import UserSettings
import os
import json

class Logger:
    def __init__(self):
        self.user_settings = UserSettings()
        self.accounts_file = os.path.join(self.user_settings.settings_dir, "accounts.json")

    def get_accounts(self):
        try:
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return []

    def get_accounts_as_list(self):
        accounts = self.get_accounts()
        return [
            [account["service"], account["email"], account["password"], account["token"], "", account["date"]]
            for account in reversed(accounts)
        ]

    def log_account(self, service_type, account_data):
        try:
            accounts = self.get_accounts()
            date = datetime.now().strftime("%Y-%m-%d %H:%M")

            accounts.append({
                "service": service_type,
                "email": account_data["email"],
                "date": date,
                "password": account_data["password"],
                "token": account_data["token"]
            })

            with open(self.accounts_file, "w", encoding="utf-8") as f:
                json.dump(accounts, f, indent=4)

        except Exception as e:
            yield f"Error while logging account: {str(e)}"
