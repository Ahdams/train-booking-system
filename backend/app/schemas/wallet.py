from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    balance: Decimal


class WalletTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: Decimal
    reference: str
    description: str
    booking_id: int | None
    created_at: datetime


class WalletCreditRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    idempotency_key: str = Field(min_length=8, max_length=80)
    description: str = Field(default="Wallet credit", max_length=255)
