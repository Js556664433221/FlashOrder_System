"""Migration: Create customer_profiles table"""
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal


async def upgrade():
    """Create the customer_profiles table using PostgreSQL syntax."""
    async with AsyncSessionLocal() as db:
        # Check if table exists using PostgreSQL information_schema
        result = await db.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_name = 'customer_profiles'")
        )
        exists = result.fetchone()

        if not exists:
            await db.execute(text("""
                CREATE TABLE customer_profiles (
                    id SERIAL PRIMARY KEY,
                    salesman_id INTEGER NOT NULL,
                    name VARCHAR NOT NULL,
                    company_name VARCHAR,
                    location VARCHAR,
                    contact_number VARCHAR NOT NULL,
                    email VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (salesman_id) REFERENCES users (id)
                )
            """))
            await db.commit()
            print("[+] Created customer_profiles table")
        else:
            print("[*] customer_profiles table already exists")


async def downgrade():
    """Drop the customer_profiles table."""
    async with AsyncSessionLocal() as db:
        await db.execute(text("DROP TABLE IF EXISTS customer_profiles CASCADE"))
        await db.commit()
        print("[-] Dropped customer_profiles table")


if __name__ == "__main__":
    asyncio.run(upgrade())
