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
  const [uploadingForOrder, setUploadingForOrder] = useState<number | null>(null);

  const isAdmin = role === 'admin';

  useEffect(() => {
    loadOrders();
    if (isAdmin) loadPayments();
  }, [isAdmin]);

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
        headers: { 'X-Simulated-Role': role || 'staff' },
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
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'staff' },
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
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'staff' },
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
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'staff' },
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

  const handleUploadPayment = async (orderId: number, file: File) => {
    setUploadingForOrder(orderId);
    try {
      await api.uploadPayment(orderId, file, role);
      await loadOrders();
      if (isAdmin) await loadPayments();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setUploadingForOrder(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'cancel requested': return 'bg-yellow-100 text-yellow-800';
      case 'pending payment':
      case 'pending': return 'bg-blue-100 text-blue-800';
      case 'paid':
      case 'verified': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      case 'payment under review': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) return <div className="text-center py-8">Loading orders...</div>;
  if (error) return <div className="text-red-500 py-4">{error}</div>;

  return (
    <div className="p-4 space-y-6">
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Orders</h2>
          <button onClick={loadOrders} className="text-sm text-purple-600 hover:underline">
            Refresh
          </button>
        </div>

        {orders.length === 0 ? (
          <div className="text-gray-500 text-center py-8">No orders found</div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                isAdmin={isAdmin}
                actionLoading={actionLoading}
                uploadingForOrder={uploadingForOrder}
                onRequestCancel={handleRequestCancel}
                onConfirmCancel={handleConfirmCancel}
                onForceCancel={handleForceCancel}
                onUploadPayment={handleUploadPayment}
                getStatusColor={getStatusColor}
              />
            ))}
          </div>
        )}
      </div>

      {/* Payment History (Admin only) */}
      {isAdmin && (
        <div className="border-t pt-6">
          <h2 className="text-xl font-semibold mb-4">Recent Payment Receipts</h2>
          {payments.length === 0 ? (
            <div className="text-gray-500 text-center py-4">No payments uploaded</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {payments.slice(0, 6).map((payment) => (
                <div key={payment.id} className="border border-gray-200 rounded p-3 flex gap-3">
                  <img
                    src={`http://localhost:8002${payment.receipt_url}`}
                    alt="Receipt"
                    className="w-16 h-16 object-cover rounded"
                  />
                  <div>
                    <div className="font-medium">{payment.order_number}</div>
                    <div className="text-sm text-gray-500">
                      {new Date(payment.uploaded_at).toLocaleString()}
                    </div>
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

interface OrderCardProps {
  order: Order;
  isAdmin: boolean;
  actionLoading: number | null;
  uploadingForOrder: number | null;
  onRequestCancel: (id: number) => void;
  onConfirmCancel: (id: number) => void;
  onForceCancel: (id: number) => void;
  onUploadPayment: (id: number, file: File) => void;
  getStatusColor: (status: string) => string;
}

function OrderCard({
  order,
  isAdmin,
  actionLoading,
  uploadingForOrder,
  onRequestCancel,
  onConfirmCancel,
  onForceCancel,
  onUploadPayment,
  getStatusColor,
}: OrderCardProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadPayment(order.id, file);
      e.target.value = '';
    }
  };

  const canPay = order.status === 'Pending Payment';
  const canCancel = !isAdmin && (order.status === 'Pending Payment' || order.status === 'Payment Under Review');

  return (
    <div
      className={`border rounded-lg p-4 ${
        order.status.toLowerCase() === 'cancel requested' ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200'
      }`}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="font-semibold">{order.order_number}</span>
          <span className={`ml-2 px-2 py-0.5 rounded text-xs ${getStatusColor(order.status)}`}>
            {order.status}
          </span>
        </div>
        <span className="font-bold text-purple-600 text-lg">${order.total_price.toFixed(2)}</span>
      </div>

      {/* Items Mini-List */}
      <div className="mb-3 p-2 bg-gray-50 rounded">
        <ul className="space-y-1">
          {order.items.map((item, idx) => (
            <li key={idx} className="flex items-center gap-2 text-sm">
              {item.product_image_url && (
                <img
                  src={item.product_image_url}
                  alt={item.product_name}
                  className="w-8 h-8 object-cover rounded"
                />
              )}
              <span className="flex-1">{item.product_name}</span>
              <span className="text-gray-500">x{item.quantity}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="text-xs text-gray-500 mb-3">
        {new Date(order.created_at).toLocaleString()}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2 items-center">
        {/* Pay Now - for staff with pending orders */}
        {canPay && !isAdmin && (
          <label className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 cursor-pointer">
            {uploadingForOrder === order.id ? 'Uploading...' : 'Pay Now'}
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
        )}

        {/* Request Cancel - staff */}
        {canCancel && (
          <button
            onClick={() => onRequestCancel(order.id)}
            disabled={actionLoading === order.id}
            className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 disabled:bg-gray-300"
          >
            {actionLoading === order.id ? 'Processing...' : 'Request Cancel'}
          </button>
        )}

        {/* Confirm Cancel - admin */}
        {isAdmin && order.status === 'Cancel Requested' && (
          <button
            onClick={() => onConfirmCancel(order.id)}
            disabled={actionLoading === order.id}
            className="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600 disabled:bg-gray-300"
          >
            Confirm Cancellation
          </button>
        )}

        {/* Force Cancel - admin */}
        {isAdmin && order.status !== 'Cancelled' && order.status !== 'Paid' && order.status !== 'Cancel Requested' && (
          <button
            onClick={() => onForceCancel(order.id)}
            disabled={actionLoading === order.id}
            className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 disabled:bg-gray-300"
          >
            Force Cancel
          </button>
        )}

        {order.status.toLowerCase() === 'cancel requested' && (
          <span className="text-xs text-yellow-600 font-medium">Awaiting admin approval</span>
        )}
      </div>
    </div>
  );
}
