import { useEffect, useState } from 'react';
import { useStore } from '../store';

interface OrderItem {
  product_name: string;
  product_image_url?: string;
  quantity: number;
  unit_price: number;
}

interface PaymentActivity {
  id: number;
  order_id: number;
  order_number: string;
  receipt_url: string;
  uploaded_at: string;
  status: string;
  order_items: OrderItem[];
}

export function PaymentUpload() {
  const { role, fetchOrders } = useStore();
  const [payments, setPayments] = useState<PaymentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  const isAdmin = role === 'admin';

  useEffect(() => {
    loadActivity();
  }, []);

  const loadActivity = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8002/payments/', {
        headers: { 'X-Simulated-Role': role || 'staff' },
      });
      if (res.ok) {
        const data = await res.json();
        setPayments(data);
      }
    } catch (e) {
      console.error('Failed to load activity:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestCancel = async (orderId: number) => {
    if (!confirm('Request cancellation for this order?')) return;
    try {
      await fetch(`http://localhost:8002/orders/${orderId}/request-cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Simulated-Role': role || 'staff' },
      });
      await loadActivity();
      fetchOrders();
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'payment under review':
        return <span className="px-2 py-0.5 rounded text-xs bg-orange-200 text-orange-800">Under Review</span>;
      case 'paid':
      case 'verified':
        return <span className="px-2 py-0.5 rounded text-xs bg-green-200 text-green-800">Verified</span>;
      case 'cancelled':
        return <span className="px-2 py-0.5 rounded text-xs bg-red-200 text-red-800">Cancelled</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs bg-gray-200 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="p-4 border-t border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Activity History</h2>
        <button
          onClick={loadActivity}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : payments.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-4xl mb-4">📋</p>
          <p>No payment activity yet</p>
          <p className="text-sm mt-2">Upload payment receipts from the Orders tab</p>
        </div>
      ) : (
        <div className="space-y-4">
          {payments.map((payment) => (
            <div key={payment.id} className="border border-gray-200 rounded-lg p-4 bg-white">
              {/* Header */}
              <div className="flex justify-between items-start mb-3">
                <div>
                  <span className="font-semibold text-lg">{payment.order_number}</span>
                  {getStatusBadge(payment.status)}
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">
                    {new Date(payment.uploaded_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Itemized List with Photos */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2 text-sm">Items:</h4>
                <ul className="space-y-2">
                  {payment.order_items.map((item, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      {item.product_image_url ? (
                        <img
                          src={item.product_image_url}
                          alt={item.product_name}
                          className="w-10 h-10 object-cover rounded"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center text-gray-400 text-xs">
                          No img
                        </div>
                      )}
                      <span className="flex-1 font-medium">{item.product_name}</span>
                      <span className="text-gray-500">x{item.quantity}</span>
                      <span className="text-gray-600">${(item.quantity * item.unit_price).toFixed(2)}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Proof of Payment */}
              <div className="mb-4">
                <h4 className="font-medium text-gray-700 mb-2 text-sm">Proof of Payment:</h4>
                <a
                  href={`http://localhost:8002${payment.receipt_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <img
                    src={`http://localhost:8002${payment.receipt_url}`}
                    alt="Payment Receipt"
                    className="max-w-xs max-h-48 object-contain rounded border border-gray-200 hover:shadow-md cursor-pointer"
                  />
                  <span className="text-xs text-blue-600 hover:underline mt-1 block">View full receipt</span>
                </a>
              </div>

              {/* Actions - Request Cancel for Under Review orders (Staff) */}
              {!isAdmin && payment.status.toLowerCase() === 'payment under review' && (
                <div className="border-t pt-3">
                  <button
                    onClick={() => handleRequestCancel(payment.order_id)}
                    className="px-3 py-1.5 bg-orange-500 text-white text-sm rounded hover:bg-orange-600"
                  >
                    Request Cancel
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
