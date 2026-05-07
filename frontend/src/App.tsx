import { useEffect, useState } from 'react';
import { ProductList, Cart, PaymentUpload, AdminDashboard, AdminNavBar, OrdersList } from './components';
import { useStore } from './store';

type Tab = 'stock' | 'cart' | 'payment' | 'orders';

function ShopApp() {
  const [activeTab, setActiveTab] = useState<Tab>('stock');
  const { fetchProducts, fetchOrders, cart, user, role, setRole } = useStore();

  const isAdmin = role === 'admin';

  // Refresh data when role changes
  useEffect(() => {
    fetchProducts();
    fetchOrders();
  }, [role]);

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  const handleSwitchToAdmin = () => {
    setRole('admin');
    // Scroll to admin section after state updates
    setTimeout(() => {
      document.getElementById('admin-section')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleSwitchToStaff = () => {
    setRole('staff');
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-purple-600 text-white p-4 shadow-md">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">FlashOrder Portal</h1>
            <p className="text-sm opacity-75">Welcome, {user.username} ({user.role})</p>
          </div>
          <div className="flex gap-3">
            {isAdmin ? (
              <button
                onClick={handleSwitchToStaff}
                className="bg-white text-purple-600 px-4 py-2 rounded text-sm font-bold hover:bg-gray-100"
              >
                Switch to Staff
              </button>
            ) : (
              <button
                onClick={handleSwitchToAdmin}
                className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded text-sm font-bold"
              >
                Switch to Admin
              </button>
            )}
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex">
          <button
            onClick={() => setActiveTab('stock')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'stock'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Stock
          </button>
          <button
            onClick={() => setActiveTab('orders')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'orders'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Orders
          </button>
          <button
            onClick={() => setActiveTab('cart')}
            className={`flex-1 py-3 text-center font-medium transition-colors relative ${
              activeTab === 'cart'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Cart
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                {cartCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('payment')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'payment'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Payment
          </button>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto bg-white shadow-lg min-h-screen">
        {activeTab === 'stock' && <ProductList />}
        {activeTab === 'orders' && <OrdersList />}
        {activeTab === 'cart' && <Cart />}
        {activeTab === 'payment' && <PaymentUpload />}

        {/* Admin Dashboard Section - only for admins */}
        {isAdmin && (
          <div id="admin-section">
            <AdminNavBar onBackToShop={() => setActiveTab('stock')} />
            <AdminDashboard />
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return <ShopApp />;
}
