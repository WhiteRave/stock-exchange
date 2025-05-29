from fastapi import Depends, HTTPException, Header
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from sqlalchemy import select
import secrets

async def get_current_user(token: str = Header(..., alias="Authorization"), db: AsyncSession = Depends(get_db)):
    if not token.startswith("TOKEN "):
        raise HTTPException(401, "Invalid auth header")
    raw = token.split(" ", 1)[1]
    res = await db.execute(select(User).where(User.token == raw))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

def create_token() -> str:
    return secrets.token_urlsafe(32)
