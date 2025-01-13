import os
import json
import requests

class CursorUsageChecker:
    def __init__(self):
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".cursor_cache")
        self.cache_file = os.path.join(self.cache_dir, "session_token.txt")
        self.api_url = "https://www.cursor.com/api/usage"

    def _get_cached_token(self):
        """Cache'den token'ı okur"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"Cache okuma hatası: {e}")
            return None

    def _get_user_id(self, raw_token):
        """Token'dan user ID'yi ayıklar"""
        try:
            return raw_token.split("%3A%3A")[0]
        except Exception:
            return None

    def get_usage(self):
        """Cursor kullanım istatistiklerini getirir"""
        raw_token = self._get_cached_token()
        if not raw_token:
            return None

        user_id = self._get_user_id(raw_token)
        if not user_id:
            return None

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
            "Te": "trailers"
        }

        try:
            response = requests.get(
                f"{self.api_url}?user={user_id}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                usage_info = {}

                for model, stats in data.items():
                    if stats.get("numRequests", 0) > 0:  # Sadece kullanılmış modelleri göster
                        usage_info[model] = stats["numRequests"]

                return usage_info
            else:
                print(f"API isteği başarısız: {response.status_code}")
                return None

        except Exception as e:
            print(f"Kullanım bilgisi alınamadı: {e}")
            return None
