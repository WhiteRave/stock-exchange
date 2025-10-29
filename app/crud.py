from sqlalchemy import select, update, delete, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Instrument, Balance, Order, Trade,
    OrderType, OrderStatus, Side, InstrumentType
)
from decimal import Decimal
import datetime
from typing import List, Optional, Dict


# Instruments
async def create_instrument(db: AsyncSession, symbol: str, name: str, instrument_type: InstrumentType) -> Instrument:
    inst = Instrument(symbol=symbol, name=name, type=instrument_type)
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return inst

async def list_instruments(db: AsyncSession, listed_only: bool = True) -> List[Instrument]:
    q = select(Instrument)
    if listed_only:
        q = q.where(Instrument.is_listed == True)
    res = await db.execute(q)
    return res.scalars().all()

async def get_instrument_by_symbol(db: AsyncSession, symbol: str) -> Optional[Instrument]:
    res = await db.execute(select(Instrument).where(Instrument.symbol == symbol))
    return res.scalar_one_or_none()

async def delist_instrument(db: AsyncSession, instrument_id: int) -> None:
    await db.execute(
        update(Instrument)
        .where(Instrument.id == instrument_id)
        .values(is_listed=False)
    )
    await db.commit()

# Balances
async def get_balances(db: AsyncSession, user_id: int) -> List[Balance]:
    res = await db.execute(select(Balance).where(Balance.user_id == user_id))
    return res.scalars().all()

async def adjust_balance(db: AsyncSession, user_id: int, instrument_id: int, delta: Decimal) -> Balance:
    res = await db.execute(
        select(Balance).where(
            Balance.user_id == user_id,
            Balance.instrument_id == instrument_id
        )
    )
    bal = res.scalar_one_or_none()
    if not bal:
        bal = Balance(user_id=user_id, instrument_id=instrument_id, amount=delta)
        db.add(bal)
    else:
        bal.amount += delta
    await db.commit()
    await db.refresh(bal)
    return bal

# Orders
async def place_order(
    db: AsyncSession,
    user_id: int,
    instrument_id: int,
    order_type: OrderType,
    side: Side,
    quantity: Decimal,
    price: Optional[Decimal] = None
) -> Order:
    order = Order(
        user_id=user_id,
        instrument_id=instrument_id,
        type=order_type,
        side=side,
        quantity=quantity,
        price=price
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order

async def cancel_order(db: AsyncSession, user_id: int, order_id: int) -> Optional[Order]:
    res = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        )
    )
    order = res.scalar_one_or_none()
    if not order:
        return None
    order.status = OrderStatus.CANCELED
    await db.commit()
    await db.refresh(order)
    return order

async def get_order(db: AsyncSession, user_id: int, order_id: int) -> Optional[Order]:
    res = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id
        )
    )
    return res.scalar_one_or_none()

async def list_active_orders(db: AsyncSession, user_id: int) -> List[Order]:
    res = await db.execute(
        select(Order).where(
            Order.user_id == user_id,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        )
    )
    return res.scalars().all()

async def get_order_book(db: AsyncSession, instrument_id: int, limit: int = 50) -> Dict[str, List[Order]]:
    asks = (await db.execute(
        select(Order)
        .where(
            Order.instrument_id == instrument_id,
            Order.side == Side.SELL,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        )
        .order_by(asc(Order.price))
        .limit(limit)
    )).scalars().all()

    bids = (await db.execute(
        select(Order)
        .where(
            Order.instrument_id == instrument_id,
            Order.side == Side.BUY,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        )
        .order_by(desc(Order.price))
        .limit(limit)
    )).scalars().all()

    return {"asks": asks, "bids": bids}

# History
async def get_trades(
    db: AsyncSession, instrument_id: int,
    start_time: datetime.datetime = None,
    end_time: datetime.datetime = None,
    limit: int = 100
) -> List[Trade]:
    q = select(Trade).where(Trade.instrument_id == instrument_id)
    if start_time:
        q = q.where(Trade.timestamp >= start_time)
    if end_time:
        q = q.where(Trade.timestamp <= end_time)
    q = q.order_by(desc(Trade.timestamp)).limit(limit)
    res = await db.execute(q)
    return res.scalars().all()

async def get_candles(
    db: AsyncSession, instrument_id: int,
    interval_min: int,
    start_time: datetime.datetime,
    end_time: datetime.datetime
) -> List[dict]:
    trades = await get_trades(db, instrument_id, start_time, end_time, limit=10000)
    buckets = {}
    for t in trades:
        ts = t.timestamp.replace(second=0, microsecond=0)
        minutes = (ts.minute // interval_min) * interval_min
        bucket_ts = ts.replace(minute=minutes)
        buckets.setdefault(bucket_ts, []).append(t)
    candles = []
    for ts, lst in sorted(buckets.items()):
        prices = [float(t.price) for t in lst]
        qtys   = [float(t.quantity) for t in lst]
        candles.append({
            "ts": ts,
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "volume": sum(qtys)
        })
    return candles
