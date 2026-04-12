import asyncpg
import os
from pathlib import Path

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ.get("NEON_DATABASE_URL", "postgresql://neondb_owner:npg_rV2GH9maPOpU@ep-floral-math-a1407vy5-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"),
            min_size=2,
            max_size=10,
        )
    return _pool


async def init_db():
    pool = await get_pool()
    migrations_dir = Path(__file__).parent / "migrations"
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            applied = await conn.fetchval(
                "SELECT 1 FROM _migrations WHERE filename = $1", sql_file.name
            )
            if not applied:
                await conn.execute(sql_file.read_text())
                await conn.execute(
                    "INSERT INTO _migrations (filename) VALUES ($1)", sql_file.name
                )
                print(f"  ✅ Migration: {sql_file.name}")


async def execute_query(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute_one(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
