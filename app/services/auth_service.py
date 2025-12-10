from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.security import create_access_token
from app.models.user import User
from app.models.wallet import Wallet
from app.services.google_auth import (
    exchange_code_for_tokens,
    fetch_google_userinfo,
)
from app.services.wallet import generate_wallet_number


async def login_with_google(
    code: str,
    state: str,
    request: Request,
    db: Session,
) -> str:
    """
    Full Google login flow:
    - validate state (if you’re storing it)
    - exchange code for tokens
    - fetch userinfo
    - upsert user
    - ensure wallet
    - issue JWT
    """
    # OPTIONAL but recommended: validate state
    # stored_state = request.cookies.get("oauth_state")
    # if not stored_state or stored_state != state:
    #     raise HTTPException(status_code=400, detail="Invalid OAuth state")

    tokens = await exchange_code_for_tokens(code)
    access_token = tokens["access_token"]
    userinfo = await fetch_google_userinfo(access_token)

    google_sub = userinfo["sub"]
    email = userinfo["email"]
    full_name = userinfo.get("name")

    user = db.query(User).filter(User.google_sub == google_sub).first()

    if not user:
        user = User(google_sub=google_sub, email=email, full_name=full_name)
        db.add(user)
        db.flush()  # get user.id

        wallet = Wallet(user_id=user.id, wallet_number=generate_wallet_number())
        db.add(wallet)

        db.commit()
        db.refresh(user)
    else:
        db.commit()

    jwt_token = create_access_token(str(user.id))
    return jwt_token