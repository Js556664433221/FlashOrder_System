import type { Product, Order, Payment, AdminDashboard } from './types';

const API_BASE = 'http://localhost:8002';

function authHeaders(role: 'admin' | 'staff' | null): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (role) {
    headers['X-Simulated-Role'] = role;
  }
  return headers;
}

export const api = {
  // Products
  async getProducts(search?: string, role?: 'admin' | 'staff' | null): Promise<Product[]> {
    const url = search
      ? `${API_BASE}/products/?search=${encodeURIComponent(search)}`
      : `${API_BASE}/products/`;
    const res = await fetch(url, { headers: authHeaders(role || 'staff') });
    if (!res.ok) throw new Error('Failed to fetch products');
    return res.json();
  },

  async getProduct(id: number, role?: 'admin' | 'staff' | null): Promise<Product> {
    const res = await fetch(`${API_BASE}/products/${id}`, { headers: authHeaders(role || 'staff') });
    if (!res.ok) throw new Error('Failed to fetch product');
    return res.json();
  },

  // Orders
  async getOrders(role?: 'admin' | 'staff' | null): Promise<Order[]> {
    const endpoint = role === 'admin' ? '/admin/orders/' : '/orders/';
    const res = await fetch(`${API_BASE}${endpoint}`, { headers: authHeaders(role || 'staff') });
    if (!res.ok) throw new Error('Failed to fetch orders');
    return res.json();
  },

  async getOrder(id: number, role?: 'admin' | 'staff' | null): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/${id}`, { headers: authHeaders(role || 'staff') });
    if (!res.ok) throw new Error('Failed to fetch order');
    return res.json();
  },

  async createOrder(items: { product_id: number; quantity: number }[], role?: 'admin' | 'staff' | null): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/`, {
      method: 'POST',
      headers: authHeaders(role || 'staff'),
      body: JSON.stringify({ items }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create order');
    }
    return res.json();
  },

  async uploadPayment(orderId: number, file: File, role?: 'admin' | 'staff' | null): Promise<Payment> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/payments/${orderId}/upload`, {
      method: 'POST',
      headers: { 'X-Simulated-Role': role || 'staff' },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to upload payment');
    }
    return res.json();
  },

  // Admin Dashboard
  async getDashboard(role?: 'admin' | 'staff' | null): Promise<AdminDashboard> {
    const res = await fetch(`${API_BASE}/admin/dashboard/summary`, {
      headers: authHeaders(role || 'staff'),
    });
    if (!res.ok) throw new Error('Failed to fetch dashboard');
    return res.json();
  },
};
