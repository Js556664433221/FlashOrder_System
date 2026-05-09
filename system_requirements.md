System Requirement: FlashOrder Portal (Integrated Version)

1. Project OverviewA lightweight, mobile-responsive web portal designed for frontline sales staff and administrators. It facilitates real-time stock inquiries, order placement with delivery/pickup options, payment verification, and comprehensive administrative management.

2. Technology Stack
Frontend: Vite + TypeScript + React/Vue 3 + Tailwind CSS.
Backend: Python (FastAPI) - Asynchronous I/O focus.
Database: PostgreSQL (Relational, ACID compliant).
AI Tools: Claude Code / Cursor (for rapid prototyping and logic generation).

3. Functional Requirements
Module A: Product & Inventory (Sales & Admin)
Grid Display: Products must be displayed in a 3x3 grid matrix (9 items per page).
Pagination: * Frontend: Controls for "Previous", "Next", and specific page numbers.
Backend: API must support limit=9 and offset parameters for efficient loading.
Quick Search: Filter products by SKU or Name via a search bar.
Real-time Balance: Ensure stock numbers reflect the latest DB state upon page load.

Module B: Cart & Order Creation (Salesman)
Customer Details: Required field for "Customer Name".
Delivery Logic:Options: Delivery or Pickup.If "Delivery" is selected, an address input field is mandatory.
Promo Code System: * Input field in the Cart/Checkout page.
Validation logic: Check code validity, expiry date, and apply discount (Percentage or Flat Amount).
Validation & Concurrency:Backend must verify stock before order confirmation.
Atomic Transactions: Use PostgreSQL transactions to prevent overselling during concurrent orders.
Official Receipt (OR): System auto-generates a unique OR number and provides a PDF version for download/viewing.

Module C: Payment & Tracking (Salesman)
Workflow: User selects a Pending Payment order to attach a receipt.
File Support: Upload images (JPG/PNG) or PDF bank slips.
Order Progression: Status transitions: Pending -> Payment Under Review -> Completed/Delivered.

Module D: Admin Management Portal (Admin Only)
Fixed Layout: A dashboard with a Fixed Sidebar and Top Navigation. Content switches in the main view area only.
Dashboard KPIs: Real-time stats on Today’s Sales, Pending Orders, and Stock Alerts.

User Management:
View Accounts: List all registered users and their roles.
Suspension: One-click "Suspend" toggle.Suspended users cannot login or place orders.
Role Promotion: Ability to create new Admin accounts or promote a "User" to "Admin".
Marketing Tools: CRUD (Create, Read, Update, Delete) interface for Promo Codes (Code, Type, Value, Expiry).

4. UI/UX & Navigation LogicTop Bar Navigation OrderProduct (Stock) - Browse items.
Cart - Checkout and Promo application.Order - Order tracking and history.
Delivery & Check Payment - Logistics and payment verification status.
Role-Based Data IsolationSalesman View: Can ONLY see orders and activity history created by themselves.
Admin View: Full visibility. Can see all orders, all users, and all system activity logs.
Implementation: Backend must filter queries based on the UserID and Role extracted from the Auth Token.

5. Data Schema (PostgreSQL)
users: id, username, password_hash, role (Admin/Salesman), status (Active/Suspended).
products: id, sku, name, stock_balance, price.
orders: id, order_number, or_number, customer_name, delivery_method, address, total_price, discount_amount, status, created_by_uuid.
order_items: id, order_id, product_id, quantity, unit_price.
payments: id, order_id, receipt_url, uploaded_at.
promo_codes: id, code, discount_type, value, expiry_date, is_active.


6. Non-Functional Requirements
Performance: API response for stock and product pagination $< 200ms$.
Mobile First: UI must be optimized for handheld devices used by sales staff on-the-go.
Security: * Role-Based Access Control (RBAC) enforced on all API endpoints.
File type validation for all uploads.
Integrity: Use row-level locking for stock updates.

7. AI-Assisted Development Plan (3-4 Days)
Day 1: DB Schema setup & FastAPI CRUD generation for Products and Users.
Day 2: Frontend Project Setup. Implement 3x3 Grid, Pagination, and Sidebar Layout.
Day 3: Core Logic: Cart, Promo Code validation, PostgreSQL Transaction for ordering, and PDF generation.
Day 4: Admin Portal (User Mgmt/Promo Mgmt) and E2E Testing (Auth & Role Isolation).