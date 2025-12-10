from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import uuid4

from app.db.session import get_db

from app.schemas.auth import JWTToken
from app.services.google_auth import build_google_auth_url
from app.services.auth_service import login_with_google

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login():
    state = str(uuid4())
    url = build_google_auth_url(state)
    return RedirectResponse(url)


@router.get("/google/callback", response_model=JWTToken)
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
):
    jwt_token = await login_with_google(
        code=code,
        state=state,
        request=request,
        db=db,
    )
    print('JWT_TOKEN', jwt_token)
    return JWTToken(access_token=jwt_token)