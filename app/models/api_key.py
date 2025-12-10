import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)

    key_hash = Column(String(128), nullable=False, unique=True)   # sha256(api_key)
    permissions = Column(String(256), nullable=False)  # "deposit,transfer,read"
    expires_at = Column(DateTime, nullable=False)

    revoked = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    @property
    def permissions_list(self) -> list[str]:
        return [p.strip() for p in self.permissions.split(",") if p.strip()]