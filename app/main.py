from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import auth, user_trading, admin

app = FastAPI(openapi_url="/openapi.json", docs_url="/docs")

# CORS (при необходимости)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем таблицы
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Роутеры
app.include_router(auth.router)
app.include_router(user_trading.router)
app.include_router(admin.router)
