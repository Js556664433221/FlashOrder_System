import type { Product, Order, Payment } from './types';

const API_BASE = 'http://localhost:8001';

export const api = {
  async getProducts(search?: string): Promise<Product[]> {
    const url = search
      ? `${API_BASE}/products/?search=${encodeURIComponent(search)}`
      : `${API_BASE}/products/`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch products');
    return res.json();
  },

  async getProduct(id: number): Promise<Product> {
    const res = await fetch(`${API_BASE}/products/${id}`);
    if (!res.ok) throw new Error('Failed to fetch product');
    return res.json();
  },

  async getOrders(): Promise<Order[]> {
    const res = await fetch(`${API_BASE}/orders/`);
    if (!res.ok) throw new Error('Failed to fetch orders');
    return res.json();
  },

  async getOrder(id: number): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/${id}`);
    if (!res.ok) throw new Error('Failed to fetch order');
    return res.json();
  },

  async createOrder(items: { product_id: number; quantity: number }[]): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create order');
    }
    return res.json();
  },

  async uploadPayment(orderId: number, file: File): Promise<Payment> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/payments/${orderId}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to upload payment');
    }
    return res.json();
  },
};
