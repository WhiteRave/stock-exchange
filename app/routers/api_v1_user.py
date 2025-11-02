from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import get_current_user
from app.models import User


router = APIRouter(prefix="/api/v1/admin/user", tags=["admin", "user"])


def admin_required(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: str, admin=Depends(admin_required), db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.external_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    await db.delete(u)
    await db.commit()
    return {"id": user_id, "name": u.name, "role": u.role.value, "api_key": u.token}


