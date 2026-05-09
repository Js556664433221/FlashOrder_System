import type { Product, Order, Payment, AdminDashboard, CheckoutData, PromoValidationResult, CustomerProfile, CustomerProfileCreate } from './types';

const API_BASE = 'http://localhost:8000';

function authHeaders(role: 'admin' | 'salesman' | null): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (role) {
    headers['X-Simulated-Role'] = role;
  }
  return headers;
}

function authHeadersNoJson(role: 'admin' | 'salesman' | null): Record<string, string> {
  const headers: Record<string, string> = {};
  if (role) {
    headers['X-Simulated-Role'] = role;
  }
  return headers;
}

// JWT-based auth header (for real authentication)
function jwtHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export interface AuthUser {
  id: number;
  username: string;
  role: string;
}

export const api = {
  // Authentication
  async getCurrentUser(token: string): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: jwtHeaders(token),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to get current user');
    }
    return res.json();
  },

  // Products
  async getProducts(search?: string, role?: 'admin' | 'salesman' | null): Promise<Product[]> {
    const url = search
      ? `${API_BASE}/products/?search=${encodeURIComponent(search)}`
      : `${API_BASE}/products/`;
    const res = await fetch(url, { headers: authHeaders(role || 'salesman') });
    if (!res.ok) throw new Error('Failed to fetch products');
    return res.json();
  },

  async getProduct(id: number, role?: 'admin' | 'salesman' | null): Promise<Product> {
    const res = await fetch(`${API_BASE}/products/${id}`, { headers: authHeaders(role || 'salesman') });
    if (!res.ok) throw new Error('Failed to fetch product');
    return res.json();
  },

  // Orders
  async getOrders(role?: 'admin' | 'salesman' | null): Promise<Order[]> {
    const endpoint = role === 'admin' ? '/admin/orders/' : '/orders/';
    const res = await fetch(`${API_BASE}${endpoint}`, { headers: authHeaders(role || 'salesman') });
    if (!res.ok) throw new Error('Failed to fetch orders');
    return res.json();
  },

  async getOrder(id: number, role?: 'admin' | 'salesman' | null): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/${id}`, { headers: authHeaders(role || 'salesman') });
    if (!res.ok) throw new Error('Failed to fetch order');
    return res.json();
  },

  async createOrder(
    items: { product_id: number; quantity: number }[],
    checkoutData: CheckoutData,
    role?: 'admin' | 'salesman' | null
  ): Promise<Order> {
    const payload = {
      items,
      customer_name: checkoutData.customer_name,
      delivery_method: checkoutData.delivery_method,
      address: checkoutData.address || undefined,
      promo_code: checkoutData.promo_code || undefined,
      remark: checkoutData.remark || undefined,
    };
    const res = await fetch(`${API_BASE}/orders/`, {
      method: 'POST',
      headers: authHeaders(role || 'salesman'),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create order');
    }
    return res.json();
  },

  getReceiptUrl(orderId: number, _role?: 'admin' | 'salesman' | null): string {
    return `${API_BASE}/orders/${orderId}/receipt`;
  },

  async downloadReceipt(orderId: number, role?: 'admin' | 'salesman' | null): Promise<Blob> {
    const res = await fetch(`${API_BASE}/orders/${orderId}/receipt`, {
      method: 'GET',
      headers: authHeadersNoJson(role || 'salesman'),
    });
    if (!res.ok) throw new Error('Failed to download receipt');
    return res.blob();
  },

  async uploadPayment(orderId: number, file: File, role?: 'admin' | 'salesman' | null): Promise<Payment> {
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

  // Promo Code Validation
  async validatePromoCode(code: string, cartTotal: number, role?: 'admin' | 'salesman' | null): Promise<PromoValidationResult> {
    const res = await fetch(`${API_BASE}/promo/validate`, {
      method: 'POST',
      headers: authHeaders(role || 'salesman'),
      body: JSON.stringify({ code, cart_total: cartTotal }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to validate promo code');
    }
    return res.json();
  },

  // Promo Code Management (Admin)
  async getPromoCodes(includeInactive: boolean = false, role?: 'admin' | 'salesman' | null): Promise<PromoCodeResponse[]> {
    const url = includeInactive
      ? `${API_BASE}/admin/promo/?include_inactive=true`
      : `${API_BASE}/admin/promo/`;
    const res = await fetch(url, { headers: authHeaders(role || 'admin') });
    if (!res.ok) throw new Error('Failed to fetch promo codes');
    return res.json();
  },

  async createPromoCode(data: { code: string; discount_type: 'percentage' | 'flat'; value: number; expiry_date?: string; is_active?: boolean }, role?: 'admin' | 'salesman' | null): Promise<PromoCodeResponse> {
    const res = await fetch(`${API_BASE}/admin/promo/`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create promo code');
    }
    return res.json();
  },

  async updatePromoCode(promoId: number, data: Partial<{ code: string; discount_type: 'percentage' | 'flat'; value: number; expiry_date?: string; is_active?: boolean }>, role?: 'admin' | 'salesman' | null): Promise<PromoCodeResponse> {
    const res = await fetch(`${API_BASE}/admin/promo/${promoId}`, {
      method: 'PATCH',
      headers: authHeaders(role || 'admin'),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to update promo code');
    }
    return res.json();
  },

  async deletePromoCode(promoId: number, role?: 'admin' | 'salesman' | null): Promise<void> {
    const res = await fetch(`${API_BASE}/admin/promo/${promoId}`, {
      method: 'DELETE',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to delete promo code');
    }
  },

  async activatePromoCode(promoId: number, role?: 'admin' | 'salesman' | null): Promise<PromoCodeResponse> {
    const res = await fetch(`${API_BASE}/admin/promo/${promoId}/activate`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to activate promo code');
    }
    return res.json();
  },

  async deactivatePromoCode(promoId: number, role?: 'admin' | 'salesman' | null): Promise<PromoCodeResponse> {
    const res = await fetch(`${API_BASE}/admin/promo/${promoId}/deactivate`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to deactivate promo code');
    }
    return res.json();
  },

  async getPromoStats(role?: 'admin' | 'salesman' | null): Promise<PromoStatsResponse[]> {
    const res = await fetch(`${API_BASE}/admin/promo/stats`, {
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) throw new Error('Failed to fetch promo stats');
    return res.json();
  },

  // Admin Dashboard
  async getDashboard(role?: 'admin' | 'salesman' | null): Promise<AdminDashboard> {
    const res = await fetch(`${API_BASE}/admin/dashboard/summary`, {
      headers: authHeaders(role || 'salesman'),
    });
    if (!res.ok) throw new Error('Failed to fetch dashboard');
    return res.json();
  },

  // Customer Profiles
  async getCustomers(role?: 'admin' | 'salesman' | null): Promise<CustomerProfile[]> {
    const res = await fetch(`${API_BASE}/customers/`, {
      headers: authHeaders(role || 'salesman'),
    });
    if (!res.ok) throw new Error('Failed to fetch customers');
    return res.json();
  },

  async createCustomer(data: CustomerProfileCreate, role?: 'admin' | 'salesman' | null): Promise<CustomerProfile> {
    const res = await fetch(`${API_BASE}/customers/`, {
      method: 'POST',
      headers: authHeaders(role || 'salesman'),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create customer');
    }
    return res.json();
  },

  // User Management
  async getUsers(role?: 'admin' | 'salesman' | null): Promise<UserResponse[]> {
    const res = await fetch(`${API_BASE}/admin/users`, {
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  },

  async toggleUserStatus(userId: number, role?: 'admin' | 'salesman' | null): Promise<UserStatusUpdateResponse> {
    const res = await fetch(`${API_BASE}/admin/users/${userId}/status`, {
      method: 'PATCH',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to toggle user status');
    }
    return res.json();
  },

  async createAdmin(data: { username: string; email: string; password: string }, role?: 'admin' | 'salesman' | null): Promise<CreateAdminResponse> {
    const res = await fetch(`${API_BASE}/admin/create-admin`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create admin');
    }
    return res.json();
  },

  async promoteUser(userId: number, role?: 'admin' | 'salesman' | null): Promise<PromoteUserResponse> {
    const res = await fetch(`${API_BASE}/admin/users/${userId}/promote`, {
      method: 'PATCH',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to promote user');
    }
    return res.json();
  },

  // Admin Order Management
  async updateAdminOrder(
    orderId: number,
    data: { status?: string; remark?: string; items?: { product_id: number; quantity: number }[] },
    role?: 'admin' | 'salesman' | null
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/orders/${orderId}`, {
      method: 'PATCH',
      headers: authHeaders(role || 'admin'),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to update order');
    }
    return res.json();
  },

  async confirmPayment(orderId: number, role?: 'admin' | 'salesman' | null): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/orders/${orderId}/confirm-payment`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to confirm payment');
    }
    return res.json();
  },

  async forceCancelOrder(orderId: number, role?: 'admin' | 'salesman' | null): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/orders/${orderId}/cancel`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to cancel order');
    }
    return res.json();
  },

  async rejectPayment(orderId: number, reason: string, role?: 'admin' | 'salesman' | null): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/orders/${orderId}/reject-payment`, {
      method: 'POST',
      headers: authHeaders(role || 'admin'),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to reject payment');
    }
    return res.json();
  },
};

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'salesman';
  status: 'Active' | 'Suspended';
  is_active: number;
  is_superadmin: number;
  created_at: string;
}

export interface UserStatusUpdateResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  message: string;
}

export interface CreateAdminResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  message: string;
}

export interface PromoteUserResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  message: string;
}

export interface PromoCodeResponse {
  id: number;
  code: string;
  discount_type: 'percentage' | 'flat';
  value: number;
  expiry_date: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PromoStatsResponse {
  id: number;
  code: string;
  discount_type: 'percentage' | 'flat';
  value: number;
  expiry_date: string | null;
  is_active: boolean;
  usage_count: number;
  total_discount_given: number;
  created_at: string;
}
