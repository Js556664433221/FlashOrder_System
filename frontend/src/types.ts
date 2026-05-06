export interface Product {
  id: number;
  sku: string;
  name: string;
  stock_balance: number;
  price: number;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
}

export type OrderStatus = 'Pending Payment' | 'Payment Under Review' | 'Paid' | 'Cancelled';

export interface Order {
  id: number;
  order_number: string;
  total_price: number;
  status: OrderStatus;
  created_at: string;
  items?: OrderItem[];
}

export interface Payment {
  id: number;
  order_id: number;
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
