import { useEffect, useState } from 'react';
import { ProductList, Cart, PaymentUpload } from './components';
import { useStore } from './store';

type Tab = 'stock' | 'cart' | 'payment';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('stock');
  const { fetchProducts, fetchOrders, cart } = useStore();

  useEffect(() => {
    fetchProducts();
    fetchOrders();
  }, []);

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-purple-600 text-white p-4 shadow-md">
        <h1 className="text-xl font-bold text-center">FlashOrder Portal</h1>
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
        {activeTab === 'cart' && <Cart />}
        {activeTab === 'payment' && <PaymentUpload />}
      </main>
    </div>
  );
}

export default App;
