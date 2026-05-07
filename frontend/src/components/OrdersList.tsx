import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { api } from '../api';

interface OrderItem {
  product_id: number;
  product_name: string;
  product_image_url?: string;
  quantity: number;
  unit_price: number;
}

interface Order {
  id: number;
  order_number: string;
  total_price: number;
  status: string;
  user_id: number;
  created_at: string;
  items: OrderItem[];
}

interface Payment {
  id: number;
  order_id: number;
  order_number: string;
  receipt_url: string;
  uploaded_at: string;
}

export function OrdersList() {
  const { role, fetchOrders, fetchProducts } = useStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const isAdmin = role === 'admin';

  useEffect(() => {
    loadOrders();
    loadPayments();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getOrders(role);
      setOrders(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const loadPayments = async () => {
    try {
      const res = await fetch(`http://localhost:8002/payments/`, {
        headers: {
          'X-Simulated-Role': role || 'staff',
        },
      });
      if (res.ok) {
        const data = await res.json();
        setPayments(data);
      }
    } catch (e) {
      console.error('Failed to load payments:', e);
    }
  };

  const handleRequestCancel = async (orderId: number) => {
    setActionLoading(orderId);
    try {
      await fetch(`http://localhost:8002/orders/${orderId}/request-cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Simulated-Role': role || 'staff',
        },
      });
      await loadOrders();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleConfirmCancel = async (orderId: number) => {
    setActionLoading(orderId);
    try {
      await fetch(`http://localhost:8002/admin/orders/${orderId}/approve-cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Simulated-Role': role || 'staff',
        },
      });
      await loadOrders();
      fetchOrders();
      fetchProducts();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleForceCancel = async (orderId: number) => {
    if (!confirm('Are you sure you want to force cancel this order?')) return;
    setActionLoading(orderId);
    try {
      await fetch(`http://localhost:8002/admin/orders/${orderId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Simulated-Role': role || 'staff',
        },
      });
      await loadOrders();
      fetchOrders();
      fetchProducts();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'cancel requested':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending payment':
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      case 'paid':
      case 'verified':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'payment under review':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) return <div className="text-center py-8">Loading orders...</div>;
  if (error) return <div className="text-red-500 py-4">{error}</div>;

  return (
    <div className="p-4 space-y-6">
      {/* Orders Section */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Orders</h2>
        {orders.length === 0 ? (
          <div className="text-gray-500 text-center py-8">No orders found</div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <div
                key={order.id}
                className={`border rounded-lg p-4 ${order.status.toLowerCase() === 'cancel requested' ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200'}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="font-semibold">{order.order_number}</span>
                    <span className={`ml-2 px-2 py-0.5 rounded text-xs ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                    {order.status.toLowerCase() === 'cancel requested' && (
                      <span className="ml-2 text-xs text-yellow-600 font-medium">Awaiting admin approval</span>
                    )}
                  </div>
                  <span className="font-bold text-purple-600">${order.total_price.toFixed(2)}</span>
                </div>
                <div className="text-sm text-gray-500 mb-3">
                  {new Date(order.created_at).toLocaleString()}
                </div>
                {/* Order Items List */}
                {order.items && order.items.length > 0 && (
                  <div className="mb-3 p-2 bg-gray-50 rounded text-sm">
                    <div className="font-medium text-gray-700 mb-2">Items:</div>
                    <ul className="space-y-2">
                      {order.items.map((item, idx) => (
                        <li key={idx} className="flex items-center gap-3">
                          {item.product_image_url && (
                            <img
                              src={item.product_image_url}
                              alt={item.product_name}
                              className="w-10 h-10 object-cover rounded"
                            />
                          )}
                          <div className="flex-1">
                            <span className="font-medium">{item.product_name}</span>
                            <span className="text-gray-500 ml-2">x{item.quantity}</span>
                          </div>
                          <span className="text-gray-600">${(item.quantity * item.unit_price).toFixed(2)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex gap-2">
                  {/* Staff: Request Cancel button for pending orders */}
                  {!isAdmin && (order.status === 'Pending Payment' || order.status === 'Payment Under Review') && (
                    <button
                      onClick={() => handleRequestCancel(order.id)}
                      disabled={actionLoading === order.id}
                      className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 disabled:bg-gray-300"
                    >
                      {actionLoading === order.id ? 'Processing...' : 'Request Cancel'}
                    </button>
                  )}
                  {/* Admin: Confirm Cancel for cancel_requested orders */}
                  {isAdmin && order.status === 'Cancel Requested' && (
                    <button
                      onClick={() => handleConfirmCancel(order.id)}
                      disabled={actionLoading === order.id}
                      className="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600 disabled:bg-gray-300"
                    >
                      {actionLoading === order.id ? 'Processing...' : 'Confirm Cancellation'}
                    </button>
                  )}
                  {/* Admin: Force Cancel for unpaid orders */}
                  {isAdmin && order.status !== 'Cancelled' && order.status !== 'Paid' && order.status !== 'Cancel Requested' && (
                    <button
                      onClick={() => handleForceCancel(order.id)}
                      disabled={actionLoading === order.id}
                      className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 disabled:bg-gray-300"
                    >
                      {actionLoading === order.id ? 'Processing...' : 'Force Cancel'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payments Section (Admin only) */}
      {isAdmin && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Payment Receipts</h2>
          {payments.length === 0 ? (
            <div className="text-gray-500 text-center py-4">No payments uploaded</div>
          ) : (
            <div className="space-y-2">
              {payments.map((payment) => (
                <div key={payment.id} className="border border-gray-200 rounded p-3 flex justify-between items-center">
                  <div>
                    <div className="font-medium">{payment.order_number}</div>
                    <div className="text-sm text-gray-500">
                      Uploaded: {new Date(payment.uploaded_at).toLocaleString()}
                    </div>
                    <a
                      href={`http://localhost:8002${payment.receipt_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      View Receipt
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
