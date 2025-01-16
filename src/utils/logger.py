from datetime import datetime


class Logger:
    def __init__(self):
        self.log_file = "ai-auto-free-accounts.txt"

    def log_account(self, service_type, account_data):
        """Log account information

        Args:
            service_type (str): Service type ("cursor" or "windsurf")
            account_data (dict): Account information
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Format the log message
            if service_type == "cursor":
                log_message = f"[{current_time}] CURSOR ACCOUNT\n"
                log_message += f"Email: {account_data['email']}\n"
                log_message += f"Password: {account_data['password']}\n"
            else:
                log_message = f"[{current_time}] WINDSURF ACCOUNT\n"
                log_message += f"Email: {account_data['email']}\n"
                log_message += f"Password: {account_data['password']}\n"
                log_message += f"Token: {account_data['token']}\n"

            log_message += "-" * 50 + "\n"

            # Append to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message)

        except Exception as e:
            print(f"Error while logging account: {str(e)}")
