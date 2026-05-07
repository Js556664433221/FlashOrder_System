import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { api } from '../api';

interface OrderItem {
  product_id: number;
  product_name: string;
  product_image_url?: string;
  quantity: number;
  unit_price: number;
  product?: {
    image_url?: string;
    name?: string;
  };
}

// Payment info embedded in order response from admin API
interface OrderPayment {
  id: number;
  order_id: number;
  receipt_url: string;
  uploaded_at: string;
}

interface Order {
  id: number;
  order_number: string;
  total_price: number;
  status: string;
  user_id: number;
  created_at: string;
  items: OrderItem[];
  payment?: OrderPayment | null;
}

// Payment interface for the Recent Payment Receipts section (has order_number)
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
  const [previewImage, setPreviewImage] = useState<string | null>(null);

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
      const res = await fetch('http://localhost:8002/payments/', {
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
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'admin' },
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
    if (!confirm('Force cancel this order?')) return;
    setActionLoading(orderId);
    try {
      await fetch(`http://localhost:8002/admin/orders/${orderId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'admin' },
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

  const handleConfirmPayment = async (orderId: number) => {
    if (!confirm('Confirm payment? Stock will be deducted.')) return;
    setActionLoading(orderId);
    try {
      await fetch(`http://localhost:8002/admin/orders/${orderId}/confirm-payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'admin' },
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
      case 'pending payment': return 'bg-blue-100 text-blue-800';
      case 'payment under review': return 'bg-orange-100 text-orange-800';
      case 'paid': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;
  if (error) return <div className="text-red-500 py-4">{error}</div>;

  return (
    <div className="p-4 space-y-6">
      {previewImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-8"
          onClick={() => setPreviewImage(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              className="absolute -top-8 right-0 text-white text-2xl"
              onClick={() => setPreviewImage(null)}
            >
              Close
            </button>
            <img
              src={previewImage}
              alt="Payment proof"
              className="max-w-full max-h-[80vh] object-contain"
            />
          </div>
        </div>
      )}

      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Orders</h2>
        <button onClick={loadOrders} className="text-sm text-purple-600 hover:underline">Refresh</button>
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
              onConfirmPayment={handleConfirmPayment}
              onUploadPayment={handleUploadPayment}
              getStatusColor={getStatusColor}
              onPreviewImage={setPreviewImage}
            />
          ))}
        </div>
      )}

      {isAdmin && payments.length > 0 && (
        <div className="border-t pt-6">
          <h2 className="text-xl font-semibold mb-4">Recent Payment Receipts</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {payments.slice(0, 6).map((p) => (
              <div
                key={p.id}
                className="border rounded p-2 cursor-pointer hover:shadow-lg"
                onClick={() => setPreviewImage(`http://localhost:8002${p.receipt_url}`)}
              >
                <img
                  src={`http://localhost:8002${p.receipt_url}`}
                  alt="Receipt"
                  className="w-full h-32 object-cover rounded"
                />
                <div className="text-xs text-gray-500 mt-1 truncate">{p.order_number}</div>
              </div>
            ))}
          </div>
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
  onConfirmPayment: (id: number) => void;
  onUploadPayment: (id: number, file: File) => void;
  getStatusColor: (status: string) => string;
  onPreviewImage: (url: string) => void;
}

function OrderCard({
  order,
  isAdmin,
  actionLoading,
  uploadingForOrder,
  onRequestCancel,
  onConfirmCancel,
  onForceCancel,
  onConfirmPayment,
  onUploadPayment,
  getStatusColor,
  onPreviewImage,
}: OrderCardProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadPayment(order.id, file);
      e.target.value = '';
    }
  };

  const isUnderReview = order.status === 'Payment Under Review';
  const canCancel = !isAdmin && (order.status === 'Pending Payment' || order.status === 'Payment Under Review');

  return (
    <div className={`border rounded-lg p-4 ${isUnderReview ? 'border-orange-300 bg-orange-50/30' : 'border-gray-200'}`}>
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="font-semibold">{order.order_number}</span>
          <span className={`ml-2 px-2 py-0.5 rounded text-xs ${getStatusColor(order.status)}`}>{order.status}</span>
        </div>
        <span className="font-bold text-purple-600 text-lg">${order.total_price.toFixed(2)}</span>
      </div>

      <div className="mb-3 p-2 bg-gray-50 rounded">
        <div className="text-xs text-gray-500 mb-1">Items:</div>
        <div className="space-y-1">
          {order.items.map((item, idx) => {
            const imageUrl = item.product_image_url || item.product?.image_url;
            return (
              <div key={idx} className="flex items-center gap-2 text-sm">
                {imageUrl && (
                  <img src={imageUrl} alt={item.product_name} className="w-8 h-8 rounded object-cover flex-shrink-0" />
                )}
                <span className="flex-1 truncate">{item.product_name}</span>
                <span className="text-gray-500 whitespace-nowrap">x{item.quantity}</span>
                <span className="text-gray-600 whitespace-nowrap">${(item.unit_price * item.quantity).toFixed(2)}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="text-xs text-gray-500 mb-3">{new Date(order.created_at).toLocaleString()}</div>

      {isUnderReview && (
        <div className="mb-3 p-3 bg-white border border-orange-200 rounded-lg">
          <div className="font-medium text-sm mb-2 text-orange-700">Payment Proof:</div>
          {order.payment?.receipt_url ? (
            <>
              <div className="text-xs text-gray-500 mb-2">Click image to enlarge</div>
              <div
                className="cursor-pointer"
                onClick={() => onPreviewImage(`http://localhost:8002${order.payment!.receipt_url}`)}
              >
                <img
                  src={`http://localhost:8002${order.payment!.receipt_url}`}
                  alt="Payment proof"
                  className="w-full h-40 object-contain rounded bg-gray-50"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    const next = e.currentTarget.nextElementSibling as HTMLElement;
                    if (next) next.classList.remove('hidden');
                  }}
                />
                <div className="hidden w-full h-32 bg-gray-100 rounded flex items-center justify-center text-gray-400">
                  Failed to load image
                </div>
              </div>
            </>
          ) : (
            <div className="w-full h-32 bg-gray-100 rounded flex items-center justify-center text-gray-400">
              No proof uploaded yet
            </div>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-2 items-center">
        {order.status === 'Pending Payment' && (
          <label className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 cursor-pointer">
            {uploadingForOrder === order.id ? 'Uploading...' : 'Upload Proof Payment'}
            <input type="file" accept=".jpg,.jpeg,.png,.pdf" className="hidden" onChange={handleFileChange} />
          </label>
        )}

        {isAdmin && isUnderReview && (
          <button
            onClick={() => onConfirmPayment(order.id)}
            disabled={actionLoading === order.id || !order.payment?.receipt_url}
            className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            title={!order.payment?.receipt_url ? 'Payment proof required before confirming' : 'Confirm this payment'}
          >
            {actionLoading === order.id ? 'Processing...' : 'Confirm Payment'}
          </button>
        )}

        {canCancel && (
          <button
            onClick={() => onRequestCancel(order.id)}
            disabled={actionLoading === order.id}
            className="px-3 py-1 bg-orange-500 text-white text-sm rounded disabled:bg-gray-300"
          >
            {actionLoading === order.id ? 'Processing...' : 'Request Cancel'}
          </button>
        )}

        {isAdmin && order.status === 'Cancel Requested' && (
          <button
            onClick={() => onConfirmCancel(order.id)}
            disabled={actionLoading === order.id}
            className="px-3 py-1 bg-yellow-500 text-white text-sm rounded disabled:bg-gray-300"
          >
            Approve Cancellation
          </button>
        )}

        {isAdmin && order.status !== 'Cancelled' && order.status !== 'Paid' && order.status !== 'Cancel Requested' && (
          <button
            onClick={() => onForceCancel(order.id)}
            disabled={actionLoading === order.id}
            className="px-3 py-1 bg-red-500 text-white text-sm rounded disabled:bg-gray-300"
          >
            Force Cancel
          </button>
        )}
      </div>
    </div>
  );
}
