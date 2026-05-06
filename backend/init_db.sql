-- FlashOrder Portal Database Schema

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    stock_balance INTEGER NOT NULL DEFAULT 0,
    price FLOAT NOT NULL
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR UNIQUE NOT NULL,
    total_price FLOAT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Pending Payment',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price FLOAT NOT NULL
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    receipt_url VARCHAR NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample data
INSERT INTO products (sku, name, stock_balance, price) VALUES
('SKU001', 'Wireless Mouse', 50, 29.99),
('SKU002', 'Mechanical Keyboard', 30, 89.99),
('SKU003', 'USB-C Hub', 25, 49.99),
('SKU004', 'Webcam HD', 40, 59.99),
('SKU005', 'Monitor Stand', 15, 39.99);
