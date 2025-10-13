from random import randint
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD
from rich.text import Text
from rich.rule import Rule
from app.client.engsel import get_family, get_package_details
from app.menus.util import pause
from app.service.auth import AuthInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance
from app.config.theme_config import get_theme

console = Console()
theme = get_theme()

def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    # Decoy setup
    decoy_data = None
    decoy_package_detail = None
    if use_decoy:
        url = "https://raw.githubusercontent.com/dratx1/engsel/refs/heads/main/family/pg-decoy-xcp.json"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            console.print(Panel("❌ Gagal mengambil data decoy package.", border_style=theme["border_error"]))
            pause()
            return None

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

        balance_treshold = decoy_package_detail["package_option"]["price"]
        console.print(Panel(
            f"⚠️ Pastikan sisa balance KURANG DARI Rp {balance_treshold:,}",
            border_style=theme["border_warning"]
        ))
        balance_answer = console.input(f"[{theme['text_sub']}]Apakah anda yakin ingin melanjutkan pembelian? (y/n):[/{theme['text_sub']}] ").strip()
        if balance_answer.lower() != "y":
            console.print(Panel("❌ Pembelian dibatalkan oleh user.", border_style=theme["border_error"]))
            pause()
            return None

    # Ambil data family
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        console.print(Panel(f"❌ Gagal mengambil data family: {family_code}", border_style=theme["border_error"]))
        pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]

    console.rule(f"[bold {theme['text_title']}]📦 Memulai Pembelian Paket Family: {family_name}[/]")

    successful_purchases = []
    packages_count = sum(len(v["package_options"]) for v in variants)
    purchase_count = 0

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            option_name = option["name"]
            option_order = option["order"]
            option_price = option["price"]
            purchase_count += 1

            console.print(Panel(
                f"🔄 Purchase {purchase_count} of {packages_count}\n🛒 {variant_name} - {option_order}. {option_name} - Rp {option_price:,}",
                border_style=theme["border_info"]
            ))

            try:
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                console.print(Panel(
                    f"❌ Gagal ambil detail paket: {variant_name} - {option_name}\n{e}",
                    border_style=theme["border_error"]
                ))
                continue

            payment_items = [
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + target_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            ]

            overwrite_amount = target_package_detail["package_option"]["price"]

            if use_decoy and decoy_package_detail:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=str(randint(1000, 9999)) + decoy_package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )
                overwrite_amount += decoy_package_detail["package_option"]["price"]

            try:
                res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, overwrite_amount)
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "Unknown error")
                    if "Bizz-err.Amount.Total" in error_msg:
                        valid_amount = int(error_msg.split("=")[1].strip())
                        console.print(f"🔁 Adjusted total amount to: Rp {valid_amount:,}")
                        res = settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", False, valid_amount)

                if res and res.get("status", "") == "SUCCESS":
                    successful_purchases.append(f"{variant_name}|{option_order}. {option_name} - Rp {option_price:,}")
                    console.print(Panel("✅ Purchase successful!", border_style=theme["border_success"]))
                    if pause_on_success:
                        pause()
                else:
                    console.print(Panel("❌ Purchase failed!", border_style=theme["border_error"]))
            except Exception as e:
                console.print(Panel(f"❌ Error saat pembelian: {e}", border_style=theme["border_error"]))

            console.rule()

    # Ringkasan sukses
    console.print(Panel(f"📦 Total pembelian sukses untuk [bold]{family_name}[/]: {len(successful_purchases)}", border_style=theme["border_success"]))
    if successful_purchases:
        table = Table(title="✅ Paket Berhasil Dibeli", box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("Detail", style=theme["text_body"])
        for item in successful_purchases:
            table.add_row(item)
        console.print(table)

    console.rule("[dim]Selesai[/]")
    pause()
