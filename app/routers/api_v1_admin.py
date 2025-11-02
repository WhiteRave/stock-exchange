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









