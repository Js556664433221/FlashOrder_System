import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { ProductManagement } from './ProductManagement';

type AdminTab = 'dashboard' | 'products';

export function AdminDashboard() {
  const { adminDashboard, fetchDashboard, user } = useStore();
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard');

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (!adminDashboard) {
    return (
      <div className="p-8 text-center">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'dashboard'
              ? 'text-purple-600 border-b-2 border-purple-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('products')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'products'
              ? 'text-purple-600 border-b-2 border-purple-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Manage Products
        </button>
      </div>

      {activeTab === 'dashboard' ? (
        <DashboardView adminDashboard={adminDashboard} user={user} />
      ) : (
        <ProductManagement />
      )}
    </div>
  );
}

function DashboardView({ adminDashboard, user }: { adminDashboard: any; user: any }) {
  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Admin Dashboard</h2>
        <span className="text-sm text-gray-500">Logged in as: {user?.username} ({user?.role})</span>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-3xl font-bold text-blue-600">{adminDashboard.total_orders}</div>
          <div className="text-sm text-gray-600">Total Orders</div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <div className="text-3xl font-bold text-yellow-600">{adminDashboard.pending_payments}</div>
          <div className="text-sm text-gray-600">Pending Payments</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="text-3xl font-bold text-green-600">{adminDashboard.paid_orders}</div>
          <div className="text-sm text-gray-600">Paid Orders</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <div className="text-3xl font-bold text-purple-600">${adminDashboard.total_revenue.toFixed(2)}</div>
          <div className="text-sm text-gray-600">Total Revenue</div>
        </div>
      </div>

      {/* Low Stock Alerts */}
      <div className="bg-red-50 p-4 rounded-lg border border-red-200 mb-8">
        <h3 className="text-lg font-semibold text-red-700 mb-3">
          Low Stock Alerts (Threshold: {adminDashboard.low_stock_alerts[0]?.threshold || 10})
        </h3>
        {adminDashboard.low_stock_alerts.length === 0 ? (
          <p className="text-gray-600">No low stock products.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-red-200">
                  <th className="text-left py-2">ID</th>
                  <th className="text-left py-2">SKU</th>
                  <th className="text-left py-2">Name</th>
                  <th className="text-right py-2">Available</th>
                  <th className="text-right py-2">Reserved</th>
                  <th className="text-right py-2">Total</th>
                </tr>
              </thead>
              <tbody>
                {adminDashboard.low_stock_alerts.map((product: any) => (
                  <tr key={product.id} className="border-b border-red-100">
                    <td className="py-2">{product.id}</td>
                    <td className="py-2">{product.sku}</td>
                    <td className="py-2">{product.name}</td>
                    <td className="py-2 text-right text-red-600 font-semibold">{product.available_stock}</td>
                    <td className="py-2 text-right">{product.reserved_stock}</td>
                    <td className="py-2 text-right">{product.physical_stock}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Order Stats */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-3">Order Statistics</h3>
        <div className="flex gap-8">
          <div>
            <span className="text-gray-500">Cancelled Orders:</span>
            <span className="ml-2 font-semibold">{adminDashboard.cancelled_orders}</span>
          </div>
          <div>
            <span className="text-gray-500">Average Order Value:</span>
            <span className="ml-2 font-semibold">
              ${adminDashboard.paid_orders > 0 ? (adminDashboard.total_revenue / adminDashboard.paid_orders).toFixed(2) : '0.00'}
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
