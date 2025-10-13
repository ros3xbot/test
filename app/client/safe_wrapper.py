from app.client.engsel import settlement_balance
from app.config.theme_config import print_panel
from app.auth.auth import AuthInstance

def safe_settlement_balance(api_key, payment_items, overwrite_amount, action="BUY_PACKAGE", is_preview=False):
    # 🔐 Refresh token sebelum transaksi
    AuthInstance.renew_active_user_token()
    tokens = AuthInstance.get_active_tokens()

    # ✅ Validasi parameter
    if not api_key or not tokens or not payment_items:
        print_panel("⚠️ Error", "Parameter tidak lengkap.")
        return None

    for item in payment_items:
        if not item.item_code or not item.token_confirmation or item.item_price is None:
            print_panel("⚠️ Error", "Item decoy tidak valid atau tidak lengkap.")
            return None

    if not isinstance(overwrite_amount, (int, float)):
        print_panel("⚠️ Error", "overwrite_amount harus berupa angka.")
        return None

    # 🧾 Kirim request
    res = settlement_balance(api_key, tokens, payment_items, action, is_preview, overwrite_amount)

    # 🛡️ Tangani error Bizz-err.Amount.Total
    if res and res.get("status", "") != "SUCCESS":
        error_msg = res.get("message", "")
        if "Bizz-err.Amount.Total" in error_msg:
            try:
                valid_amount = int(error_msg.split("=")[1].strip())
                AuthInstance.renew_active_user_token()
                tokens = AuthInstance.get_active_tokens()
                res = settlement_balance(api_key, tokens, payment_items, action, is_preview, valid_amount)
            except:
                print_panel("⚠️ Error", "Gagal parsing jumlah valid dari pesan error.")
                return None

        elif res.get("status") == "INVALID_REQUEST":
            print_panel("⚠️ Error", f"Permintaan tidak valid. Pesan: {res.get('message')}")
            return None

    return res
