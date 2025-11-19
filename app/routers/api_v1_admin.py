from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Instrument
from app import crud, schemas

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def admin_required(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user


@router.delete("/user/{user_id}", response_model=schemas.User)
async def delete_user(user_id: str, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.external_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    await db.delete(u)
    await db.commit()
    return schemas.User(
        id=user_id,
        name=u.name,
        role=schemas.UserRole(u.role.value),
        api_key=u.token,
    )


@router.delete("/user/{user_id}", response_model=schemas.User, tags=["admin", "user"])
async def delete_user(user_id: str, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.external_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    await db.delete(u)
    await db.commit()
    return schemas.User(
        id=user_id,
        name=u.name,
        role=schemas.UserRole(u.role.value),
        api_key=u.token,
    )


@router.post("/instrument", response_model=schemas.Ok)
async def add_instrument(body: schemas.Instrument, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    if not body.ticker.isupper():
        raise HTTPException(422, "Ticker must be uppercase")
    await crud.create_instrument(db, symbol=body.ticker, name=body.name, instrument_type=crud.InstrumentType.MEMECOIN)
    return schemas.Ok()


@router.delete("/instrument/{ticker}", response_model=schemas.Ok)
async def delete_instrument(ticker: str, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    inst = await crud.get_instrument_by_symbol(db, ticker)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.delist_instrument(db, inst.id)
    return schemas.Ok()


@router.post("/balance/deposit", response_model=schemas.Ok, tags=["admin", "balance"])
async def deposit(
    body: schemas.Body_deposit_api_v1_admin_balance_deposit_post,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    u = (
        await db.execute(select(User).where(User.external_id == body.user_id))
    ).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    inst = await crud.get_instrument_by_symbol(db, body.ticker)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.adjust_balance(db, u.id, inst.id, Decimal(body.amount))
    return schemas.Ok()


@router.post("/balance/withdraw", response_model=schemas.Ok, tags=["admin", "balance"])
async def withdraw(
    body: schemas.Body_withdraw_api_v1_admin_balance_withdraw_post,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    u = (
        await db.execute(select(User).where(User.external_id == body.user_id))
    ).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    inst = await crud.get_instrument_by_symbol(db, body.ticker)
    if not inst:
        raise HTTPException(404, "Instrument not found")
    await crud.adjust_balance(db, u.id, inst.id, Decimal(-body.amount))
    return schemas.Ok()







