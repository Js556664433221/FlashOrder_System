import { useStore } from '../store';
import type { Product } from '../types';

export function ProductList() {
  const { products, isLoading, error, searchQuery, setSearchQuery, fetchProducts, addToCart } = useStore();

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
            <ProductCard key={product.id} product={product} onAdd={() => addToCart(product)} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProductCard({ product, onAdd }: { product: Product; onAdd: () => void }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm text-gray-500">{product.sku}</span>
          <h3 className="font-semibold text-lg">{product.name}</h3>
        </div>
        <span className="text-purple-600 font-bold">${product.price.toFixed(2)}</span>
      </div>
      <div className="flex justify-between items-center mt-4">
        <div>
          <span className="text-sm text-gray-500">Stock:</span>
          <span className={`ml-1 font-medium ${product.stock_balance > 0 ? 'text-green-600' : 'text-red-500'}`}>
            {product.stock_balance}
          </span>
        </div>
        <button
          onClick={onAdd}
          disabled={product.stock_balance <= 0}
          className="px-3 py-1 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
}
