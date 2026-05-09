"""
Seed script to populate the database with additional test products.
Run with: python -m app.seed_products
"""
import asyncio
import random

from sqlalchemy import text
from app.database import AsyncSessionLocal, engine


async def seed_additional_products():
    """Seed additional products covering the specified categories."""

    products_data = [
        # Furniture
        {
            "sku": "SKU-FURN-001",
            "name": "Office Table",
            "description": "Sturdy wooden office table, 120x60cm",
            "category": "Furniture",
            "image_url": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=400",
            "physical_stock": 12,
            "reserved_stock": 0,
            "price": 299.99
        },
        {
            "sku": "SKU-FURN-002",
            "name": "Ergonomic Chair",
            "description": "Adjustable lumbar support, breathable mesh",
            "category": "Furniture",
            "image_url": "https://images.unsplash.com/photo-1580480055273-228ffde8d8ab?w=400",
            "physical_stock": 8,
            "reserved_stock": 0,
            "price": 459.99
        },

        # Toys
        {
            "sku": "SKU-TOYS-001",
            "name": "Designer Blind Box",
            "description": "Mystery collectible figurine set",
            "category": "Toys",
            "image_url": "https://images.unsplash.com/photo-1608889825205-eebdb9fc5806?w=400",
            "physical_stock": 50,
            "reserved_stock": 0,
            "price": 24.99
        },
        {
            "sku": "SKU-TOYS-002",
            "name": "Action Figure",
            "description": "12-inch articulated action figure with accessories",
            "category": "Toys",
            "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "physical_stock": 25,
            "reserved_stock": 0,
            "price": 49.99
        },

        # Electric Hardware
        {
            "sku": "SKU-ELEC-001",
            "name": "Power Strip",
            "description": "6-outlet surge protector with USB ports",
            "category": "Electric Hardware",
            "image_url": "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400",
            "physical_stock": 35,
            "reserved_stock": 0,
            "price": 34.99
        },
        {
            "sku": "SKU-ELEC-002",
            "name": "LED Bulb",
            "description": "10W equivalent, 800 lumens, 6500K daylight",
            "category": "Electric Hardware",
            "image_url": "https://images.unsplash.com/photo-1563142836-cb9c0d8e3d5d?w=400",
            "physical_stock": 100,
            "reserved_stock": 0,
            "price": 9.99
        },

        # Tools
        {
            "sku": "SKU-TOOL-001",
            "name": "Multi-tool Kit",
            "description": "18-in-1 stainless steel multi-tool with case",
            "category": "Tools",
            "image_url": "https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400",
            "physical_stock": 20,
            "reserved_stock": 0,
            "price": 79.99
        },
        {
            "sku": "SKU-TOOL-002",
            "name": "Screwdriver Set",
            "description": "48-piece precision screwdriver set",
            "category": "Tools",
            "image_url": "https://images.unsplash.com/photo-1581147036324-c47b7bb27a06?w=400",
            "physical_stock": 30,
            "reserved_stock": 0,
            "price": 44.99
        },

        # Storage
        {
            "sku": "SKU-STOR-001",
            "name": "128GB Pendrive",
            "description": "USB 3.0 flash drive, 100MB/s read speed",
            "category": "Storage",
            "image_url": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=400",
            "physical_stock": 75,
            "reserved_stock": 0,
            "price": 14.99
        },
        {
            "sku": "SKU-STOR-002",
            "name": "2TB HDD",
            "description": "External hard drive, USB 3.0, plug-and-play",
            "category": "Storage",
            "image_url": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=400",
            "physical_stock": 40,
            "reserved_stock": 0,
            "price": 89.99
        },
        {
            "sku": "SKU-STOR-003",
            "name": "1TB NVMe SSD",
            "description": "M.2 NVMe SSD, 3500MB/s read speed",
            "category": "Storage",
            "image_url": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=400",
            "physical_stock": 15,
            "reserved_stock": 0,
            "price": 129.99
        },

        # Accessories
        {
            "sku": "SKU-ACC-001",
            "name": "USB-C Cable",
            "description": "2m braided USB-C to USB-C cable, 100W PD",
            "category": "Accessories",
            "image_url": "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400",
            "physical_stock": 60,
            "reserved_stock": 0,
            "price": 19.99
        },
        {
            "sku": "SKU-ACC-002",
            "name": "Laptop Sleeve",
            "description": "15.6-inch neoprene sleeve, water-resistant",
            "category": "Accessories",
            "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400",
            "physical_stock": 45,
            "reserved_stock": 0,
            "price": 29.99
        },

        # Additional items for 3x3 grid testing (3 more pages of 9)
        {
            "sku": "SKU-FURN-003",
            "name": "Standing Desk Converter",
            "description": "Adjustable height sit-stand workstation",
            "category": "Furniture",
            "image_url": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=400",
            "physical_stock": 10,
            "reserved_stock": 0,
            "price": 349.99
        },
        {
            "sku": "SKU-TOYS-003",
            "name": "Remote Control Car",
            "description": "High-speed RC car with rechargeable battery",
            "category": "Toys",
            "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "physical_stock": 18,
            "reserved_stock": 0,
            "price": 89.99
        },
        {
            "sku": "SKU-ELEC-003",
            "name": "Smart Plug",
            "description": "WiFi-enabled smart plug, voice control compatible",
            "category": "Electric Hardware",
            "image_url": "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400",
            "physical_stock": 55,
            "reserved_stock": 0,
            "price": 24.99
        },
        {
            "sku": "SKU-TOOL-003",
            "name": "Digital Multimeter",
            "description": "Auto-ranging multimeter for electrical testing",
            "category": "Tools",
            "image_url": "https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400",
            "physical_stock": 22,
            "reserved_stock": 0,
            "price": 54.99
        },
        {
            "sku": "SKU-STOR-004",
            "name": "512GB MicroSD Card",
            "description": "High-speed microSD card with adapter",
            "category": "Storage",
            "image_url": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=400",
            "physical_stock": 65,
            "reserved_stock": 0,
            "price": 44.99
        },
        {
            "sku": "SKU-ACC-003",
            "name": "Wireless Charger",
            "description": "15W fast wireless charging pad",
            "category": "Accessories",
            "image_url": "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400",
            "physical_stock": 38,
            "reserved_stock": 0,
            "price": 34.99
        },
    ]

    async with engine.begin() as conn:
        # Check existing SKUs to avoid duplicates
        result = await conn.execute(text("SELECT sku FROM products"))
        existing_skus = {row[0] for row in result.fetchall()}

        inserted_count = 0
        for product in products_data:
            if product["sku"] in existing_skus:
                print(f"  Skipping existing SKU: {product['sku']}")
                continue

            await conn.execute(text("""
                INSERT INTO products (sku, name, description, category, image_url, physical_stock, reserved_stock, price, version)
                VALUES (:sku, :name, :description, :category, :image_url, :physical_stock, :reserved_stock, :price, 1)
            """), product)

            inserted_count += 1
            print(f"  Inserted: {product['name']} ({product['category']})")

        return inserted_count


async def main():
    print("=" * 60)
    print("SEEDING ADDITIONAL TEST PRODUCTS")
    print("=" * 60)

    print("\nInserting products by category...")
    count = await seed_additional_products()

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {count} products inserted successfully!")
    print("=" * 60)

    # Verify categories
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT DISTINCT category FROM products
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """))
        categories = [row[0] for row in result.fetchall()]
        print(f"\nAvailable categories ({len(categories)}):")
        for cat in categories:
            print(f"  - {cat}")

        result = await conn.execute(text("SELECT COUNT(*) FROM products"))
        total = result.scalar()
        print(f"\nTotal products in database: {total}")


if __name__ == "__main__":
    asyncio.run(main())
