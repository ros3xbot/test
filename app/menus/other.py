import requests
from app.client.engsel import get_family_v2, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.util_helper import print_panel, live_loading
from app.client.ewallet import show_multipayment_v2
from app.client.qris import show_qris_payment_v2
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem
from app.config.theme_config import get_theme

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

console = Console()

def show_main_other():
    theme = get_theme()
    while True:
        clear_screen()

        console.print(Panel(
            Align.center("✨ Menu Paket Lainnya ✨", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        menu_table.add_column("No", justify="right", style=theme["text_key"], width=4)
        menu_table.add_column("Daftar Paket", style=theme["text_body"])
        menu_table.add_row("1", "🔥 Paket v1 (Family-Based)")
        menu_table.add_row("2", "💳 Paket v2 (Multi-Payment)")
        menu_table.add_row("00", f"[{theme['text_sub']}]⬅️ Kembali ke menu utama[/]")

        console.print(Panel(
            menu_table,
            border_style=theme["border_primary"],
            padding=(0, 0),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]Pilih menu:[/{theme['text_sub']}] ").strip().lower()
        if choice == "1":
            show_hot_menu()
        elif choice == "2":
            show_hot_menu2()
        elif choice == "00":
            #live_loading(text="Kembali ke menu utama...", theme=theme)
            return
        else:
            print_panel("⚠️ Error", "Input tidak valid. Silahkan coba lagi.")
            pause()



def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("Paket v1", vertical="middle"),
            style=theme["text_title"],
            border_style=theme["border_warning"],
            padding=(1, 2),
            expand=True,
        ))

        try:
            response = requests.get("https://raw.githubusercontent.com/dratx1/engsel/refs/heads/main/family/anu.json", timeout=30)
            response.raise_for_status()
            hot_packages = response.json()
        except Exception:
            print_panel("⚠️ Error", "Gagal mengambil data hot package.")
            pause()
            return

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_number"], width=6)
        table.add_column("Family", style=theme["text_body"])
        table.add_column("Variant", style=theme["text_body"])
        table.add_column("Option", style=theme["text_body"])

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(str(idx), p["family_name"], p["variant_name"], p["option_name"])

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))
        console.print(Panel("00. Kembali ke menu utama", border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih nomor paket:[/{theme['text_sub']}] ").strip().lower()
        if choice == "00":
            return

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected = hot_packages[int(choice) - 1]
            family_code = selected["family_code"]
            is_enterprise = selected["is_enterprise"]

            family_data = get_family_v2(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print_panel("⚠️ Error", "Gagal mengambil data family.")
                pause()
                continue

            option_code = None
            for variant in family_data["package_variants"]:
                if variant["name"] == selected["variant_name"]:
                    for option in variant["package_options"]:
                        if option["order"] == selected["order"]:
                            option_code = option["package_option_code"]
                            break

            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                print_panel("⚠️ Error", "Paket tidak ditemukan.")
                pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid.")
            pause()

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("Paket v2", vertical="middle"),
            style=theme["text_title"],
            border_style=theme["border_warning"],
            padding=(1, 2),
            expand=True,
        ))

        try:
            response = requests.get("https://raw.githubusercontent.com/dratx1/engsel/refs/heads/main/family/anu2.json", timeout=30)
            response.raise_for_status()
            hot_packages = response.json()
        except Exception:
            print_panel("⚠️ Error", "Gagal mengambil data hot package.")
            pause()
            return

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_number"], width=6)
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", style=theme["text_money"])

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(str(idx), p["name"], f"Rp {p['price']}")

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))
        console.print(Panel("00. Kembali ke menu utama", border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih nomor paket:[/{theme['text_sub']}] ").strip().lower()
        if choice == "00":
            return

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected = hot_packages[int(choice) - 1]
            packages = selected.get("packages", [])
            if not packages:
                print_panel("⚠️ Error", "Paket tidak tersedia.")
                pause()
                continue

            payment_items = []
            for pkg in packages:
                detail = get_package_details(
                    api_key,
                    tokens,
                    pkg["family_code"],
                    pkg["variant_code"],
                    pkg["order"],
                    pkg["is_enterprise"],
                )
                if not detail:
                    print_panel("⚠️ Error", f"Gagal mengambil detail untuk {pkg['family_code']}.")
                    pause()
                    return

                payment_items.append(PaymentItem(
                    item_code=detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=detail["package_option"]["price"],
                    item_name=detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=detail["token_confirmation"],
                ))

            clear_screen()
            console.print(Panel(
                f"[bold]{selected['name']}[/]\n\nHarga: Rp {selected['price']}\n\nDetail: {selected['detail']}",
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True,
            ))

            while True:
                console.print(Panel("Pilih Metode Pembelian:\n1. E-Wallet\n2. QRIS\n3. Saldo\n00. Kembali", border_style=theme["border_primary"], padding=(0, 1), expand=True))
                method = console.input(f"[{theme['text_sub']}]Metode (nomor):[/{theme['text_sub']}] ").strip().lower()

                if method == "1":
                    show_multipayment_v2(api_key, tokens, payment_items, "BUY_PACKAGE", True)
                    input("Tekan enter untuk kembali...")
                    return
                elif method == "2":
                    show_qris_payment_v2(api_key, tokens, payment_items, "BUY_PACKAGE", True)
                    input("Tekan enter untuk kembali...")
                    return
                elif method == "3":
                    settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", True)
                    input("Tekan enter untuk kembali...")
                    return
                elif method == "00":
                    break
                else:
                    print_panel("⚠️ Error", "Metode tidak valid.")
                    pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid.")
            pause()

