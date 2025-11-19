from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.database import get_db
from app.auth import get_current_user
from app.models import Balance, Instrument
from app import schemas

router = APIRouter(prefix="/api/v1", tags=["balance"])


@router.get("/balance", tags=["balance"], response_model=schemas.BalanceMap)
async def get_balances(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Balance).where(Balance.user_id == user.id))
    balances = res.scalars().all()
    out = {}
    for b in balances:
        inst: Instrument = b.instrument
        out[inst.symbol] = int(Decimal(b.amount))
    return schemas.BalanceMap(root=out)







