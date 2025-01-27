import os
import requests


class UsageChecker:
    def __init__(self):
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".cursor_cache")
        self.cache_file = os.path.join(self.cache_dir, "session_token.txt")
        self.api_url = "https://www.cursor.com/api/usage"

    def _cursor_get_user_id(self, raw_token):
        """Token'dan user ID'yi ayıklar"""
        try:
            return raw_token.split("%3A%3A")[0]
        except Exception:
            return None

    def cursor_get_usage(self, raw_token):
        """Cursor kullanım istatistiklerini getirir"""
        if not raw_token:
            return "-"

        user_id = self._cursor_get_user_id(raw_token)
        if not user_id:
            return "-"

        headers = {
            "Cookie": f"WorkosCursorSessionToken={raw_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Accept": "*/*",
            "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.cursor.com/settings",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Te": "trailers",
        }

        try:
            response = requests.get(f"{self.api_url}?user={user_id}", headers=headers)

            if response.status_code == 200:
                data = response.json()
                usage_info = {}

                for model, stats in data.items():
                    if (
                        stats.get("numRequests", 0) > 0
                    ):  # Sadece kullanılmış modelleri göster
                        renamed_model = model.replace("gpt-4", "Premium").replace(
                            "gpt-3.5-turbo", "Free"
                        )
                        usage_info[renamed_model] = (
                            f"{stats['numRequests']}/{stats['maxRequestUsage']}"
                        )

                usage_str = "\n".join(
                    [f"{model}: {usage}" for model, usage in usage_info.items()]
                )
                return usage_str if usage_str else "+"
            else:
                return "+"

        except Exception:
            return "-"
