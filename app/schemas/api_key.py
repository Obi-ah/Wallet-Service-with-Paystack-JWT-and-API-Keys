from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Literal
from uuid import UUID


PermissionLiteral = Literal["deposit", "transfer", "read"]
ExpiryLiteral = Literal["1H", "1D", "1M", "1Y"]


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., max_length=128)
    permissions: List[PermissionLiteral]
    expiry: ExpiryLiteral


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    expires_at: datetime


class ApiKeyRolloverRequest(BaseModel):
    expired_key_id: UUID
    expiry: ExpiryLiteral