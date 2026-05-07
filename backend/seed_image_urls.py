#!/usr/bin/env python
"""Seed image URLs for all products based on name keywords."""
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/flashorder"

# Keywords to match product names with appropriate images
IMAGE_MAP = {
    'mouse': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400',
    'keyboard': 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400',
    'hub': 'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400',
    'webcam': 'https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=400',
    'monitor': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400',
    'headset': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
    'cable': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd1b?w=400',
    'charger': 'https://images.unsplash.com/photo-1583863788434-e58c1cd02b0b?w=400',
    'stand': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400',
    'test': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400',
    'lim': 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400',
}

DEFAULT_IMAGE = 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400'

async def seed():
    conn = await asyncpg.connect(
        user='postgres', password='postgres', database='flashorder'
    )

    # Get all products without images
    products = await conn.fetch("SELECT id, name FROM products WHERE image_url IS NULL OR image_url = ''")

    for product in products:
        name_lower = product['name'].lower()
        matched_url = None

        for keyword, url in IMAGE_MAP.items():
            if keyword in name_lower:
                matched_url = url
                break

        if not matched_url:
            matched_url = DEFAULT_IMAGE

        await conn.execute(
            "UPDATE products SET image_url = $1 WHERE id = $2",
            matched_url, product['id']
        )
        print(f"Updated {product['name']} -> {matched_url[:50]}...")

    # Also update products that might have empty string images
    await conn.execute(
        "UPDATE products SET image_url = $1 WHERE image_url IS NULL OR image_url = ''",
        DEFAULT_IMAGE
    )

    print(f"\nTotal products updated: {len(products)}")
    await conn.close()

asyncio.run(seed())
