from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings, SettingsConfigDict


# -----------------------------
# Config via env (.env opcional)
# -----------------------------
class Settings(BaseSettings):
    PG_USER: str = "olga"
    PG_PASSWORD: str = "olga"
    PG_HOST: str = "127.0.0.1"      # docker mapeado para localhost
    PG_PORT: int = 5432
    PG_DB: str = "olga_ai"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.PG_USER}:{settings.PG_PASSWORD}"
    f"@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"
)


# -----------------------------
# Base + Engine + Session
# -----------------------------
class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# -----------------------------
# Dependency (FastAPI)
# -----------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# -----------------------------
# Health-check do banco (opcional)
# -----------------------------
async def ping_db() -> bool:
    from sqlalchemy import text
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT 1"))
        return res.scalar_one() == 1
