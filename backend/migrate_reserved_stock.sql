-- Migration: Add physical_stock and reserved_stock columns, rename stock_balance
-- This script handles the case where stock_balance exists

-- Add new columns
ALTER TABLE products ADD COLUMN IF NOT EXISTS physical_stock INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS reserved_stock INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS description VARCHAR;

-- Migrate data: physical_stock = stock_balance, reserved_stock = 0
UPDATE products SET physical_stock = stock_balance WHERE physical_stock IS NULL OR physical_stock = 0;
UPDATE products SET reserved_stock = 0 WHERE reserved_stock IS NULL;

-- Drop old column if it exists
-- ALTER TABLE products DROP COLUMN IF EXISTS stock_balance;
