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

export type UserRole = 'salesman' | 'admin';
export type UserStatus = 'Active' | 'Suspended';

export interface User {
  id: number;
  username: string;
  email?: string;
  role: UserRole;
  status?: UserStatus;
  is_active?: number;
  is_superadmin?: number;
  created_at?: string;
}

export interface OrderItem {
  product_id: number;
  product_name: string;
  product_image_url?: string;
  product_sku?: string;
  quantity: number;
  unit_price: number;
}

export interface Payment {
  id: number;
  order_id: number;
  receipt_url: string;
  rejection_reason?: string;
  rejected_at?: string;
  uploaded_at: string;
}

export type OrderStatus =
  | 'Pending Payment'
  | 'Payment Under Review'
  | 'Payment Rejected'
  | 'Paid'
  | 'Preparing'
  | 'Ready for Pickup'
  | 'Shipped'
  | 'Completed'
  | 'Cancel Requested'
  | 'Cancelled';

export type DeliveryMethod = 'Delivery' | 'Pickup';

export interface Order {
  id: number;
  order_number: string;
  or_number: string;
  customer_name: string;
  delivery_method: DeliveryMethod;
  address?: string;
  total_price: number;
  discount_amount: number;
  status: string;
  remark?: string;
  user_id: number;
  created_at: string;
  items: OrderItem[];
  payment?: Payment;
}

export interface CheckoutData {
  customer_name: string;
  delivery_method: DeliveryMethod;
  address?: string;
  promo_code?: string;
  remark?: string;
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
  today_sales: number;
  pending_orders: number;
  paid_orders: number;
  cancelled_orders: number;
  low_stock_alerts: LowStockAlert[];
  total_revenue: number;
}

export interface PromoValidationResult {
  valid: boolean;
  code?: string;
  discount_type?: 'percentage' | 'flat';
  discount_value?: number;
  message: string;
}

export interface CustomerProfile {
  id: number;
  salesman_id: number;
  name: string;
  company_name?: string;
  location?: string;
  contact_number: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerProfileCreate {
  name: string;
  company_name?: string;
  location?: string;
  contact_number: string;
  email?: string;
}
