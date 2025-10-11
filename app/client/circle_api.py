import os
import requests
import uuid
import json
from datetime import datetime, timezone
from app.client.encrypt import decrypt_xdata
from app.config.theme_config import get_theme

# Ambil dari .env
BASE_API_URL = os.getenv("BASE_API_URL")
API_KEY = os.getenv("API_KEY")
UA = os.getenv("UA")

# ====================
# Helper Signature & Timestamp
# ====================

def java_like_timestamp(now: datetime) -> str:
    ms2 = f"{int(now.microsecond / 10000):02d}"
    tz = now.strftime("%z")
    tz_colon = tz[:-2] + ":" + tz[-2:] if tz else "+00:00"
    return now.strftime(f"%Y-%m-%dT%H:%M:%S.{ms2}") + tz_colon

def get_x_signature_circle(package_code: str, token_confirmation: str, path: str, method: str, timestamp: int) -> str:
    SERVER_URL = "https://flask-poin.onrender.com/get-signature-point"
    payload = {
        "package_code": package_code,
        "token_confirmation": token_confirmation,
        "path": path,
        "method": method,
        "timestamp": timestamp,
    }
    response = requests.post(SERVER_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    if "signature" not in data:
        raise ValueError(f"Invalid response: {data}")
    return data["signature"]

def build_headers(tokens: dict, sig_time_sec: int, x_sig: str, x_requested_at: datetime) -> dict:
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

def post_circle(tokens: dict, path: str, payload: dict, package_code: str = "", token_confirmation: str = "", method: str = "POST", decrypt=True):
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    sig_time_sec = timestamp // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    x_sig = get_x_signature_circle(package_code, token_confirmation, path, method, timestamp)

    headers = build_headers(tokens, sig_time_sec, x_sig, x_requested_at)
    url = f"{BASE_API_URL}/{path}"
    resp = requests.post(url, headers=headers, json=payload, timeout=30)

    try:
        return decrypt_xdata(resp.json()) if decrypt else resp.json()
    except Exception:
        return resp.json()

# ====================
# XL Circle API Client
# ====================

def validate_member(tokens: dict, msisdn: str):
    path = "family-hub/api/v8/members/validate"
    payload = {
        "lang": "id",
        "is_enterprise": False,
        "msisdn": msisdn
    }
    return post_circle(tokens, path, payload, package_code=msisdn, token_confirmation="validate")

def check_group_status(tokens: dict, msisdn: str):
    return validate_member(tokens, msisdn)

def get_group_info(tokens: dict, group_id: str):
    path = "family-hub/api/v8/members/info"
    payload = {
        "lang": "id",
        "is_enterprise": False,
        "group_id": group_id
    }
    return post_circle(tokens, path, payload, package_code=group_id, token_confirmation="info")

def get_spending_tracker(tokens: dict, family_id: str, parent_subs_id: str):
    path = "gamification/api/v8/family-hub/spending-tracker"
    payload = {
        "lang": "id",
        "is_enterprise": False,
        "family_id": family_id,
        "parent_subs_id": parent_subs_id
    }
    return post_circle(tokens, path, payload, package_code=family_id, token_confirmation=parent_subs_id)

def get_bonus_list(tokens: dict, family_id: str, parent_subs_id: str):
    path = "gamification/api/v8/family-hub/bonus/list"
    payload = {
        "lang": "id",
        "is_enterprise": False,
        "family_id": family_id,
        "parent_subs_id": parent_subs_id
    }
    return post_circle(tokens, path, payload, package_code=family_id, token_confirmation=parent_subs_id)

def get_package_detail_circle(tokens: dict, package_option_code: str):
    path = "api/v8/xl-stores/options/detail"
    payload = {
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
    }
    return post_circle(tokens, path, payload, package_code=package_option_code, token_confirmation="detail")

def get_addons_circle(tokens: dict, package_option_code: str):
    path = "api/v8/xl-stores/options/addons-pinky-box"
    payload = {
        "is_enterprise": False,
        "lang": "id",
        "package_option_code": package_option_code
    }
    return post_circle(tokens, path, payload, package_code=package_option_code, token_confirmation="addons")

def get_intercept_page(tokens: dict, package_option_code: str):
    path = "misc/api/v8/utility/intercept-page"
    payload = {
        "is_enterprise": False,
        "lang": "id",
        "package_option_code": package_option_code
    }
    return post_circle(tokens, path, payload, package_code=package_option_code, token_confirmation="intercept")

def get_payment_methods_option(tokens: dict, package_option_code: str, token_confirmation: str):
    path = "payments/api/v8/payment-methods-option"
    payload = {
        "is_enterprise": False,
        "is_referral": False,
        "lang": "id",
        "payment_target": package_option_code,
        "payment_type": "FAMILY_HUB_MEMBER",
        "token_confirmation": token_confirmation
    }
    return post_circle(tokens, path, payload, package_code=package_option_code, token_confirmation=token_confirmation)
