from pydantic import BaseModel, Field, RootModel
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum


# === Enums (match openapi.json) ===

class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


# === Shared/simple schemas ===

class Ok(BaseModel):
    success: Literal[True] = True


class CreateOrderResponse(BaseModel):
    success: Literal[True] = True
    order_id: str


# === Public user & auth ===

class NewUser(BaseModel):
    name: str = Field(min_length=3)


class User(BaseModel):
    id: str  # uuid4
    name: str
    role: UserRole
    api_key: str


# === Instrument & orderbook ===

class Instrument(BaseModel):
    name: str
    ticker: str


class Level(BaseModel):
    price: int
    qty: int


class L2OrderBook(BaseModel):
    bid_levels: List[Level]
    ask_levels: List[Level]


# === Orders & bodies ===

class LimitOrderBody(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field(ge=1)
    price: int = Field(gt=0)


class MarketOrderBody(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field(ge=1)


class LimitOrder(BaseModel):
    id: str  # uuid4
    status: OrderStatus
    user_id: str  # uuid4
    timestamp: datetime
    body: LimitOrderBody
    filled: int = 0


class MarketOrder(BaseModel):
    id: str  # uuid4
    status: OrderStatus
    user_id: str  # uuid4
    timestamp: datetime
    body: MarketOrderBody


# === Transactions / history ===

class Transaction(BaseModel):
    ticker: str
    amount: int
    price: int
    timestamp: datetime


# === Balances ===

class BalanceMap(RootModel[Dict[str, int]]):
    pass


# === Admin balance bodies ===

class Body_deposit_api_v1_admin_balance_deposit_post(BaseModel):
    user_id: str  # uuid
    ticker: str
    amount: int = Field(gt=0)


class Body_withdraw_api_v1_admin_balance_withdraw_post(BaseModel):
    user_id: str  # uuid
    ticker: str
    amount: int = Field(gt=0)


# === Validation errors (for completeness with openapi.json) ===

class ValidationError(BaseModel):
    loc: List[object]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    detail: Optional[List[ValidationError]] = None

