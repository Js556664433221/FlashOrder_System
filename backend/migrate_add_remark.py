"""Add remark column to orders table"""
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
            # Check if remark column exists
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'remark'
            """))
            exists = result.fetchone()

            if not exists:
                await conn.execute(text("""
                    ALTER TABLE orders ADD COLUMN remark TEXT
                """))
                print("Added 'remark' column to orders table")
            else:
                print("'remark' column already exists")

        await engine.dispose()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate())
