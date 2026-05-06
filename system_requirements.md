这份 `system_requirement.md` 采用了模块化设计，重点突出了 **Vite + TS** 的前端架构和 **PostgreSQL** 的数据一致性，非常适合作为 3-4 天快速开发的指导文档。

---

# System Requirement: FlashOrder Portal

## 1. Project Overview
A lightweight, mobile-responsive web portal designed for frontline sales and counter staff to manage stock inquiries, place orders, and upload payment proofs in real-time.

---

## 2. Technology Stack
*   **Frontend:** Vite + TypeScript + React/Vue 3 + Tailwind CSS.
*   **Backend:** Python (FastAPI) - Asynchronous I/O focus.
*   **Database:** PostgreSQL (Relational, ACID compliant).
*   **AI Tools:** Claude Code / Cursor (for rapid prototyping and logic generation).

---

## 3. Functional Requirements

### Module A: Real-time Stock Balance
*   **Inventory List:** View all products with their current "Available" quantity.
*   **Quick Search:** Filter products by SKU or Name via a search bar.
*   **Data Accuracy:** Ensure stock numbers reflect the latest database state upon page load.

### Module B: Cart & Order Placement
*   **Shopping Cart:** Add/remove items and specify quantities.
*   **Validation:** 
    *   Backend must verify stock availability *before* order confirmation.
    *   Atomic stock deduction (PostgreSQL Transactions) to prevent overselling.
*   **Order Creation:** 
    *   Generate a unique `Order ID`.
    *   Set initial status to `Pending Payment`.

### Module C: Payment Proof Upload
*   **Workflow:** User selects a `Pending Payment` order to attach a receipt.
*   **File Support:** Upload images (JPG/PNG) or PDF bank slips.
*   **Status Update:** Automatically transition order status to `Payment Under Review` upon successful upload.

---

## 4. System Architecture & Data Schema

### Core Database Tables (PostgreSQL)
1.  **`products`**: `id`, `sku`, `name`, `stock_balance`, `price`.
2.  **`orders`**: `id`, `order_number`, `total_price`, `status`, `created_at`.
3.  **`order_items`**: `id`, `order_id`, `product_id`, `quantity`, `unit_price`.
4.  **`payments`**: `id`, `order_id`, `receipt_url`, `uploaded_at`.

---

## 5. Non-Functional Requirements
*   **Performance:** API response for stock inquiry should be $< 200ms$.
*   **Responsiveness:** UI must be optimized for mobile devices (Sales staff on-the-go).
*   **Data Integrity:** Use PostgreSQL row-level locking or transactions to handle concurrent orders safely.
*   **Security:** Basic file type validation for uploads to prevent malicious scripts.

---

## 6. AI-Assisted Development Plan (3-4 Days)
*   **Phase 1:** AI-generated DB Schema & FastAPI boilerplate (CRUD).
*   **Phase 2:** Vite + TS project setup & responsive UI component generation.
*   **Phase 3:** Integration of Order state machine and File Upload logic.
*   **Phase 4:** End-to-end testing (AI-generated unit tests) & Bug fixing.

---

这份文档现在可以作为你 AI 助手的 "System Prompt" 或者开发指南。既然你要用 Vite + TS，建议你在初始化项目时直接让 AI 帮你生成对应的 **Interface** 定义，这样后期对接 FastAPI 的 JSON 响应时会非常丝滑。需要我帮你写一份初始的 `types.ts` 定义吗？