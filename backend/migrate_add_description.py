import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def migrate():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder')
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='products' AND column_name='description'
        """))
        if not result.fetchone():
            await conn.execute(text('ALTER TABLE products ADD COLUMN description VARCHAR'))
            print('Added description column')
        else:
            print('description column already exists')
    await engine.dispose()

asyncio.run(migrate())