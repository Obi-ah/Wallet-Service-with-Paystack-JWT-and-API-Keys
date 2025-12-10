from pydantic import BaseModel
from typing import Literal
from decimal import Decimal


class TransactionHistoryItem(BaseModel):
    type: Literal["deposit", "transfer_in", "transfer_out"]
    amount: Decimal
    status: Literal["success", "failed", "pending"]