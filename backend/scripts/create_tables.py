#!/usr/bin/env python3
"""Create DB tables from SQLAlchemy models for local dev. Run from backend: python -m scripts.create_tables"""
import asyncio

from app.database import Base, engine
from app import models  # noqa: F401 — register models with Base


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


if __name__ == "__main__":
    asyncio.run(main())
