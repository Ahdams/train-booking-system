from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..dependencies import DbSession
from ..models import User
from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def to_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession):
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        nin=payload.nin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), user.is_admin)
    return TokenResponse(access_token=token, user=to_response(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive")

    token = create_access_token(str(user.id), user.is_admin)
    return TokenResponse(access_token=token, user=to_response(user))
