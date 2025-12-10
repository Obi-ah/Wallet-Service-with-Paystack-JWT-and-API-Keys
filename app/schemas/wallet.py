from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from uuid import UUID


class DepositRequest(BaseModel):
    amount: int = Field(..., gt=0)  # in base currency units (e.g. Naira)


class DepositInitResponse(BaseModel):
    reference: str
    authorization_url: str


class DepositStatusResponse(BaseModel):
    reference: str
    status: Literal["success", "failed", "pending"]
    amount: int


class BalanceResponse(BaseModel):
    balance: int


class TransferRequest(BaseModel):
    wallet_number: str
    amount: int = Field(..., gt=0)


class TransferResponse(BaseModel):
    status: str
    message: str