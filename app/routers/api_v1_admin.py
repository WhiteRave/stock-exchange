from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Instrument, Balance
from app import crud

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def admin_required(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user


@router.delete("/user/{user_id}")
async def delete_user(user_id: str, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.external_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    await db.delete(u)
    await db.commit()
    return {"id": user_id, "name": u.name, "role": u.role.value, "api_key": u.token}


@router.post("/instrument")
async def add_instrument(body: dict, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    name = body.get("name")
    ticker = body.get("ticker")
    if not name or not ticker or not ticker.isupper():
        raise HTTPException(422, "Invalid instrument")
    inst = await crud.create_instrument(db, symbol=ticker, name=name, instrument_type=crud.InstrumentType.MEMECOIN)
    return {"success": True}


@router.delete("/instrument/{ticker}")
async def delete_instrument(ticker: str, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    inst = await crud.get_instrument_by_symbol(db, ticker)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.delist_instrument(db, inst.id)
    return {"success": True}


@router.post("/balance/deposit")
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
    bal = await crud.adjust_balance(db, u.id, inst.id, Decimal(amount))
    return {"success": True}


@router.post("/balance/withdraw")
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
    bal = await crud.adjust_balance(db, u.id, inst.id, Decimal(-amount))
    return {"success": True}



