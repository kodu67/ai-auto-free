from DrissionPage.common import Keys
import time
import re
from locale_manager import LocaleManager


class EmailVerificationHandler:
    def __init__(self, browser, mail_url="https://tempmail.plus"):
        self.browser = browser
        self.mail_url = mail_url
        self.locale = LocaleManager().get_locale()

    def get_verification_code(self, email):
        username = email.split("@")[0]
        code = None

        try:
            print(self.locale["email"]["processing"])
            tab_mail = self.browser.new_tab(self.mail_url)
            self.browser.activate_tab(tab_mail)

            self._input_username(tab_mail, username)

            code = self._get_latest_mail_code(tab_mail)

            self._cleanup_mail(tab_mail)

            tab_mail.close()

        except Exception as e:
            print(f"{self.locale['email']['verification_failed']}: {str(e)}")

        return code

    def _input_username(self, tab, username):
        while True:
            if tab.ele("@id=pre_button"):
                tab.actions.click("@id=pre_button")
                time.sleep(0.5)
                tab.run_js('document.getElementById("pre_button").value = ""')
                time.sleep(0.5)
                tab.actions.input(username).key_down(Keys.ENTER).key_up(Keys.ENTER)
                break
            time.sleep(1)

    def _get_latest_mail_code(self, tab):
        code = None
        while True:
            new_mail = tab.ele("@class=mail")
            if new_mail:
                if new_mail.text:
                    tab.actions.click("@class=mail")
                    break
                else:
                    break
            time.sleep(1)

        if tab.ele("@class=overflow-auto mb-20"):
            email_content = tab.ele("@class=overflow-auto mb-20").text
            verification_code = re.search(
                r"verification code is (\d{6})", email_content
            )
            if verification_code:
                code = verification_code.group(1)
                print(self.locale["email"]["almost_success"])
            else:
                print(self.locale["email"]["execution_failed"])

        return code

    def _cleanup_mail(self, tab):
        if tab.ele("@id=delete_mail"):
            tab.actions.click("@id=delete_mail")
            time.sleep(1)

        if tab.ele("@id=confirm_mail"):
            tab.actions.click("@id=confirm_mail")
