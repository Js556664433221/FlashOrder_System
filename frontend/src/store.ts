import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Product, CartItem, Order, Payment, User, CheckoutData, PromoValidationResult } from './types';
import { api } from './api';

interface AppliedPromo {
  code: string;
  validation: PromoValidationResult;
}

interface Store {
  // User state
  user: User;
  role: 'admin' | 'salesman';
  isAuthenticated: boolean;
  // Data state
  products: Product[];
  categories: string[];
  cart: CartItem[];
  orders: Order[];
  searchQuery: string;
  selectedCategory: string;
  isLoading: boolean;
  error: string | null;
  // Pagination state
  currentPage: number;
  totalPages: number;
  // Admin state
  adminDashboard: AdminDashboard | null;
  // Last placed order for receipt download
  lastPlacedOrder: Order | null;
  // Promo state - single applied promo
  appliedPromo: AppliedPromo | null;
  promoReplacedMessage: string | null;
  setRole: (role: 'admin' | 'salesman') => void;
  setSearchQuery: (q: string) => void;
  setSelectedCategory: (category: string) => void;
  setCurrentPage: (page: number) => void;
  fetchProducts: (page?: number) => Promise<void>;
  fetchCategories: () => Promise<void>;
  addToCart: (product: Product) => void;
  removeFromCart: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  setAppliedPromo: (code: string, validation: PromoValidationResult, wasReplaced?: boolean) => void;
  clearAppliedPromo: () => void;
  clearPromoReplacedMessage: () => void;
  placeOrder: (checkoutData: CheckoutData) => Promise<Order>;
  fetchOrders: () => Promise<void>;
  uploadPayment: (orderId: number, file: File) => Promise<Payment>;
  downloadReceipt: (orderId: number) => Promise<void>;
  clearLastOrder: () => void;
  // Admin methods
  fetchDashboard: () => Promise<void>;
}

interface AdminDashboard {
  total_orders: number;
  today_sales: number;
  pending_orders: number;
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
      user: { id: 1, username: 'Admin User', role: 'admin', is_superadmin: 1 },
      role: 'admin',
      isAuthenticated: true,
      products: [],
      categories: [],
      cart: [],
      orders: [],
      searchQuery: '',
      selectedCategory: '',
      isLoading: false,
      error: null,
      currentPage: 1,
      totalPages: 1,
      adminDashboard: null,
      lastPlacedOrder: null,
      appliedPromo: null,
      promoReplacedMessage: null,

      setRole: (role) => {
        const username = role === 'admin' ? 'Admin User' : 'Salesman User';
        const is_superadmin = role === 'admin' ? 1 : 0;
        set({ role, user: { id: 1, username, role, is_superadmin } });
      },

      setSearchQuery: (q) => set({ searchQuery: q, currentPage: 1 }),

      setSelectedCategory: (category) => set({ selectedCategory: category, currentPage: 1 }),

      setCurrentPage: (page) => set({ currentPage: page }),

      fetchProducts: async (page = 1) => {
        set({ isLoading: true, error: null });
        try {
          const result = await api.getProducts(
            get().searchQuery || undefined,
            get().role,
            page,
            9,
            get().selectedCategory || undefined
          );
          set({ products: result.products, totalPages: result.total_pages, isLoading: false });
        } catch (e) {
          const error = e as Error;
          console.error('fetchProducts error details:', {
            message: error.message,
            name: error.name,
            cause: error.cause,
            stack: error.stack?.split('\n').slice(0, 3).join('\n')
          });
          set({ error: error.message || 'Failed to fetch products', isLoading: false });
        }
      },

      fetchCategories: async () => {
        try {
          const categories = await api.getCategories(get().role);
          set({ categories });
        } catch (e) {
          const error = e as Error;
          console.error('fetchCategories error details:', {
            message: error.message,
            name: error.name,
            cause: error.cause,
            stack: error.stack?.split('\n').slice(0, 3).join('\n')
          });
          // Non-critical, don't update error state
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

      setAppliedPromo: (code: string, validation: PromoValidationResult, wasReplaced = false) => {
        const message = wasReplaced && get().appliedPromo
          ? 'New promo code applied. Previous discount has been replaced.'
          : null;
        set({
          appliedPromo: { code, validation },
          promoReplacedMessage: message,
        });
      },

      clearAppliedPromo: () => set({ appliedPromo: null, promoReplacedMessage: null }),

      clearPromoReplacedMessage: () => set({ promoReplacedMessage: null }),

      placeOrder: async (checkoutData: CheckoutData): Promise<Order> => {
        const cart = get().cart;
        if (cart.length === 0) throw new Error('Cart is empty');

        // Validate checkout data
        if (!checkoutData.customer_name.trim()) {
          throw new Error('Customer name is required');
        }
        if (checkoutData.delivery_method === 'Delivery' && !checkoutData.address?.trim()) {
          throw new Error('Address is required for delivery orders');
        }

        const items = cart.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        }));

        const order = await api.createOrder(items, checkoutData, get().role);
        await get().fetchProducts();
        set({
          cart: [],
          orders: [order, ...get().orders],
          lastPlacedOrder: order
        });
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

      downloadReceipt: async (orderId: number): Promise<void> => {
        try {
          const blob = await api.downloadReceipt(orderId, get().role);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `OR_${orderId}_receipt.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        } catch (e) {
          throw new Error('Failed to download receipt');
        }
      },

      clearLastOrder: () => set({ lastPlacedOrder: null }),

      fetchDashboard: async () => {
        set({ isLoading: true, error: null });
        try {
          const dashboard = await api.getDashboard(get().role);
          set({ adminDashboard: dashboard, isLoading: false });
        } catch (e) {
          set({ error: (e as Error).message, isLoading: false });
        }
      },
    }),
    {
      name: 'flashorder-storage',
      partialize: (state) => ({ role: state.role }),
    }
  )
);
