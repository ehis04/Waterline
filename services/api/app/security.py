"""Tenant isolation and input sanitization security helpers."""

import re
from fastapi import Header, HTTPException

DEFAULT_DEMO_TENANT = "demo"

# Maps canonical portfolio keys to their owning tenant ID.
PORTFOLIO_TENANT_OWNERS: dict[str, str] = {
    "overlapping_etfs": DEFAULT_DEMO_TENANT,
    "uk_wrapper_split": DEFAULT_DEMO_TENANT,
    "student_starter": DEFAULT_DEMO_TENANT,
}

_TENANT_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def get_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> str:
    """Extract and validate tenant identifier from X-Tenant-ID header, defaulting to demo."""
    if x_tenant_id is None:
        return DEFAULT_DEMO_TENANT
    cleaned = x_tenant_id.strip()
    if not cleaned or not _TENANT_ID_RE.match(cleaned):
        raise HTTPException(status_code=403, detail="Invalid or unauthorized tenant identifier")
    return cleaned


def get_portfolio_owner(portfolio_key: str) -> str:
    """Return the owning tenant ID for a canonical portfolio key."""
    return PORTFOLIO_TENANT_OWNERS.get(portfolio_key, DEFAULT_DEMO_TENANT)


def verify_portfolio_tenant_access(portfolio_key: str, tenant_id: str) -> None:
    """Enforce tenant ownership on portfolio access, raising 403 on cross-tenant requests."""
    owner = get_portfolio_owner(portfolio_key)
    if tenant_id != owner:
        raise HTTPException(
            status_code=403,
            detail="Access denied: portfolio belongs to a different tenant",
        )


def is_csv_formula_injection(value: str) -> bool:
    """Return True if a CSV cell string begins with a spreadsheet formula trigger."""
    stripped = value.lstrip(" ")
    return value.startswith(_FORMULA_PREFIXES) or stripped.startswith(_FORMULA_PREFIXES)


def sanitize_csv_cell(value: str) -> str:
    """Neutralize potential CSV formula injection payloads by prefixing an apostrophe."""
    if is_csv_formula_injection(value):
        return f"'{value}"
    return value
