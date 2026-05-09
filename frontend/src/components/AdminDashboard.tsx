import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { ProductManagement } from './ProductManagement';
import {
  TrendingUp,
  Clock,
  AlertTriangle,
  Package,
  ShoppingCart,
  DollarSign,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { formatCurrency } from '../utils';
import { KPICardSkeleton, FadeInContent } from './LoadingSpinner';

type AdminTab = 'dashboard' | 'products';

export function AdminDashboard() {
  const { adminDashboard, fetchDashboard, isLoading, error } = useStore();
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleRefresh = () => {
    fetchDashboard();
  };

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-dark-800">Dashboard Overview</h2>
          <p className="text-sm text-dark-500">Real-time statistics and metrics</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-surface-50 border border-dark-200 rounded-xl hover:bg-surface-100 transition-colors disabled:opacity-50 shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''} text-primary-600`} />
          <span className="text-sm font-medium text-dark-700">Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-200 mb-6">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'dashboard'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-dark-500 hover:text-dark-700'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('products')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'products'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-dark-500 hover:text-dark-700'
          }`}
        >
          Manage Products
        </button>
      </div>

      {activeTab === 'dashboard' ? (
        error && !adminDashboard ? (
          <ErrorState message={error} onRetry={handleRefresh} />
        ) : adminDashboard ? (
          <DashboardView adminDashboard={adminDashboard} onRefresh={handleRefresh} />
        ) : (
          <LoadingSkeleton />
        )
      ) : (
        <ProductManagement />
      )}
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="bg-surface-50 rounded-xl border border-accent-red/30 p-8 text-center shadow-sm">
      <div className="w-16 h-16 bg-accent-red/10 rounded-full flex items-center justify-center mx-auto mb-4">
        <AlertTriangle className="w-8 h-8 text-accent-red" />
      </div>
      <h3 className="text-lg font-semibold text-dark-800 mb-2">Failed to Load Dashboard</h3>
      <p className="text-dark-600 mb-4">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
      >
        Retry
      </button>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* KPI Cards Skeleton with Spinner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <KPICardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

interface DashboardViewProps {
  adminDashboard: any;
  onRefresh: () => void;
}

