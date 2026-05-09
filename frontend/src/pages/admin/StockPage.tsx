import { Package, Plus, Search, AlertTriangle, CheckCircle } from 'lucide-react';

export function StockPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Stock Management</h2>
          <p className="text-sm text-gray-500">Manage product inventory and stock levels</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
          <Plus className="w-4 h-4" />
          <span className="font-medium">Add Product</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by SKU or product name..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
            />
          </div>
          <div className="flex gap-2">
            <select className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none">
              <option value="all">All Status</option>
              <option value="in-stock">In Stock</option>
              <option value="low-stock">Low Stock</option>
              <option value="out-of-stock">Out of Stock</option>
            </select>
          </div>
        </div>
      </div>

      {/* Product Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">SKU</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Product</th>
                <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">Price</th>
                <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">Physical</th>
                <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">Available</th>
                <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Status</th>
                <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {/* Empty state example row */}
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center">
                  <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 font-medium">No products found</p>
                  <p className="text-sm text-gray-400 mt-1">Add your first product to get started</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-green-700">0</div>
              <div className="text-sm text-green-600">Products In Stock</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl border border-yellow-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-700">0</div>
              <div className="text-sm text-yellow-600">Low Stock Items</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl border border-red-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Package className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-red-700">0</div>
              <div className="text-sm text-red-600">Out of Stock</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
