from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from app.db.session import get_db
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyRolloverRequest
from app.deps.auth import AuthContext, get_auth_context
from app.services.api_keys import create_api_key, compute_expires_at
from app.models.api_key import ApiKey

router = APIRouter(prefix="/keys", tags=["api_keys"])


@router.post("/create", response_model=ApiKeyCreateResponse)
async def create_key(
    body: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    try:
        plain, api_key = create_api_key(
            db=db,
            user_id=auth.user.id,
            name=body.name,
            permissions=body.permissions,
            expiry=body.expiry,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiKeyCreateResponse(api_key=plain, expires_at=api_key.expires_at)


@router.post("/rollover", response_model=ApiKeyCreateResponse)
async def rollover_key(
    body: ApiKeyRolloverRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == body.expired_key_id, ApiKey.user_id == auth.user.id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if api_key.expires_at > datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Key is not expired")

    # reuse permissions
    permissions = api_key.permissions_list

    try:
        plain, new_key = create_api_key(
            db=db,
            user_id=auth.user.id,
            name=api_key.name,
            permissions=permissions,
            expiry=body.expiry,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiKeyCreateResponse(api_key=plain, expires_at=new_key.expires_at)