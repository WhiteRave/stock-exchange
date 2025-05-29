from fastapi import APIRouter, Depends, HTTPException
from app.schemas import UserCreate, TokenResponse
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.auth import create_token
from sqlalchemy import select
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.username == data.username))
    if res.scalar_one_or_none():
        raise HTTPException(400, "Username taken")
    user = User(
        username=data.username,
        hashed_password=pwd_ctx.hash(data.password),
        token=create_token()
    )
    db.add(user)
    await db.commit()
    return TokenResponse(token=user.token)
