# FlashOrder Portal

A lightweight, mobile-responsive e-commerce portal with role-based access control for managing stock, orders, payments, and admin operations.

## Features

- **Role-Based Access Control**: Staff and Admin roles with different permissions
- **Real-time Stock Management**: Physical, reserved, and available stock tracking
- **Order Management**: Place orders, request cancellations, upload payment proofs
- **Admin Dashboard**: View statistics, low stock alerts, manage products
- **Payment Workflow**: Upload receipts, confirm payments, verify transactions
- **Product Catalog**: Images, search, add/edit/restock products

## Technology Stack

- **Frontend**: Vite + React + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI (async)
- **Database**: PostgreSQL with asyncpg driver
- **ORM**: SQLAlchemy 2.0 (async)

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python run_migration.py    # Run database migrations
python run_server.py       # Starts on port 8002
```

### Frontend

```bash
cd frontend
npm install
npm run dev              # Starts on port 5173
```

### Access

Open http://localhost:5173 in your browser.

- **Default role**: Staff (can view products, place orders, upload payments)
- **Switch to Admin**: Click "Switch to Admin" button in header

## API Endpoints

### Products (Staff)
- `GET /products/` - List products (with optional `?search=` filter)
- `GET /products/{id}` - Get single product

### Orders (Staff)
- `GET /orders/` - List user's orders
- `POST /orders/` - Create order
- `POST /orders/{id}/request-cancel` - Request cancellation

### Payments
- `POST /payments/{order_id}/upload` - Upload payment receipt
- `GET /payments/` - List payment history with order items

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/products` | GET | List all products |
| `/admin/products` | POST | Create new product |
| `/admin/products/{id}` | PATCH | Update/restock product |
| `/admin/orders` | GET | List all orders |
| `/admin/orders/{id}/confirm-payment` | POST | Confirm payment, deduct stock |
| `/admin/orders/{id}/cancel` | POST | Force cancel order |
| `/admin/orders/{id}/approve-cancel` | POST | Approve cancellation |
| `/admin/inventory/restock` | POST | Add stock to product |
| `/admin/dashboard/summary` | GET | Dashboard statistics |

### Authentication

Uses `X-Simulated-Role` header (dev mode):
- `X-Simulated-Role: staff` - Staff access
- `X-Simulated-Role: admin` - Admin access

## Database Schema

### Products
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| sku | VARCHAR | Unique SKU |
| name | VARCHAR | Product name |
| description | VARCHAR | Optional description |
| image_url | VARCHAR | Product image URL |
| physical_stock | INTEGER | Total physical stock |
| reserved_stock | INTEGER | Reserved stock |
| price | FLOAT | Unit price |
| version | INTEGER | Optimistic lock |

### Orders
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| order_number | VARCHAR | Unique order ID |
| total_price | FLOAT | Order total |
| status | VARCHAR | Order status |
| user_id | INTEGER | Ordering user |
| created_at | TIMESTAMP | Creation time |

### Order Items
| Column | Type | Description |
|--------|------|-------------|
| product_id | INTEGER | FK to products |
| product_name | VARCHAR | Product name at order time |
| product_image_url | VARCHAR | Image URL at order time |
| quantity | INTEGER | Quantity ordered |
| unit_price | FLOAT | Price at order time |

### Payments
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| order_id | INTEGER | FK to orders |
| receipt_url | VARCHAR | Uploaded file path |
| uploaded_at | TIMESTAMP | Upload time |

## Order Status Flow

```
Pending Payment → Payment Under Review → Paid
     ↓                 ↓
  Cancelled ← Cancel Requested → Cancelled (after approval)
```

## Development

### Running Migrations

```bash
python run_migration.py    # Adds missing columns
python fix_stock_balance.py  # Removes legacy stock_balance column
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder | PostgreSQL connection |
