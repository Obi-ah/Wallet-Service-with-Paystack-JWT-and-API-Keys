import random
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from fastapi import HTTPException, status

from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus


def generate_wallet_number() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def get_or_create_wallet_for_user(db: Session, user_id) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if wallet:
        return wallet
    from app.services.wallet import generate_wallet_number
    wallet = Wallet(user_id=user_id, wallet_number=generate_wallet_number())
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def get_wallet_balance(db: Session, wallet: Wallet) -> int:
    # we store Numeric; convert to int
    return int(wallet.balance)


def perform_transfer(
    db: Session,
    sender_wallet: Wallet,
    recipient_wallet: Wallet,
    amount: int,
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")

    if sender_wallet.id == recipient_wallet.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to self")

    if sender_wallet.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )

    # Atomic operation
    from sqlalchemy.exc import IntegrityError

    try:
        # pessimistic, still simple: rely on single transaction
        sender_wallet.balance = sender_wallet.balance - amount
        recipient_wallet.balance = recipient_wallet.balance + amount

        # create transactions
        tx_out = Transaction(
            wallet_id=sender_wallet.id,
            type=TransactionType.transfer_out,
            status=TransactionStatus.success,
            amount=Decimal(amount),
            reference=f"TR_OUT_{sender_wallet.id.hex}_{datetime.utcnow().timestamp()}",
        )
        tx_in = Transaction(
            wallet_id=recipient_wallet.id,
            type=TransactionType.transfer_in,
            status=TransactionStatus.success,
            amount=Decimal(amount),
            reference=f"TR_IN_{recipient_wallet.id.hex}_{datetime.utcnow().timestamp()}",
        )

        db.add(tx_out)
        db.add(tx_in)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transfer failed")