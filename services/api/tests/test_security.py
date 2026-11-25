"""Security tests: log redaction, cross-tenant isolation, and CSV injection sanitization."""

import io
import logging
from fastapi.testclient import TestClient
import pytest

from app.logging_utils import REDACTED, RedactingFilter, redact_sensitive_data, redact_text
from app.main import app
from app.security import PORTFOLIO_TENANT_OWNERS, is_csv_formula_injection, sanitize_csv_cell

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Structured Log Redaction Tests
# ---------------------------------------------------------------------------


def test_redact_sensitive_data_dict_fields():
    payload = {
        "Authorization": "Bearer super_secret_jwt_token",
        "api_key": "wl_live_abc123",
        "token": "tok_999888",
        "email": "investor@example.com",
        "account_number": "DE89370400440532013000",
        "portfolio_id": "overlapping_etfs",
        "nested": {
            "Token": "nested_tok",
            "EMAIL": "nested@example.org",
            "safe_metric": 42,
        },
    }
    redacted = redact_sensitive_data(payload)
    assert redacted["Authorization"] == REDACTED
    assert redacted["api_key"] == REDACTED
    assert redacted["token"] == REDACTED
    assert redacted["email"] == REDACTED
    assert redacted["account_number"] == REDACTED
    assert redacted["portfolio_id"] == "overlapping_etfs"
    assert redacted["nested"]["Token"] == REDACTED
    assert redacted["nested"]["EMAIL"] == REDACTED
    assert redacted["nested"]["safe_metric"] == 42


def test_redact_text_inline_patterns():
    raw = (
        "Request failed Authorization: Bearer my.jwt.token "
        "api_key=secret123 token=tok_abc email=alice@example.com "
        "account_number=ACC-998877"
    )
    masked = redact_text(raw)
    assert "my.jwt.token" not in masked
    assert "secret123" not in masked
    assert "tok_abc" not in masked
    assert "alice@example.com" not in masked
    assert "ACC-998877" not in masked
    assert masked.count(REDACTED) == 5


def test_redacting_filter_scrubs_log_records():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    handler.addFilter(RedactingFilter())

    logger = logging.getLogger("waterline.test_redaction")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    logger.propagate = False

    logger.info(
        "Auth header Authorization: Bearer abc.def.ghi api_key=key_123 token=tok_456 "
        "for user bob@example.com account_number=1234567890",
        extra={
            "email": "bob@example.com",
            "api_key": "key_123",
            "account_number": "1234567890",
        },
    )

    output = stream.getvalue()
    assert "abc.def.ghi" not in output
    assert "key_123" not in output
    assert "tok_456" not in output
    assert "bob@example.com" not in output
    assert "1234567890" not in output
    assert REDACTED in output


# ---------------------------------------------------------------------------
# 2. Cross-Tenant Isolation Harness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/v1/portfolios/overlapping_etfs", None),
        ("GET", "/v1/portfolios/overlapping_etfs/xray", None),
        ("POST", "/v1/runs/risk", {"portfolio_id": "overlapping_etfs", "confidence": 0.95}),
        (
            "POST",
            "/v1/runs/scenario",
            {"portfolio_id": "overlapping_etfs", "shocks": []},
        ),
        (
            "POST",
            "/v1/runs/breaking-point",
            {"portfolio_id": "overlapping_etfs", "loss_threshold": 0.15},
        ),
    ],
)
def test_cross_tenant_access_rejected_with_error_response(method, path, body):
    res = client.request(
        method,
        path,
        json=body,
        headers={"X-Tenant-ID": "tenant-unauthorized"},
    )
    assert res.status_code == 403
    err = res.json()
    assert err["code"] == "HTTP_403"
    assert "request_id" in err
    assert "positions" not in err
    assert "ZZET" not in res.text


def test_list_portfolios_filters_out_other_tenants_holdings():
    res = client.get("/v1/portfolios", headers={"X-Tenant-ID": "tenant-other"})
    assert res.status_code == 200
    assert res.json() == []


def test_invalid_tenant_header_rejected():
    res = client.get("/v1/portfolios", headers={"X-Tenant-ID": "   "})
    assert res.status_code == 403
    err = res.json()
    assert err["code"] == "HTTP_403"


def test_custom_tenant_owner_isolation(monkeypatch):
    monkeypatch.setitem(PORTFOLIO_TENANT_OWNERS, "student_starter", "tenant-a")

    # Owner tenant-a succeeds
    ok_res = client.get("/v1/portfolios/student_starter", headers={"X-Tenant-ID": "tenant-a"})
    assert ok_res.status_code == 200
    assert ok_res.json()["portfolio_id"] == "student_starter"

    # Cross-tenant tenant-b is denied without leaking holdings
    denied_res = client.get("/v1/portfolios/student_starter", headers={"X-Tenant-ID": "tenant-b"})
    assert denied_res.status_code == 403
    assert denied_res.json()["code"] == "HTTP_403"
    assert "positions" not in denied_res.json()


# ---------------------------------------------------------------------------
# 3. CSV Formula Injection Sanitizer Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        "=CMD|' /C calc'!A0",
        "+1+1",
        "-1+1",
        "@SUM(1+1)*cmd|' /C calc'!A0",
        "\t=HYPERLINK(\"http://evil.example\")",
        "\r=1+1",
        "  =1+1",
    ],
)
def test_csv_formula_injection_detected_and_sanitized(payload):
    assert is_csv_formula_injection(payload) is True
    sanitized = sanitize_csv_cell(payload)
    assert sanitized.startswith("'")
    assert sanitized == f"'{payload}"


@pytest.mark.parametrize(
    "safe_value",
    [
        "ZZET00000017",
        "Global Core Equity UCITS ETF",
        "100.50",
        "EUR",
        "",
    ],
)
def test_csv_safe_values_unchanged(safe_value):
    assert is_csv_formula_injection(safe_value) is False
    assert sanitize_csv_cell(safe_value) == safe_value
