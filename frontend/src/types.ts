export interface Product {
  id: number;
  sku: string;
  name: string;
  physical_stock: number;
  reserved_stock: number;
  available_stock: number;
  price: number;
  description?: string;
  image_url?: string;
}

export type UserRole = 'staff' | 'admin';

export interface User {
  id: number;
  username: string;
  role: UserRole;
}

export interface OrderItem {
  product_id: number;
  product_name: string;
  product_image_url?: string;
  quantity: number;
  unit_price: number;
}

export type OrderStatus = 'Pending Payment' | 'Payment Under Review' | 'Paid' | 'Cancel Requested' | 'Cancelled';

export interface Order {
  id: number;
  order_number: string;
  total_price: number;
  status: string;
  user_id: number;
  created_at: string;
  items: OrderItem[];
}

export interface Payment {
  id: number;
  order_id: number;
  order_number: string;
  receipt_url: string;
  uploaded_at: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface LowStockAlert {
  id: number;
  sku: string;
  name: string;
  physical_stock: number;
  reserved_stock: number;
  available_stock: number;
  threshold: number;
}

export interface AdminDashboard {
  total_orders: number;
  pending_payments: number;
  paid_orders: number;
  cancelled_orders: number;
  low_stock_alerts: LowStockAlert[];
  total_revenue: number;
}
