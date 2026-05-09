import { useEffect } from 'react';
import { useStore } from '../../store';
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
import { formatCurrency } from '../../utils';

export function DashboardPage() {
  const { adminDashboard, fetchDashboard, isLoading } = useStore();

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleRefresh = () => {
    fetchDashboard();
  };

  if (!adminDashboard) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-xl p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-24 mb-4" />
              <div className="h-8 bg-gray-200 rounded w-32" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const kpiCards = [
    {
      id: 'today-sales',
      title: "Today's Sales",
      value: formatCurrency(adminDashboard.today_sales),
      icon: TrendingUp,
      bgGradient: 'from-green-50 to-emerald-50',
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      borderColor: 'border-green-200',
      valueColor: 'text-green-700',
    },
    {
      id: 'pending-orders',
      title: 'Pending Orders',
      value: adminDashboard.pending_orders.toString(),
      icon: Clock,
      bgGradient: 'from-yellow-50 to-amber-50',
      iconBg: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      borderColor: 'border-yellow-200',
      valueColor: 'text-yellow-700',
    },
    {
      id: 'low-stock',
      title: 'Stock Alerts',
      value: adminDashboard.low_stock_alerts.length.toString(),
      icon: AlertTriangle,
      bgGradient: 'from-red-50 to-rose-50',
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      borderColor: 'border-red-200',
      valueColor: 'text-red-600',
      highlight: adminDashboard.low_stock_alerts.length > 0,
    },
    {
      id: 'total-revenue',
      title: 'Total Revenue',
      value: formatCurrency(adminDashboard.total_revenue),
      icon: DollarSign,
      bgGradient: 'from-purple-50 to-violet-50',
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
      borderColor: 'border-purple-200',
      valueColor: 'text-purple-700',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Dashboard Overview</h2>
          <p className="text-sm text-gray-500">Real-time statistics and metrics</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium">Refresh</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              className={`relative bg-gradient-to-br ${card.bgGradient} rounded-xl border ${card.borderColor} p-5 overflow-hidden transition-transform hover:scale-[1.02]`}
            >
              <div className="absolute top-0 right-0 w-20 h-20 opacity-10 transform translate-x-6 -translate-y-6">
                <Icon className={`w-full h-full ${card.iconColor}`} />
              </div>
              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-600">{card.title}</span>
                  <div className={`p-2 rounded-lg ${card.iconBg}`}>
                    <Icon className={`w-5 h-5 ${card.iconColor}`} />
                  </div>
                </div>
                <div className={`text-2xl lg:text-3xl font-bold ${card.valueColor}`}>
                  {card.value}
                </div>
                {card.highlight && (
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

      {/* Order Statistics */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Orders', value: adminDashboard.total_orders, icon: ShoppingCart, color: 'blue' },
          { label: 'Paid Orders', value: adminDashboard.paid_orders, icon: CheckCircle, color: 'green' },
          { label: 'Cancelled', value: adminDashboard.cancelled_orders, icon: XCircle, color: 'gray' },
        ].map((stat) => {
          const Icon = stat.icon;
          const colors: Record<string, string> = { blue: 'text-blue-600 bg-blue-50', green: 'text-green-600 bg-green-50', gray: 'text-gray-600 bg-gray-50' };
          return (
            <div key={stat.label} className="bg-white rounded-xl border border-gray-200 text-center p-4">
              <div className={`inline-flex p-2 rounded-lg mb-2 ${colors[stat.color]}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="text-2xl font-bold text-gray-800">{stat.value}</div>
              <div className="text-sm text-gray-500">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* Stock Alerts */}
      <div className={`rounded-xl border p-5 ${adminDashboard.low_stock_alerts.length > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
        <div className="flex items-center gap-2 mb-4">
          <Package className={`w-5 h-5 ${adminDashboard.low_stock_alerts.length > 0 ? 'text-red-600' : 'text-green-600'}`} />
          <h3 className={`text-lg font-semibold ${adminDashboard.low_stock_alerts.length > 0 ? 'text-red-700' : 'text-green-700'}`}>
            Stock Alerts
            {adminDashboard.low_stock_alerts.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-sm rounded-full">
                {adminDashboard.low_stock_alerts.length}
              </span>
            )}
          </h3>
        </div>
        {adminDashboard.low_stock_alerts.length === 0 ? (
          <div className="text-center py-6">
            <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-2" />
            <p className="text-green-700 font-medium">All products are well-stocked!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-red-200">
                  <th className="text-left py-2 px-2 font-semibold text-red-700">SKU</th>
                  <th className="text-left py-2 px-2 font-semibold text-red-700">Product</th>
                  <th className="text-right py-2 px-2 font-semibold text-red-700">Available</th>
                  <th className="text-right py-2 px-2 font-semibold text-red-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {adminDashboard.low_stock_alerts.slice(0, 5).map((p: any) => (
                  <tr key={p.id} className="border-b border-red-100">
                    <td className="py-2 px-2 font-mono text-gray-600">{p.sku}</td>
                    <td className="py-2 px-2 font-medium text-gray-800">{p.name}</td>
                    <td className="py-2 px-2 text-right font-bold text-red-600">{p.available_stock}</td>
                    <td className="py-2 px-2 text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${p.available_stock === 0 ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'}`}>
                        {p.available_stock === 0 ? 'Out of Stock' : 'Low Stock'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Avg Order Value */}
      <div className="text-center text-sm text-gray-500">
        Avg Order Value: <span className="font-semibold text-gray-700">
          {adminDashboard.paid_orders > 0 ? formatCurrency(adminDashboard.total_revenue / adminDashboard.paid_orders) : formatCurrency(0)}
        </span>
      </div>
    </div>
  );
}
