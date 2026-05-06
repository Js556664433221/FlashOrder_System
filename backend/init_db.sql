-- FlashOrder Portal Database Schema

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    physical_stock INTEGER NOT NULL DEFAULT 0,
    reserved_stock INTEGER NOT NULL DEFAULT 0,
    price FLOAT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
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
INSERT INTO products (sku, name, description, physical_stock, reserved_stock, price, version) VALUES
('SKU001', 'Wireless Mouse', 'Ergonomic wireless mouse with adjustable DPI', 50, 0, 29.99, 1),
('SKU002', 'Mechanical Keyboard', 'RGB mechanical keyboard with Cherry MX switches', 30, 0, 89.99, 1),
('SKU003', 'USB-C Hub', '7-in-1 USB-C hub with HDMI and ethernet', 25, 0, 49.99, 1),
('SKU004', 'Webcam HD', '1080p HD webcam with built-in microphone', 40, 0, 59.99, 1),
('SKU005', 'Monitor Stand', 'Adjustable aluminum monitor stand', 15, 0, 39.99, 1);
