import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { api } from '../api';
import { formatCurrency } from '../utils';
import {
  Inbox,
  Upload,
  AlertTriangle,
  RefreshCw,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  Package,
  X,
  Image as ImageIcon,
  FileText,
  ChevronDown,
  Filter,
} from 'lucide-react';
import { StatusProgressBar, StatusBadge } from './StatusProgressBar';
import { LoadingSpinner, ButtonSpinner, FadeInContent } from './LoadingSpinner';
import type { Order } from '../types';

const API_BASE = 'http://localhost:8000';

export function OrdersList() {
  const { role, fetchOrders, fetchProducts } = useStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [_payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [uploadingForOrder, setUploadingForOrder] = useState<number | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [previewOrderNumber, setPreviewOrderNumber] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const isAdmin = role === 'admin';

  useEffect(() => {
    loadOrders();
    if (isAdmin) loadPayments();

    const interval = setInterval(() => {
      loadOrders();
      if (isAdmin) loadPayments();
    }, 30000);

    return () => clearInterval(interval);
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
      const res = await fetch(`${API_BASE}/payments/`, {
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
      await fetch(`${API_BASE}/orders/${orderId}/request-cancel`, {
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
      await fetch(`${API_BASE}/admin/orders/${orderId}/approve-cancel`, {
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
      await fetch(`${API_BASE}/admin/orders/${orderId}/cancel`, {
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
      await fetch(`${API_BASE}/admin/orders/${orderId}/confirm-payment`, {
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

  const filteredOrders = statusFilter === 'all'
    ? orders
    : orders.filter(o => o.status === statusFilter);

  const pendingCount = orders.filter(o =>
    o.status === 'Pending Payment' || o.status === 'Payment Under Review'
  ).length;

  return (
    <div className="p-6">
      {/* Image Preview Modal */}
      {previewImage && (
        <div
          className="fixed inset-0 bg-dark-950/95 z-50 flex items-center justify-center p-8"
          onClick={() => setPreviewImage(null)}
        >
          <button
            className="absolute top-6 right-6 w-10 h-10 bg-dark-800 hover:bg-dark-700 text-white rounded-full flex items-center justify-center transition-colors"
            onClick={() => setPreviewImage(null)}
          >
            <X className="w-6 h-6" />
          </button>
          {previewOrderNumber && (
            <div className="absolute top-6 left-6 bg-dark-800 text-white px-4 py-2 rounded-xl font-mono">
              {previewOrderNumber}
            </div>
          )}
          <img
            src={previewImage}
            alt="Payment proof"
            className="max-w-full max-h-[85vh] object-contain rounded-2xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
            <Inbox className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-dark-900">Order Inbox</h2>
            <p className="text-dark-500">
              {isAdmin ? 'Manage and process customer orders' : 'Track your orders and payments'}
            </p>
          </div>
        </div>
        <button
          onClick={loadOrders}
          className="flex items-center gap-2 px-4 py-2 bg-surface-50 border border-dark-200 rounded-xl hover:bg-surface-100 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-primary-600 ${loading ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium text-dark-700">Refresh</span>
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-surface-50 rounded-xl border border-transparent hover:border-primary-500 p-4 hover:shadow-lg transition-all duration-300 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-900">{orders.length}</div>
              <div className="text-xs text-dark-500">Total Orders</div>
            </div>
          </div>
        </div>
        <div className="bg-surface-50 rounded-xl border border-transparent hover:border-primary-500 p-4 hover:shadow-lg transition-all duration-300 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-accent-amber/10 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-accent-amber" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-900">{pendingCount}</div>
              <div className="text-xs text-dark-500">Pending</div>
            </div>
          </div>
        </div>
        <div className="bg-surface-50 rounded-xl border border-transparent hover:border-primary-500 p-4 hover:shadow-lg transition-all duration-300 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-accent-green/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-accent-green" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-900">
                {orders.filter(o => o.status === 'Completed').length}
              </div>
              <div className="text-xs text-dark-500">Completed</div>
            </div>
          </div>
        </div>
        <div className="bg-surface-50 rounded-xl border border-transparent hover:border-primary-500 p-4 hover:shadow-lg transition-all duration-300 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <Package className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-900">
                {formatCurrency(orders.reduce((sum, o) => sum + o.total_price, 0)).replace('RM ', '')}
              </div>
              <div className="text-xs text-dark-500">Total Value</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3 mb-6">
        <Filter className="w-5 h-5 text-dark-400" />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-surface-50 border border-dark-200 rounded-xl text-dark-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="all">All Status</option>
          <option value="Pending Payment">Pending Payment</option>
          <option value="Payment Under Review">Payment Under Review</option>
          <option value="Paid">Paid</option>
          <option value="Preparing">Preparing</option>
          <option value="Ready for Pickup">Ready for Pickup</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <span className="text-sm text-dark-500">
          Showing {filteredOrders.length} orders
        </span>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-accent-red/10 border border-accent-red/30 rounded-xl text-accent-red">
          {error}
        </div>
      )}

      {loading ? (
        <FadeInContent
          isLoading={true}
          minHeight="min-h-[400px]"
          loadingComponent={
            <>
              <LoadingSpinner size="lg" />
              <p className="text-primary-600 text-lg mt-4 font-medium">Loading orders...</p>
            </>
          }
        />
      ) : filteredOrders.length === 0 ? (
        <div className="text-center py-20 bg-surface-100 rounded-2xl border border-dark-200">
          <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Inbox className="w-10 h-10 text-primary-400" />
          </div>
          <h3 className="text-xl font-semibold text-dark-700 mb-2">No Orders Found</h3>
          <p className="text-dark-500">Orders will appear here once customers place them</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredOrders.map((order) => (
            <OrderInboxCard
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
              onPreviewImage={(url, orderNumber) => {
                setPreviewImage(url);
                setPreviewOrderNumber(orderNumber);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface OrderInboxCardProps {
  order: Order;
  isAdmin: boolean;
  actionLoading: number | null;
  uploadingForOrder: number | null;
  onRequestCancel: (id: number) => void;
  onConfirmCancel: (id: number) => void;
  onForceCancel: (id: number) => void;
  onConfirmPayment: (id: number) => void;
  onUploadPayment: (id: number, file: File) => void;
  onPreviewImage: (url: string, orderNumber: string) => void;
}

function OrderInboxCard({
  order,
  isAdmin,
  actionLoading,
  uploadingForOrder,
  onRequestCancel,
  onConfirmCancel,
  onForceCancel,
  onConfirmPayment,
  onUploadPayment,
  onPreviewImage,
}: OrderInboxCardProps) {
  const [expanded, setExpanded] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadPayment(order.id, file);
      e.target.value = '';
    }
  };

  const isUnderReview = order.status === 'Payment Under Review';
  const isRejected = order.status === 'Payment Rejected';
  const isPending = order.status === 'Pending Payment';
  const canCancel = !isAdmin && (isPending || isRejected);
  const canUpload = !isAdmin && (isPending || isRejected);

  const statusStyles: Record<string, string> = {
    'Pending Payment': 'border-l-blue-500 bg-blue-50/30',
    'Payment Under Review': 'border-l-accent-amber bg-accent-amber/5',
    'Payment Rejected': 'border-l-accent-red bg-accent-red/5',
    'Paid': 'border-l-accent-green bg-accent-green/5',
    'Preparing': 'border-l-primary-500 bg-primary-50/30',
    'Ready for Pickup': 'border-l-indigo-500 bg-indigo-50/30',
    'Completed': 'border-l-accent-green bg-accent-green/5',
    'Cancelled': 'border-l-dark-400 bg-dark-100',
    'Cancel Requested': 'border-l-yellow-500 bg-yellow-50/30',
  };

  const currentStyle = statusStyles[order.status] || 'border-l-dark-300';

  return (
    <div className={`rounded-2xl border-2 border-transparent hover:border-primary-500 border-l-4 hover:shadow-lg hover:scale-[1.02] transition-all duration-300 ease-in-out ${currentStyle} overflow-hidden`}>
      {/* Header */}
      <div
        className="p-5 cursor-pointer hover:bg-surface-100/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <span className="font-mono font-bold text-dark-900">{order.order_number}</span>
                <StatusBadge status={order.status} />
              </div>
              <div className="text-sm text-dark-500 mt-1">
                {order.items.length} item{order.items.length !== 1 ? 's' : ''} • {new Date(order.created_at).toLocaleString()}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-2xl font-bold text-primary-600">{formatCurrency(order.total_price)}</div>
              {order.discount_amount > 0 && (
                <div className="text-sm text-accent-green">-RM {order.discount_amount.toFixed(2)}</div>
              )}
            </div>
            <ChevronDown className={`w-5 h-5 text-dark-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="border-t border-dark-200 bg-surface-50 p-5">
          {/* Items */}
          <div className="mb-5">
            <h4 className="text-sm font-semibold text-dark-600 mb-3">Order Items</h4>
            <div className="space-y-2">
              {order.items.map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 bg-surface-100 rounded-xl">
                  {item.product_image_url ? (
                    <img
                      src={item.product_image_url}
                      alt={item.product_name}
                      className="w-10 h-10 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 bg-dark-200 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-dark-400" />
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="font-medium text-dark-800">{item.product_name}</div>
                    <div className="text-sm text-dark-500">Qty: {item.quantity} × {formatCurrency(item.unit_price)}</div>
                  </div>
                  <div className="font-semibold text-dark-800">
                    {formatCurrency(item.unit_price * item.quantity)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Status Progress */}
          <div className="mb-5">
            <h4 className="text-sm font-semibold text-dark-600 mb-3">Order Progress</h4>
            <StatusProgressBar status={order.status} />
          </div>

          {/* Payment Proof */}
          {isUnderReview && order.payment?.receipt_url && (
            <div className="mb-5 p-4 bg-accent-amber/10 border border-accent-amber/30 rounded-xl">
              <div className="flex items-center gap-3 mb-3">
                <ImageIcon className="w-5 h-5 text-accent-amber" />
                <span className="font-semibold text-dark-800">Payment Proof Uploaded</span>
              </div>
              <img
                src={`${API_BASE}${order.payment.receipt_url}`}
                alt="Payment proof"
                className="w-full max-h-48 object-contain rounded-xl bg-white cursor-pointer hover:opacity-90"
                onClick={() => onPreviewImage(`${API_BASE}${order.payment!.receipt_url}`, order.order_number)}
              />
              <p className="text-sm text-dark-500 mt-2">Click to view full size</p>
            </div>
          )}

          {/* Rejection Reason */}
          {isRejected && order.payment?.rejection_reason && (
            <div className="mb-5 p-4 bg-accent-red/10 border border-accent-red/30 rounded-xl">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-accent-red">Payment Rejected</div>
                  <div className="text-dark-700 mt-1">Reason: {order.payment.rejection_reason}</div>
                  {order.payment.rejected_at && (
                    <div className="text-sm text-dark-500 mt-1">
                      {new Date(order.payment.rejected_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {/* Upload Payment */}
            {canUpload && (
              <label className={`px-5 py-2.5 rounded-xl font-semibold flex items-center gap-2 cursor-pointer transition-all ${
                isRejected
                  ? 'bg-accent-red text-white hover:bg-accent-red/90'
                  : 'bg-accent-green text-white hover:bg-accent-green/90'
              } ${uploadingForOrder === order.id ? 'opacity-50 cursor-wait' : ''}`}>
                {uploadingForOrder === order.id ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    {isRejected ? 'Re-upload Proof' : 'Upload Payment Proof'}
                  </>
                )}
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf"
                  className="hidden"
                  onChange={handleFileChange}
                  disabled={uploadingForOrder === order.id}
                />
              </label>
            )}

            {/* Admin Confirm Payment */}
            {isAdmin && isUnderReview && (
              <button
                onClick={() => onConfirmPayment(order.id)}
                disabled={actionLoading === order.id || !order.payment?.receipt_url}
                className="px-5 py-2.5 bg-accent-green text-white rounded-xl font-semibold hover:bg-accent-green/90 disabled:bg-dark-200 disabled:text-dark-400 flex items-center gap-2 transition-all"
              >
                {actionLoading === order.id ? (
                  <>
                    <ButtonSpinner size="sm" />
                    Confirming...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Confirm Payment
                  </>
                )}
              </button>
            )}

            {/* Request Cancel */}
            {canCancel && (
              <button
                onClick={() => onRequestCancel(order.id)}
                disabled={actionLoading === order.id}
                className="px-5 py-2.5 bg-dark-400 text-white rounded-xl font-semibold hover:bg-dark-500 disabled:bg-dark-200 flex items-center gap-2 transition-all"
              >
                <XCircle className="w-4 h-4" />
                Request Cancel
              </button>
            )}

            {/* Admin Approve Cancel */}
            {isAdmin && order.status === 'Cancel Requested' && (
              <button
                onClick={() => onConfirmCancel(order.id)}
                disabled={actionLoading === order.id}
                className="px-5 py-2.5 bg-accent-amber text-dark-900 rounded-xl font-semibold hover:bg-accent-amber/90 disabled:bg-dark-200 flex items-center gap-2 transition-all"
              >
                <CheckCircle className="w-4 h-4" />
                Approve Cancellation
              </button>
            )}

            {/* Admin Force Cancel */}
            {isAdmin && !['Cancelled', 'Paid', 'Cancel Requested', 'Completed'].includes(order.status) && (
              <button
                onClick={() => onForceCancel(order.id)}
                disabled={actionLoading === order.id}
                className="px-5 py-2.5 bg-accent-red text-white rounded-xl font-semibold hover:bg-accent-red/90 disabled:bg-dark-200 flex items-center gap-2 transition-all"
              >
                <XCircle className="w-4 h-4" />
                Force Cancel
              </button>
            )}

            {/* View Payment Proof */}
            {order.payment?.receipt_url && (
              <button
                onClick={() => onPreviewImage(`${API_BASE}${order.payment!.receipt_url}`, order.order_number)}
                className="px-5 py-2.5 bg-primary-100 text-primary-700 rounded-xl font-semibold hover:bg-primary-200 flex items-center gap-2 transition-all"
              >
                <Eye className="w-4 h-4" />
                View Proof
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
