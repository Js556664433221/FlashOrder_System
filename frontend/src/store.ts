import { create } from 'zustand';
import type { Product, CartItem, Order, Payment } from './types';
import { api } from './api';

interface Store {
  products: Product[];
  cart: CartItem[];
  orders: Order[];
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
  setSearchQuery: (q: string) => void;
  fetchProducts: () => Promise<void>;
  addToCart: (product: Product) => void;
  removeFromCart: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  placeOrder: () => Promise<Order>;
  fetchOrders: () => Promise<void>;
  uploadPayment: (orderId: number, file: File) => Promise<Payment>;
}

export const useStore = create<Store>((set, get) => ({
  products: [],
  cart: [],
  orders: [],
  searchQuery: '',
  isLoading: false,
  error: null,

  setSearchQuery: (q) => set({ searchQuery: q }),

  fetchProducts: async () => {
    set({ isLoading: true, error: null });
    try {
      const products = await api.getProducts(get().searchQuery || undefined);
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
    const order = await api.createOrder(items);
    set({ cart: [], orders: [...get().orders, order] });
    return order;
  },

  fetchOrders: async () => {
    try {
      const orders = await api.getOrders();
      set({ orders });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  uploadPayment: async (orderId: number, file: File): Promise<Payment> => {
    const payment = await api.uploadPayment(orderId, file);
    await get().fetchOrders();
    return payment;
  },
}));
