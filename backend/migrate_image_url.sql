-- Migration: Add image_url column to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url VARCHAR;

-- Update existing products with sample image URLs
UPDATE products SET image_url = 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400' WHERE sku = 'SKU001';
UPDATE products SET image_url = 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400' WHERE sku = 'SKU002';
UPDATE products SET image_url = 'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400' WHERE sku = 'SKU003';
UPDATE products SET image_url = 'https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=400' WHERE sku = 'SKU004';
UPDATE products SET image_url = 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400' WHERE sku = 'SKU005';
