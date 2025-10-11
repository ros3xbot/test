from app.service.auth import AuthInstance
from app.client.balance import settlement_balance
from app.client.qris import show_qris_payment
from app.client.ewallet import show_multipayment
from app.menus.util import clear_screen, pause
from app.menus.util_helper import print_panel, get_rupiah
from app.config.theme_config import get_theme
from app.menus.package import get_packages_by_family
from app.menus.family_grup import show_family_menu
from app.menus.bookmark import show_bookmark_menu
from app.type_dict import PaymentItem
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

console = Console()


def show_bundle_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    cart_items = []
    display_cart = []
    total_price = 0

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("🛒 Keranjang Paket Bundle", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))


        if cart_items:
            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("No", justify="right", style=theme["text_key"], width=4)
            table.add_column("Nama Paket", style=theme["text_body"])
            table.add_column("Harga", style=theme["text_money"], justify="right")

            for i, item in enumerate(display_cart, start=1):
                table.add_row(str(i), item["name"], get_rupiah(item["price"]))

            console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))
            console.print(f"[{theme['text_body']}]Total Harga: Rp {get_rupiah(total_price)}[/]")
        else:
            print_panel("ℹ️ Info", "Keranjang masih kosong.")

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("1", "Tambah dari Bookmark")
        nav.add_row("2", "Tambah dari Family Code Tersimpan")
        nav.add_row("3", "Tambah dari Family Code Manual")
        nav.add_row("4", f"[{theme['text_err']}]Hapus Item dari Keranjang[/]")
        if cart_items:
            nav.add_row("5", "💳 Lanjutkan ke Pembayaran")
        nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()

        def add_to_cart(detail, name):
            nonlocal total_price
            option = detail["package_option"]
            cart_items.append(PaymentItem(
                item_code=option["package_option_code"],
                product_type="", item_price=option["price"],
                item_name=option["name"], tax=0,
                token_confirmation=detail["token_confirmation"]
            ))
            display_cart.append({"name": name, "price": option["price"]})
            total_price += option["price"]
            print_panel("✅ Ditambahkan", f"Paket '{name}' berhasil masuk keranjang.")
            pause()

        if choice == "1":
            result = show_bookmark_menu(return_package_detail=True)
            if isinstance(result, tuple):
                detail, name = result
                if detail:
                    add_to_cart(detail, name)

        elif choice == "2":
            result = show_family_menu(return_package_detail=True)
            if result == "MAIN":
                break
            elif isinstance(result, tuple):
                detail, name = result
                if detail:
                    add_to_cart(detail, name)

        elif choice == "3":
            fc = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
            result = get_packages_by_family(fc, return_package_detail=True)
            if result:
                detail, name = result
                add_to_cart(detail, name)

        elif choice == "4" and cart_items:
            idx = console.input(f"[{theme['text_sub']}]Nomor item yang ingin dihapus:[/{theme['text_sub']}] ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(cart_items):
                i = int(idx) - 1
                removed = display_cart.pop(i)
                cart_items.pop(i)
                total_price -= removed["price"]
                print_panel("🗑️ Dihapus", f"Item '{removed['name']}' telah dihapus.")
                pause()
            else:
                print_panel("⚠️ Error", "Nomor item tidak valid.")
                pause()

        elif choice == "5" and cart_items:
            clear_screen()
            console.print(Panel("💳 Konfirmasi Pembayaran Bundle", style=theme["border_info"], expand=True))

            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("No", justify="right", style=theme["text_key"], width=4)
            table.add_column("Nama Paket", style=theme["text_body"])
            table.add_column("Harga", style=theme["text_money"], justify="right")

            for i, item in enumerate(display_cart, start=1):
                table.add_row(str(i), item["name"], get_rupiah(item["price"]))

            console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))
            console.print(f"[{theme['text_body']}]Total Pembayaran: Rp {get_rupiah(total_price)}[/]")

            nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
            nav.add_column(justify="right", style=theme["text_key"], width=6)
            nav.add_column(style=theme["text_body"])
            nav.add_row("1", "💳 E-Wallet (DANA, GoPay, OVO)")
            nav.add_row("2", "💳 ShopeePay")
            nav.add_row("3", "📱 QRIS")
            nav.add_row("4", "💰 Pulsa")
            nav.add_row("0", "↩️ Batal")

            console.print(Panel(nav, border_style=theme["border_info"], padding=(0, 1), expand=True))

            method = console.input(f"[{theme['text_sub']}]Pilih metode pembayaran:[/{theme['text_sub']}] ").strip()
            payment_for = "BUY_PACKAGE"

            if method == "1":
                show_multipayment(api_key, tokens, cart_items, payment_for, True, exclude_shopeepay=True)
            elif method == "2":
                show_multipayment(api_key, tokens, cart_items, payment_for, True, force_payment_method="SHOPEEPAY")
            elif method == "3":
                show_qris_payment(api_key, tokens, cart_items, payment_for, True)
            elif method == "4":
                settlement_balance(api_key, tokens, cart_items, payment_for, True)
            else:
                continue

            console.input(f"[{theme['text_sub']}]✅ Pembayaran selesai. Tekan Enter untuk kembali...[/{theme['text_sub']}]")
            break

        elif choice == "00":
            break

        else:
            print_panel("⚠️ Error", "Pilihan tidak valid.")
            pause()

