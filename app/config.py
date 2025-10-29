from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql+asyncpg://user:pass@localhost/db")
    SECRET_KEY: str = Field(default="4f3b2d1e8a7c6e5f4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ECHO_SQLALCHEMY: bool = Field(default=False)

    class Config:
        env_file = ".env"

settings = Settings()
