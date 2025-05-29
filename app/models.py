from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum, datetime

Base = declarative_base()

class InstrumentType(str, enum.Enum):
    STOCK = "stock"
    BOND = "bond"
    MEMECOIN = "memecoin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    token = Column(String, unique=True, index=True)

    balances = relationship("Balance", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(InstrumentType), nullable=False)
    is_listed = Column(Boolean, default=True)

class Balance(Base):
    __tablename__ = "balances"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    amount = Column(Numeric(20, 8), default=0)

    user = relationship("User", back_populates="balances")
    instrument = relationship("Instrument")

class OrderStatus(str, enum.Enum):
    NEW = "new"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELED = "canceled"

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"

class Side(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    side = Column(Enum(Side), nullable=False)
    price = Column(Numeric(20, 8), nullable=True)
    quantity = Column(Numeric(20, 8), nullable=False)
    filled = Column(Numeric(20, 8), default=0)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="orders")
    instrument = relationship("Instrument")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    buy_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sell_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    price = Column(Numeric(20,8), nullable=False)
    quantity = Column(Numeric(20,8), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    instrument = relationship("Instrument")
