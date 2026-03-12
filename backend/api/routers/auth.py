from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_user_db
from api.email import send_verification_email
from api.limiter import limiter
from api.schemas import LoginRequest, LoginResponse, RegisterRequest, UserOut
from api.security import (
    create_access_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenBody(BaseModel):
    token: str


class EmailBody(BaseModel):
    email: str


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_user_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    token_str, expires = generate_verification_token()
    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        verification_token=token_str,
        verification_token_expires=expires,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    send_verification_email(user.email, user.username, token_str)
    return user


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_user_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email address not verified")

    token = create_access_token(user.id, user.email)
    return LoginResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/verify-email")
def verify_email(body: TokenBody, db: Session = Depends(get_user_db)):
    user = db.query(User).filter(User.verification_token == body.token).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    expires = user.verification_token_expires
    if expires is not None:
        # Make timezone-aware for comparison
        if expires.tzinfo is None:
            from datetime import timezone as _tz
            expires = expires.replace(tzinfo=_tz.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=400, detail="Verification token expired")

    user.is_email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
@limiter.limit("3/minute")
def resend_verification(request: Request, body: EmailBody, db: Session = Depends(get_user_db)):
    user = db.query(User).filter(User.email == body.email).first()
    # Always return 200 to avoid email enumeration
    if user is None or user.is_email_verified:
        return {"message": "If that email exists and is unverified, a new link has been sent"}

    token_str, expires = generate_verification_token()
    user.verification_token = token_str
    user.verification_token_expires = expires
    db.commit()

    send_verification_email(user.email, user.username, token_str)
    return {"message": "If that email exists and is unverified, a new link has been sent"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
