import { useState } from 'react';
import { useStore } from '../store';
import { Checkout } from './Checkout';
import { api } from '../api';
import { ShoppingCart, Minus, Plus, Trash2, ArrowRight, Tag, Percent, Package } from 'lucide-react';
import { formatCurrency, formatDiscount } from '../utils';

export function Cart() {
  const { cart, removeFromCart, updateQuantity, clearCart, fetchProducts, fetchOrders,
          appliedPromo, setAppliedPromo, clearAppliedPromo, promoReplacedMessage, clearPromoReplacedMessage } = useStore();
  const [showCheckout, setShowCheckout] = useState(false);
  const [showPromoInput, setShowPromoInput] = useState(false);
  const [promoCode, setPromoCode] = useState('');

  const subtotal = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const discount = appliedPromo?.validation.valid ? (appliedPromo.validation.discount_value || 0) : 0;
  const total = Math.max(0, subtotal - discount);

  const handlePlaceOrder = () => {
    setShowCheckout(true);
  };

  const handleCheckoutSuccess = async () => {
    setShowCheckout(false);
    fetchProducts();
    fetchOrders();
  };

  const handleRemove = (productId: number) => {
    removeFromCart(productId);
  };

  const handleQuantityChange = (productId: number, newQuantity: number) => {
    updateQuantity(productId, newQuantity);
  };

  const handleApplyPromo = async () => {
    if (!promoCode.trim() || subtotal === 0) return;

    setShowPromoInput(false);
    const wasReplaced = appliedPromo !== null;
    const trimmedCode = promoCode.trim();

    try {
      const result = await api.validatePromoCode(trimmedCode, subtotal, 'salesman');
      setAppliedPromo(trimmedCode, result, wasReplaced);
    } catch (e) {
      setAppliedPromo(trimmedCode, {
        valid: false,
        message: (e as Error).message || 'Invalid promo code'
      }, wasReplaced);
    }
  };

  const handleRemovePromo = () => {
    setPromoCode('');
    clearAppliedPromo();
  };

  return (
    <>
      <div className="p-4 border-t border-dark-200 bg-white">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-dark-900">Shopping Cart</h2>
            {cart.length > 0 && (
              <span className="bg-primary-100 text-primary-700 text-sm font-medium px-2 py-1 rounded-full">
                {cart.length} {cart.length === 1 ? 'item' : 'items'}
              </span>
            )}
          </div>
          {cart.length > 0 && (
            <button
              onClick={clearCart}
              className="text-sm text-accent-red hover:text-accent-red/80 font-medium flex items-center gap-1 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Clear All
            </button>
          )}
        </div>

        {cart.length === 0 ? (
          <div className="text-center py-12 bg-surface-100 rounded-xl border border-dark-200">
            <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package className="w-10 h-10 text-primary-400" />
            </div>
            <p className="text-dark-500 text-lg font-medium">Your cart is empty</p>
            <p className="text-dark-400 text-sm mt-1">Add some products to get started</p>
          </div>
        ) : (
          <>
            {/* Cart Items */}
            <div className="space-y-3 mb-4">
              {cart.map((item) => (
                <div
                  key={item.product.id}
                  className="flex gap-3 p-3 bg-surface-100 rounded-xl border border-dark-100"
                >
                  {item.product.image_url ? (
                    <img
                      src={item.product.image_url}
                      alt={item.product.name}
                      className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                    />
                  ) : (
                    <div className="w-20 h-20 bg-dark-100 rounded-lg flex-shrink-0 flex items-center justify-center">
                      <Package className="w-8 h-8 text-dark-400" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-dark-900 truncate">
                      {item.product.name}
                    </h3>
                    <p className="text-sm text-dark-500 mb-2 font-mono">
                      SKU: {item.product.sku}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-bold text-primary-600">
                        {formatCurrency(item.product.price)}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleQuantityChange(item.product.id, item.quantity - 1)}
                          className="w-8 h-8 rounded-full bg-surface-50 border border-dark-200 hover:bg-dark-100 flex items-center justify-center transition-colors"
                        >
                          <Minus className="w-4 h-4 text-dark-600" />
                        </button>
                        <span className="w-10 text-center font-semibold text-lg text-dark-800">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => handleQuantityChange(item.product.id, item.quantity + 1)}
                          className="w-8 h-8 rounded-full bg-surface-50 border border-dark-200 hover:bg-dark-100 flex items-center justify-center transition-colors"
                        >
                          <Plus className="w-4 h-4 text-dark-600" />
                        </button>
                        <button
                          onClick={() => handleRemove(item.product.id)}
                          className="ml-2 p-2 text-accent-red hover:bg-accent-red/10 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Total and Checkout */}
            <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-4 mb-4 border border-primary-200">
              {/* Promo Code Section */}
              {appliedPromo?.validation.valid ? (
                <>
                  {promoReplacedMessage && (
                    <div className="mb-3 p-2 bg-accent-amber/10 border border-accent-amber/30 rounded-lg text-accent-amber text-sm text-center">
                      {promoReplacedMessage}
                    </div>
                  )}
                  <div className="flex items-center justify-between mb-3 pb-3 border-b border-primary-200">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-accent-green/20 rounded-lg">
                        <Percent className="w-4 h-4 text-accent-green" />
                      </div>
                      <span className="text-accent-green font-medium">
                        {appliedPromo.code}: {formatDiscount(discount)}
                      </span>
                    </div>
                    <button
                      onClick={handleRemovePromo}
                      className="text-dark-400 hover:text-accent-red transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </>
              ) : showPromoInput ? (
                <div className="mb-3 pb-3 border-b border-primary-200">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={promoCode}
                      onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                      onKeyDown={(e) => e.key === 'Enter' && handleApplyPromo()}
                      placeholder="Enter promo code"
                      className="flex-1 px-3 py-2 border border-dark-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none uppercase bg-surface-50"
                    />
                    <button
                      onClick={handleApplyPromo}
                      className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
                    >
                      Apply
                    </button>
                    <button
                      onClick={() => setShowPromoInput(false)}
                      className="px-3 py-2 text-dark-400 hover:text-dark-600 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                  {appliedPromo && !appliedPromo.validation.valid && (
                    <p className="mt-2 text-sm text-accent-red">{appliedPromo.validation.message}</p>
                  )}
                </div>
              ) : (
                <div className="mb-3 pb-3 border-b border-primary-200">
                  <button
                    onClick={() => {
                      setShowPromoInput(true);
                      clearPromoReplacedMessage();
                    }}
                    className="flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium text-sm"
                  >
                    <Tag className="w-4 h-4" />
                    Have a promo code?
                  </button>
                </div>
              )}

              {/* Subtotal */}
              <div className="flex justify-between items-center mb-2">
                <span className="text-dark-600">Subtotal ({cart.length} items)</span>
                <span className="font-semibold text-dark-800">{formatCurrency(subtotal)}</span>
              </div>

              {/* Discount (if applied) */}
              {discount > 0 && (
                <div className="flex justify-between items-center mb-2 text-accent-green">
                  <span>Discount</span>
                  <span className="font-medium">{formatDiscount(discount)}</span>
                </div>
              )}

              {/* Total */}
              <div className="flex justify-between items-center pt-2 border-t border-primary-200">
                <span className="text-lg font-bold text-dark-900">Total</span>
                <span className="text-2xl font-bold text-accent-green">
                  {formatCurrency(total)}
                </span>
              </div>
            </div>

            {/* Checkout Button */}
            <button
              onClick={handlePlaceOrder}
              className="w-full py-4 bg-primary-600 text-white font-bold rounded-xl hover:bg-primary-700 transition-all flex items-center justify-center gap-2 shadow-xl shadow-primary-500/50"
            >
              Proceed to Checkout
              <ArrowRight className="w-5 h-5" />
            </button>
          </>
        )}
      </div>

      {/* Checkout Modal */}
      {showCheckout && (
        <Checkout
          onClose={() => setShowCheckout(false)}
          onSuccess={handleCheckoutSuccess}
        />
      )}
    </>
  );
}
