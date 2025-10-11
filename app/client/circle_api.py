import os
import requests
import uuid
from app.service.crypto import decrypt_xdata, get_signature, java_like_timestamp

# Ambil dari .env
BASE_API_URL = os.getenv("BASE_API_URL")
API_KEY = os.getenv("API_KEY")
UA = os.getenv("UA")

def _build_headers(tokens: dict, sig_time_sec: int, x_sig: str, x_requested_at) -> dict:
    return {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.7.0",
    }

def _post(tokens: dict, path: str, payload: dict, decrypt=True):
    url = f"{BASE_API_URL}/{path}"
    sig_time_sec, x_sig, x_requested_at = get_signature(path, payload)
    headers = _build_headers(tokens, sig_time_sec, x_sig, x_requested_at)
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        return decrypt_xdata(resp.json()) if decrypt else resp.json()
    except Exception:
        return resp.json()

# ====================
# XL Circle API Client
# ====================

def validate_member(tokens: dict, msisdn: str):
    return _post(tokens, "family-hub/api/v8/members/validate", {
        "lang": "id",
        "is_enterprise": False,
        "msisdn": msisdn
    })

def check_group_status(tokens: dict, msisdn: str):
    return validate_member(tokens, msisdn)

def get_group_info(tokens: dict, group_id: str):
    return _post(tokens, "family-hub/api/v8/members/info", {
        "lang": "id",
        "is_enterprise": False,
        "group_id": group_id
    })

def get_spending_tracker(tokens: dict, family_id: str, parent_subs_id: str):
    return _post(tokens, "gamification/api/v8/family-hub/spending-tracker", {
        "lang": "id",
        "is_enterprise": False,
        "family_id": family_id,
        "parent_subs_id": parent_subs_id
    })

def get_bonus_list(tokens: dict, family_id: str, parent_subs_id: str):
    return _post(tokens, "gamification/api/v8/family-hub/bonus/list", {
        "lang": "id",
        "is_enterprise": False,
        "family_id": family_id,
        "parent_subs_id": parent_subs_id
    })

def get_package_detail_circle(tokens: dict, package_option_code: str):
    return _post(tokens, "api/v8/xl-stores/options/detail", {
        "lang": "id",
        "is_enterprise": False,
        "family_role_hub": "MEMBER",
        "is_autobuy": False,
        "is_migration": False,
        "is_shareable": False,
        "is_transaction_routine": False,
        "is_upsell_pdp": False,
        "migration_type": "",
        "package_family_code": "",
        "package_option_code": package_option_code,
        "package_variant_code": ""
    })

def get_addons_circle(tokens: dict, package_option_code: str):
    return _post(tokens, "api/v8/xl-stores/options/addons-pinky-box", {
        "is_enterprise": False,
        "lang": "id",
        "package_option_code": package_option_code
    })

def get_intercept_page(tokens: dict, package_option_code: str):
    return _post(tokens, "misc/api/v8/utility/intercept-page", {
        "is_enterprise": False,
        "lang": "id",
        "package_option_code": package_option_code
    })

def get_payment_methods_option(tokens: dict, package_option_code: str, token_confirmation: str):
    return _post(tokens, "payments/api/v8/payment-methods-option", {
        "is_enterprise": False,
        "is_referral": False,
        "lang": "id",
        "payment_target": package_option_code,
        "payment_type": "FAMILY_HUB_MEMBER",
        "token_confirmation": token_confirmation
    })
