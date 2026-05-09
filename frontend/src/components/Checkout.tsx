import { useState, useEffect, useRef } from 'react';
import { useStore } from '../store';
import { api } from '../api';
import type { CheckoutData, DeliveryMethod, CustomerProfile, CustomerProfileCreate } from '../types';
import { FileText, MapPin, User, Package, Percent, X, Download, Check, Loader2, Tag, MessageSquare, ChevronDown, Search, Save } from 'lucide-react';
import { formatCurrency, formatDiscount } from '../utils';
import { ButtonSpinner } from './LoadingSpinner';

interface CheckoutProps {
  onClose?: () => void;
  onSuccess?: () => void;
}

export function Checkout({ onClose, onSuccess }: CheckoutProps) {
  const { cart, placeOrder, lastPlacedOrder, downloadReceipt, clearLastOrder,
          appliedPromo, setAppliedPromo, clearAppliedPromo, role } = useStore();
  const [customerName, setCustomerName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [location, setLocation] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [email, setEmail] = useState('');
  const [deliveryMethod, setDeliveryMethod] = useState<DeliveryMethod>('Pickup');
  const [address, setAddress] = useState('');
  const [remark, setRemark] = useState('');
  const [showPromoInput, setShowPromoInput] = useState(false);
  const [promoCode, setPromoCode] = useState(appliedPromo?.code || '');
  const [promoLoading, setPromoLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // Customer profile states
  const [customers, setCustomers] = useState<CustomerProfile[]>([]);
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false);
  const [customerSearch, setCustomerSearch] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerProfile | null>(null);
  const [saveAsNewCustomer, setSaveAsNewCustomer] = useState(false);
  const [_isSavingCustomer, setIsSavingCustomer] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const subtotal = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const discount = appliedPromo?.validation.valid ? (appliedPromo.validation.discount_value || 0) : 0;
  const total = Math.max(0, subtotal - discount);

  // Fetch customer profiles on mount
  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const data = await api.getCustomers(role);
        setCustomers(data);
      } catch (e) {
        console.error('Failed to fetch customers:', e);
      }
    };
    fetchCustomers();
  }, [role]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowCustomerDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (lastPlacedOrder) {
      setShowSuccess(true);
    }
  }, [lastPlacedOrder]);

  useEffect(() => {
    if (appliedPromo) {
      setPromoCode(appliedPromo.code);
    }
  }, [appliedPromo]);

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) {
      clearAppliedPromo();
      return;
    }

    setPromoLoading(true);
    const wasReplaced = appliedPromo !== null;
    const trimmedCode = promoCode.trim().toUpperCase();

    try {
      const result = await api.validatePromoCode(trimmedCode, subtotal, role);
      setAppliedPromo(trimmedCode, result, wasReplaced);
      setShowPromoInput(false);
    } catch (e) {
      setAppliedPromo(trimmedCode, {
        valid: false,
        message: (e as Error).message || 'Failed to validate promo code'
      }, wasReplaced);
    } finally {
      setPromoLoading(false);
    }
  };

  const handlePromoCodeChange = (value: string) => {
    const upperValue = value.toUpperCase();
    setPromoCode(upperValue);
  };

  const handleRemovePromo = () => {
    setPromoCode('');
    clearAppliedPromo();
    setShowPromoInput(false);
  };

  const handleSelectCustomer = (customer: CustomerProfile) => {
    setSelectedCustomer(customer);
    setCustomerName(customer.name);
    setCompanyName(customer.company_name || '');
    setLocation(customer.location || '');
    setContactNumber(customer.contact_number);
    setEmail(customer.email || '');
    setCustomerSearch('');
    setShowCustomerDropdown(false);
  };

  const handleClearCustomer = () => {
    setSelectedCustomer(null);
    setCustomerName('');
    setCompanyName('');
    setLocation('');
    setContactNumber('');
    setEmail('');
  };

  const handleSaveCustomer = async (): Promise<boolean> => {
    if (!customerName.trim() || !location.trim() || !contactNumber.trim()) {
      return false;
    }

    setIsSavingCustomer(true);
    try {
      const customerData: CustomerProfileCreate = {
        name: customerName.trim(),
        company_name: companyName.trim() || undefined,
        location: location.trim() || undefined,
        contact_number: contactNumber.trim(),
        email: email.trim() || undefined,
      };
      const newCustomer = await api.createCustomer(customerData, role);
      setCustomers(prev => [newCustomer, ...prev]);
      setSelectedCustomer(newCustomer);
      return true;
    } catch (e) {
      console.error('Failed to save customer:', e);
      return false;
    } finally {
      setIsSavingCustomer(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!customerName.trim()) {
      setError('Customer name is required');
      return;
    }
    if (!location.trim()) {
      setError('Location is required');
      return;
    }
    if (!contactNumber.trim()) {
      setError('Contact number is required');
      return;
    }

    setIsSubmitting(true);

    try {
      if (saveAsNewCustomer) {
        const saved = await handleSaveCustomer();
        if (!saved) {
          setError('Failed to save customer profile. Please check the required fields.');
          setIsSubmitting(false);
          return;
        }
      }

      const checkoutData: CheckoutData = {
        customer_name: customerName,
        delivery_method: deliveryMethod,
        address: deliveryMethod === 'Delivery' ? address : undefined,
        promo_code: appliedPromo?.validation.valid ? appliedPromo.code : undefined,
        remark: remark.trim() || undefined,
      };

      await placeOrder(checkoutData);
      clearAppliedPromo();
      setShowSuccess(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadReceipt = async () => {
    if (lastPlacedOrder) {
      try {
        await downloadReceipt(lastPlacedOrder.id);
      } catch (e) {
        setError('Failed to download receipt');
      }
    }
  };

  const handleCloseSuccess = () => {
    setShowSuccess(false);
    setCustomerName('');
    setCompanyName('');
    setLocation('');
    setContactNumber('');
    setEmail('');
    setAddress('');
    setRemark('');
    setPromoCode('');
    setDeliveryMethod('Pickup');
    setSelectedCustomer(null);
    setSaveAsNewCustomer(false);
    clearLastOrder();
    if (onSuccess) onSuccess();
  };

  const filteredCustomers = customers.filter(c =>
    c.name.toLowerCase().includes(customerSearch.toLowerCase()) ||
    c.company_name?.toLowerCase().includes(customerSearch.toLowerCase()) ||
    c.contact_number.includes(customerSearch)
  );

  // Success modal
  if (showSuccess && lastPlacedOrder) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-surface-50 rounded-xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
          <div className="text-center">
            <div className="w-16 h-16 bg-accent-green/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package className="w-8 h-8 text-accent-green" />
            </div>
            <h2 className="text-2xl font-bold text-dark-900 mb-2">Order Placed!</h2>
            <p className="text-dark-600 mb-4">
              Your order has been successfully placed.
            </p>

            <div className="bg-surface-100 rounded-xl p-4 mb-6 text-left">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-dark-500">Order Number</span>
                <span className="font-mono font-semibold">{lastPlacedOrder.order_number}</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-dark-500">OR Number</span>
                <span className="font-mono font-semibold text-primary-600">{lastPlacedOrder.or_number}</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-dark-500">Customer</span>
                <span className="font-medium text-dark-800">{lastPlacedOrder.customer_name}</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-dark-500">Delivery</span>
                <span className="font-medium text-dark-800">{lastPlacedOrder.delivery_method}</span>
              </div>
              {lastPlacedOrder.discount_amount > 0 && (
                <div className="flex justify-between items-center text-accent-green mt-2 pt-2 border-t border-dark-200">
                  <span className="text-sm">Discount</span>
                  <span className="font-medium">{formatDiscount(lastPlacedOrder.discount_amount)}</span>
                </div>
              )}
              <div className="flex justify-between items-center mt-2 pt-2 border-t border-dark-200">
                <span className="text-sm font-bold text-dark-900">Total</span>
                <span className="font-bold text-lg text-accent-green">
                  {formatCurrency(lastPlacedOrder.total_price)}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleDownloadReceipt}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition-colors"
              >
                <Download className="w-5 h-5" />
                Download Receipt
              </button>
              <button
                onClick={handleCloseSuccess}
                className="flex-1 px-4 py-3 bg-dark-100 text-dark-700 font-semibold rounded-xl hover:bg-dark-200 transition-colors"
              >
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface-50 rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-surface-50 border-b border-dark-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-dark-900">Checkout</h2>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-dark-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-dark-500" />
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-accent-red/10 border border-accent-red/30 rounded-xl text-accent-red text-sm">
              {error}
            </div>
          )}

          {/* Customer Selection Dropdown */}
          <div className="mb-5 relative" ref={dropdownRef}>
            <label className="block text-sm font-medium text-dark-700 mb-2">
              <User className="w-4 h-4 inline mr-1" />
              Select Existing Customer (Optional)
            </label>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowCustomerDropdown(!showCustomerDropdown)}
                className="w-full px-4 py-3 border border-dark-200 rounded-xl text-left bg-surface-50 hover:bg-surface-100 transition-colors flex items-center justify-between"
              >
                <span className={selectedCustomer ? 'text-dark-900' : 'text-dark-400'}>
                  {selectedCustomer
                    ? `${selectedCustomer.name}${selectedCustomer.company_name ? ` - ${selectedCustomer.company_name}` : ''}`
                    : 'Search or select a customer...'}
                </span>
                <ChevronDown className={`w-5 h-5 text-dark-400 transition-transform ${showCustomerDropdown ? 'rotate-180' : ''}`} />
              </button>

              {showCustomerDropdown && (
                <div className="absolute z-10 w-full mt-1 bg-surface-50 border border-dark-200 rounded-xl shadow-lg">
                  <div className="p-2 border-b border-dark-200">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
                      <input
                        type="text"
                        value={customerSearch}
                        onChange={(e) => setCustomerSearch(e.target.value)}
                        placeholder="Search by name, company, or phone..."
                        className="w-full pl-10 pr-4 py-2.5 border border-dark-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-surface-50"
                        autoFocus
                      />
                    </div>
                  </div>

                  <div className="max-h-60 overflow-y-auto">
                    {filteredCustomers.length === 0 ? (
                      <div className="p-4 text-center text-dark-500 text-sm">
                        {customers.length === 0
                          ? 'No saved customers yet'
                          : 'No customers match your search'}
                      </div>
                    ) : (
                      filteredCustomers.map((customer) => (
                        <button
                          key={customer.id}
                          type="button"
                          onClick={() => handleSelectCustomer(customer)}
                          className="w-full px-4 py-3 text-left hover:bg-surface-100 border-b border-dark-100 last:border-b-0"
                        >
                          <div className="font-medium text-dark-900">{customer.name}</div>
                          <div className="text-sm text-dark-500">
                            {customer.company_name && <span>{customer.company_name} - </span>}
                            {customer.contact_number}
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {selectedCustomer && (
              <button
                type="button"
                onClick={handleClearCustomer}
                className="mt-2 text-sm text-dark-500 hover:text-accent-red flex items-center gap-1"
              >
                <X className="w-4 h-4" />
                Clear selection
              </button>
            )}
          </div>

          {/* Divider */}
          <div className="relative mb-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-dark-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-surface-50 text-dark-500">Customer Details</span>
            </div>
          </div>

          {/* Customer Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Customer Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-dark-700 mb-1.5">
                <User className="w-4 h-4 inline mr-1" />
                Customer Name <span className="text-accent-red">*</span>
              </label>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Enter customer name"
                required
                className="w-full px-3 py-2.5 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-surface-50"
              />
            </div>

            {/* Company Name */}
            <div>
              <label className="block text-sm font-medium text-dark-700 mb-1.5">
                Company / Shop Name
              </label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Enter company or shop name"
                className="w-full px-3 py-2.5 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-surface-50"
              />
            </div>

            {/* Contact Number */}
            <div>
              <label className="block text-sm font-medium text-dark-700 mb-1.5">
                Contact Number <span className="text-accent-red">*</span>
              </label>
              <input
                type="tel"
                value={contactNumber}
                onChange={(e) => setContactNumber(e.target.value)}
                placeholder="Enter contact number"
                required
                className="w-full px-3 py-2.5 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-surface-50"
              />
            </div>

            {/* Location */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-dark-700 mb-1.5">
                <MapPin className="w-4 h-4 inline mr-1" />
                Location <span className="text-accent-red">*</span>
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Enter location or address"
                required
                className="w-full px-3 py-2.5 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-surface-50"
              />
            </div>

            {/* Email - Optional */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-dark-700 mb-1.5">
                Email <span className="text-dark-400 text-xs">(optional)</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email address"
                className="w-full px-3 py-2.5 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all bg-surface-50"
              />
            </div>
          </div>

          {/* Validation Summary */}
          {(customerName || location || contactNumber) && (
            <div className="mb-4 p-2 bg-accent-amber/10 border border-accent-amber/30 rounded-xl text-xs text-accent-amber">
              Fields marked with <span className="text-accent-red">*</span> are required before placing order
            </div>
          )}

          {/* Save as New Customer Checkbox */}
          <div className="mb-5 p-3 bg-primary-50 border border-primary-200 rounded-xl">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={saveAsNewCustomer}
                onChange={(e) => setSaveAsNewCustomer(e.target.checked)}
                className="w-5 h-5 text-primary-600 border-dark-300 rounded focus:ring-primary-500"
              />
              <div className="flex items-center gap-2">
                <Save className="w-4 h-4 text-primary-600" />
                <span className="text-sm font-medium text-primary-700">Save as new customer profile</span>
              </div>
            </label>
            <p className="mt-1 text-xs text-primary-600 ml-8">
              Save these details for future one-click orders
            </p>
          </div>

          {/* Delivery Method */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-dark-700 mb-2">
              <Package className="w-4 h-4 inline mr-1" />
              Delivery Method <span className="text-accent-red">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setDeliveryMethod('Pickup')}
                className={`p-4 border-2 rounded-xl text-center transition-all ${
                  deliveryMethod === 'Pickup'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-dark-200 hover:border-dark-300 text-dark-700'
                }`}
              >
                <div className="text-2xl mb-1">🏪</div>
                <div className="font-medium">Pickup</div>
              </button>
              <button
                type="button"
                onClick={() => setDeliveryMethod('Delivery')}
                className={`p-4 border-2 rounded-xl text-center transition-all ${
                  deliveryMethod === 'Delivery'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-dark-200 hover:border-dark-300 text-dark-700'
                }`}
              >
                <div className="text-2xl mb-1">🚚</div>
                <div className="font-medium">Delivery</div>
              </button>
            </div>
          </div>

          {/* Address - Only show for Delivery */}
          {deliveryMethod === 'Delivery' && (
            <div className="mb-5 animate-in slide-in-from-top-2 duration-200">
              <label className="block text-sm font-medium text-dark-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                Delivery Address <span className="text-accent-red">*</span>
              </label>
              <textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Enter complete delivery address"
                required={deliveryMethod === 'Delivery'}
                rows={3}
                className="w-full px-4 py-3 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all resize-none bg-surface-50"
              />
            </div>
          )}

          {/* Promo Code */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-dark-700 mb-2">
              <Percent className="w-4 h-4 inline mr-1" />
              Promo Code (Optional)
            </label>
            {appliedPromo?.validation.valid ? (
              <div className="flex items-center gap-2">
                <div className="flex-1 px-4 py-3 bg-accent-green/10 border border-accent-green/30 rounded-xl flex items-center gap-2">
                  <Check className="w-5 h-5 text-accent-green" />
                  <span className="text-accent-green font-medium">
                    {appliedPromo.code}: {formatDiscount(discount)}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleRemovePromo}
                  className="p-2 text-dark-400 hover:text-accent-red hover:bg-accent-red/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ) : showPromoInput ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={promoCode}
                  onChange={(e) => handlePromoCodeChange(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleApplyPromo())}
                  placeholder="Enter promo code"
                  className="flex-1 px-4 py-3 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all uppercase bg-surface-50"
                />
                <button
                  type="button"
                  onClick={handleApplyPromo}
                  disabled={!promoCode.trim() || promoLoading}
                  className="px-6 py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 disabled:bg-dark-200 disabled:text-dark-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {promoLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Apply'
                  )}
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setShowPromoInput(true)}
                className="flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
              >
                <Tag className="w-4 h-4" />
                Have a promo code?
              </button>
            )}
            {appliedPromo && !appliedPromo.validation.valid && (
              <p className="mt-2 text-sm text-accent-red">
                {appliedPromo.validation.message}
              </p>
            )}
            {appliedPromo?.validation.valid && showPromoInput === false && (
              <button
                type="button"
                onClick={() => setShowPromoInput(true)}
                className="mt-2 text-sm text-dark-500 hover:text-dark-700"
              >
                Change promo code
              </button>
            )}
          </div>

          {/* Remark */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-dark-700 mb-2">
              <MessageSquare className="w-4 h-4 inline mr-1" />
              Order Remark (Optional)
            </label>
            <textarea
              value={remark}
              onChange={(e) => setRemark(e.target.value)}
              placeholder="Add special instructions or notes for this order..."
              rows={2}
              maxLength={500}
              className="w-full px-4 py-3 border border-dark-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all resize-none bg-surface-50"
            />
            <p className="mt-1 text-xs text-dark-400">{remark.length}/500 characters</p>
          </div>

          {/* Order Summary */}
          <div className="bg-surface-100 rounded-xl p-4 mb-6">
            <h3 className="font-semibold text-dark-900 mb-3">Order Summary</h3>
            <div className="space-y-2 mb-3 max-h-40 overflow-y-auto">
              {cart.map((item) => (
                <div key={item.product.id} className="flex justify-between text-sm">
                  <span className="text-dark-600">
                    {item.product.name} x {item.quantity}
                  </span>
                  <span className="font-medium text-dark-800">
                    {formatCurrency(item.product.price * item.quantity)}
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t border-dark-200 pt-3 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-dark-600">Subtotal</span>
                <span className="font-medium text-dark-800">{formatCurrency(subtotal)}</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between items-center text-accent-green">
                  <span>Discount</span>
                  <span className="font-medium">{formatDiscount(discount)}</span>
                </div>
              )}
              <div className="flex justify-between items-center pt-2 border-t border-dark-200">
                <span className="text-lg font-bold text-dark-900">Total</span>
                <span className="text-xl font-bold text-accent-green">
                  {formatCurrency(total)}
                </span>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || cart.length === 0}
            className="w-full py-4 bg-accent-green text-white font-bold rounded-xl hover:bg-accent-green/90 disabled:bg-dark-200 disabled:text-dark-400 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-xl shadow-accent-green/50"
          >
            {isSubmitting ? (
              <>
                <ButtonSpinner size="md" />
                Processing...
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                Place Order
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
