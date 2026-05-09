"""Add payment rejection fields to payments table"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder")

        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            # Check if rejection_reason column exists
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'payments' AND column_name = 'rejection_reason'
            """))
            exists = result.fetchone()

            if not exists:
                await conn.execute(text("""
                    ALTER TABLE payments ADD COLUMN rejection_reason TEXT
                """))
                print("Added 'rejection_reason' column to payments table")
            else:
                print("'rejection_reason' column already exists")

            # Check if rejected_at column exists
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'payments' AND column_name = 'rejected_at'
            """))
            exists = result.fetchone()

            if not exists:
                await conn.execute(text("""
                    ALTER TABLE payments ADD COLUMN rejected_at TIMESTAMP
                """))
                print("Added 'rejected_at' column to payments table")
            else:
                print("'rejected_at' column already exists")

        await engine.dispose()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate())