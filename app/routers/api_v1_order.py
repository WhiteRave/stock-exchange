from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
import uuid
import datetime
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models import (
    Instrument, Order, Trade, Balance,
    OrderType, OrderStatus, Side
)

router = APIRouter(prefix="/api/v1", tags=["order"])


def to_api_status(status: OrderStatus) -> str:
    mapping = {
        OrderStatus.NEW: "NEW",
        OrderStatus.PARTIAL: "PARTIALLY_EXECUTED",
        OrderStatus.FILLED: "EXECUTED",
        OrderStatus.CANCELED: "CANCELLED",
    }
    return mapping[status]


async def get_or_create_balance(db: AsyncSession, user_id: int, instrument_id: int) -> Balance:
    res = await db.execute(select(Balance).where(Balance.user_id == user_id, Balance.instrument_id == instrument_id))
    bal = res.scalar_one_or_none()
    if not bal:
        bal = Balance(user_id=user_id, instrument_id=instrument_id, amount=Decimal(0))
        db.add(bal)
        await db.flush()
    return bal


async def execute_against_book(db: AsyncSession, inst: Instrument, incoming: Order) -> None:
    if incoming.side == Side.BUY:
        q = select(Order).where(
            Order.instrument_id == inst.id,
            Order.side == Side.SELL,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        ).order_by(Order.price.asc())
    else:
        q = select(Order).where(
            Order.instrument_id == inst.id,
            Order.side == Side.BUY,
            Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIAL])
        ).order_by(Order.price.desc())

    book = (await db.execute(q)).scalars().all()

    remaining = Decimal(incoming.quantity) - Decimal(incoming.filled)
    for resting in book:
        if remaining <= 0:
            break
        if incoming.type == OrderType.LIMIT and resting.price is not None and incoming.price is not None:
            if incoming.side == Side.BUY and Decimal(incoming.price) < Decimal(resting.price):
                break
            if incoming.side == Side.SELL and Decimal(incoming.price) > Decimal(resting.price):
                break
        trade_qty = min(remaining, Decimal(resting.quantity) - Decimal(resting.filled))
        if trade_qty <= 0:
            continue
        trade_price = Decimal(resting.price) if resting.price is not None else Decimal(incoming.price or 0)

        buyer_id = incoming.user_id if incoming.side == Side.BUY else resting.user_id
        seller_id = resting.user_id if incoming.side == Side.BUY else incoming.user_id

        buyer_bal = await get_or_create_balance(db, buyer_id, inst.id)
        seller_bal = await get_or_create_balance(db, seller_id, inst.id)

        buyer_bal.amount = Decimal(buyer_bal.amount) + trade_qty
        seller_bal.amount = Decimal(seller_bal.amount) - trade_qty

        incoming.filled = Decimal(incoming.filled) + trade_qty
        resting.filled = Decimal(resting.filled) + trade_qty
        if Decimal(resting.filled) >= Decimal(resting.quantity):
            resting.status = OrderStatus.FILLED
        else:
            resting.status = OrderStatus.PARTIAL

        db.add(Trade(
            buy_order_id=incoming.id if incoming.side == Side.BUY else resting.id,
            sell_order_id=resting.id if incoming.side == Side.BUY else incoming.id,
            instrument_id=inst.id,
            price=trade_price,
            quantity=trade_qty,
            timestamp=datetime.datetime.utcnow(),
        ))

        remaining = Decimal(incoming.quantity) - Decimal(incoming.filled)

    if remaining <= 0:
        incoming.status = OrderStatus.FILLED
    elif Decimal(incoming.filled) > 0:
        incoming.status = OrderStatus.PARTIAL
    else:
        incoming.status = OrderStatus.NEW


@router.post("/order")
async def create_order(body: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    is_limit = "price" in body and body.get("price") is not None
    ticker = body.get("ticker")
    direction = body.get("direction")
    qty = body.get("qty")
    if not ticker or direction not in ("BUY", "SELL") or not isinstance(qty, int) or qty < 1:
        raise HTTPException(422, "Invalid order body")
    inst = (await db.execute(select(Instrument).where(Instrument.symbol == ticker))).scalar_one_or_none()
    if not inst or not inst.is_listed:
        raise HTTPException(404, "Instrument not found or delisted")

    order = Order(
        external_id=str(uuid.uuid4()),
        user_id=user.id,
        instrument_id=inst.id,
        type=OrderType.LIMIT if is_limit else OrderType.MARKET,
        side=Side.BUY if direction == "BUY" else Side.SELL,
        quantity=Decimal(qty),
        price=Decimal(body["price"]) if is_limit else None,
    )
    db.add(order)
    await db.flush()

    await execute_against_book(db, inst, order)
    await db.commit()
    return {"success": True, "order_id": order.external_id}


@router.get("/order")
async def list_orders(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Order).where(Order.user_id == user.id))).scalars().all()
    def serialize(o: Order):
        base = {
            "id": o.external_id,
            "status": to_api_status(o.status),
            "user_id": user.external_id,
            "timestamp": o.created_at,
            "filled": int(Decimal(o.filled)) if o.type == OrderType.LIMIT else 0,
        }
        body = {
            "direction": "BUY" if o.side == Side.BUY else "SELL",
            "ticker": o.instrument.symbol,
            "qty": int(Decimal(o.quantity)),
        }
        if o.type == OrderType.LIMIT:
            body["price"] = int(Decimal(o.price or 0))
            base["body"] = body
            return base
        else:
            base["body"] = body
            return base
    return [serialize(o) for o in rows]


@router.get("/order/{order_id}")
async def get_order(order_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    o = (await db.execute(select(Order).where(Order.external_id == order_id, Order.user_id == user.id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Order not found")
    return {
        "id": o.external_id,
        "status": to_api_status(o.status),
        "user_id": user.external_id,
        "timestamp": o.created_at,
        "body": {
            "direction": "BUY" if o.side == Side.BUY else "SELL",
            "ticker": o.instrument.symbol,
            "qty": int(Decimal(o.quantity)),
            **({"price": int(Decimal(o.price or 0))} if o.type == OrderType.LIMIT else {}),
        },
        **({"filled": int(Decimal(o.filled))} if o.type == OrderType.LIMIT else {}),
    }


@router.delete("/order/{order_id}")
async def cancel_order(order_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    o = (await db.execute(select(Order).where(Order.external_id == order_id, Order.user_id == user.id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Order not found")
    if o.status not in (OrderStatus.NEW, OrderStatus.PARTIAL):
        raise HTTPException(400, "Cannot cancel")
    o.status = OrderStatus.CANCELED
    await db.commit()
    return {"success": True}







