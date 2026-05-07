-- FlashOrder Portal Database Schema

-- Users table (for RBAC)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'staff',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    image_url VARCHAR,
    physical_stock INTEGER NOT NULL DEFAULT 0,
    reserved_stock INTEGER NOT NULL DEFAULT 0,
    price FLOAT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

-- Orders table (with user_id for multi-tenant)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR UNIQUE NOT NULL,
    total_price FLOAT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Pending Payment',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES users(id)
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
INSERT INTO products (sku, name, description, image_url, physical_stock, reserved_stock, price, version) VALUES
('SKU001', 'Wireless Mouse', 'Ergonomic wireless mouse with adjustable DPI', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400', 50, 0, 29.99, 1),
('SKU002', 'Mechanical Keyboard', 'RGB mechanical keyboard with Cherry MX switches', 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400', 30, 0, 89.99, 1),
('SKU003', 'USB-C Hub', '7-in-1 USB-C hub with HDMI and ethernet', 'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400', 25, 0, 49.99, 1),
('SKU004', 'Webcam HD', '1080p HD webcam with built-in microphone', 'https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=400', 40, 0, 59.99, 1),
('SKU005', 'Monitor Stand', 'Adjustable aluminum monitor stand', 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400', 15, 0, 39.99, 1);