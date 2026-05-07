import { useState } from 'react';
import { useStore } from '../store';
import type { Product } from '../types';

export function ProductList() {
  const { products, isLoading, error, searchQuery, setSearchQuery, fetchProducts } = useStore();

  return (
    <div className="p-4">
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Search by SKU or name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <button
          onClick={() => fetchProducts()}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Search
        </button>
      </div>

      {error && <div className="text-red-500 mb-4">{error}</div>}
      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProductCard({ product }: { product: Product }) {
  const { addToCart, fetchProducts } = useStore();
  const [quantity, setQuantity] = useState(1);

  const availableStock = product.available_stock ?? (product.physical_stock - product.reserved_stock);
  const maxQuantity = Math.max(1, availableStock);

  const handleAdd = async () => {
    if (quantity > 0 && quantity <= maxQuantity) {
      for (let i = 0; i < quantity; i++) {
        addToCart(product);
      }
      setQuantity(1);
      fetchProducts();
    }
  };

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value) || 1;
    const clamped = Math.max(1, Math.min(val, maxQuantity));
    setQuantity(clamped);
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
      {product.image_url ? (
        <div className="h-40 bg-gray-100 overflow-hidden">
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover"
          />
        </div>
      ) : (
        <div className="h-40 bg-gray-100 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <svg className="w-12 h-12 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-xs">No image</span>
          </div>
        </div>
      )}
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <div>
            <span className="text-sm text-gray-500">{product.sku}</span>
            <h3 className="font-semibold text-lg">{product.name}</h3>
          </div>
          <span className="text-purple-600 font-bold">${product.price.toFixed(2)}</span>
        </div>
        <p className="text-sm text-gray-500 mb-3">{product.description || 'No description'}</p>
        <div className="flex justify-between items-center mt-4">
          <div>
            <span className="text-sm text-gray-500">Stock:</span>
            <span className={`ml-1 font-medium ${availableStock > 0 ? 'text-green-600' : 'text-red-500'}`}>
              {availableStock}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              max={maxQuantity}
              value={quantity}
              onChange={handleQuantityChange}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-center"
            />
            <button
              onClick={handleAdd}
              disabled={availableStock <= 0}
              className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Add
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
