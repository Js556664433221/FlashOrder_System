import { useStore } from '../store';

export function Cart() {
  const { cart, removeFromCart, updateQuantity, placeOrder, clearCart, fetchProducts, fetchOrders } = useStore();
  const total = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);

  const handlePlaceOrder = async () => {
    try {
      await placeOrder();
      // Refresh products to show updated stock
      fetchProducts();
      fetchOrders();
      alert('Order placed successfully!');
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const handleRemove = (productId: number) => {
    removeFromCart(productId);
  };

  const handleQuantityChange = (productId: number, newQuantity: number) => {
    updateQuantity(productId, newQuantity);
  };

  return (
    <div className="p-4 border-t border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Shopping Cart</h2>
        {cart.length > 0 && (
          <button onClick={clearCart} className="text-sm text-red-500 hover:text-red-700">
            Clear Cart
          </button>
        )}
      </div>

      {cart.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Your cart is empty</div>
      ) : (
        <>
          <div className="space-y-3 mb-4">
            {cart.map((item) => (
              <div key={item.product.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                {item.product.image_url && (
                  <img
                    src={item.product.image_url}
                    alt={item.product.name}
                    className="w-16 h-16 object-cover rounded"
                  />
                )}
                <div className="flex-1">
                  <div className="font-medium">{item.product.name}</div>
                  <div className="text-sm text-gray-500">
                    ${item.product.price.toFixed(2)} x {item.quantity}
                    <span className="ml-2 font-semibold text-purple-600">
                      = ${(item.product.price * item.quantity).toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleQuantityChange(item.product.id, item.quantity - 1)}
                    className="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center"
                  >
                    -
                  </button>
                  <span className="w-8 text-center">{item.quantity}</span>
                  <button
                    onClick={() => handleQuantityChange(item.product.id, item.quantity + 1)}
                    className="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center"
                  >
                    +
                  </button>
                  <button
                    onClick={() => handleRemove(item.product.id)}
                    className="ml-2 text-red-500 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-between items-center pt-4 border-t border-gray-200">
            <div className="text-xl font-bold">Total: ${total.toFixed(2)}</div>
            <button
              onClick={handlePlaceOrder}
              className="px-6 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700"
            >
              Place Order
            </button>
          </div>
        </>
      )}
    </div>
  );
}
