"""
Safaricom Daraja B2C (Business to Customer) helpers — e.g. salary payouts to staff M-Pesa.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings


class MpesaConfigError(Exception):
    pass


class MpesaAPIError(Exception):
    pass


_KENYA_MSISDN = re.compile(r"^254[17]\d{8}$")


def normalize_mpesa_msisdn(raw: str) -> str:
    """Normalize Kenyan mobile numbers to 2547XXXXXXXX / 2541XXXXXXXX for Daraja PartyB."""
    if not raw:
        return ""
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) == 12 and digits.startswith("254") and digits[3] in "17":
        normalized = digits
    elif len(digits) == 10 and digits.startswith("0") and digits[1] in "17":
        normalized = "254" + digits[1:]
    elif len(digits) == 9 and digits[0] in "17":
        normalized = "254" + digits
    else:
        raise ValueError(
            "Use a valid Kenyan M-Pesa number (e.g. 0712345678 or 254712345678)."
        )
    if not _KENYA_MSISDN.match(normalized):
        raise ValueError(
            "Use a valid Kenyan M-Pesa number (e.g. 0712345678 or 254712345678)."
        )
    return normalized


def mpesa_amount_to_int(amount: Decimal) -> int:
    """B2C Amount is in whole KES."""
    n = int(amount.quantize(Decimal("1")))
    if n < 1:
        raise ValueError("Payout amount must be at least 1 KES.")
    return n


def _base_url() -> str:
    env = getattr(settings, "MPESA_ENV", "sandbox") or "sandbox"
    if str(env).lower() == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def assert_mpesa_b2c_configured() -> None:
    required = [
        ("MPESA_CONSUMER_KEY", getattr(settings, "MPESA_CONSUMER_KEY", "")),
        ("MPESA_CONSUMER_SECRET", getattr(settings, "MPESA_CONSUMER_SECRET", "")),
        ("MPESA_SHORTCODE", getattr(settings, "MPESA_SHORTCODE", "")),
        ("MPESA_INITIATOR_NAME", getattr(settings, "MPESA_INITIATOR_NAME", "")),
        ("MPESA_SECURITY_CREDENTIAL", getattr(settings, "MPESA_SECURITY_CREDENTIAL", "")),
        ("MPESA_B2C_RESULT_URL", getattr(settings, "MPESA_B2C_RESULT_URL", "")),
        ("MPESA_B2C_QUEUE_TIMEOUT_URL", getattr(settings, "MPESA_B2C_QUEUE_TIMEOUT_URL", "")),
    ]
    missing = [name for name, val in required if not (val and str(val).strip())]
    if missing:
        raise MpesaConfigError(
            "M-Pesa B2C is not configured. Set these in your environment: "
            + ", ".join(missing)
        )


def get_access_token() -> str:
    assert_mpesa_b2c_configured()
    base = _base_url()
    url = f"{base}/oauth/v1/generate?grant_type=client_credentials"
    key = settings.MPESA_CONSUMER_KEY
    secret = settings.MPESA_CONSUMER_SECRET
    resp = requests.get(url, auth=(key, secret), timeout=45)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise MpesaAPIError(f"OAuth response missing access_token: {data}")
    return token


def initiate_b2c_payment(
    *,
    phone: str,
    amount_kes: int,
    remarks: str,
) -> dict[str, Any]:
    """
    Call Daraja B2C Payment Request. Returns parsed JSON (includes ConversationID on success).
    """
    assert_mpesa_b2c_configured()
    token = get_access_token()
    base = _base_url()
    url = f"{base}/mpesa/b2c/v1/paymentrequest"
    command_id = getattr(settings, "MPESA_B2C_COMMAND_ID", "SalaryPayment")
    payload = {
        "InitiatorName": settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_SECURITY_CREDENTIAL,
        "CommandID": command_id,
        "Amount": str(amount_kes),
        "PartyA": str(settings.MPESA_SHORTCODE),
        "PartyB": phone,
        "Remarks": (remarks or "Wage payment")[:255],
        "QueueTimeOutURL": settings.MPESA_B2C_QUEUE_TIMEOUT_URL,
        "ResultURL": settings.MPESA_B2C_RESULT_URL,
        "Occasion": "",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=45)
    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise MpesaAPIError(f"Invalid JSON from Daraja (HTTP {resp.status_code})") from exc
    if resp.status_code >= 400:
        raise MpesaAPIError(f"Daraja HTTP {resp.status_code}: {data}")
    return data


def parse_b2c_result_body(body: dict[str, Any]) -> dict[str, Any]:
    """Flatten Daraja B2C result callback for storage and status updates."""
    result = body.get("Result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = None
    if not isinstance(result, dict):
        result = body

    out: dict[str, Any] = {
        "result_type": str(result.get("ResultType", "")),
        "result_code": result.get("ResultCode"),
        "result_desc": str(result.get("ResultDesc", "")),
        "conversation_id": str(result.get("ConversationID", "") or ""),
        "originator_conversation_id": str(result.get("OriginatorConversationID", "") or ""),
        "transaction_id": "",
        "receipt": "",
    }
    if out["result_code"] is not None:
        out["result_code_str"] = str(out["result_code"])

    params = result.get("ResultParameters") or {}
    param_list = params.get("ResultParameter") or []
    if isinstance(param_list, dict):
        param_list = [param_list]
    for item in param_list:
        if not isinstance(item, dict):
            continue
        key = item.get("Key")
        val = item.get("Value")
        if key == "TransactionReceipt":
            out["receipt"] = str(val or "")
        if key == "TransactionID":
            out["transaction_id"] = str(val or "")
    return out
