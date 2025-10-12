import requests
from app.client.engsel import get_family, get_package_details
from app.menus.util import pause, clear_screen
from app.menus.util_helper import print_panel
from app.service.auth import AuthInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance

from rich.table import Table
from rich.panel import Panel
from rich.align import Align

def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens() or {}
    theme = get_theme()

    clear_screen()
    console.print(Panel(
        Align.center(f"🛒 Pembelian Paket Family: {family_code}", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))

    decoy_package_detail = None
    if use_decoy:
        try:
            response = requests.get("https://me.mashu.lol/pg-decoy-xcp.json", timeout=30)
            decoy_data = response.json()
            decoy_package_detail = get_package_details(
                api_key,
                tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"],
            )
            threshold = decoy_package_detail["package_option"]["price"]
            print_panel("⚠️ Konfirmasi", f"Pastikan sisa balance KURANG DARI Rp{threshold} sebelum lanjut.")
            confirm = console.input(f"[{theme['text_sub']}]Lanjutkan pembelian? (y/n):[/{theme['text_sub']}] ").strip().lower()
            if confirm != "y":
                print_panel("ℹ️ Info", "Pembelian dibatalkan oleh pengguna.")
                pause()
                return None
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal mengambil data decoy: {e}")
            pause()
            return None

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("⚠️ Error", f"Gagal mengambil data family: {family_code}")
        pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]

    total_packages = sum(len(v["package_options"]) for v in variants)
    successful_purchases = []
    purchase_count = 0

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            purchase_count += 1
            option_name = option["name"]
            option_order = option["order"]
            option_price = option["price"]

            console.print(Panel(
                f"[bold]{variant_name}[/] - {option_order}. {option_name}\nHarga: Rp {get_rupiah(option_price)}",
                title=f"[{theme['text_title']}]Pembelian {purchase_count} dari {total_packages}[/]",
                border_style=theme["border_primary"],
                padding=(1, 2),
                expand=True
            ))

            try:
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option_order,
                    None,
                    None,
                )
            except Exception as e:
                print_panel("⚠️ Error", f"Gagal mengambil detail paket: {e}")
                continue

            payment_items = [
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=f"{option_order}. {target_package_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            ]

            if use_decoy and decoy_package_detail:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=f"{option_order}. {decoy_package_detail['package_option']['name']}",
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )

            overwrite_amount = sum(item.item_price for item in payment_items)

            try:
                res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, overwrite_amount)
                if res and res.get("status", "") != "SUCCESS":
                    msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in msg:
                        valid_amount = int(msg.split("=")[1].strip())
                        res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, valid_amount)

                if res and res.get("status", "") == "SUCCESS":
                    successful_purchases.append(f"{variant_name}|{option_order}. {option_name} - {option_price}")
                    print_panel("✅ Sukses", f"Paket berhasil dibeli: {option_name}")
                    if pause_on_success:
                        pause()
                else:
                    print_panel("⚠️ Gagal", f"Gagal membeli paket: {option_name}")
            except Exception as e:
                print_panel("⚠️ Error", f"Exception saat pembelian: {e}")
            console.print("")

    console.print(Panel(
        f"Total pembelian sukses untuk family [bold]{family_name}[/]: {len(successful_purchases)}",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True
    ))

    if successful_purchases:
        table = Table(title="📦 Paket yang berhasil dibeli", box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Detail Paket", style=theme["text_body"])
        for i, item in enumerate(successful_purchases, start=1):
            table.add_row(str(i), item)
        console.print(table)

    pause()

