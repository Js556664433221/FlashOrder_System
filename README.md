# FlashOrder Portal Documentation

## Project Overview

FlashOrder Portal is a lightweight, mobile-responsive web portal for frontline sales and counter staff to manage stock inquiries, place orders, and upload payment proofs in real-time.

## Technology Stack

- **Frontend:** Vite + TypeScript + React + Tailwind CSS
- **Backend:** Python FastAPI (Async)
- **Database:** PostgreSQL with asyncpg driver
- **ORM:** SQLAlchemy 2.0 (Async)

## Project Structure

```
cart system/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Cart.tsx
│   │   │   ├── PaymentUpload.tsx
│   │   │   └── ProductList.tsx
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── store.ts
│   │   ├── types.ts
│   │   ├── index.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py
│   │   ├── routers/
│   │   │   ├── orders.py
│   │   │   ├── payments.py
│   │   │   └── products.py
│   │   └── schemas/
│   │       └── __init__.py
│   ├── uploads/
│   ├── init_db.sql
│   └── requirements.txt
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- PostgreSQL 14+

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set the database URL environment variable:
   ```bash
   export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder
   ```
   Or on Windows:
   ```bash
   set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the dev server:
   ```bash
   npm run dev
   ```

## API Documentation

Interactive API documentation is available via Swagger UI when the server is running:

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

You can test all API endpoints directly from the Swagger UI interface.

## API Endpoints

### Root
- `GET /` - Returns welcome message

### Health Check
- `GET /health` - Returns server health status

### Products
- `GET /products/` - List all products
  - Query params: `search` (optional) - Filter by SKU or name
- `GET /products/{product_id}` - Get a single product

### Orders
- `GET /orders/` - List all orders
- `GET /orders/{order_id}` - Get a single order
- `POST /orders/` - Create a new order
  - Body: `{ "items": [{ "product_id": 1, "quantity": 2 }] }`

### Payments
- `POST /payments/{order_id}/upload` - Upload payment receipt
  - Body: multipart/form-data with `file` field
  - Accepted file types: JPG, PNG, PDF

## Database Schema

### Products
| Column        | Type    | Description           |
|--------------|---------|----------------------|
| id           | INTEGER | Primary key          |
| sku          | VARCHAR | Unique product SKU   |
| name         | VARCHAR | Product name         |
| stock_balance| INTEGER | Available stock      |
| price        | FLOAT   | Product price         |
| version      | INTEGER | Optimistic lock version |

### Orders
| Column       | Type    | Description                    |
|-------------|---------|-------------------------------|
| id          | INTEGER | Primary key                   |
| order_number| VARCHAR | Unique order identifier        |
| total_price | FLOAT   | Order total                   |
| status      | VARCHAR | Order status                  |
| created_at  | TIMESTAMP | Creation timestamp          |

### Order Items
| Column     | Type    | Description           |
|-----------|---------|----------------------|
| id        | INTEGER | Primary key          |
| order_id  | INTEGER | Foreign key to orders |
| product_id| INTEGER | Foreign key to products|
| quantity  | INTEGER | Item quantity        |
| unit_price| FLOAT   | Price at time of order|

### Payments
| Column      | Type    | Description           |
|------------|---------|----------------------|
| id         | INTEGER | Primary key          |
| order_id   | INTEGER | Foreign key to orders |
| receipt_url| VARCHAR | Path to uploaded file |
| uploaded_at| TIMESTAMP | Upload timestamp   |

## Order Status Flow

1. `Pending Payment` - Initial status when order is created
2. `Payment Under Review` - After payment receipt is uploaded
3. `Paid` - After payment is confirmed
4. `Cancelled` - If order is cancelled

## Environment Variables

| Variable      | Default                                        | Description           |
|--------------|-----------------------------------------------|----------------------|
| DATABASE_URL | postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder | PostgreSQL connection string |

## Development Notes

- The backend uses async SQLAlchemy with `asyncpg` driver for non-blocking database operations
- All file uploads are stored in the `backend/uploads/` directory
- Uploaded files are served statically at `/uploads/{filename}`
- Stock is atomically deducted when an order is placed to prevent overselling
