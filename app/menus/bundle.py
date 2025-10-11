from app.service.auth import AuthInstance
from app.service.bookmark import BookmarkInstance
from app.service.family_bookmark import FamilyBookmarkInstance
from app.client.engsel import get_family, get_package, get_package_details
from app.client.balance import settlement_balance
from app.client.qris import show_qris_payment
from app.client.ewallet import show_multipayment
from app.menus.util import clear_screen, pause
from app.menus.util_helper import print_panel, get_rupiah
from app.config.theme_config import get_theme
from app.menus.package import get_packages_by_family
from app.type_dict import PaymentItem
from app.menus.family_grup show_family_menu
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD

console = Console()


def get_package_from_bookmark():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    clear_screen()
    console.print(Panel("📌 Tambah Paket dari Bookmark", style=theme["border_info"], expand=True))

    bookmarks = BookmarkInstance.get_bookmarks()
    if not bookmarks:
        print_panel("ℹ️ Info", "Tidak ada bookmark tersimpan.")
        pause()
        return None, None

    table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column("No", justify="right", style=theme["text_key"], width=4)
    table.add_column("Family", style=theme["text_body"])
    table.add_column("Varian", style=theme["text_body"])
    table.add_column("Paket", style=theme["text_body"])
    table.add_column("Masa Aktif", style=theme["text_date"])

    for idx, bm in enumerate(bookmarks, start=1):
        validity = bm.get("validity", "-")
        table.add_row(str(idx), bm["family_name"], bm["variant_name"], bm["option_name"], validity)

    console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

    nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    nav.add_column(justify="right", style=theme["text_key"], width=6)
    nav.add_column(style=theme["text_body"])
    nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu sebelumnya[/]")

    console.print(Panel(nav, border_style=theme["border_info"], padding=(0, 1), expand=True))

    choice = console.input(f"[{theme['text_sub']}]Pilih nomor paket:[/{theme['text_sub']}] ").strip()
    if choice == "00":
        return None, None

    if not choice.isdigit() or not (1 <= int(choice) <= len(bookmarks)):
        print_panel("⚠️ Error", "Pilihan tidak valid.")
        pause()
        return None, None

    selected = bookmarks[int(choice) - 1]
    family_data = get_family(api_key, tokens, selected["family_code"], selected["is_enterprise"])
    if not family_data:
        print_panel("⚠️ Error", "Gagal mengambil data family.")
        pause()
        return None, None

    variant_code = next((v["package_variant_code"] for v in family_data["package_variants"] if v["name"] == selected["variant_name"]), None)
    detail = get_package_details(api_key, tokens, selected["family_code"], variant_code, selected["order"], selected["is_enterprise"])
    if not detail:
        print_panel("⚠️ Error", "Gagal mengambil detail paket.")
        pause()
        return None, None

    name = f"{selected['family_name']} - {selected['variant_name']} - {selected['option_name']}"
    return detail, name


def get_package_from_family_bookmark():
    theme = get_theme()
    clear_screen()
    console.print(Panel("📌 Tambah Paket dari Bookmark Family Code", style=theme["border_info"], expand=True))

    bookmarks = FamilyBookmarkInstance.get_bookmarks()
    if not bookmarks:
        print_panel("ℹ️ Info", "Tidak ada bookmark family code tersimpan.")
        pause()
        return None, None

    table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column("No", justify="right", style=theme["text_key"], width=4)
    table.add_column("Family", style=theme["text_body"])
    table.add_column("Kode", style=theme["border_warning"])

    for idx, bm in enumerate(bookmarks, start=1):
        table.add_row(str(idx), bm["family_name"], bm["family_code"])

    console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

    nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    nav.add_column(justify="right", style=theme["text_key"], width=6)
    nav.add_column(style=theme["text_body"])
    nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu sebelumnya[/]")

    console.print(Panel(nav, border_style=theme["border_info"], padding=(0, 1), expand=True))

    choice = console.input(f"[{theme['text_sub']}]Pilih nomor family code:[/{theme['text_sub']}] ").strip()
    if choice == "00":
        return None, None

    if not choice.isdigit() or not (1 <= int(choice) <= len(bookmarks)):
        print_panel("⚠️ Error", "Pilihan tidak valid.")
        pause()
        return None, None

    selected = bookmarks[int(choice) - 1]
    return get_packages_by_family(selected["family_code"], return_package_detail=True)


def show_bundle_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    cart_items = []
    display_cart = []
    total_price = 0

    while True:
        clear_screen()
        console.print(Panel("🛒 Keranjang Paket Bundle", style=theme["border_info"], expand=True))

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
        nav.add_row("4", "Hapus Item dari Keranjang")
        if cart_items:
            nav.add_row("5", "💳 Lanjutkan ke Pembayaran")
        nav.add_row("00", "↩️ Kembali ke Menu Utama")

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
            detail, name = get_package_from_bookmark()
            if detail: add_to_cart(detail, name)

        elif choice == "2":
            detail, name = show_family_menu()
            if detail: add_to_cart(detail, name)

        elif choice == "3":
            fc = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
            result = get_packages_by_family(fc, return_package_detail=True)
            if result:
                detail, name = result
                detail: add_to_cart(detail, name)

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
