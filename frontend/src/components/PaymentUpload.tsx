import { useState } from 'react';
import { useStore } from '../store';

export function PaymentUpload() {
  const { orders, fetchOrders, uploadPayment } = useStore();
  const [selectedOrder, setSelectedOrder] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedReceiptUrl, setUploadedReceiptUrl] = useState<string | null>(null);

  const pendingOrders = orders.filter((o) => o.status === 'Pending Payment');

  const handleUpload = async () => {
    if (!selectedOrder || !file) return;
    setUploading(true);
    try {
      const payment = await uploadPayment(selectedOrder, file);
      setUploadedReceiptUrl(payment.receipt_url);
      alert('Payment proof uploaded successfully!');
      setSelectedOrder(null);
      setFile(null);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4 border-t border-gray-200">
      <h2 className="text-xl font-semibold mb-4">Payment Proof Upload</h2>

      <button
        onClick={() => fetchOrders()}
        className="mb-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
      >
        Refresh Orders
      </button>

      {pendingOrders.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No orders pending payment
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Order
            </label>
            <select
              value={selectedOrder || ''}
              onChange={(e) => setSelectedOrder(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">-- Select an order --</option>
              {pendingOrders.map((order) => (
                <option key={order.id} value={order.id}>
                  {order.order_number} - ${order.total_price.toFixed(2)}
                </option>
              ))}
            </select>
          </div>

          {selectedOrder && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Receipt (JPG, PNG, or PDF)
              </label>
              <input
                type="file"
                accept=".jpg,.jpeg,.png,.pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full"
              />
            </div>
          )}

          {file && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full px-4 py-2 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 disabled:bg-gray-300"
            >
              {uploading ? 'Uploading...' : 'Upload Payment Proof'}
            </button>
          )}

          {uploadedReceiptUrl && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg">
              <p className="text-green-700 font-medium mb-2">Upload successful!</p>
              <img
                src={`http://localhost:8000${uploadedReceiptUrl}`}
                alt="Uploaded receipt"
                className="max-w-full h-auto rounded-lg shadow-md"
              />
            </div>
          )}
        </div>
      )}

      <div className="mt-6">
        <h3 className="font-medium mb-2">Recent Orders</h3>
        <div className="space-y-2">
          {orders.slice(0, 5).map((order) => (
            <div key={order.id} className="p-3 bg-gray-50 rounded-lg flex justify-between items-center">
              <div>
                <span className="font-medium">{order.order_number}</span>
                <span className="text-sm text-gray-500 ml-2">${order.total_price.toFixed(2)}</span>
              </div>
              <span
                className={`text-sm px-2 py-1 rounded ${
                  order.status === 'Pending Payment'
                    ? 'bg-yellow-100 text-yellow-800'
                    : order.status === 'Payment Under Review'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {order.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
