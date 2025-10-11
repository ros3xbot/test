import json
import sys
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, get_addons, get_package_details, send_api_request
from app.service.bookmark import BookmarkInstance
from app.client.purchase import settlement_bounty, settlement_loyalty
from app.menus.util import clear_screen, pause, display_html
from app.menus.util_helper import print_panel, get_rupiah, live_loading
from app.client.qris import show_qris_payment
from app.client.ewallet import show_multipayment
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem
from app.config.theme_config import get_theme

from rich.console import Console,Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.box import MINIMAL_DOUBLE_HEAD
from rich.align import Align
from rich.markup import escape

console = Console()

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order=-1):
    clear_screen()

    package = get_package(api_key, tokens, package_option_code)
    theme = get_theme()
    if not package:
        print_panel("⚠️ Error", "Gagal memuat detail paket.")
        pause()
        return "BACK"

    option = package.get("package_option", {})
    family = package.get("package_family", {})
    variant = package.get("package_detail_variant", {})
    price = option.get("price", 0)
    formatted_price = get_rupiah(price)
    validity = option.get("validity", "-")
    detail = display_html(option.get("tnc", ""))
    point = option.get("point", "-")
    plan_type = family.get("plan_type", "-")
    payment_for = family.get("payment_for", "") or "BUY_PACKAGE"
    token_confirmation = package.get("token_confirmation", "")
    ts_to_sign = package.get("timestamp", "")

    option_name = option.get("name", "")
    family_name = family.get("name", "")
    variant_name = variant.get("name", "")
    title = f"{family_name} - {variant_name} - {option_name}".strip()

    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]

    # Informasi Paket
    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_column(justify="left")
    info_table.add_row("Nama", f": [bold {theme['text_body']}]{title}[/]")
    info_table.add_row("Harga", f": Rp [{theme['text_money']}]{formatted_price}[/]")
    info_table.add_row("Masa Aktif", f": [{theme['text_date']}]{validity}[/]")
    info_table.add_row("Point", f": [{theme['text_body']}]{point}[/]")
    info_table.add_row("Plan Type", f": [{theme['text_body']}]{plan_type}[/]")
    info_table.add_row("Payment For", f": [{theme['text_body']}]{payment_for}[/]")

    console.print(Panel(info_table, title="📦 Detail Paket", border_style=theme["border_info"], expand=True))

    # Benefit
    benefits = option.get("benefits", [])
    if benefits:
        benefit_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        benefit_table.add_column("Nama", style=theme["text_body"])
        benefit_table.add_column("Jenis", style=theme["text_body"])
        benefit_table.add_column("Unli", style=theme["border_info"], justify="center")
        benefit_table.add_column("Total", style=theme["text_body"], justify="right")

        for b in benefits:
            dt = b["data_type"]
            total = b["total"]
            is_unli = b["is_unlimited"]

            if is_unli:
                total_str = {"VOICE": "menit", "TEXT": "SMS", "DATA": "kuota"}.get(dt, dt)
            else:
                if dt == "VOICE":
                    total_str = f"{total / 60:.0f} menit"
                elif dt == "TEXT":
                    total_str = f"{total} SMS"
                elif dt == "DATA":
                    if total >= 1_000_000_000:
                        total_str = f"{total / (1024 ** 3):.2f} GB"
                    elif total >= 1_000_000:
                        total_str = f"{total / (1024 ** 2):.2f} MB"
                    elif total >= 1_000:
                        total_str = f"{total / 1024:.2f} KB"
                    else:
                        total_str = f"{total} B"
                else:
                    total_str = f"{total} ({dt})"

            benefit_table.add_row(b["name"], dt, "YES" if is_unli else "-", total_str)

        console.print(Panel(benefit_table, title="🎁 Benefit Paket", border_style=theme["border_success"], padding=(0, 0), expand=True))

    # Addons
    #addons = get_addons(api_key, tokens, package_option_code)
    #console.print(Panel(json.dumps(addons, indent=2), title="🧩 Addons", border_style=theme["border_info"], expand=True))

    # Syarat & Ketentuan
    console.print(Panel(detail, title="📜 Syarat & Ketentuan", border_style=theme["border_warning"], expand=True))

    # Opsi Pembelian
    option_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    option_table.add_column(justify="right", style=theme["text_key"], width=6)
    option_table.add_column(justify="left", style=theme["text_body"])
    option_table.add_row("1", "Beli dengan Pulsa")
    option_table.add_row("2", "Beli dengan E-Wallet")
    option_table.add_row("3", "Bayar dengan QRIS")
    if payment_for == "REDEEM_VOUCHER":
        option_table.add_row("4", "Ambil sebagai bonus")
        option_table.add_row("5", "Beli dengan Poin")
    if option_order != -1:
        option_table.add_row("0", "Tambah ke Bookmark")
    #option_table.add_row("9", "Simulasi Pembelian dari d.json")
    option_table.add_row("00", f"[{theme['text_sub']}]Kembali ke daftar paket[/]")
    option_table.add_row("99", f"[{theme['text_err']}]Kembali ke menu utama[/]")

    console.print(Panel(option_table, title="🛒 Opsi Pembelian", border_style=theme["border_info"], expand=True))

    # Interaksi
    while True:
        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "BACK"
        elif choice == "99":
            return "MAIN"
        elif choice == "0" and option_order != -1:
            success = BookmarkInstance.add_bookmark(
                family_code=family.get("package_family_code", ""),
                family_name=family_name,
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            msg = "Paket berhasil ditambahkan ke bookmark." if success else "Paket sudah ada di bookmark."
            print_panel("✅ Info", msg)
            pause()
        elif choice == "1":
            settlement_balance(api_key, tokens, payment_items, payment_for, True, amount_used="first")
            console.input("✅ Pembelian selesai. Tekan Enter untuk kembali.")
            return True
        elif choice == "2":
            show_multipayment(api_key, tokens, payment_items, payment_for, True, amount_used="first")
            console.input("✅ Silahkan lakukan pembayaran. Tekan Enter untuk kembali.")
            return True
        elif choice == "3":
            show_qris_payment(api_key, tokens, payment_items, payment_for, True, amount_used="first")
            console.input("✅ Silahkan lakukan pembayaran. Tekan Enter untuk kembali.")
            return True
        elif choice == "4" and payment_for == "REDEEM_VOUCHER":
            settlement_bounty(api_key, tokens, token_confirmation, ts_to_sign, package_option_code, price, variant_name)
            console.input("✅ Bonus berhasil diambil. Tekan Enter untuk kembali.")
            return True
        elif choice == "5" and payment_for == "REDEEM_VOUCHER":
            settlement_loyalty(api_key, tokens, token_confirmation, ts_to_sign, package_option_code, price)
            console.input("✅ Pembelian dengan poin selesai. Tekan Enter untuk kembali.")
            return True
        elif choice == "9":
            try:
                d = json.load(open("d.json", "r"))
                d_id = 0
                pd = get_package_details(
                    api_key,
                    tokens,
                    d[d_id]["fc"],
                    d[d_id]["vc"],
                    d[d_id]["oo"],
                    d[d_id]["ie"],
                    d[d_id]["mt"],
                )

                payment_items.append(
                    PaymentItem(
                        item_code=pd["package_option"]["package_option_code"],
                        product_type="",
                        item_price=pd["package_option"]["price"],
                        item_name=pd["package_option"]["name"],
                        tax=0,
                        token_confirmation=pd["token_confirmation"],
                    )
                )

                show_qris_payment(api_key, tokens, payment_items, payment_for, True, amount_used="")
                console.input("✅ Simulasi pembelian selesai. Tekan Enter untuk kembali.")
            except Exception as e:
                print_panel("⚠️ Error", f"Gagal melakukan simulasi: {e}")
                pause()
        else:
            print_panel("⚠️ Error", "Pilihan tidak valid. Silakan pilih sesuai menu.")


def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    if not tokens:
        print_panel("⚠️ Error", "Tidak ditemukan token pengguna aktif.")
        pause()
        return "BACK"

    # Memuat data paket family tanpa animasi
    data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)

    if not data:
        print_panel("⚠️ Error", "Gagal memuat data paket family.")
        pause()
        return "BACK"

    packages = []

    while True:
        clear_screen()

        # Panel info family
        info_text = Text()
        info_text.append("Nama: ", style=theme["text_body"])
        info_text.append(f"{data['package_family']['name']}\n", style=theme["text_value"])
        info_text.append("Kode: ", style=theme["text_body"])
        info_text.append(f"{family_code}\n", style=theme["border_warning"])
        info_text.append("Tipe: ", style=theme["text_body"])
        info_text.append(f"{data['package_family']['package_family_type']}\n", style=theme["text_value"])
        info_text.append("Jumlah Varian: ", style=theme["text_body"])
        info_text.append(f"{len(data['package_variants'])}\n", style=theme["text_value"])

        console.print(Panel(
            info_text,
            title=f"[{theme['text_title']}]✨ Info Paket Family ✨[/]",
            border_style=theme["border_info"],
            padding=(0, 2),
            expand=True
        ))

        # Tabel daftar paket
        package_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        package_table.add_column("No", justify="right", style=theme["text_key"], width=4)
        package_table.add_column("Varian", style=theme["text_body"])
        package_table.add_column("Nama Paket", style=theme["text_body"])
        package_table.add_column("Harga", style=theme["text_money"], justify="right")

        packages.clear()
        option_number = 1
        for variant in data["package_variants"]:
            variant_name = variant["name"]
            for option in variant["package_options"]:
                option_name = option["name"]
                formatted_price = get_rupiah(option["price"])
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })
                package_table.add_row(
                    str(option_number),
                    variant_name,
                    option_name,
                    formatted_price
                )
                option_number += 1

        console.print(Panel(
            package_table,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        # Panel navigasi
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu sebelumnya[/]")
        nav_table.add_row("99", f"[{theme['text_err']}]Kembali ke menu utama[/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_info"],
            padding=(0, 1),
            expand=True
        ))

        # Input pilihan
        pkg_choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor):[/{theme['text_sub']}] ").strip()
        if pkg_choice == "00":
            return "BACK"
        elif pkg_choice == "99":
            return "MAIN"

        if not pkg_choice.isdigit():
            print_panel("⚠️ Error", "Input tidak valid. Masukkan nomor paket.")
            pause()
            continue

        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        if not selected_pkg:
            print_panel("⚠️ Error", "Paket tidak ditemukan. Silakan masukkan nomor yang benar.")
            pause()
            continue

        result = show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"]
        )

        if result == "MAIN":
            return "MAIN"
        elif result == "BACK":
            continue
        elif result is True:
            continue  # kembali ke daftar paket setelah pembelian


