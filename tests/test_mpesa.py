import base64
import json

import pytest

from app import mpesa


@pytest.mark.parametrize(
    ("phone", "expected"),
    [
        ("0712 345 678", "254712345678"),
        ("+254 712-345-678", "254712345678"),
        ("254112345678", "254112345678"),
    ],
)
def test_normalize_phone_number(phone, expected):
    assert mpesa.normalize_phone_number(phone) == expected


@pytest.mark.parametrize("phone", ["12345", "071234567", "254912345678", ""])
def test_reject_invalid_phone_number(phone):
    with pytest.raises(ValueError, match="valid Kenyan mobile"):
        mpesa.normalize_phone_number(phone)


def test_initiate_stk_push_uses_sandbox_and_never_returns_credentials(monkeypatch):
    monkeypatch.setenv("MPESA_CONSUMER_KEY", "sandbox-key")
    monkeypatch.setenv("MPESA_CONSUMER_SECRET", "sandbox-secret")
    monkeypatch.setenv("MPESA_PASSKEY", "sandbox-passkey")
    monkeypatch.setenv("MPESA_SHORTCODE", "174379")
    monkeypatch.setenv("MPESA_CALLBACK_URL", "https://demo.example/api/mpesa/callback")
    requests = []
    responses = [
        {"access_token": "temporary-token"},
        {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_123",
            "CustomerMessage": "Prompt sent",
        },
    ]

    class FakeResponse:
        def __init__(self, body):
            self.body = json.dumps(body).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return self.body

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeResponse(responses.pop(0))

    monkeypatch.setattr(mpesa, "urlopen", fake_urlopen)
    result = mpesa.initiate_stk_push("0712345678", 10)

    assert len(requests) == 2
    token_request, token_timeout = requests[0]
    assert token_request.full_url.startswith(mpesa.SANDBOX_BASE_URL)
    assert token_timeout == 15
    assert token_request.get_header("Authorization") == "Basic " + base64.b64encode(
        b"sandbox-key:sandbox-secret"
    ).decode("ascii")

    stk_request, _ = requests[1]
    assert stk_request.full_url == (
        f"{mpesa.SANDBOX_BASE_URL}/mpesa/stkpush/v1/processrequest"
    )
    assert stk_request.get_header("Authorization") == "Bearer temporary-token"
    payload = json.loads(stk_request.data)
    assert payload["Amount"] == 10
    assert payload["PhoneNumber"] == "254712345678"
    assert payload["CallBackURL"] == "https://demo.example/api/mpesa/callback"
    assert result == {
        "checkout_request_id": "ws_CO_123",
        "customer_message": "Prompt sent",
    }
    assert "sandbox-secret" not in str(result)
    assert "sandbox-passkey" not in str(result)


def test_initiate_stk_push_accepts_existing_env_names(monkeypatch):
    monkeypatch.setenv("CONSUMER_KEY", "legacy-key")
    monkeypatch.setenv("CONSUMER_SECRET", "legacy-secret")
    monkeypatch.setenv("PASSKEY", "legacy-passkey")
    monkeypatch.setenv("SHORT_CODE", "174379")
    monkeypatch.setenv("CALLBACK_URL", "https://demo.example/callback")
    for name in (
        "MPESA_CONSUMER_KEY",
        "MPESA_CONSUMER_SECRET",
        "MPESA_PASSKEY",
        "MPESA_SHORTCODE",
        "MPESA_CALLBACK_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    class FakeResponse:
        def __init__(self, body):
            self.body = json.dumps(body).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return self.body

    responses = [
        {"access_token": "legacy-token"},
        {"ResponseCode": "0", "CheckoutRequestID": "legacy-checkout"},
    ]
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)
        return FakeResponse(responses.pop(0))

    monkeypatch.setattr(mpesa, "urlopen", fake_urlopen)
    result = mpesa.initiate_stk_push("0712345678", 10)
    assert len(calls) == 2
    assert calls[0].get_header("Authorization") == "Basic " + base64.b64encode(
        b"legacy-key:legacy-secret"
    ).decode("ascii")
    stk_payload = json.loads(calls[1].data)
    assert stk_payload["BusinessShortCode"] == "174379"
    assert stk_payload["CallBackURL"] == "https://demo.example/callback"
    assert result["checkout_request_id"] == "legacy-checkout"


def test_initiate_stk_push_requires_sandbox_configuration(monkeypatch):
    for name in (
        "MPESA_CONSUMER_KEY",
        "MPESA_CONSUMER_SECRET",
        "MPESA_PASSKEY",
        "MPESA_SHORTCODE",
        "MPESA_CALLBACK_URL",
        "CONSUMER_KEY",
        "CONSUMER_SECRET",
        "PASSKEY",
        "SHORT_CODE",
        "CALLBACK_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(mpesa.MpesaConfigurationError, match="MPESA_CONSUMER_KEY"):
        mpesa.initiate_stk_push("0712345678", 10)


def test_initiate_stk_push_rejects_zero_amount():
    with pytest.raises(ValueError, match="at least KES 1"):
        mpesa.initiate_stk_push("0712345678", 0)
