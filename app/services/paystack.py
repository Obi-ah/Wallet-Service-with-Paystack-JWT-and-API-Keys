import hmac
import hashlib
import httpx
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from app.core.config import settings
from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus


async def initialize_deposit(
    db: Session,
    wallet: Wallet,
    amount: int,
    customer_email: str,
) -> tuple[str, str]:
    """
    amount is in base unit (e.g. Naira). Paystack expects kobo.
    """
    reference = f"DEP_{wallet.id.hex}_{int(datetime.utcnow().timestamp())}"

    # Create pending transaction
    tx = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.deposit,
        status=TransactionStatus.pending,
        amount=Decimal(amount),
        reference=reference,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    payload = {
        "email": customer_email,
        "amount": amount * 100,  # to kobo
        "reference": reference,
        "callback_url": "",  # optional
    }

    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.PAYSTACK_BASE_URL}/transaction/initialize", json=payload, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to initialize Paystack transaction")

    data = resp.json()["data"]
    return reference, data["authorization_url"]


def verify_paystack_signature(request: Request, body: bytes) -> None:
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Paystack signature")

    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        body,
        hashlib.sha512,
    ).hexdigest()

    if computed != signature:
        raise HTTPException(status_code=400, detail="Invalid Paystack signature")