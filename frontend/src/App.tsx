import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ProductList, Cart, PaymentUpload, OrdersList } from './components';
import { AdminLayout } from './components/AdminLayout';
import {
  DashboardPage,
  StockPage,
  OrdersPage,
  UsersPage,
  MarketingPage,
} from './pages/admin';
import { useStore } from './store';

type Tab = 'stock' | 'cart' | 'payment' | 'orders';

function ShopApp() {
  const [activeTab, setActiveTab] = useState<Tab>('stock');
  const { fetchProducts, fetchOrders, cart, user, role, setRole } = useStore();
  const navigate = useNavigate();

  const handleSwitchToAdmin = () => {
    setRole('admin');
    navigate('/admin/dashboard');
  };

  useEffect(() => {
    fetchProducts();
    fetchOrders();
  }, [role]);

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="min-h-screen bg-surface-100">
      {/* Glassmorphic Header */}
      <header className="sticky top-0 z-50 bg-primary-600/90 backdrop-blur-md text-white shadow-lg border-b border-primary-500/20">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">FlashOrder Portal</h1>
            <p className="text-sm opacity-80">Welcome, {user.username} ({user.role})</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleSwitchToAdmin}
              className="bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all border border-white/20"
            >
              Admin Panel
            </button>
          </div>
        </div>
      </header>

      {/* Glassmorphic Navigation Tabs */}
      <nav className="sticky top-[72px] z-40 bg-surface-50/80 backdrop-blur-md border-b border-primary-500/20">
        <div className="max-w-4xl mx-auto flex">
          <button
            onClick={() => setActiveTab('stock')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'stock'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-dark-500 hover:text-dark-700'
            }`}
          >
            Product (Stock)
          </button>
          <button
            onClick={() => setActiveTab('cart')}
            className={`flex-1 py-3 text-center font-medium transition-colors relative ${
              activeTab === 'cart'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-dark-500 hover:text-dark-700'
            }`}
          >
            Cart
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-accent-red text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-semibold">
                {cartCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('orders')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'orders'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-dark-500 hover:text-dark-700'
            }`}
          >
            Order
          </button>
          <button
            onClick={() => setActiveTab('payment')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'payment'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-dark-500 hover:text-dark-700'
            }`}
          >
            Delivery & Check Payment
          </button>
        </div>
      </nav>

      {/* Main Content - White for contrast */}
      <main className="max-w-4xl mx-auto bg-white shadow-lg min-h-screen">
        {activeTab === 'stock' && <ProductList />}
        {activeTab === 'orders' && <OrdersList />}
        {activeTab === 'cart' && <Cart />}
        {activeTab === 'payment' && <PaymentUpload />}
      </main>
    </div>
  );
}

function AdminGuard() {
  const { role } = useStore();
  if (role !== 'admin') {
    return <Navigate to="/" replace />;
  }
  return <AdminLayout />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ShopApp />} />
      <Route path="/admin" element={<AdminGuard />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="stock" element={<StockPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="marketing" element={<MarketingPage />} />
      </Route>
    </Routes>
  );
}
