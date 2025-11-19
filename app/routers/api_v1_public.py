from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from decimal import Decimal
import uuid
import datetime

from app.database import get_db
from app.auth import create_token
from app.models import User, Instrument, Order, Trade, Side, OrderStatus
from app import schemas

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.post("/register", response_model=schemas.User)
async def register(data: schemas.NewUser, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Name taken")
    user = User(
        external_id=str(uuid.uuid4()),
        username=data.name,
        name=data.name,
        token=create_token(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return schemas.User(
        id=user.external_id,
        name=user.name,
        role=schemas.UserRole(user.role.value),
        api_key=user.token,
    )


@router.get("/instrument", response_model=List[schemas.Instrument])
async def list_instruments(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Instrument).where(Instrument.is_listed == True))
    instruments: List[Instrument] = res.scalars().all()
    return [schemas.Instrument(name=i.name, ticker=i.symbol) for i in instruments]


@router.get("/orderbook/{ticker}", response_model=schemas.L2OrderBook)
async def get_orderbook(
    ticker: str,
    limit: int = Query(10, le=25),
    db: AsyncSession = Depends(get_db)
):
    inst = (await db.execute(select(Instrument).where(Instrument.symbol == ticker))).scalar_one_or_none()
    if not inst or not inst.is_listed:
        raise HTTPException(404, "Instrument not found")
    asks = (await db.execute(
        select(Order).where(
            Order.instrument_id == inst.id,
            Order.side == Side.SELL,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        ).order_by(Order.price.asc()).limit(limit)
    )).scalars().all()
    bids = (await db.execute(
        select(Order).where(
            Order.instrument_id == inst.id,
            Order.side == Side.BUY,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        ).order_by(Order.price.desc()).limit(limit)
    )).scalars().all()

    def levelize(rows: List[Order]):
        return [
            schemas.Level(
                price=int(Decimal(o.price)),
                qty=int(Decimal(o.quantity) - Decimal(o.filled))
            )
            for o in rows
            if o.price is not None
        ]

    return schemas.L2OrderBook(
        bid_levels=levelize(bids),
        ask_levels=levelize(asks)
    )


@router.get("/transactions/{ticker}", response_model=List[schemas.Transaction])
async def get_transaction_history(
    ticker: str,
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    inst = (await db.execute(select(Instrument).where(Instrument.symbol == ticker))).scalar_one_or_none()
    if not inst:
        raise HTTPException(404, "Instrument not found")
    trades = (await db.execute(
        select(Trade)
        .where(Trade.instrument_id == inst.id)
        .order_by(Trade.timestamp.desc())
        .limit(limit)
    )).scalars().all()
    return [
        schemas.Transaction(
            ticker=ticker,
            amount=int(Decimal(t.quantity)),
            price=int(Decimal(t.price)),
            timestamp=t.timestamp,
        )
        for t in trades
    ]








