"""
Migration script to add category column to products table.
Run this once to update the database schema.
"""
import asyncio
import sys
import os

from sqlalchemy import text
from app.database import AsyncSessionLocal, engine


async def migrate():
    async with engine.begin() as conn:
        # Check if column already exists using PostgreSQL system catalog
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'category'
        """))
        columns = [row[0] for row in result.fetchall()]

        if 'category' not in columns:
            print("Adding 'category' column to products table...")
            await conn.execute(text(
                "ALTER TABLE products ADD COLUMN category VARCHAR"
            ))
            print("Column 'category' added successfully!")
        else:
            print("Column 'category' already exists.")

        # Seed some sample categories
        print("\nSeeding sample categories...")
        await conn.execute(text("""
            UPDATE products
            SET category = CASE
                WHEN id <= 3 THEN 'Electronics'
                WHEN id <= 6 THEN 'Accessories'
                WHEN id <= 9 THEN 'Tools'
                ELSE 'General'
            END
            WHERE category IS NULL OR category = ''
        """))
        print("Categories seeded!")


if __name__ == "__main__":
    asyncio.run(migrate())