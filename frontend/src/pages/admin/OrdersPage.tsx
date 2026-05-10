import { useState, useEffect } from 'react';
import { useStore } from '../../store';
import { api } from '../../api';
import {
  Search,
  Eye,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Edit3,
  MessageSquare,
  Package,
  Truck,
  X,
  Save,
  AlertTriangle,
  Image as ImageIcon,
  Check,
  RefreshCw,
  Bell,
  FileText,
  Clock,
} from 'lucide-react';
import { formatCurrency, formatDiscount, ORDER_STATUSES } from '../../utils';
import { StatusBadge } from '../../components/StatusProgressBar';
import { LoadingSpinner, ButtonSpinner, FadeInContent } from '../../components/LoadingSpinner';
import type { Order } from '../../types';

export function OrdersPage() {
  const { orders, fetchOrders } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showRemarkModal, setShowRemarkModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showProofModal, setShowProofModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [remarkText, setRemarkText] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isModalLoading, setIsModalLoading] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, []);

  const filteredOrders = orders.filter((order) => {
    const matchesSearch =
      order.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Auto-refresh every 30 seconds for the salesman delivery & check payment page
  useEffect(() => {
    const interval = setInterval(() => {
      fetchOrders();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchOrders]);

  const handleStatusChange = async (order: Order, newStatus: string) => {
    if (newStatus === 'Paid') {
      if (!confirm(`Confirm payment for order ${order.order_number}? Stock will be deducted.`)) return;
    } else if (!confirm(`Change order ${order.order_number} status to "${newStatus}"?`)) return;

    setIsUpdating(true);
    try {
      if (newStatus === 'Paid') {
        await api.confirmPayment(order.id);
      } else {
        await api.updateAdminOrder(order.id, { status: newStatus as any });
      }
      await fetchOrders();
    } catch (e) {
      alert(`Failed to update status: ${(e as Error).message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleConfirmPayment = async () => {
    if (!selectedOrder) return;

    setIsUpdating(true);
    try {
      await api.confirmPayment(selectedOrder.id);
      await fetchOrders();
      setShowProofModal(false);
      setSelectedOrder(null);
    } catch (e) {
      alert(`Failed to confirm payment: ${(e as Error).message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleSaveRemark = async () => {
    if (!selectedOrder) return;

    setIsUpdating(true);
    try {
      await api.updateAdminOrder(selectedOrder.id, { remark: remarkText });
      await fetchOrders();
      setShowRemarkModal(false);
      setSelectedOrder(null);
      setRemarkText('');
    } catch (e) {
      alert(`Failed to save remark: ${(e as Error).message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRejectPayment = async () => {
    if (!selectedOrder || !rejectReason.trim()) return;

    setIsUpdating(true);
    try {
      await api.rejectPayment(selectedOrder.id, rejectReason);
      await fetchOrders();
      setShowRejectModal(false);
      setShowProofModal(false);
      setSelectedOrder(null);
      setRejectReason('');
    } catch (e) {
      alert(`Failed to reject payment: ${(e as Error).message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleMarkReady = async (order: Order) => {
    if (!confirm(`Mark order ${order.order_number} as ready?\n\nThis will notify the customer that their ${order.delivery_method === 'Delivery' ? 'order is ready to ship' : 'order is ready for pickup'}.`)) return;

    setIsUpdating(true);
    try {
      const newStatus = order.delivery_method === 'Delivery' ? 'Ready to Ship' : 'Ready for Pickup';
      await api.updateAdminOrder(order.id, { status: newStatus as any });
      await fetchOrders();
    } catch (e) {
      alert(`Failed to update status: ${(e as Error).message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleGenerateInvoice = async (order: Order) => {
    try {
      const blob = await api.downloadReceipt(order.id, 'admin');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `OR_${order.or_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Failed to generate invoice: ${(e as Error).message}`);
    }
  };

  const handleDonePreparing = async (order: Order) => {
    const actionText = order.delivery_method === 'Delivery'
      ? 'This will mark the order as Shipped and notify the customer.'
      : 'This will mark the order as Ready for Collection and notify the customer.';

    if (!confirm(`Mark order ${order.order_number} as done preparing?\n\n${actionText}`)) return;

    setIsUpdating(true);
    try {
      const result = await api.donePreparing(order.id);
      alert(
        `Order ${order.order_number} has been updated to "${result.status}".\n\n` +
        `Customer "${order.customer_name}" has been notified.`
      );
      await fetchOrders();
    } catch (e) {
      alert(`Failed to mark as done preparing: ${(e as Error).message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const openProofModal = (order: Order) => {
    setIsModalLoading(true);
    setSelectedOrder(order);
    setRejectReason('');
    setShowProofModal(true);
    setIsModalLoading(false);
  };

  const openRejectModal = (order: Order) => {
    setSelectedOrder(order);
    setRejectReason('');
    setShowRejectModal(true);
  };

  const openRemarkModal = (order: Order) => {
    setSelectedOrder(order);
    setRemarkText(order.remark || '');
    setShowRemarkModal(true);
  };

  const openDetailModal = (order: Order) => {
    setIsModalLoading(true);
    setSelectedOrder(order);
    setShowDetailModal(true);
    setIsModalLoading(false);
  };

  const closeDetailModal = () => {
    setShowDetailModal(false);
    setSelectedOrder(null);
  };

  const closeProofModal = () => {
    setShowProofModal(false);
    setSelectedOrder(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Order Review</h2>
        <p className="text-sm text-gray-500">Review and manage all orders</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by order number or customer..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
            >
              <option value="all">All Status</option>
              {ORDER_STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Orders List */}
      <div className="space-y-4">
        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <p className="text-gray-500 font-medium">No orders found</p>
            <p className="text-sm text-gray-400 mt-1">Orders will appear here once placed</p>
          </div>
        ) : (
          filteredOrders.map((order) => (
            <div key={order.id} className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <span className="font-mono font-semibold text-gray-800">{order.order_number}</span>
                    <StatusBadge status={order.status} />
                    {order.remark && (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-purple-50 text-purple-600 rounded text-xs">
                        <MessageSquare className="w-3 h-3" />
                        Has remark
                      </span>
                    )}
                    {order.payment?.rejection_reason && (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-red-50 text-red-600 rounded text-xs">
                        <AlertTriangle className="w-3 h-3" />
                        Rejected
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                    <span>Customer: <span className="font-medium text-gray-700">{order.customer_name}</span></span>
                    <span>Items: <span className="font-medium text-gray-700">{order.items.length}</span></span>
                    <span>Method: <span className="font-medium text-gray-700">{order.delivery_method}</span></span>
                    <span>Date: <span className="font-medium text-gray-700">{new Date(order.created_at).toLocaleDateString()}</span></span>
                  </div>
                  {/* Status Progress Bar */}
                  <div className="mt-3">
                    <StatusBadge status={order.status} />
                  </div>
                  {order.remark && (
                    <div className="mt-2 p-2 bg-purple-50 rounded-lg text-sm text-purple-700">
                      <MessageSquare className="w-3 h-3 inline mr-1" />
                      {order.remark}
                    </div>
                  )}
                  {order.payment?.rejection_reason && (
                    <div className="mt-2 p-2 bg-red-50 rounded-lg text-sm text-red-700">
                      <AlertTriangle className="w-3 h-3 inline mr-1" />
                      Rejection reason: {order.payment.rejection_reason}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-800">{formatCurrency(order.total_price)}</div>
                    {order.discount_amount > 0 && (
                      <div className="text-xs text-green-600">{formatDiscount(order.discount_amount)} discount</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => openDetailModal(order)}
                      className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-5 h-5" />
                    </button>
                    {order.status === 'Payment Under Review' && (
                      <button
                        onClick={() => openProofModal(order)}
                        className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                        title="View Payment Proof"
                      >
                        <ImageIcon className="w-5 h-5" />
                      </button>
                    )}
                    <button
                      onClick={() => openRemarkModal(order)}
                      className="p-2 text-purple-500 hover:bg-purple-50 rounded-lg transition-colors"
                      title="Add/Edit Remark"
                    >
                      <Edit3 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
                {/* Pending Review - No payment proof uploaded */}
                {order.status === 'Pending Payment' && (
                  <>
                    <span className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-100 text-blue-700 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Awaiting Payment
                    </span>
                    <button
                      onClick={() => openRemarkModal(order)}
                      className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                    >
                      <Edit3 className="w-3 h-3 inline mr-1" />
                      Add Remark
                    </button>
                  </>
                )}
                {/* Review - Payment proof uploaded, needs confirmation */}
                {order.status === 'Payment Under Review' && (
                  <button
                    onClick={() => openProofModal(order)}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <ImageIcon className="w-3 h-3" />
                    View & Verify Proof
                  </button>
                )}
                {/* Paid - Auto-transitions to Preparing on confirm, but allow manual override */}
                {order.status === 'Paid' && order.delivery_method === 'Delivery' && (
                  <button
                    onClick={() => handleStatusChange(order, 'Preparing')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Package className="w-3 h-3" />
                    Start Preparing
                  </button>
                )}
                {/* Paid Pickup - Can mark as Ready directly */}
                {order.status === 'Paid' && order.delivery_method === 'Pickup' && (
                  <button
                    onClick={() => handleMarkReady(order)}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Bell className="w-3 h-3" />
                    Mark Ready for Pickup
                  </button>
                )}
                {/* Preparing - Done Preparing button */}
                {order.status === 'Preparing' && (
                  <button
                    onClick={() => handleDonePreparing(order)}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Check className="w-3 h-3" />
                    Done Preparing
                  </button>
                )}
                {/* Ready for Pickup / Ready to Ship / Ready for Collection - Generate Invoice */}
                {(order.status === 'Ready for Pickup' || order.status === 'Ready to Ship') && (
                  <button
                    onClick={() => handleGenerateInvoice(order)}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-cyan-600 text-white hover:bg-cyan-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <FileText className="w-3 h-3" />
                    Generate Invoice
                  </button>
                )}
                {/* Ready for Pickup - Customer collected */}
                {order.status === 'Ready for Pickup' && order.delivery_method === 'Pickup' && (
                  <button
                    onClick={() => handleStatusChange(order, 'Completed')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Check className="w-3 h-3" />
                    Customer Collected - Complete
                  </button>
                )}
                {/* Ready to Ship - Shipped */}
                {order.status === 'Ready to Ship' && (
                  <button
                    onClick={() => handleStatusChange(order, 'Shipped')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Truck className="w-3 h-3" />
                    Mark as Shipped
                  </button>
                )}
                {/* Shipped - Mark as Completed */}
                {order.status === 'Shipped' && (
                  <button
                    onClick={() => handleStatusChange(order, 'Completed')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Check className="w-3 h-3" />
                    Mark as Completed
                  </button>
                )}
                {/* Cancelled orders */}
                {(order.status === 'Pending Payment' || order.status === 'Payment Rejected') && (
                  <button
                    onClick={() => handleStatusChange(order, 'Cancelled')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors bg-gray-500 text-white hover:bg-gray-600 disabled:opacity-50"
                  >
                    Cancel Order
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Remark Modal */}
      {showRemarkModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-800">Order Remark</h3>
              <button onClick={() => setShowRemarkModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="mb-2 text-sm text-gray-500">
              Order: <span className="font-mono font-medium">{selectedOrder.order_number}</span>
            </div>
            <textarea
              value={remarkText}
              onChange={(e) => setRemarkText(e.target.value)}
              placeholder="Add a remark for this order (e.g., 'Customer requested express delivery')"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none resize-none"
              rows={4}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setShowRemarkModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRemark}
                disabled={isUpdating}
                className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {isUpdating ? <ButtonSpinner size="sm" /> : <Save className="w-4 h-4" />}
                {isUpdating ? 'Saving...' : 'Save Remark'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Proof Modal */}
      {showProofModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-bold text-gray-800">Payment Proof Review</h3>
                <p className="text-sm text-gray-500">Order: <span className="font-mono">{selectedOrder.order_number}</span></p>
              </div>
              <button onClick={closeProofModal} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Loading State */}
            {isModalLoading && (
              <FadeInContent
                isLoading={true}
                minHeight="min-h-[300px]"
                loadingComponent={
                  <>
                    <LoadingSpinner size="lg" />
                    <p className="text-primary-600 mt-4 font-medium">Loading order details...</p>
                  </>
                }
              />
            )}

            {/* Content */}
            {!isModalLoading && (
              <div className="flex-1 overflow-y-auto p-4">
                {/* Payment Proof Image */}
              {selectedOrder.payment?.receipt_url ? (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Uploaded Bank Slip</h4>
                  <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                    <img
                      src={`http://localhost:8002${selectedOrder.payment.receipt_url}`}
                      alt="Payment Proof"
                      className="w-full max-h-96 object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                        const fallback = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                        if (fallback) fallback.classList.remove('hidden');
                      }}
                    />
                    <div className="hidden p-8 text-center text-gray-500">
                      <ImageIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      <p>Failed to load image</p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Uploaded: {selectedOrder.payment.uploaded_at ? new Date(selectedOrder.payment.uploaded_at).toLocaleString() : 'Unknown'}
                  </p>
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500 border border-dashed border-gray-300 rounded-lg mb-4">
                  <ImageIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No payment proof uploaded</p>
                </div>
              )}

              {/* Rejection reason if exists */}
              {selectedOrder.payment?.rejection_reason && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
                  <div className="flex items-center gap-2 text-red-700 font-medium mb-1">
                    <AlertTriangle className="w-4 h-4" />
                    Previous Rejection Reason
                  </div>
                  <p className="text-red-800">{selectedOrder.payment.rejection_reason}</p>
                </div>
              )}

              {/* Order Summary */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Order Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Customer</span>
                    <span className="font-medium">{selectedOrder.customer_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Items</span>
                    <span className="font-medium">{selectedOrder.items.length} product(s)</span>
                  </div>
                  <div className="flex justify-between items-center pt-2 border-t border-gray-200">
                    <span className="font-medium text-gray-800">Total</span>
                    <span className="font-bold text-lg text-green-600">{formatCurrency(selectedOrder.total_price)}</span>
                  </div>
                </div>
              </div>

              {/* Quick Items Preview */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Items</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedOrder.items.slice(0, 4).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
                      {item.product_image_url ? (
                        <img
                          src={item.product_image_url}
                          alt={item.product_name}
                          className="w-8 h-8 object-cover rounded"
                        />
                      ) : (
                        <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center">
                          <Package className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                      <div className="text-sm">
                        <span className="font-medium text-gray-800">{item.product_name}</span>
                        <span className="text-gray-500 ml-1">×{item.quantity}</span>
                      </div>
                    </div>
                  ))}
                  {selectedOrder.items.length > 4 && (
                    <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-lg text-xs text-gray-500">
                      +{selectedOrder.items.length - 4}
                    </div>
                  )}
                </div>
              </div>
            </div>
            )}

            {/* Actions */}
            {!isModalLoading && (
              <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowProofModal(false);
                    openRejectModal(selectedOrder);
                  }}
                  disabled={isUpdating}
                  className="px-6 py-2.5 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                >
                  {isUpdating ? <ButtonSpinner size="sm" /> : <XCircle className="w-4 h-4" />}
                  {isUpdating ? 'Rejecting...' : 'Reject'}
                </button>
                <button
                  onClick={handleConfirmPayment}
                  disabled={isUpdating || !selectedOrder.payment?.receipt_url}
                  className="px-6 py-2.5 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                >
                  {isUpdating ? <ButtonSpinner size="sm" /> : <CheckCircle className="w-4 h-4" />}
                  {isUpdating ? 'Confirming...' : 'Confirm Payment'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reject Payment Modal */}
      {showRejectModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-800">Reject Payment</h3>
              <button onClick={() => setShowRejectModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="mb-2 text-sm text-gray-500">
              Order: <span className="font-mono font-medium">{selectedOrder.order_number}</span>
            </div>
            <p className="text-gray-600 text-sm mb-4">
              The salesman will be able to upload a new payment proof after rejection.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Enter reason for rejection (e.g., 'Payment amount does not match', 'Receipt is blurry')"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none resize-none"
              rows={3}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectPayment}
                disabled={isUpdating || !rejectReason.trim()}
                className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {isUpdating ? <ButtonSpinner size="sm" /> : <AlertTriangle className="w-4 h-4" />}
                {isUpdating ? 'Rejecting...' : 'Reject Payment'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Order Detail Modal */}
      {showDetailModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-800">Order Details</h3>
                <p className="text-sm text-gray-500">{selectedOrder.order_number}</p>
              </div>
              <button onClick={closeDetailModal} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Loading State */}
            {isModalLoading && (
              <FadeInContent
                isLoading={true}
                minHeight="min-h-[400px]"
                loadingComponent={
                  <>
                    <LoadingSpinner size="lg" />
                    <p className="text-primary-600 mt-4 font-medium">Loading order details...</p>
                  </>
                }
              />
            )}

            {!isModalLoading && (
              <div className="p-6 space-y-6">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Status</span>
                  <StatusBadge status={selectedOrder.status} />
                </div>

              {/* Customer Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-500">Customer Name</span>
                  <p className="font-medium text-gray-800">{selectedOrder.customer_name}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Delivery Method</span>
                  <p className="font-medium text-gray-800">{selectedOrder.delivery_method}</p>
                </div>
                {selectedOrder.address && (
                  <div className="col-span-2">
                    <span className="text-sm text-gray-500">Address</span>
                    <p className="font-medium text-gray-800">{selectedOrder.address}</p>
                  </div>
                )}
                <div>
                  <span className="text-sm text-gray-500">Order Date</span>
                  <p className="font-medium text-gray-800">{new Date(selectedOrder.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">OR Number</span>
                  <p className="font-mono font-medium text-purple-600">{selectedOrder.or_number}</p>
                </div>
              </div>

              {/* Remark */}
              {selectedOrder.remark && (
                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-2 text-purple-700 font-medium mb-2">
                    <MessageSquare className="w-4 h-4" />
                    Remark
                  </div>
                  <p className="text-purple-800">{selectedOrder.remark}</p>
                </div>
              )}

              {/* Items */}
              <div>
                <h4 className="font-medium text-gray-800 mb-3">Order Items ({selectedOrder.items.length})</h4>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Header */}
                  <div className="grid grid-cols-12 gap-3 px-4 py-2 bg-gray-100 text-xs font-semibold text-gray-600 uppercase">
                    <div className="col-span-1"></div>
                    <div className="col-span-6">Product</div>
                    <div className="col-span-2 text-center">Qty</div>
                    <div className="col-span-1 text-center">Unit</div>
                    <div className="col-span-2 text-right">Subtotal</div>
                  </div>
                  {/* Items */}
                  {selectedOrder.items.map((item, idx) => (
                    <div key={idx} className={`grid grid-cols-12 gap-3 px-4 py-3 items-center ${idx !== selectedOrder.items.length - 1 ? 'border-b border-gray-100' : ''} ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                      {/* Thumbnail */}
                      <div className="col-span-1">
                        {item.product_image_url ? (
                          <img
                            src={item.product_image_url}
                            alt={item.product_name}
                            className="w-12 h-12 object-cover rounded-lg border border-gray-200"
                          />
                        ) : (
                          <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                            <Package className="w-6 h-6 text-gray-400" />
                          </div>
                        )}
                      </div>
                      {/* Product Info */}
                      <div className="col-span-6 flex flex-col justify-center">
                        <p className="font-medium text-gray-800">{item.product_name}</p>
                        {item.product_sku && (
                          <p className="text-xs text-gray-500">SKU: {item.product_sku}</p>
                        )}
                      </div>
                      {/* Quantity */}
                      <div className="col-span-2 text-center flex items-center justify-center">
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded font-medium text-sm">
                          ×{item.quantity}
                        </span>
                      </div>
                      {/* Unit Price */}
                      <div className="col-span-1 text-center flex items-center justify-center text-sm text-gray-600">
                        {formatCurrency(item.unit_price)}
                      </div>
                      {/* Subtotal */}
                      <div className="col-span-2 text-right flex items-center justify-end font-medium text-gray-800">
                        {formatCurrency(item.unit_price * item.quantity)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Totals */}
              <div className="border-t border-gray-200 pt-4 space-y-2">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal</span>
                  <span>{formatCurrency(selectedOrder.total_price + selectedOrder.discount_amount)}</span>
                </div>
                {selectedOrder.discount_amount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>{formatDiscount(selectedOrder.discount_amount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold text-gray-800 pt-2 border-t border-gray-200">
                  <span>Total</span>
                  <span className="text-green-600">{formatCurrency(selectedOrder.total_price)}</span>
                </div>
              </div>

              {/* Status Actions */}
              <div className="border-t border-gray-200 pt-4">
                <h4 className="font-medium text-gray-800 mb-3">Update Status</h4>
                <div className="flex flex-wrap gap-2">
                  {/* Pending Review - No payment proof uploaded */}
                  {selectedOrder.status === 'Pending Payment' && (
                    <>
                      <span className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg font-medium flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Awaiting Payment
                      </span>
                      <button
                        onClick={() => {
                          openRemarkModal(selectedOrder);
                          setShowDetailModal(false);
                        }}
                        className="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
                      >
                        <Edit3 className="w-4 h-4" />
                        Add Remark
                      </button>
                    </>
                  )}
                  {/* Review - Payment proof uploaded */}
                  {selectedOrder.status === 'Payment Under Review' && (
                    <button
                      onClick={() => {
                        setShowDetailModal(false);
                        openProofModal(selectedOrder);
                      }}
                      disabled={isUpdating}
                      className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                    >
                      <ImageIcon className="w-4 h-4" />
                      View & Verify Proof
                    </button>
                  )}
                  {/* Paid Delivery - Start Preparing */}
                  {selectedOrder.status === 'Paid' && selectedOrder.delivery_method === 'Delivery' && (
                    <button
                      onClick={() => {
                        handleStatusChange(selectedOrder, 'Preparing');
                        setShowDetailModal(false);
                      }}
                      disabled={isUpdating}
                      className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                    >
                      <Package className="w-4 h-4" />
                      Start Preparing
                    </button>
                  )}
                  {/* Paid Pickup - Mark Ready for Pickup */}
                  {selectedOrder.status === 'Paid' && selectedOrder.delivery_method === 'Pickup' && (
                    <button
                      onClick={() => {
                        handleMarkReady(selectedOrder);
                        setShowDetailModal(false);
                      }}
                      disabled={isUpdating}
                      className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                    >
                      <Bell className="w-4 h-4" />
                      Mark Ready for Pickup
                    </button>
                  )}
                  {/* Preparing - Done Preparing */}
                  {selectedOrder.status === 'Preparing' && (
                    <button
                      onClick={() => {
                        handleDonePreparing(selectedOrder);
                        setShowDetailModal(false);
                      }}
                      disabled={isUpdating}
                      className="px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Done Preparing
                    </button>
                  )}
                  {/* Ready for Pickup / Ready to Ship / Ready for Collection - Generate Invoice */}
                  {(selectedOrder.status === 'Ready for Pickup' || selectedOrder.status === 'Ready to Ship') && (
                    <>
                      <button
                        onClick={() => {
                          handleGenerateInvoice(selectedOrder);
                        }}
                        disabled={isUpdating}
                        className="px-4 py-2 bg-cyan-600 text-white font-medium rounded-lg hover:bg-cyan-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                      >
                        <FileText className="w-4 h-4" />
                        Generate Invoice
                      </button>
                      {selectedOrder.status === 'Ready for Pickup' && (
                        <button
                          onClick={() => {
                            handleStatusChange(selectedOrder, 'Completed');
                            setShowDetailModal(false);
                          }}
                          disabled={isUpdating}
                          className="px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                        >
                          <Check className="w-4 h-4" />
                          Customer Collected - Complete
                        </button>
                      )}
                      {selectedOrder.status === 'Ready to Ship' && (
                        <button
                          onClick={() => {
                            handleStatusChange(selectedOrder, 'Shipped');
                            setShowDetailModal(false);
                          }}
                          disabled={isUpdating}
                          className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                        >
                          <Truck className="w-4 h-4" />
                          Mark as Shipped
                        </button>
                      )}
                    </>
                  )}
                  {/* Shipped - Mark as Completed */}
                  {selectedOrder.status === 'Shipped' && (
                    <button
                      onClick={() => {
                        handleStatusChange(selectedOrder, 'Completed');
                        setShowDetailModal(false);
                      }}
                      disabled={isUpdating}
                      className="px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Mark as Completed
                    </button>
                  )}
                </div>
              </div>
            </div>
            )}
          </div>
        </div>
      )}

      {/* Pagination */}
      {filteredOrders.length > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Showing {filteredOrders.length} orders</span>
          <div className="flex items-center gap-2">
            <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg disabled:opacity-50" disabled>
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium">1</span>
            <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg disabled:opacity-50" disabled>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
