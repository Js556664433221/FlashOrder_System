import { useStore } from '../store';

export function PaymentUpload() {
  const { orders, fetchOrders } = useStore();
  const recentPayments = orders.filter((o) => o.status === 'Payment Under Review');

  return (
    <div className="p-4 border-t border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Payment History</h2>
        <button
          onClick={() => fetchOrders()}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
        >
          Refresh
        </button>
      </div>

      {recentPayments.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-4xl mb-4">📋</p>
          <p>No payments under review</p>
          <p className="text-sm mt-2">Upload payment receipts directly from the Orders tab</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-600 mb-4">
            {recentPayments.length} order(s) awaiting payment verification
          </p>
          {recentPayments.map((order) => (
            <div key={order.id} className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <span className="font-semibold">{order.order_number}</span>
                  <span className="ml-2 px-2 py-0.5 rounded text-xs bg-orange-200 text-orange-800">
                    Under Review
                  </span>
                </div>
                <span className="font-bold text-purple-600">${order.total_price.toFixed(2)}</span>
              </div>
              <div className="text-sm text-gray-500 mt-1">
                Submitted: {new Date(order.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
