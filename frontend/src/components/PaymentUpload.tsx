import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { FileText, RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { LoadingSpinner, FadeInContent } from './LoadingSpinner';

const API_BASE = 'http://localhost:8000';

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
      const res = await fetch(`${API_BASE}/payments/`, {
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
      await fetch(`${API_BASE}/orders/${orderId}/request-cancel`, {
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
    const statusLower = status.toLowerCase();
    if (statusLower === 'payment under review') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-accent-amber/10 text-accent-amber border border-accent-amber/30">
          <Clock className="w-3.5 h-3.5" />
          Under Review
        </span>
      );
    }
    if (statusLower === 'paid' || statusLower === 'verified') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-accent-green/10 text-accent-green border border-accent-green/30">
          <CheckCircle className="w-3.5 h-3.5" />
          Verified
        </span>
      );
    }
    if (statusLower === 'cancelled') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-dark-200 text-dark-600 border border-dark-300">
          <XCircle className="w-3.5 h-3.5" />
          Cancelled
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-dark-100 text-dark-600 border border-dark-200">
        {status}
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-dark-900">Activity History</h2>
            <p className="text-dark-500">Track your payment uploads and status</p>
          </div>
        </div>
        <button
          onClick={loadActivity}
          className="flex items-center gap-2 px-4 py-2 bg-surface-50 border border-dark-200 rounded-xl hover:bg-surface-100 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-primary-600 ${loading ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium text-dark-700">Refresh</span>
        </button>
      </div>

      {loading ? (
        <FadeInContent
          isLoading={true}
          minHeight="min-h-[400px]"
          loadingComponent={
            <>
              <LoadingSpinner size="lg" />
              <p className="text-primary-600 text-lg mt-4 font-medium">Loading activity...</p>
            </>
          }
        />
      ) : payments.length === 0 ? (
        <div className="text-center py-20 bg-surface-100 rounded-2xl border border-dark-200">
          <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-10 h-10 text-primary-400" />
          </div>
          <h3 className="text-xl font-semibold text-dark-700 mb-2">No Activity Yet</h3>
          <p className="text-dark-500">Payment activity will appear here after you place orders</p>
        </div>
      ) : (
        <div className="space-y-4">
          {payments.map((payment) => (
            <div key={payment.id} className="bg-surface-50 rounded-2xl border-2 border-transparent hover:border-primary-500 overflow-hidden hover:shadow-lg hover:scale-[1.02] transition-all duration-300 ease-in-out">
              {/* Header */}
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                      <FileText className="w-6 h-6 text-primary-600" />
                    </div>
                    <div>
                      <span className="font-mono font-bold text-lg text-dark-900">{payment.order_number}</span>
                      <div className="mt-1">{getStatusBadge(payment.status)}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-dark-500">
                      {new Date(payment.uploaded_at).toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Items */}
                <div className="p-4 bg-surface-100 rounded-xl mb-4">
                  <h4 className="text-sm font-semibold text-dark-600 mb-3">Order Items</h4>
                  <div className="space-y-2">
                    {payment.order_items.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        {item.product_image_url ? (
                          <img
                            src={item.product_image_url}
                            alt={item.product_name}
                            className="w-10 h-10 object-cover rounded-lg"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-dark-200 rounded-lg flex items-center justify-center text-dark-400 text-xs">
                            No img
                          </div>
                        )}
                        <span className="flex-1 font-medium text-dark-800">{item.product_name}</span>
                        <span className="text-dark-500">x{item.quantity}</span>
                        <span className="font-semibold text-dark-800">RM {(item.quantity * item.unit_price).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Proof of Payment */}
                {payment.receipt_url && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-dark-600 mb-2">Payment Proof</h4>
                    <a
                      href={`${API_BASE}${payment.receipt_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block"
                    >
                      <img
                        src={`${API_BASE}${payment.receipt_url}`}
                        alt="Payment Receipt"
                        className="max-w-sm max-h-48 object-contain rounded-xl border border-dark-200 hover:shadow-lg transition-shadow cursor-pointer bg-white p-2"
                      />
                      <span className="text-sm text-primary-600 hover:underline mt-2 block">Click to view full size</span>
                    </a>
                  </div>
                )}

                {/* Actions */}
                {!isAdmin && payment.status.toLowerCase() === 'payment under review' && (
                  <div className="border-t border-dark-200 pt-4">
                    <button
                      onClick={() => handleRequestCancel(payment.order_id)}
                      className="px-4 py-2 bg-dark-400 text-white text-sm font-semibold rounded-xl hover:bg-dark-500 transition-colors"
                    >
                      Request Cancellation
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
