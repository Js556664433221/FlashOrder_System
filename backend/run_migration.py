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

        # Add image_url column
        await conn.execute("""
            ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url VARCHAR;
        """)
        print("Added image_url column")

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

        # Update image URLs
        image_urls = {
            'SKU001': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400',
            'SKU002': 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400',
            'SKU003': 'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400',
            'SKU004': 'https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=400',
            'SKU005': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400',
        }
        for sku, url in image_urls.items():
            await conn.execute(f"UPDATE products SET image_url = '{url}' WHERE sku = '{sku}'")
        print("Updated image URLs")

        print("Migration completed successfully!")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
