from fastapi import APIRouter, Depends, HTTPException, Query
from decimal import Decimal
from typing import List
import datetime

from app.auth import get_current_user
from app.database import get_db
from app import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/trade",
    tags=["trade"]
)

@router.get("/balances", response_model=List[schemas.BalanceOut])
async def read_balances(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    bals = await crud.get_balances(db, user.id)
    return [
        schemas.BalanceOut(
            instrument=b.instrument.symbol,
            amount=float(b.amount)
        )
        for b in bals
    ]

@router.post("/orders", response_model=schemas.OrderOut)
async def create_order(
    o: schemas.OrderCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    inst = await crud.get_instrument_by_symbol(db, o.instrument)
    if not inst or not inst.is_listed:
        raise HTTPException(404, "Instrument not found or delisted")
    order = await crud.place_order(
        db, user.id, inst.id,
        o.type, o.side,
        Decimal(o.quantity),
        Decimal(o.price) if o.price else None
    )
    return schemas.OrderOut(
        id=order.id,
        instrument=inst.symbol,
        side=order.side,
        type=order.type,
        quantity=float(order.quantity),
        filled=float(order.filled),
        status=order.status,
        price=float(order.price) if order.price else None,
        created_at=order.created_at
    )

@router.delete("/orders/{order_id}", response_model=schemas.OrderOut)
async def cancel_order(
    order_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.cancel_order(db, user.id, order_id)
    if not order:
        raise HTTPException(404, "Order not found or cannot be cancelled")
    return schemas.OrderOut(
        id=order.id,
        instrument=order.instrument.symbol,
        side=order.side,
        type=order.type,
        quantity=float(order.quantity),
        filled=float(order.filled),
        status=order.status,
        price=float(order.price) if order.price else None,
        created_at=order.created_at
    )

@router.get("/orders/{order_id}", response_model=schemas.OrderOut)
async def get_order_status(
    order_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.get_order(db, user.id, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return schemas.OrderOut(
        id=order.id,
        instrument=order.instrument.symbol,
        side=order.side,
        type=order.type,
        quantity=float(order.quantity),
        filled=float(order.filled),
        status=order.status,
        price=float(order.price) if order.price else None,
        created_at=order.created_at
    )

@router.get("/orders", response_model=List[schemas.OrderOut])
async def list_active_orders(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    orders = await crud.list_active_orders(db, user.id)
    return [
        schemas.OrderOut(
            id=o.id,
            instrument=o.instrument.symbol,
            side=o.side,
            type=o.type,
            quantity=float(o.quantity),
            filled=float(o.filled),
            status=o.status,
            price=float(o.price) if o.price else None,
            created_at=o.created_at
        )
        for o in orders
    ]

@router.get("/orderbook/{symbol}", response_model=schemas.OrderBookOut)
async def order_book(
    symbol: str,
    depth: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    inst = await crud.get_instrument_by_symbol(db, symbol)
    if not inst or not inst.is_listed:
        raise HTTPException(404, "Instrument not found")
    book = await crud.get_order_book(db, inst.id, limit=depth)
    return schemas.OrderBookOut(
        asks=[schemas.OrderBookSide(price=float(o.price), quantity=float(o.quantity)) for o in book["asks"]],
        bids=[schemas.OrderBookSide(price=float(o.price), quantity=float(o.quantity)) for o in book["bids"]],
    )

@router.get("/history/{symbol}", response_model=List[schemas.Candle])
async def history(
    symbol: str,
    interval: int = Query(1, ge=1),
    start: datetime.datetime = Query(...),
    end: datetime.datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    inst = await crud.get_instrument_by_symbol(db, symbol)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    candles = await crud.get_candles(db, inst.id, interval, start, end)
    return [schemas.Candle(**c) for c in candles]
