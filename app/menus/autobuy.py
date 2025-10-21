import time
import base64
import qrcode
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from app.service.auth import AuthInstance
from app.client.ewallet import settlement_multipayment
from app.client.qris import show_qris_payment, settlement_qris
from app.client.engsel import get_package_details
from app.client.balance import settlement_balance
from app.menus.util import pause
from app.config.theme_config import get_theme

console = Console()
theme = get_theme()

def execute_unlimited_tiktok_autobuy():
    active_user = AuthInstance.get_active_user()
    if not active_user:
        console.print(f"[{theme['text_err']}]Silakan login terlebih dahulu.[/]")
        pause()
        return

    console.print(Panel("🔍 Memeriksa harga paket Unlimited Tiktok...", border_style=theme["border_info"]))
    packages_to_check = [
        { "order": 1, "expected_price": 99000, "variant_name": "For Xtra Combo", "option_name": "Premium" },
        { "order": 2, "expected_price": 75000, "variant_name": "For Xtra Combo", "option_name": "VIP" },
        { "order": 3, "expected_price": 51000, "variant_name": "For Xtra Combo", "option_name": "Plus" },
        { "order": 4, "expected_price": 33000, "variant_name": "For Xtra Combo", "option_name": "Basic" },
    ]

    package_details_list = []
    prices_match_count = 0

    for pkg in packages_to_check:
        detail = get_package_details(
            AuthInstance.api_key,
            active_user["tokens"],
            "08a3b1e6-8e78-4e45-a540-b40f06871cfe",
            pkg["variant_name"],
            pkg["order"],
            None,
            silent=True
        )
        if not detail:
            console.print(f"[{theme['text_err']}]Gagal mengambil detail untuk paket order {pkg['order']}[/]")
            pause()
            return
        detail["order_from_request"] = pkg["order"]
        package_details_list.append(detail)
        if detail["package_option"]["price"] == pkg["expected_price"]:
            prices_match_count += 1

    if prices_match_count == 0:
        console.print(Panel("⚠️ Harga tidak sesuai. Ulangi besok atau ganti kartu 🔥😎", border_style=theme["border_err"]))
        pause()
        return
    elif prices_match_count < len(packages_to_check):
        console.print("✅ Beberapa harga sesuai, lanjut ke proses pembayaran Tiktok...")
    else:
        console.print("✅ Semua harga sesuai, melanjutkan pembelian pulsa...")

        basic = next((d for d in package_details_list if d.get("order_from_request") == 4), None)
        if not basic:
            console.print(f"[{theme['text_err']}]Detail paket Basic tidak ditemukan.[/]")
            pause()
            return

        payment_items = [{
            "item_code": basic["package_option"]["package_option_code"],
            "product_type": "",
            "item_price": basic["package_option"]["price"],
            "item_name": f"{basic.get('package_detail_variant', {}).get('name', '')} {basic['package_option']['name']}".strip(),
            "tax": 0,
            "token_confirmation": basic["token_confirmation"],
        }]

        response = settlement_balance(
            AuthInstance.api_key,
            active_user["tokens"],
            payment_items,
            "BUY_PACKAGE",
            ask_overwrite=False,
            amount_used="first"
        )

        if not response or response.get("status") != "SUCCESS":
            console.print(f"[{theme['text_err']}]Gagal melakukan pembayaran dengan pulsa.[/]")
            pause()
            return

        console.print(Panel("⏳ Tunggu 10 menit, jangan tutup Termux...", border_style=theme["border_warning"]))
        try:
            for i in range(600, 0, -1):
                console.print(f"[{theme['text_sub']}]Waktu tersisa: {i//60:02d}:{i%60:02d}[/]", end="\r")
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("⛔ Proses dibatalkan.")
            return

        console.print("🔄 Refresh token...")
        if not AuthInstance.renew_active_user_token():
            console.print(f"[{theme['text_err']}]Gagal refresh token.[/]")
            pause()
            return
        active_user = AuthInstance.get_active_user()

    console.print("📦 Mengambil detail paket Tiktok...")
    tiktok = get_package_details(
        AuthInstance.api_key,
        active_user["tokens"],
        "08a3b1e6-8e78-4e45-a540-b40f06871cfe",
        "For Xtra Combo",
        6,
        None,
        silent=False
    )

    if not tiktok:
        console.print(f"[{theme['text_err']}]Gagal mengambil detail paket Tiktok.[/]")
        pause()
        return

    payment_items = [{
        "item_code": tiktok["package_option"]["package_option_code"],
        "product_type": "",
        "item_price": tiktok["package_option"]["price"],
        "item_name": f"{tiktok.get('package_detail_variant', {}).get('name', '')} {tiktok['package_option']['name']}".strip(),
        "tax": 0,
        "token_confirmation": tiktok["token_confirmation"],
    }]

    console.print("💳 Memproses pembayaran QRIS...")
    trx_id = settlement_qris(
        AuthInstance.api_key,
        active_user["tokens"],
        payment_items,
        "BUY_PACKAGE",
        ask_overwrite=False,
        amount_overwrite=30000
    )

    if not trx_id:
        console.print(f"[{theme['text_err']}]Gagal membuat transaksi QRIS.[/]")
        pause()
        return

    qris_data = show_qris_payment(AuthInstance.api_key, active_user["tokens"], trx_id)
    if qris_data:
        console.print(Panel("✅ Kode QRIS berhasil dibuat! Silakan scan.", border_style=theme["border_success"]))
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1, border=1)
        qr.add_data(qris_data)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        b64 = base64.urlsafe_b64encode(qris_data.encode()).decode()
        console.print(f"\n🌐 Link QRIS: https://ki-ar-kod.netlify.app/?data={b64}")
    else:
        console.print(f"[{theme['text_err']}]Gagal mengambil data QRIS.[/]")
    pause()
