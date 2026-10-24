import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.gemma import ConfigError, GemmaUnavailable, ask_gemma
from app.finance import calculate_net_returns, compare_mmfs
from app.mpesa import (
    MpesaConfigurationError,
    MpesaRequestError,
    initiate_stk_push,
    normalize_phone_number,
)

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"

# The Files API sniffs the type from the extension, so the temp file has to end
# in the right one. Only formats we have reason to trust are allowed through.
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_QUESTION_CHARS = 2000
DEMO_DATA_NOTICE = (
    "Illustrative demo data only; rates and withdrawal times are not live or "
    "verified. Confirm current terms, fees, and provider authorization before investing."
)
FINANCE_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "finance.txt"

app = FastAPI(title="Jenga student finance guide")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class FinanceRequest(BaseModel):
    principal: float = Field(ge=0)
    monthly_topup: float = Field(ge=0)
    duration_years: int = Field(ge=1, le=50)
    gross_rate: float = Field(default=10.5, ge=0, le=100)
    question: str = Field(default="", max_length=MAX_QUESTION_CHARS)


class MpesaStkRequest(BaseModel):
    phone_number: str = Field(min_length=9, max_length=20)
    amount_kes: int = Field(ge=1)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _build_finance_plan(request: FinanceRequest) -> dict:
    funds = compare_mmfs(int(request.principal))
    projection = calculate_net_returns(
        request.principal,
        request.monthly_topup,
        request.duration_years * 12,
        request.gross_rate,
    )
    return {
        "funds": funds,
        "projection": projection,
        "gross_rate": request.gross_rate,
        "duration_months": request.duration_years * 12,
        "data_notice": DEMO_DATA_NOTICE,
    }


@app.post("/api/finance/plan")
def finance_plan(request: FinanceRequest) -> dict:
    return _build_finance_plan(request)


@app.post("/api/mpesa/stk-push")
def mpesa_stk_push(request: MpesaStkRequest) -> dict:
    try:
        phone_number = normalize_phone_number(request.phone_number)
        return initiate_stk_push(phone_number, request.amount_kes)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except MpesaConfigurationError as exc:
        log.warning("M-Pesa sandbox is not configured: %s", exc)
        raise HTTPException(503, "M-Pesa sandbox is not configured yet.")
    except MpesaRequestError:
        log.exception("M-Pesa sandbox STK push failed")
        raise HTTPException(502, "Could not send the M-Pesa sandbox prompt.")


@app.post("/api/mpesa/callback")
def mpesa_callback(payload: dict) -> dict:
    try:
        result_code = payload["Body"]["stkCallback"]["ResultCode"]
    except (KeyError, TypeError):
        raise HTTPException(400, "Invalid M-Pesa callback payload.")
    if not isinstance(result_code, int):
        raise HTTPException(400, "Invalid M-Pesa callback result.")
    log.info("M-Pesa sandbox callback received with result code %d", result_code)
    return {"ResultCode": 0, "ResultDesc": "Callback received."}


@app.post("/api/finance/advice")
def finance_advice(request: FinanceRequest) -> dict:
    plan = _build_finance_plan(request)
    question = request.question.strip() or (
        f"I have KES {request.principal:,.0f} to invest today and can add "
        f"KES {request.monthly_topup:,.0f} every month. Which MMFs can I join, "
        f"and how much could I have in {request.duration_years} year(s)?"
    )
    prompt = (
        f"Student question: {question}\n\n"
        "Tool results from compare_mmfs and calculate_net_returns "
        "(treat these as the source of truth; do not alter the figures):\n"
        f"{plan}\n\n"
        "Explain the eligible demo funds and projection in plain language. "
        "Mention the 15% withholding tax, state that these are illustrative "
        "estimates rather than guarantees, and remind the student to verify "
        "current fund terms. Do not claim a fund is licensed."
    )
    try:
        answer = ask_gemma(
            prompt, system_prompt=FINANCE_PROMPT_PATH.read_text(encoding="utf-8").strip()
        )
    except GemmaUnavailable:
        raise HTTPException(503, "Gemma is busy right now. Please try again in a minute.")
    except ConfigError:
        log.exception("server misconfigured")
        raise HTTPException(500, "The server isn't configured correctly.")
    except Exception:
        log.exception("Gemma finance advice request failed")
        raise HTTPException(502, "The model rejected this request.")
    return {"answer": answer.text, "model": answer.model, "attempts": answer.attempts}


# A plain `def` (not async) on purpose: FastAPI runs it in a worker thread, and
# ask_gemma blocks on network calls and sleeps between retries. In an `async def`
# that would stall every other request.
@app.post("/api/ask")
def ask(
    question: str = Form(...),
    image: Optional[UploadFile] = File(None),
) -> dict:
    question = question.strip()
    if not question:
        raise HTTPException(400, "Please type a question.")
    if len(question) > MAX_QUESTION_CHARS:
        raise HTTPException(400, f"Question is too long (max {MAX_QUESTION_CHARS} characters).")

    # Browsers send an empty file part when nothing was chosen, so check the
    # filename rather than just `is not None`.
    has_image = image is not None and bool(image.filename)

    #error handling logic: GemmaUnavailable is a transient error
    # , ConfigError is a server misconfiguration, 
    # and any other exception is treated as a non-transient API error.
    try:
        if not has_image:
            answer = ask_gemma(question)
        else:
            suffix = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
            if suffix is None:
                raise HTTPException(415, "Please upload a JPEG, PNG or WebP image.")
            data = image.file.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(413, f"Image is too large (max {MAX_IMAGE_BYTES // 1024 // 1024} MB).")
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"upload{suffix}"
                path.write_bytes(data)
                answer = ask_gemma(question, path)
    except HTTPException:
        raise
    except GemmaUnavailable:
        raise HTTPException(503, "Gemma is busy right now. Please try again in a minute.")
    except ConfigError:
        log.exception("server misconfigured")
        raise HTTPException(500, "The server isn't configured correctly.")
    except Exception:
        # Non-transient API errors land here (bad key, rejected request). The
        # details go to the log, not to the browser.
        log.exception("Gemma request failed")
        raise HTTPException(502, "The model rejected this request.")

    return {"answer": answer.text, "model": answer.model, "attempts": answer.attempts}
