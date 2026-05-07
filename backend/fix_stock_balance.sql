-- Fix: Remove stock_balance column if it exists (replaced by physical_stock/reserved_stock)
ALTER TABLE products DROP COLUMN IF EXISTS stock_balance;
