from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta  # install python-dateutil
from typing import List
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.core.security import generate_api_key

VALID_PERMISSIONS = {"deposit", "transfer", "read"}
VALID_EXPIRIES = {"1H", "1D", "1M", "1Y"}


def compute_expires_at(code: str) -> datetime:
    now = datetime.now(UTC)
    if code == "1H":
        return now + timedelta(hours=1)
    if code == "1D":
        return now + timedelta(days=1)
    if code == "1M":
        return now + relativedelta(months=1)
    if code == "1Y":
        return now + relativedelta(years=1)
    raise ValueError("Invalid expiry code")


def create_api_key(db: Session, user_id, name: str, permissions: List[str], expiry: str) -> tuple[str, ApiKey]:
    # validate perms
    if not set(permissions).issubset(VALID_PERMISSIONS):
        raise ValueError("Invalid permissions")

    # enforce max 5 active
    from datetime import datetime
    active_count = (
        db.query(ApiKey)
        .filter(
            ApiKey.user_id == user_id,
            ApiKey.revoked == False,
            ApiKey.expires_at > datetime.utcnow(),
        )
        .count()
    )
    if active_count >= 5:
        raise RuntimeError("Maximum number of active API keys reached")

    expires_at = compute_expires_at(expiry)
    plain, key_hash = generate_api_key()
    perms_str = ",".join(permissions)

    api_key = ApiKey(
        user_id=user_id,
        name=name,
        key_hash=key_hash,
        permissions=perms_str,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return plain, api_key