"""Minimal Daraja sandbox STK Push integration."""

import base64
import json
import os
import re
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"


class MpesaConfigurationError(RuntimeError):
    """The app is missing required Daraja sandbox configuration."""


class MpesaRequestError(RuntimeError):
    """Daraja rejected a request or could not be reached."""


def _required_setting(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise MpesaConfigurationError(f"{' or '.join(names)} is not configured.")


def normalize_phone_number(phone_number: str) -> str:
    """Normalize Kenyan mobile numbers to Daraja's 2547... format."""
    compact = re.sub(r"[\s-]", "", phone_number)
    if compact.startswith("+"):
        compact = compact[1:]
    if compact.startswith("0"):
        compact = "254" + compact[1:]
    if not re.fullmatch(r"254[17]\d{8}", compact):
        raise ValueError("Enter a valid Kenyan mobile number, such as 0712345678.")
    return compact


def _post_json(url: str, payload: dict, *, headers: dict | None = None) -> dict:
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read()
    except HTTPError as exc:
        raise MpesaRequestError(f"Daraja returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise MpesaRequestError("Could not reach the Daraja sandbox.") from exc
    try:
        result = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MpesaRequestError("Daraja returned an unreadable response.") from exc
    if not isinstance(result, dict):
        raise MpesaRequestError("Daraja returned an unexpected response.")
    return result


def initiate_stk_push(phone_number: str, amount_kes: int) -> dict[str, str]:
    """Ask a phone to approve a one-time sandbox payment; does not verify payment."""
    if amount_kes < 1:
        raise ValueError("Payment amount must be at least KES 1.")

    consumer_key = _required_setting("MPESA_CONSUMER_KEY", "CONSUMER_KEY")
    consumer_secret = _required_setting("MPESA_CONSUMER_SECRET", "CONSUMER_SECRET")
    passkey = _required_setting("MPESA_PASSKEY", "PASSKEY")
    shortcode = _required_setting("MPESA_SHORTCODE", "SHORT_CODE")
    callback_url = _required_setting("MPESA_CALLBACK_URL", "CALLBACK_URL")
    phone = normalize_phone_number(phone_number)

    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode("utf-8")
    ).decode("ascii")
    token_url = (
        f"{SANDBOX_BASE_URL}/oauth/v1/generate?"
        f"{urlencode({'grant_type': 'client_credentials'})}"
    )
    token_request = Request(token_url, headers={"Authorization": f"Basic {credentials}"})
    try:
        with urlopen(token_request, timeout=15) as response:
            token_body = json.loads(response.read())
    except HTTPError as exc:
        raise MpesaRequestError(f"Daraja authentication returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise MpesaRequestError("Could not reach Daraja authentication.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MpesaRequestError("Daraja authentication returned an unreadable response.") from exc
    if not isinstance(token_body, dict) or not token_body.get("access_token"):
        raise MpesaRequestError("Daraja did not return an access token.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode("utf-8")
    ).decode("ascii")
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount_kes,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "JengaAdvisor",
        "TransactionDesc": "Jenga demo",
    }
    result = _post_json(
        f"{SANDBOX_BASE_URL}/mpesa/stkpush/v1/processrequest",
        payload,
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )
    if str(result.get("ResponseCode")) != "0":
        message = result.get("ResponseDescription") or "Daraja did not accept the request."
        raise MpesaRequestError(str(message))
    return {
        "checkout_request_id": str(result.get("CheckoutRequestID", "")),
        "customer_message": str(
            result.get("CustomerMessage")
            or "Check your phone and approve the prompt if you want to pay."
        ),
    }
