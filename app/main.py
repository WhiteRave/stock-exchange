from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import api_v1_public, api_v1_balance, api_v1_order, api_v1_admin, api_v1_user

app = FastAPI(openapi_url="/openapi.json", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Роутеры
app.include_router(api_v1_public.router)
app.include_router(api_v1_balance.router)
app.include_router(api_v1_order.router)
app.include_router(api_v1_admin.router)
app.include_router(api_v1_user.router)
