import sqlite3
import os
from locale_manager import LocaleManager


class CursorAuthManager:
    """Cursor kimlik doğrulama yöneticisi"""

    def __init__(self):
        self.locale_manager = LocaleManager()
        # İşletim sistemini kontrol et
        if os.name == "nt":  # Windows
            self.db_path = os.path.join(
                os.getenv("APPDATA"), "Cursor", "User", "globalStorage", "state.vscdb"
            )
        else:  # macOS
            self.db_path = os.path.expanduser(
                "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
            )

    def update_auth(self, email=None, access_token=None, refresh_token=None):
        """
        Cursor kimlik doğrulama bilgilerini günceller
        :param email: Yeni e-posta adresi
        :param access_token: Yeni erişim anahtarı
        :param refresh_token: Yeni yenileme anahtarı
        :return: bool Güncellemenin başarılı olup olmadığı
        """
        updates = []
        # Giriş durumu
        updates.append(("cursorAuth/cachedSignUpType", "Auth_0"))

        if email is not None:
            updates.append(("cursorAuth/cachedEmail", email))
        if access_token is not None:
            updates.append(("cursorAuth/accessToken", access_token))
        if refresh_token is not None:
            updates.append(("cursorAuth/refreshToken", refresh_token))

        if not updates:
            print(self.locale_manager.get_text("cursor.auth.no_update_values"))
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for key, value in updates:
                # Eğer hiç satır güncellenmezse, anahtar mevcut değil demektir, ekleme yap
                # accessToken'ın var olup olmadığını kontrol et
                check_query = f"SELECT COUNT(*) FROM itemTable WHERE key = ?"
                cursor.execute(check_query, (key,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO itemTable (key, value) VALUES (?, ?)"
                    cursor.execute(insert_query, (key, value))
                else:
                    update_query = "UPDATE itemTable SET value = ? WHERE key = ?"
                    cursor.execute(update_query, (value, key))

                if cursor.rowcount > 0:
                    print(self.locale_manager.get_text("cursor.auth.update_success").format(key.split('/')[-1]))
                else:
                    print(self.locale_manager.get_text("cursor.auth.update_failed").format(key.split('/')[-1]))

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"{self.locale_manager.get_text('cursor.auth.db_error')}: {str(e)}")
            return False
        except Exception as e:
            print(f"{self.locale_manager.get_text('cursor.auth.error')}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
