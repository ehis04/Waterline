"""Receipt verification endpoint."""

from fastapi import APIRouter
from app.contracts import ReceiptVerifyRequest, ReceiptVerifyResponse
from dag.receipt import verify_receipt_integrity

router = APIRouter(prefix="/v1/receipts", tags=["Receipts"])


@router.post("/verify", response_model=ReceiptVerifyResponse)
def verify_receipt(req: ReceiptVerifyRequest) -> ReceiptVerifyResponse:
    """Verify cryptographic integrity and canonical RFC 8785 hash of a calculation receipt."""
    receipt = req.receipt
    run_id = receipt.get("run_id", "unknown")
    integrity = receipt.get("integrity", {})
    recorded_sha = integrity.get("receipt_sha256", "")

    if not recorded_sha:
        return ReceiptVerifyResponse(
            valid=False,
            run_id=run_id,
            receipt_sha256="",
            reason="Missing integrity.receipt_sha256 digest in receipt document",
        )

    is_valid = verify_receipt_integrity(receipt)
    return ReceiptVerifyResponse(
        valid=is_valid,
        run_id=run_id,
        receipt_sha256=recorded_sha,
        reason=None if is_valid else "Hash mismatch: Canonical RFC 8785 representation does not match recorded SHA-256",
    )
