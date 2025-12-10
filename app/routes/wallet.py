from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.db.session import get_db
from app.deps.auth import require_permission, AuthContext
from app.schemas.wallet import (
    DepositRequest,
    DepositInitResponse,
    BalanceResponse,
    TransferRequest,
    TransferResponse,
    DepositStatusResponse,
)
from app.schemas.transaction import TransactionHistoryItem
from app.services.wallet import get_or_create_wallet_for_user, get_wallet_balance, perform_transfer
from app.services.paystack import initialize_deposit, verify_paystack_signature
from app.models.transaction import Transaction, TransactionStatus
from app.models.wallet import Wallet

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/deposit", response_model=DepositInitResponse)
async def deposit(
    body: DepositRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_permission("deposit")),
):
    print('WALLET W')
    wallet = get_or_create_wallet_for_user(db, auth.user.id)
    ref, auth_url = await initialize_deposit(
        db=db,
        wallet=wallet,
        amount=body.amount,
        customer_email=auth.user.email,
    )
    return DepositInitResponse(reference=ref, authorization_url=auth_url)


@router.post("/paystack/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    print('PAYSTACK WEBHOOK')
    body = await request.body()

    # 1. Validate signature
    verify_paystack_signature(request, body)

    payload = await request.json()  # FastAPI will parse from body again
    print('PAYSTACK WEBHOOK',payload)
    event = payload.get("event")
    data = payload.get("data", {})

    reference = data.get("reference")
    status_from_ps = data.get("status")  # "success", "failed", etc.
    amount_kobo = data.get("amount", 0)

    if not reference:
        raise HTTPException(status_code=400, detail="Missing reference")

    tx = db.query(Transaction).filter(Transaction.reference == reference).first()
    if not tx:
        # Optionally create a record or just ignore
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Idempotency: if already success, just ack
    if tx.status == TransactionStatus.success:
        return {"status": True}

    # Only credit on success (and maybe on specific event)
    if status_from_ps != "success":
        tx.status = TransactionStatus.failed
        db.commit()
        return {"status": True}

    # Convert amount from kobo to base
    amount = int(amount_kobo) // 100

    # Sanity: ensure amount matches the original
    if int(tx.amount) != amount:
        # you might log this mismatch
        pass

    # Credit wallet atomically
    wallet = db.query(Wallet).filter(Wallet.id == tx.wallet_id).with_for_update().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    from decimal import Decimal
    wallet.balance = wallet.balance + Decimal(amount)
    tx.status = TransactionStatus.success
    db.commit()

    return {"status": True}


@router.get("/deposit/{reference}/status", response_model=DepositStatusResponse)
async def deposit_status(
    reference: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_permission("read")),
):
    tx = db.query(Transaction).filter(Transaction.reference == reference).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return DepositStatusResponse(
        reference=tx.reference,
        status=tx.status.value,
        amount=int(tx.amount),
    )


@router.get("/balance", response_model=BalanceResponse)
async def balance(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_permission("read")),
):
    from app.models.wallet import Wallet

    wallet = db.query(Wallet).filter(Wallet.user_id == auth.user.id).first()
    if not wallet:
        # should not normally happen
        wallet = get_or_create_wallet_for_user(db, auth.user.id)

    return BalanceResponse(balance=int(wallet.balance))


@router.post("/transfer", response_model=TransferResponse)
async def transfer(
    body: TransferRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_permission("transfer")),
):
    from app.models.wallet import Wallet

    sender_wallet = db.query(Wallet).filter(Wallet.user_id == auth.user.id).first()
    if not sender_wallet:
        raise HTTPException(status_code=400, detail="Sender wallet not found")

    recipient_wallet = (
        db.query(Wallet).filter(Wallet.wallet_number == body.wallet_number).first()
    )
    if not recipient_wallet:
        raise HTTPException(status_code=404, detail="Recipient wallet not found")

    perform_transfer(db, sender_wallet, recipient_wallet, body.amount)

    return TransferResponse(status="success", message="Transfer completed")


@router.get("/transactions", response_model=list[TransactionHistoryItem])
async def transactions(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_permission("read")),
):
    from app.models.wallet import Wallet
    from app.models.transaction import Transaction

    wallet = db.query(Wallet).filter(Wallet.user_id == auth.user.id).first()
    if not wallet:
        return []

    txs = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return [
        TransactionHistoryItem(
            type=tx.type.value,
            amount=tx.amount,
            status=tx.status.value,
        )
        for tx in txs
    ]


