"""
Database migration script for promo tracking and super admin features.

Adds:
1. is_superadmin column to users table
2. promo_codes table
3. applied_promo_id column to orders table
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set in environment")
    exit(1)

async def migrate():
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        print("\n--- Running Migrations ---\n")

        # 1. Check if is_superadmin column exists
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'is_superadmin'
        """))
        if result.scalar() is None:
            print("Adding is_superadmin column to users table...")
            await conn.execute(text("""
                ALTER TABLE users ADD COLUMN is_superadmin INTEGER NOT NULL DEFAULT 0
            """))
            print("is_superadmin column added!")
        else:
            print("is_superadmin column already exists")

        # 2. Check if promo_codes table exists
        result = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'promo_codes'
        """))
        if result.scalar() is None:
            print("Creating promo_codes table...")
            await conn.execute(text("""
                CREATE TABLE promo_codes (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR UNIQUE NOT NULL,
                    discount_type VARCHAR(20) NOT NULL,
                    value FLOAT NOT NULL,
                    expiry_date TIMESTAMP,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("promo_codes table created!")
        else:
            print("promo_codes table already exists")

        # 3. Check if applied_promo_id column exists (without FK constraint for now)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'orders' AND column_name = 'applied_promo_id'
        """))
        if result.scalar() is None:
            print("Adding applied_promo_id column to orders table...")
            await conn.execute(text("""
                ALTER TABLE orders ADD COLUMN applied_promo_id INTEGER
            """))
            print("applied_promo_id column added!")
        else:
            print("applied_promo_id column already exists")

        # 4. Set is_superadmin=1 for existing admin user (user id 1)
        result = await conn.execute(text("""
            UPDATE users SET is_superadmin = 1 WHERE id = 1
        """))
        print(f"Set is_superadmin=1 for user ID 1")

        print("\n--- Migrations Complete ---\n")

if __name__ == "__main__":
    asyncio.run(migrate())