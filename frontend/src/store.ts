import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Product, CartItem, Order, Payment, User } from './types';
import { api } from './api';

interface Store {
  // User state
  user: User;
  role: 'admin' | 'staff';
  isAuthenticated: boolean;
  // Data state
  products: Product[];
  cart: CartItem[];
  orders: Order[];
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
  // Admin state
  adminDashboard: AdminDashboard | null;
  setRole: (role: 'admin' | 'staff') => void;
  setSearchQuery: (q: string) => void;
  fetchProducts: () => Promise<void>;
  addToCart: (product: Product) => void;
  removeFromCart: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  placeOrder: () => Promise<Order>;
  fetchOrders: () => Promise<void>;
  uploadPayment: (orderId: number, file: File) => Promise<Payment>;
  // Admin methods
  fetchDashboard: () => Promise<void>;
}

interface AdminDashboard {
  total_orders: number;
  pending_payments: number;
  paid_orders: number;
  cancelled_orders: number;
  low_stock_alerts: LowStockAlert[];
  total_revenue: number;
}

interface LowStockAlert {
  id: number;
  sku: string;
  name: string;
  physical_stock: number;
  reserved_stock: number;
  available_stock: number;
  threshold: number;
}

export const useStore = create<Store>()(
  persist(
    (set, get) => ({
      user: { id: 1, username: 'Staff User', role: 'staff' },
      role: 'staff',
      isAuthenticated: true,
      products: [],
      cart: [],
      orders: [],
      searchQuery: '',
      isLoading: false,
      error: null,
      adminDashboard: null,

      setRole: (role) => {
        const username = role === 'admin' ? 'Admin User' : 'Staff User';
        set({ role, user: { id: 1, username, role } });
      },

      setSearchQuery: (q) => set({ searchQuery: q }),

      fetchProducts: async () => {
        set({ isLoading: true, error: null });
        try {
          const products = await api.getProducts(get().searchQuery || undefined, get().role);
          set({ products, isLoading: false });
        } catch (e) {
          set({ error: (e as Error).message, isLoading: false });
        }
      },

      addToCart: (product) => {
        const cart = get().cart;
        const existing = cart.find((item) => item.product.id === product.id);
        if (existing) {
          set({
            cart: cart.map((item) =>
              item.product.id === product.id
                ? { ...item, quantity: item.quantity + 1 }
                : item
            ),
          });
        } else {
          set({ cart: [...cart, { product, quantity: 1 }] });
        }
      },

      removeFromCart: (productId) => {
        set({ cart: get().cart.filter((item) => item.product.id !== productId) });
      },

      updateQuantity: (productId, quantity) => {
        if (quantity <= 0) {
          get().removeFromCart(productId);
          return;
        }
        set({
          cart: get().cart.map((item) =>
            item.product.id === productId ? { ...item, quantity } : item
          ),
        });
      },

      clearCart: () => set({ cart: [] }),

      placeOrder: async () => {
        const cart = get().cart;
        if (cart.length === 0) throw new Error('Cart is empty');
        const items = cart.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        }));
        const order = await api.createOrder(items, get().role);
        await get().fetchProducts();
        set({ cart: [], orders: [...get().orders, order] });
        return order;
      },

      fetchOrders: async () => {
        try {
          const orders = await api.getOrders(get().role);
          set({ orders });
        } catch (e) {
          set({ error: (e as Error).message });
        }
      },

      uploadPayment: async (orderId: number, file: File): Promise<Payment> => {
        const payment = await api.uploadPayment(orderId, file, get().role);
        await get().fetchOrders();
        return payment;
      },

      fetchDashboard: async () => {
        try {
          const dashboard = await api.getDashboard(get().role);
          set({ adminDashboard: dashboard });
        } catch (e) {
          set({ error: (e as Error).message });
        }
      },
    }),
    {
      name: 'flashorder-storage',
      partialize: (state) => ({ role: state.role }),
    }
  )
);