def fetch_my_packages():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    if not tokens:
        print_panel("⚠️ Error", "Tidak ditemukan token pengguna aktif.")
        pause()
        return "BACK"

    id_token = tokens.get("id_token")
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }

    while True:
        clear_screen()

        with live_loading("Mengambil daftar paket aktif Anda...", theme):
            res = send_api_request(api_key, path, payload, id_token, "POST")

        if res.get("status") != "SUCCESS":
            print_panel("⚠️ Error", "Gagal mengambil paket.")
            pause()
            return "BACK"

        quotas = res["data"]["quotas"]
        if not quotas:
            print_panel("ℹ️ Info", "Tidak ada paket aktif ditemukan.")
            pause()
            return "BACK"

        console.print(Panel(
            Align.center("📦 Paket Aktif Saya", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        my_packages = []
        for num, quota in enumerate(quotas, start=1):
            quota_code = quota["quota_code"]
            group_code = quota["group_code"]
            group_name = quota["group_name"]
            quota_name = quota["name"]
            family_code = "N/A"

            with live_loading(f"Paket #{num}", theme):
                package_details = get_package(api_key, tokens, quota_code)

            if package_details:
                family_code = package_details["package_family"]["package_family_code"]

            benefits = quota.get("benefits", [])
            benefit_table = None
            if benefits:
                benefit_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
                benefit_table.add_column("Nama", style=theme["text_body"])
                benefit_table.add_column("Jenis", style=theme["text_body"])
                benefit_table.add_column("Kuota", style=theme["text_body"], justify="right")

                for b in benefits:
                    name = b.get("name", "")
                    dt = b.get("data_type", "N/A")
                    r = b.get("remaining", 0)
                    t = b.get("total", 0)

                    if dt == "DATA":
                        def fmt(val):
                            if val >= 1_000_000_000:
                                return f"{val / (1024 ** 3):.2f} GB"
                            elif val >= 1_000_000:
                                return f"{val / (1024 ** 2):.2f} MB"
                            elif val >= 1_000:
                                return f"{val / 1024:.2f} KB"
                            return f"{val} B"
                        r_str = fmt(r)
                        t_str = fmt(t)
                    elif dt == "VOICE":
                        r_str = f"{r / 60:.2f} menit"
                        t_str = f"{t / 60:.2f} menit"
                    elif dt == "TEXT":
                        r_str = f"{r} SMS"
                        t_str = f"{t} SMS"
                    else:
                        r_str = str(r)
                        t_str = str(t)

                    benefit_table.add_row(name, dt, f"{r_str} / {t_str}")

            package_text = Text()
            package_text.append(f"📦 Paket {num}\n", style="bold")
            package_text.append("Nama: ", style=theme["border_info"])
            package_text.append(f"{quota_name}\n", style=theme["text_sub"])
            package_text.append("Quota Code: ", style=theme["border_info"])
            package_text.append(f"{quota_code}\n", style=theme["text_body"])
            package_text.append("Family Code: ", style=theme["border_info"])
            package_text.append(f"{family_code}\n", style=theme["border_warning"])
            package_text.append("Group Code: ", style=theme["border_info"])
            package_text.append(f"{group_code}\n", style=theme["text_body"])

            panel_content = [package_text]
            if benefit_table:
                panel_content.append(benefit_table)

            console.print(Panel(
                Group(*panel_content),
                border_style=theme["border_primary"],
                padding=(0, 1),
                expand=True
            ))

            my_packages.append({
                "number": num,
                "quota_code": quota_code,
            })

        package_range = f"(1–{len(my_packages)})"
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row(package_range, f"[{theme['text_body']}]Pilih nomor paket untuk pembelian ulang")
        nav_table.add_row("00", f"[{theme['text_err']}]Kembali ke menu utama")

        console.print(Panel(
            nav_table,
            border_style=theme["border_info"],
            padding=(0, 1),
            expand=True
        ))

        while True:
            choice = console.input(f"[{theme['text_sub']}]Masukkan nomor paket {package_range} atau 00:[/{theme['text_sub']}] ").strip().lower()
            if choice == "00":
                with live_loading("Kembali ke menu utama...", theme):
                    pass
                return "BACK"

            if not choice.isdigit():
                print_panel("⚠️ Error", "Input tidak valid. Masukkan nomor paket atau 00.")
                continue

            selected_pkg = next((pkg for pkg in my_packages if str(pkg["number"]) == choice), None)
            if not selected_pkg:
                print_panel("⚠️ Error", f"Nomor paket tidak ditemukan. Masukkan angka {package_range} atau 00.")
                continue

            result = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)

            if result == "MAIN":
                return "BACK"
            elif result == "BACK":
                with live_loading("Kembali ke daftar paket...", theme):
                    pass
                break
            elif result is True:
                return "BACK"

