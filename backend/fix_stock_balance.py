#!/usr/bin/env python
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/flashorder"

async def fix():
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    uri_parts = db_url.replace("postgresql://", "").split("@")
    auth = uri_parts[0].split(":")
    host_db = uri_parts[1].split("/")
    host_port = host_db[0].split(":")

    conn = await asyncpg.connect(
        user=auth[0],
        password=auth[1],
        host=host_port[0],
        port=int(host_port[1]) if len(host_port) > 1 else 5432,
        database=host_db[1]
    )

    try:
        # Check if stock_balance column exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'stock_balance'
            )
        """)
        if exists:
            # Drop the column
            await conn.execute("ALTER TABLE products DROP COLUMN stock_balance")
            print("Dropped stock_balance column")
        else:
            print("stock_balance column does not exist - no action needed")
    finally:
        await conn.close()

asyncio.run(fix())
