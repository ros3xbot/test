from dotenv import load_dotenv
load_dotenv()

import sys
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.menus.util import pause
from app.menus.util_helper import clear_screen
from app.client.engsel import get_balance, get_profile, get_package
from app.client.engsel2 import get_tiering_info
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.config.theme_config import get_theme

console = Console()
theme = get_theme()
WIDTH = 55

def show_main_menu_rich(profile):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    pulsa_str = f"{profile['balance']:,}"

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_row(" Nomor", f": 📞 [bold]{profile['number']}[/]")
    info_table.add_row(" Type", f": 🧾 {profile['subscription_type']} ({profile['subscriber_id']})")
    info_table.add_row(" Pulsa", f": 💰 Rp [bold {theme['text_money']}]{pulsa_str}[/]")
    info_table.add_row(" Aktif", f": ⏳ [{theme['text_date']}]{expired_at_dt}[/]")
    info_table.add_row(" Tiering", f": 🏅 [{theme['text_date']}]{profile['point_info']}[/]")

    console.print(Panel(info_table, title=f"[{theme['text_title']}]✨ Informasi Akun ✨[/]", border_style=theme["border_info"], padding=(1, 2), expand=True))

    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style=theme["text_key"], width=6)
    menu_table.add_column("Menu", style=theme["text_body"])
    menu_table.add_row("1", "🔐 Login/Ganti akun")
    menu_table.add_row("2", "📑 Lihat Paket Saya")
    menu_table.add_row("3", "🔥 Beli Paket Hot Promo")
    menu_table.add_row("4", "🔥 Beli Paket Hot Promo-2")
    menu_table.add_row("5", "🔍 Beli Paket Berdasarkan Option Code")
    menu_table.add_row("6", "📦 Beli Paket Berdasarkan Family Code")
    menu_table.add_row("7", "🔁 Beli Semua Paket di Family Code (loop)")
    menu_table.add_row("8", "📜 Riwayat Transaksi")
    menu_table.add_row("9", "👨‍👩‍👧‍👦 Family Plan / Akrab Organizer")
    menu_table.add_row("10", "🧬 Circle [WIP]")
    menu_table.add_row("00", "⭐ Bookmark Paket")
    menu_table.add_row("99", f"[{theme['text_err']}]⛔ Tutup aplikasi [/]")

    console.print(Panel(menu_table, title=f"[{theme['text_title']}]✨ Menu Utama ✨[/]", border_style=theme["border_primary"], padding=(0, 1), expand=True))

def main():
    while True:
        active_user = AuthInstance.get_active_user()

        if active_user:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            profile_data = get_profile(AuthInstance.api_key, active_user["tokens"]["access_token"], active_user["tokens"]["id_token"])

            tiering_data = {}
            if profile_data["profile"]["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])

            profile = {
                "number": active_user["number"],
                "subscriber_id": profile_data["profile"]["subscriber_id"],
                "subscription_type": profile_data["profile"]["subscription_type"],
                "balance": balance.get("remaining", 0),
                "balance_expired_at": balance.get("expired_at", 0),
                "point_info": f"Points: {tiering_data.get('current_point', 'N/A')} | Tier: {tiering_data.get('tier', 'N/A')}"
            }

            show_main_menu_rich(profile)
            choice = input("Pilih menu: ").strip()

            if choice == "1":
                selected = show_account_menu()
                if selected: AuthInstance.set_active_user(selected)
            elif choice == "2":
                fetch_my_packages()
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = input("Masukkan option code (99 untuk batal): ")
                if option_code != "99":
                    show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)
            elif choice == "6":
                family_code = input("Masukkan family code (99 untuk batal): ")
                if family_code != "99":
                    get_packages_by_family(family_code)
            elif choice == "7":
                family_code = input("Masukkan family code (99 untuk batal): ")
                if family_code == "99": continue
                start = input("Mulai dari option ke (default 1): ")
                try: start = int(start)
                except: start = 1
                use_decoy = input("Gunakan decoy? (y/n): ").lower() == "y"
                pause_each = input("Pause tiap sukses? (y/n): ").lower() == "y"
                delay = input("Delay antar pembelian (detik): ")
                try: delay = int(delay)
                except: delay = 0
                purchase_by_family(family_code, use_decoy, pause_each, delay, start)
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                console.print(f"[{theme['text_err']}]Keluar dari aplikasi...[/]")
                sys.exit(0)
            elif choice == "t":
                res = get_package(AuthInstance.api_key, active_user["tokens"], "")
                print(json.dumps(res, indent=2))
                input("Tekan Enter untuk lanjut...")
            elif choice == "s":
                enter_sentry_mode()
            else:
                console.print(f"[{theme['text_err']}]Pilihan tidak valid. Coba lagi.[/]")
                pause()
        else:
            selected = show_account_menu()
            if selected:
                AuthInstance.set_active_user(selected)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(f"\n[{theme['text_err']}]Keluar dari aplikasi.[/]")