function DashboardView({ adminDashboard }: DashboardViewProps) {
  // Safe access with fallback defaults
  const todaySales = adminDashboard?.today_sales ?? 0;
  const pendingOrders = adminDashboard?.pending_orders ?? 0;
  const lowStockAlerts = adminDashboard?.low_stock_alerts ?? [];
  const totalRevenue = adminDashboard?.total_revenue ?? 0;
  const totalOrders = adminDashboard?.total_orders ?? 0;
  const paidOrders = adminDashboard?.paid_orders ?? 0;
  const cancelledOrders = adminDashboard?.cancelled_orders ?? 0;

  const kpiCards = [
    {
      id: 'today-sales',
      title: "Today's Sales",
      value: formatCurrency(todaySales),
      icon: TrendingUp,
      color: 'green',
      bgGradient: 'from-green-50 to-emerald-50',
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      borderColor: 'border-green-200',
    },
    {
      id: 'pending-orders',
      title: 'Pending Orders',
      value: pendingOrders.toString(),
      icon: Clock,
      color: 'yellow',
      bgGradient: 'from-yellow-50 to-amber-50',
      iconBg: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      borderColor: 'border-yellow-200',
    },
    {
      id: 'low-stock',
      title: 'Stock Alerts',
      value: lowStockAlerts.length.toString(),
      icon: AlertTriangle,
      color: 'red',
      bgGradient: 'from-red-50 to-rose-50',
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      borderColor: 'border-red-200',
      highlight: lowStockAlerts.length > 0,
    },
    {
      id: 'total-revenue',
      title: 'Total Revenue',
      value: formatCurrency(totalRevenue),
      icon: DollarSign,
      color: 'purple',
      bgGradient: 'from-primary-50 to-primary-100',
      iconBg: 'bg-primary-100',
      iconColor: 'text-primary-600',
      borderColor: 'border-primary-200',
    },
  ];

  const orderStats = [
    {
      label: 'Total Orders',
      value: totalOrders,
      icon: ShoppingCart,
      color: 'blue',
    },
    {
      label: 'Paid Orders',
      value: paidOrders,
      icon: CheckCircle,
      color: 'green',
    },
    {
      label: 'Cancelled',
      value: cancelledOrders,
      icon: XCircle,
      color: 'gray',
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid with fade-in */}
      <FadeInContent isLoading={false} minHeight="auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiCards.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.id}
                className={`relative bg-gradient-to-br ${card.bgGradient} rounded-xl border ${card.borderColor} p-5 overflow-hidden transition-all hover:shadow-md animate-fade-in`}
              >
                {/* Background decoration */}
                <div className="absolute top-0 right-0 w-20 h-20 opacity-10 transform translate-x-6 -translate-y-6">
                  <Icon className={`w-full h-full ${card.highlight ? 'text-red-500' : `text-${card.color}-500`}`} />
                </div>

                <div className="relative">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-dark-600">{card.title}</span>
                    <div className={`p-2 rounded-lg ${card.iconBg}`}>
                      <Icon className={`w-5 h-5 ${card.iconColor}`} />
                    </div>
                  </div>
                  <div className={`text-2xl lg:text-3xl font-bold ${card.highlight ? 'text-red-600' : `text-${card.color}-700`}`}>
                    {card.value}
                  </div>
                  {card.highlight && card.id === 'low-stock' && (
                    <div className="mt-2 flex items-center gap-1 text-xs text-red-600 font-medium">
                      <AlertCircle className="w-3 h-3" />
                      Action required
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </FadeInContent>

      {/* Order Statistics Row */}
      <div className="bg-surface-50 rounded-xl border border-dark-200 p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-dark-800 mb-4">Order Statistics</h3>
        <div className="grid grid-cols-3 gap-4">
          {orderStats.map((stat) => {
            const Icon = stat.icon;
            const colorClasses: Record<string, string> = {
              blue: 'text-accent-blue bg-accent-blue/10',
              green: 'text-accent-green bg-accent-green/10',
              gray: 'text-dark-500 bg-dark-100',
            };
            return (
              <div key={stat.label} className="text-center p-4 rounded-xl bg-surface-100">
                <div className={`inline-flex p-2 rounded-lg mb-2 ${colorClasses[stat.color]}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="text-2xl font-bold text-dark-800">{stat.value}</div>
                <div className="text-sm text-dark-500">{stat.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Low Stock Alerts */}
      <div className={`rounded-xl border p-5 ${lowStockAlerts.length > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
        <div className="flex items-center gap-2 mb-4">
          <Package className={`w-5 h-5 ${lowStockAlerts.length > 0 ? 'text-red-600' : 'text-green-600'}`} />
          <h3 className={`text-lg font-semibold ${lowStockAlerts.length > 0 ? 'text-red-700' : 'text-green-700'}`}>
            Stock Alerts
            {lowStockAlerts.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-sm rounded-full">
                {lowStockAlerts.length}
              </span>
            )}
          </h3>
        </div>

        {lowStockAlerts.length === 0 ? (
          <div className="text-center py-6">
            <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-2" />
            <p className="text-green-700 font-medium">All products are well-stocked!</p>
            <p className="text-sm text-green-600">No inventory issues detected.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-red-200">
                  <th className="text-left py-2 px-2 font-semibold text-red-700">SKU</th>
                  <th className="text-left py-2 px-2 font-semibold text-red-700">Product Name</th>
                  <th className="text-right py-2 px-2 font-semibold text-red-700">Available</th>
                  <th className="text-right py-2 px-2 font-semibold text-red-700">Threshold</th>
                  <th className="text-right py-2 px-2 font-semibold text-red-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {lowStockAlerts.map((product: any) => (
                  <tr key={product.id} className="border-b border-red-100 hover:bg-red-100/50">
                    <td className="py-2 px-2 font-mono text-dark-500">{product.sku}</td>
                    <td className="py-2 px-2 font-medium text-dark-800">{product.name}</td>
                    <td className="py-2 px-2 text-right font-bold text-red-600">{product.available_stock}</td>
                    <td className="py-2 px-2 text-right text-dark-500">{product.threshold}</td>
                    <td className="py-2 px-2 text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        product.available_stock === 0
                          ? 'bg-red-200 text-red-800'
                          : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {product.available_stock === 0 ? 'Out of Stock' : 'Low Stock'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Stats Footer */}
      <div className="text-center text-sm text-dark-500">
        <p>
          Average Order Value: <span className="font-semibold text-dark-700">
            {paidOrders > 0 ? formatCurrency(totalRevenue / paidOrders) : formatCurrency(0)}
          </span>
        </p>
      </div>
    </div>
  );
}
