import { useState, useEffect } from 'react';
import { Plus, Search, Tag, Percent, Calendar, Edit2, Trash2, Copy, ToggleRight, ToggleLeft, X, Loader2, BarChart3, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { api } from '../../api';
import type { PromoStatsResponse } from '../../api';

type SortField = 'code' | 'usage_count' | 'total_discount_given' | 'created_at';
type SortDirection = 'asc' | 'desc';

interface CreatePromoFormData {
  code: string;
  discount_type: 'percentage' | 'flat';
  value: number;
  expiry_date: string;
  is_active: boolean;
}

export function MarketingPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [promos, setPromos] = useState<PromoStatsResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInactive, setShowInactive] = useState(false);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('usage_count');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const [formData, setFormData] = useState<CreatePromoFormData>({
    code: '',
    discount_type: 'percentage',
    value: 0,
    expiry_date: '',
    is_active: true,
  });

  const fetchPromos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPromoStats('admin');
      setPromos(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load promo codes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPromos();
  }, [showInactive]);

  const handleToggleActive = async (promoId: number) => {
    try {
      setTogglingId(promoId);
      const promo = promos.find(p => p.id === promoId);
      if (promo?.is_active) {
        await api.deactivatePromoCode(promoId, 'admin');
      } else {
        await api.activatePromoCode(promoId, 'admin');
      }
      await fetchPromos();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to toggle promo status');
    } finally {
      setTogglingId(null);
    }
  };

  const handleDelete = async (promoId: number) => {
    if (!confirm('Are you sure you want to delete this promo code? This action cannot be undone.')) {
      return;
    }
    try {
      setDeletingId(promoId);
      await api.deletePromoCode(promoId, 'admin');
      await fetchPromos();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete promo code');
    } finally {
      setDeletingId(null);
    }
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
    setFormError(null);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.code.trim()) {
      setFormError('Promo code is required');
      return;
    }
    if (formData.value <= 0) {
      setFormError('Discount value must be greater than 0');
      return;
    }
    if (formData.discount_type === 'percentage' && formData.value > 100) {
      setFormError('Percentage discount cannot exceed 100%');
      return;
    }

    try {
      setSubmitting(true);
      await api.createPromoCode({
        ...formData,
        expiry_date: formData.expiry_date || undefined,
      }, 'admin');
      setShowCreateModal(false);
      setFormData({
        code: '',
        discount_type: 'percentage',
        value: 0,
        expiry_date: '',
        is_active: true,
      });
      await fetchPromos();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create promo code');
    } finally {
      setSubmitting(false);
    }
  };

  const closeCreateModal = () => {
    setShowCreateModal(false);
    setFormData({
      code: '',
      discount_type: 'percentage',
      value: 0,
      expiry_date: '',
      is_active: true,
    });
    setFormError(null);
  };

  const getDiscountDisplay = (promo: PromoStatsResponse) => {
    if (promo.discount_type === 'percentage') {
      return `${promo.value}% OFF`;
    }
    return `₱${promo.value} OFF`;
  };

  const isExpired = (expiryDate: string | null) => {
    if (!expiryDate) return false;
    return new Date(expiryDate) < new Date();
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3.5 h-3.5 text-gray-400" />;
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="w-3.5 h-3.5 text-purple-600" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-purple-600" />
    );
  };

  const filteredPromos = promos
    .filter((promo) =>
      promo.code.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      let aVal: string | number | Date;
      let bVal: string | number | Date;

      switch (sortField) {
        case 'usage_count':
          aVal = a.usage_count;
          bVal = b.usage_count;
          break;
        case 'total_discount_given':
          aVal = a.total_discount_given;
          bVal = b.total_discount_given;
          break;
        case 'created_at':
          aVal = new Date(a.created_at);
          bVal = new Date(b.created_at);
          break;
        case 'code':
        default:
          aVal = a.code.toLowerCase();
          bVal = b.code.toLowerCase();
          break;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

  return (
    <div className="space-y-6">
      {/* Create Promo Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
            <div className="bg-purple-50 px-6 py-4 border-b border-purple-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Tag className="w-5 h-5 text-purple-600" />
                  </div>
                  <h3 className="text-lg font-bold text-purple-800">Create New Promo</h3>
                </div>
                <button onClick={closeCreateModal} className="p-1 hover:bg-purple-100 rounded-lg transition-colors">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
            <form onSubmit={handleFormSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Promo Code</label>
                <input
                  type="text"
                  name="code"
                  value={formData.code}
                  onChange={handleFormChange}
                  placeholder="e.g., SUMMER20"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none uppercase"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Discount Type</label>
                <select
                  name="discount_type"
                  value={formData.discount_type}
                  onChange={handleFormChange}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                >
                  <option value="percentage">Percentage (%)</option>
                  <option value="flat">Flat Amount (PHP)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Discount Value
                  {formData.discount_type === 'percentage' && <span className="text-gray-400 ml-1">(max 100%)</span>}
                  {formData.discount_type === 'flat' && <span className="text-gray-400 ml-1">(PHP)</span>}
                </label>
                <input
                  type="number"
                  name="value"
                  value={formData.value || ''}
                  onChange={handleFormChange}
                  placeholder={formData.discount_type === 'percentage' ? '10' : '50'}
                  min="0"
                  max={formData.discount_type === 'percentage' ? '100' : undefined}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date (Optional)</label>
                <input
                  type="date"
                  name="expiry_date"
                  value={formData.expiry_date}
                  onChange={handleFormChange}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                />
                <p className="text-xs text-gray-400 mt-1">Leave empty for no expiration</p>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  name="is_active"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={handleFormChange}
                  className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                  Active immediately after creation
                </label>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={closeCreateModal}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  Create Promo
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Marketing / Promo Codes</h2>
          <p className="text-sm text-gray-500">Create and manage promotional discounts</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            />
            Show Inactive
          </label>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="font-medium">Create Promo</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Tag className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-700">{promos.length}</div>
              <div className="text-sm text-blue-600">Total Codes</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <ToggleRight className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-green-700">{promos.filter(p => p.is_active).length}</div>
              <div className="text-sm text-green-600">Active</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-xl border border-purple-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Percent className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-700">
                {promos.filter(p => p.discount_type === 'percentage').length}
              </div>
              <div className="text-sm text-purple-600">Percentage</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl border border-yellow-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Tag className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-700">
                {promos.filter(p => p.discount_type === 'flat').length}
              </div>
              <div className="text-sm text-yellow-600">Flat Amount</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-xl border border-teal-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-100 rounded-lg">
              <BarChart3 className="w-5 h-5 text-teal-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-teal-700">
                {promos.reduce((sum, p) => sum + p.usage_count, 0)}
              </div>
              <div className="text-sm text-teal-600">Total Uses</div>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search promo codes..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
          />
        </div>
      </div>

      {/* Promo Codes Grid */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <p className="text-red-500">{error}</p>
            <button
              onClick={fetchPromos}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : filteredPromos.length === 0 ? (
          <div className="p-12 text-center">
            <Tag className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No promo codes found</p>
            <p className="text-sm text-gray-400 mt-1">Create your first promo code to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-sm font-semibold text-gray-600">
                    <button
                      onClick={() => handleSort('code')}
                      className="flex items-center gap-1 hover:text-purple-600 transition-colors"
                    >
                      Code {getSortIcon('code')}
                    </button>
                  </th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Discount</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Expiry</th>
                  <th className="px-4 py-3 text-sm font-semibold text-gray-600">
                    <button
                      onClick={() => handleSort('usage_count')}
                      className="mx-auto flex items-center justify-center gap-1 hover:text-purple-600 transition-colors"
                    >
                      Uses {getSortIcon('usage_count')}
                    </button>
                  </th>
                  <th className="px-4 py-3 text-sm font-semibold text-gray-600">
                    <button
                      onClick={() => handleSort('total_discount_given')}
                      className="mx-auto flex items-center justify-center gap-1 hover:text-purple-600 transition-colors"
                    >
                      Revenue Impact {getSortIcon('total_discount_given')}
                    </button>
                  </th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Status</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredPromos.map((promo) => (
                  <tr key={promo.id} className={`hover:bg-gray-50 ${!promo.is_active ? 'opacity-60' : ''}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className={`p-1.5 rounded-lg ${promo.discount_type === 'percentage' ? 'bg-purple-100' : 'bg-blue-100'}`}>
                          {promo.discount_type === 'percentage' ? (
                            <Percent className={`w-4 h-4 ${promo.is_active ? 'text-purple-600' : 'text-gray-400'}`} />
                          ) : (
                            <Tag className={`w-4 h-4 ${promo.is_active ? 'text-blue-600' : 'text-gray-400'}`} />
                          )}
                        </div>
                        <span className="font-mono font-bold text-gray-800">{promo.code}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(promo.code)}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                          title="Copy code"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`font-bold text-lg ${
                        promo.discount_type === 'percentage' ? 'text-purple-600' : 'text-blue-600'
                      }`}>
                        {getDiscountDisplay(promo)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1 text-sm">
                        <Calendar className={`w-4 h-4 ${isExpired(promo.expiry_date) ? 'text-red-500' : 'text-gray-400'}`} />
                        {promo.expiry_date ? (
                          <span className={isExpired(promo.expiry_date) ? 'text-red-600 font-medium' : 'text-gray-600'}>
                            {new Date(promo.expiry_date).toLocaleDateString()}
                            {isExpired(promo.expiry_date) && ' (Expired)'}
                          </span>
                        ) : (
                          <span className="text-gray-400">No expiration</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <BarChart3 className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-700">{promo.usage_count}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-medium text-green-600">
                        {promo.total_discount_given > 0 ? `-₱${promo.total_discount_given.toFixed(2)}` : '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                        promo.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}>
                        {promo.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleToggleActive(promo.id)}
                          disabled={togglingId === promo.id}
                          className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${
                            promo.is_active
                              ? 'text-red-500 hover:bg-red-50'
                              : 'text-green-500 hover:bg-green-50'
                          }`}
                          title={promo.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {togglingId === promo.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : promo.is_active ? (
                            <ToggleLeft className="w-4 h-4" />
                          ) : (
                            <ToggleRight className="w-4 h-4" />
                          )}
                        </button>
                        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors" title="Edit">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(promo.id)}
                          disabled={deletingId === promo.id}
                          className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                          title="Delete"
                        >
                          {deletingId === promo.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}