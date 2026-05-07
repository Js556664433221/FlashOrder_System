#!/usr/bin/env python
"""Migrate database schema to support reserved stock."""
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/flashorder"

async def migrate():
    # Parse URL for asyncpg
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
        # Add new columns
        await conn.execute("""
            ALTER TABLE products ADD COLUMN IF NOT EXISTS physical_stock INTEGER DEFAULT 0;
        """)
        print("Added physical_stock column")

        await conn.execute("""
            ALTER TABLE products ADD COLUMN IF NOT EXISTS reserved_stock INTEGER DEFAULT 0;
        """)
        print("Added reserved_stock column")

        await conn.execute("""
            ALTER TABLE products ADD COLUMN IF NOT EXISTS description VARCHAR;
        """)
        print("Added description column")

        await conn.execute("""
            ALTER TABLE products ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
        """)
        print("Added version column")

        # Migrate existing data
        await conn.execute("""
            UPDATE products SET physical_stock = stock_balance
            WHERE physical_stock IS NULL OR physical_stock = 0;
        """)
        print("Migrated stock_balance to physical_stock")

        await conn.execute("""
            UPDATE products SET reserved_stock = 0 WHERE reserved_stock IS NULL;
        """)
        print("Set reserved_stock to 0 for existing products")

        print("Migration completed successfully!")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
