from fastapi import Depends, Header, HTTPException, status
from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.security import decode_access_token, hash_api_key
from app.db.session import get_db
from app.models.user import User
from app.models.api_key import ApiKey


class AuthContext:
    def __init__(self, user: User, via: str, api_key: Optional[ApiKey] = None,) -> None:
        self.user = user
        self.via = via
        self.api_key = api_key

    @property
    def permissions(self) -> List[str]:
        if not self.api_key:
            # JWT user: full access
            return ["deposit", "transfer", "read"]
        return self.api_key.permissions_list


async def get_auth_context(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None, convert_underscores=False),
) -> AuthContext:
    if x_api_key:
        # API key auth
        key_hash = hash_api_key(x_api_key)
        api_key = (
            db.query(ApiKey)
            .filter(ApiKey.key_hash == key_hash, ApiKey.revoked == False)
            .first()
        )
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if api_key.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=401, detail="Expired API key")

        user = db.query(User).filter(User.id == api_key.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found for API key")

        return AuthContext(user=user, via="api_key", api_key=api_key)

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid JWT")

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid JWT payload")

        user = db.query(User).filter(User.id == UUID(sub)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return AuthContext(user=user, via="jwt")

    raise HTTPException(status_code=401, detail="Authentication required")


def require_permission(permission: str):
    async def _inner(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        # JWT user has full permissions by spec
        if auth.via == "api_key" and permission not in auth.permissions:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return auth

    return _inner