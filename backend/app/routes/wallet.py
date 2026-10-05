from decimal import Decimal
from secrets import token_hex
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..dependencies import DbSession, get_current_user
from ..models import User, Wallet, WalletTransaction
from ..schemas.wallet import WalletCreditRequest, WalletResponse, WalletTransactionResponse

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])


def get_or_create_wallet(db, user_id: int) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id).with_for_update())
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
        db.add(wallet)
        db.flush()
    return wallet


@router.get("", response_model=WalletResponse)
def get_wallet(db: DbSession, current_user: Annotated[User, Depends(get_current_user)]):
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == current_user.id))
    if wallet is None:
        wallet = Wallet(user_id=current_user.id, balance=Decimal("0.00"))
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


@router.get("/transactions", response_model=list[WalletTransactionResponse])
def transaction_history(db: DbSession, current_user: Annotated[User, Depends(get_current_user)]):
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == current_user.id))
    if wallet is None:
        return []
    return db.scalars(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
    ).all()


@router.post("/credit", response_model=WalletTransactionResponse, status_code=status.HTTP_201_CREATED)
def credit_wallet(
    payload: WalletCreditRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
):
    wallet = get_or_create_wallet(db, current_user.id)
    existing = db.scalar(select(WalletTransaction).where(WalletTransaction.reference == payload.idempotency_key))
    if existing:
        return existing

    wallet.balance += payload.amount
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="credit",
        amount=payload.amount,
        reference=payload.idempotency_key,
        description=payload.description,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
