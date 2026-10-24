"""HTTP-layer tests. ask_gemma is stubbed, so these check validation and error
mapping only; the model call itself is covered in test_gemma.py."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.gemma import Answer, GemmaUnavailable

client = TestClient(main.app)


def post(question="what is this?", files=None):
    return client.post("/api/ask", data={"question": question}, files=files)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_index_page_is_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "Student money guide" in res.text


def test_blank_question_is_rejected():
    assert post("   ").status_code == 400


def test_non_image_upload_is_rejected():
    res = post(files={"image": ("notes.txt", b"hello", "text/plain")})
    assert res.status_code == 415


def test_oversized_image_is_rejected(monkeypatch):
    monkeypatch.setattr(main, "MAX_IMAGE_BYTES", 10)
    res = post(files={"image": ("big.png", b"x" * 11, "image/png")})
    assert res.status_code == 413


def test_text_only_question(monkeypatch):
    seen = {}

    def fake(prompt, image_path=None, **_):
        seen["args"] = (prompt, image_path)
        return Answer(text="an answer", model="m1", attempts=1)

    monkeypatch.setattr(main, "ask_gemma", fake)
    res = post("hello there")
    assert res.status_code == 200
    assert res.json() == {"answer": "an answer", "model": "m1", "attempts": 1}
    assert seen["args"] == ("hello there", None)


def test_finance_plan_returns_comparison_and_projection():
    res = client.post(
        "/api/finance/plan",
        json={
            "principal": 1000,
            "monthly_topup": 500,
            "duration_years": 1,
            "gross_rate": 10.5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert [fund["name"] for fund in data["funds"]] == [
        "Etica MMF",
        "Cytonn MMF",
        "Ziidi MMF",
    ]
    assert data["projection"]["total_contributions_kes"] == 7000
    assert data["projection"]["projected_net_kes"] > 7000
    assert "not live or verified" in data["data_notice"]


def test_finance_advice_uses_tool_results_and_finance_prompt(monkeypatch):
    seen = {}

    def fake(prompt, **kwargs):
        seen["prompt"] = prompt
        seen["system_prompt"] = kwargs["system_prompt"]
        return Answer(text="An educational estimate.", model="m1", attempts=1)

    monkeypatch.setattr(main, "ask_gemma", fake)
    res = client.post(
        "/api/finance/advice",
        json={
            "principal": 1000,
            "monthly_topup": 500,
            "duration_years": 1,
            "gross_rate": 10.5,
            "question": "Which funds fit?",
        },
    )
    assert res.status_code == 200
    assert res.json()["answer"] == "An educational estimate."
    assert "compare_mmfs" in seen["prompt"]
    assert "calculate_net_returns" in seen["prompt"]
    assert "15% withholding tax" in seen["system_prompt"]


def test_finance_plan_rejects_invalid_values():
    res = client.post(
        "/api/finance/plan",
        json={"principal": -1, "monthly_topup": 0, "duration_years": 1},
    )
    assert res.status_code == 422


def test_mpesa_stk_push_validates_and_normalizes_phone(monkeypatch):
    seen = {}

    def fake_push(phone_number, amount_kes):
        seen["request"] = (phone_number, amount_kes)
        return {"checkout_request_id": "checkout-1", "customer_message": "Prompt sent"}

    monkeypatch.setattr(main, "initiate_stk_push", fake_push)
    res = client.post(
        "/api/mpesa/stk-push",
        json={"phone_number": "+254 712-345-678", "amount_kes": 10},
    )
    assert res.status_code == 200
    assert seen["request"] == ("254712345678", 10)


def test_mpesa_stk_push_rejects_invalid_phone():
    res = client.post(
        "/api/mpesa/stk-push",
        json={"phone_number": "1234567890", "amount_kes": 10},
    )
    assert res.status_code == 400
    assert "valid Kenyan mobile" in res.json()["detail"]


def test_mpesa_stk_push_reports_missing_sandbox_config(monkeypatch):
    def unconfigured(*_):
        raise main.MpesaConfigurationError("MPESA_CONSUMER_KEY is not configured.")

    monkeypatch.setattr(main, "initiate_stk_push", unconfigured)
    res = client.post(
        "/api/mpesa/stk-push",
        json={"phone_number": "0712345678", "amount_kes": 10},
    )
    assert res.status_code == 503
    assert "not configured" in res.json()["detail"]


def test_mpesa_callback_acknowledges_valid_result():
    res = client.post(
        "/api/mpesa/callback",
        json={"Body": {"stkCallback": {"ResultCode": 1032}}},
    )
    assert res.status_code == 200
    assert res.json() == {"ResultCode": 0, "ResultDesc": "Callback received."}


def test_mpesa_callback_rejects_invalid_payload():
    res = client.post("/api/mpesa/callback", json={})
    assert res.status_code == 400


def test_image_is_written_with_the_right_extension(monkeypatch):
    seen = {}

    def fake(prompt, image_path=None, **_):
        # The temp file only exists during the call, so inspect it in here.
        seen["suffix"] = Path(image_path).suffix
        seen["bytes"] = Path(image_path).read_bytes()
        return Answer(text="ok", model="m1", attempts=1)

    monkeypatch.setattr(main, "ask_gemma", fake)
    res = post(files={"image": ("photo.png", b"png-bytes", "image/png")})
    assert res.status_code == 200
    assert seen == {"suffix": ".png", "bytes": b"png-bytes"}


def test_unavailable_maps_to_503(monkeypatch):
    def fake(*_, **__):
        raise GemmaUnavailable("nope")

    monkeypatch.setattr(main, "ask_gemma", fake)
    res = post()
    assert res.status_code == 503
    assert "busy" in res.json()["detail"]


def test_unexpected_error_maps_to_502_without_leaking_details(monkeypatch):
    def fake(*_, **__):
        raise ValueError("secret internal detail")

    monkeypatch.setattr(main, "ask_gemma", fake)
    res = post()
    assert res.status_code == 502
    assert "secret" not in res.text
