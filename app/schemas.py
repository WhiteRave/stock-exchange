from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models import OrderType, Side, OrderStatus, InstrumentType

class TokenResponse(BaseModel):
    token: str

class UserCreate(BaseModel):
    username: str
    password: str

class InstrumentIn(BaseModel):
    symbol: str
    name: str
    type: InstrumentType

class InstrumentOut(BaseModel):
    id: int
    symbol: str
    name: str
    type: InstrumentType
    is_listed: bool

class BalanceOut(BaseModel):
    instrument: str
    amount: float

class OrderCreate(BaseModel):
    instrument: str
    side: Side
    type: OrderType
    quantity: float
    price: Optional[float]

class OrderOut(BaseModel):
    id: int
    instrument: str
    side: Side
    type: OrderType
    quantity: float
    filled: float
    status: OrderStatus
    price: Optional[float]
    created_at: datetime

class OrderBookSide(BaseModel):
    price: float
    quantity: float

class OrderBookOut(BaseModel):
    asks: List[OrderBookSide]
    bids: List[OrderBookSide]

class Candle(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
