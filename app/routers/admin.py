from fastapi import APIRouter, Depends, HTTPException
from decimal import Decimal

from app.auth import get_current_user
from app.database import get_db
from app import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

def admin_required(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(delete(crud.User).where(crud.User.id == user_id))
    if res.rowcount == 0:
        raise HTTPException(404, "User not found")
    await db.commit()
    return {"detail": "User deleted"}

@router.post("/balances/{user_id}/{symbol}", response_model=schemas.BalanceOut)
async def change_balance(
    user_id: int,
    symbol: str,
    amount: float,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    inst = await crud.get_instrument_by_symbol(db, symbol)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    bal = await crud.adjust_balance(db, user_id, inst.id, Decimal(amount))
    return schemas.BalanceOut(instrument=inst.symbol, amount=float(bal.amount))

@router.post("/instruments", response_model=schemas.InstrumentOut)
async def add_instrument(
    inp: schemas.InstrumentIn,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    inst = await crud.create_instrument(db, inp.symbol, inp.name, inp.type)
    return schemas.InstrumentOut(
        id=inst.id,
        symbol=inst.symbol,
        name=inst.name,
        type=inst.type,
        is_listed=inst.is_listed
    )

@router.delete("/instruments/{symbol}")
async def delist_instrument(
    symbol: str,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    inst = await crud.get_instrument_by_symbol(db, symbol)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.delist_instrument(db, inst.id)
    return {"detail": "Instrument delisted"}
