from utils.locale import Locale
from utils.helper import Helper
from utils.usage import UsageChecker
from config.settings import Settings
from config import constants
from config.user_settings import UserSettings
from elevate import elevate
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from questionary import Choice, Style, select

class AutoFreeApp:
    def __init__(self):
        self.helper = Helper()
        self.usage_checker = UsageChecker()
        self.cursor_usage = self.usage_checker.cursor_get_usage()
        self.locale = Locale()
        self.settings = Settings()
        self.user_settings = UserSettings()
        self.running = True
        self.console = Console()
        self.custom_style = Style([
            ('qmark', 'fg:#FF1493 bold'),       # Parlak pembe
            ('question', 'bold'),
            ('answer', 'fg:#00FF00 bold'),      # Parlak yeşil
            ('pointer', 'fg:#FF00FF bold'),     # Parlak magenta
            ('highlighted', 'fg:#FF69B4 bold'), # Parlak pembe
            ('selected', 'fg:#00FFFF bold'),    # Parlak cyan
        ])

        # Özellik durumları
        self.cursor_enabled = True
        self.cursor_maintenance = False
        self.cursor_maintenance_message = ""
        self.windsurf_enabled = True
        self.windsurf_maintenance = False
        self.windsurf_maintenance_message = ""

    def check_admin_rights(self):
        """Yönetici yetkilerini kontrol eder ve gerekirse ister"""
        if not self.helper.is_admin():
            self.helper.show_main()
            print("\n" + self.locale.get_text("admin.need_admin"))
            elevate(graphical=True)

            if not self.helper.is_admin():
                input("\n" + self.locale.get_text("common.press_enter"))
                return False
        return True

    def show_main_menu(self):
        """Ana menüyü gösterir"""
        self.helper.show_main()

        # Cursor kullanım istatistiklerini göster
        if self.cursor_usage:
            table = Table(title="Cursor", show_header=True, header_style="bold magenta")
            table.add_column("Model", style="cyan")
            table.add_column("Request", justify="right", style="green")

            for model, requests in self.cursor_usage.items():
                table.add_row(model, str(requests))

            self.console.print(table)
            print("")

        # Giriş mesajını göster
        try:
            self.helper.show_landing_message()
            self.console.print(Panel.fit(
                self.helper.show_repo(),
                title="GitHub",
                border_style="blue",
            ))
            self.helper.show_bitcoin()

        except Exception as e:
            self.console.print(f"[red]Hata: {str(e)}[/red]")

        choices = [
            Choice(title=self.locale.get_text("menu.cursor"), value="1"),
            Choice(title=self.locale.get_text("menu.windsurf"), value="2"),
            Choice(title=self.locale.get_text("menu.machine_id_reset"), value="3"),
            Choice(title=self.locale.get_text("menu.settings"), value="4"),
            Choice(title=self.locale.get_text("menu.exit"), value="5")
        ]

        return select(
            self.locale.get_text("menu.select_option"),
            choices=choices,
            style=self.custom_style
        ).ask()

    def run_cursor_creator(self):
        """Cursor hesap oluşturucuyu çalıştırır"""
        if not self.cursor_enabled:
            self.console.print(
                Panel.fit(
                    self.locale.get_text("features.disabled").format(
                        self.locale.get_text("menu.cursor")
                    ),
                    title="⚠️ Disabled",
                    border_style="red"
                )
            )

            if self.cursor_maintenance:
                self.console.print(f"\n[yellow]{self.cursor_maintenance_message}[/yellow]")

            self.helper.press_enter()
            return

        try:
            from auth.machine_id import CursorMachineIDResetter

            resetter = CursorMachineIDResetter()
            resetter.reset_machine_id()

            from auth.cursor_auth import CursorAuthManager

            self.helper.show_main()
            self.run_machine_id_reset(show_continue=False)
            print("\n")
            CursorAuthManager()

        except Exception as e:
            self.console.print(
                Panel.fit(
                    f"{self.locale.get_text('cursor.registration_failed')}\n{str(e)}",
                    title="❌ Error",
                    border_style="red"
                )
            )
            self.helper.press_enter()

    def run_machine_id_reset(self, show_continue=True):
        """Machine ID sıfırlama işlemini çalıştırır"""
        self.helper.clear_screen()
        self.console.print("\n[bold blue]" + self.locale.get_text("machine_id_reset.starting") + "[/bold blue]")

        try:
            from auth.machine_id import CursorMachineIDResetter

            cursor_machine_id = CursorMachineIDResetter()
            success, message = cursor_machine_id.reset_machine_id()

            if success:
                self.console.print(Panel.fit(
                    f"{self.locale.get_text('machine_id_reset.success')}\n\n{self.locale.get_text('machine_id_reset.changes')}\n{message}",
                    title="✅ Success",
                    border_style="green"
                ))
            else:
                self.console.print(Panel.fit(
                    f"{self.locale.get_text('machine_id_reset.failed')}\n{message}",
                    title="❌ Error",
                    border_style="red"
                ))

        except Exception as e:
            self.console.print(Panel.fit(
                f"{self.locale.get_text('machine_id_reset.failed')}\n{str(e)}",
                title="❌ Error",
                border_style="red"
            ))

        if show_continue:
            self.helper.press_enter()

    def run_windsurf_creator(self):
        """Windsurf hesap oluşturucuyu çalıştırır"""
        if not self.windsurf_enabled:
            self.console.print(
                Panel.fit(
                    self.locale.get_text("features.disabled").format(
                        self.locale.get_text("menu.windsurf")
                    ),
                    title="⚠️ Disabled",
                    border_style="red"
                )
            )
            self.helper.press_enter()
            return

        if self.windsurf_maintenance:
            self.console.print(Panel.fit(
                self.windsurf_maintenance_message,
                title="🔧 In Maintenance",
                border_style="yellow"
            ))
            self.helper.press_enter()
            return

        self.helper.clear_screen()
        self.console.print("\n[bold blue]" + self.locale.get_text("windsurf.starting") + "[/bold blue]")

        from auth.windsurf_auth import WindsurfAuthManager
        WindsurfAuthManager()

    def check_settings(self):
        """Uzak ayarları kontrol eder"""
        try:
            settings = self.settings.get_settings_json()
            current_version = self.settings.get_version()
            # Versiyon kontrolü
            latest_version = settings.get("latest_version")
            if latest_version and int(latest_version) > int(current_version):
                print("\n" + self.locale.get_text("updates.available"))
                print(self.locale.get_text("updates.message").format(latest_version))
                print(
                    self.locale.get_text("updates.download").format(
                        constants.RELEASE_URL
                    )
                )
                changelog = (
                    settings.get("changelog", {})
                    .get(latest_version, {})
                    .get(self.locale.current_locale, "")
                )
                if changelog:
                    print(":: " + changelog)

                self.helper.press_enter()

            # Özellik kontrolü
            features = settings.get("features", {})

            # Cursor kontrolü
            cursor_settings = features.get("cursor", {})
            if not cursor_settings.get("enabled", True):
                self.cursor_enabled = False
            if cursor_settings.get("maintenance", False):
                self.cursor_maintenance = True
                self.cursor_maintenance_message = cursor_settings[
                    "maintenance_message"
                ][self.locale.current_locale]

            # Windsurf kontrolü
            windsurf_settings = features.get("windsurf", {})
            if not windsurf_settings.get("enabled", True):
                self.windsurf_enabled = False
            if windsurf_settings.get("maintenance", False):
                self.windsurf_maintenance = True
                self.windsurf_maintenance_message = windsurf_settings[
                    "maintenance_message"
                ][self.locale.current_locale]

        except Exception as e:
            print(e)

    def show_settings_menu(self):
        """Ayarlar menüsünü gösterir"""
        while True:
            self.helper.show_main()
            self.console.print("\n[bold cyan]" + self.locale.get_text("settings.title") + "[/bold cyan]")

            current_visibility = self.user_settings.is_browser_visible()
            current_email_verifier = self.user_settings.get_email_verifier()

            choices = [
                Choice(
                    title=f"{self.locale.get_text('settings.browser_visibility')} [{self.locale.get_text('settings.yes') if current_visibility else self.locale.get_text('settings.no')}]",
                    value="1"
                ),
                Choice(
                    title=f"{self.locale.get_text('settings.email_verifier')} [{current_email_verifier}]",
                    value="2"
                )
            ]

            # IMAP seçili ise IMAP ayarları seçeneğini ekle
            if current_email_verifier == "imap":
                choices.append(Choice(
                    title=self.locale.get_text("settings.imap_settings"),
                    value="4"
                ))

            choices.append(Choice(title=self.locale.get_text("menu.back"), value="3"))

            choice = select(
                self.locale.get_text("settings.select_option"),
                choices=choices,
                style=self.custom_style
            ).ask()

            if choice == "1":
                options = [
                    Choice(title=self.locale.get_text("settings.yes"), value="yes"),
                    Choice(title=self.locale.get_text("settings.no"), value="no")
                ]

                option = select(
                    self.locale.get_text("settings.select_option"),
                    choices=options,
                    style=self.custom_style
                ).ask()

                if option == "yes":
                    if not current_visibility:
                        self.user_settings.toggle_browser_visibility()
                    self.console.print("\n[green]" + self.locale.get_text("settings.saved") + "[/green]")
                    self.helper.press_enter()
                elif option == "no":
                    if current_visibility:
                        self.user_settings.toggle_browser_visibility()
                    self.console.print("\n[green]" + self.locale.get_text("settings.saved") + "[/green]")
                    self.helper.press_enter()

            elif choice == "2":
                verifier_options = [
                    Choice(title="Temporary", value="temp"),
                    Choice(title="IMAP", value="imap")
                ]

                verifier = select(
                    self.locale.get_text("settings.select_email_verifier"),
                    choices=verifier_options,
                    style=self.custom_style
                ).ask()

                self.user_settings.set_email_verifier(verifier)
                self.console.print("\n[green]" + self.locale.get_text("settings.saved") + "[/green]")
                self.helper.press_enter()

            elif choice == "3":
                break
            elif choice == "4":
                self.user_settings.set_imap_email_settings()

    def run(self):
        """Uygulamayı çalıştırır"""
        while self.running:
            choice = self.show_main_menu()

            if choice == "1":
                self.run_cursor_creator()
            elif choice == "2":
                self.run_windsurf_creator()
            elif choice == "3":
                self.run_machine_id_reset()
            elif choice == "4":
                self.show_settings_menu()
            elif choice == "5":
                self.running = False
