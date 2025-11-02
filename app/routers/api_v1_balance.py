from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.database import get_db
from app.auth import get_current_user
from app.models import Balance, Instrument, User
from app import crud

router = APIRouter(prefix="/api/v1", tags=["balance"])


@router.get("/balance")
async def get_balances(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Balance).where(Balance.user_id == user.id))
    balances = res.scalars().all()
    out = {}
    for b in balances:
        inst: Instrument = b.instrument
        out[inst.symbol] = int(Decimal(b.amount))
    return out


def admin_required(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user


@router.post("/admin/balance/deposit")
async def deposit(body: dict, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    user_id = body.get("user_id")
    ticker = body.get("ticker")
    amount = body.get("amount")
    if not user_id or not ticker or not isinstance(amount, int) or amount <= 0:
        raise HTTPException(422, "Invalid body")
    u = (await db.execute(select(User).where(User.external_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    inst = await crud.get_instrument_by_symbol(db, ticker)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.adjust_balance(db, u.id, inst.id, Decimal(amount))
    return {"success": True}


@router.post("/admin/balance/withdraw")
async def withdraw(body: dict, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    user_id = body.get("user_id")
    ticker = body.get("ticker")
    amount = body.get("amount")
    if not user_id or not ticker or not isinstance(amount, int) or amount <= 0:
        raise HTTPException(422, "Invalid body")
    u = (await db.execute(select(User).where(User.external_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    inst = await crud.get_instrument_by_symbol(db, ticker)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.adjust_balance(db, u.id, inst.id, Decimal(-amount))
    return {"success": True}







