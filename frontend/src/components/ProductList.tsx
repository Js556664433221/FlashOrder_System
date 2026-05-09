import { useState } from 'react';
import { useStore } from '../store';
import type { Product } from '../types';
import { formatCurrency } from '../utils';
import { Search, Package, ShoppingBag, Check } from 'lucide-react';
import { LoadingSpinner, FadeInContent } from './LoadingSpinner';

export function ProductList() {
  const { products, isLoading, error, searchQuery, setSearchQuery, fetchProducts } = useStore();
  const [addedItems, setAddedItems] = useState<number[]>([]);

  return (
    <div className="p-6">
      {/* Hero Search Bar */}
      <div className="mb-8">
        <div className="relative max-w-2xl mx-auto">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-6 h-6 text-dark-400" />
          <input
            type="text"
            placeholder="Search products by name or SKU..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchProducts()}
            className="w-full pl-14 pr-32 py-4 text-lg border-2 border-dark-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-surface-50 shadow-sm transition-all"
          />
          <button
            onClick={() => fetchProducts()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition-colors shadow-md"
          >
            Search
          </button>
        </div>
      </div>

      {/* Results count */}
      {!isLoading && products.length > 0 && (
        <div className="mb-4 text-dark-500">
          Showing <span className="font-semibold text-dark-700">{products.length}</span> products
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-accent-red/10 border border-accent-red/30 rounded-xl text-accent-red text-center">
          {error}
        </div>
      )}

      {isLoading ? (
        <FadeInContent
          isLoading={true}
          minHeight="min-h-[400px]"
          loadingComponent={
            <>
              <LoadingSpinner size="lg" className="animate-pulse" />
              <p className="text-primary-600 text-lg mt-4 font-medium">Loading products...</p>
            </>
          }
        />
      ) : products.length === 0 ? (
        <div className="text-center py-20 bg-surface-100 rounded-2xl border border-dark-200">
          <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Package className="w-12 h-12 text-primary-400" />
          </div>
          <h3 className="text-xl font-semibold text-dark-700 mb-2">No Products Found</h3>
          <p className="text-dark-500">Try adjusting your search or check back later</p>
        </div>
      ) : (
        <FadeInContent isLoading={false} minHeight="min-h-[200px]">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                justAdded={addedItems.includes(product.id)}
                onAdd={() => {
                  setAddedItems(prev => [...prev, product.id]);
                  setTimeout(() => {
                    setAddedItems(prev => prev.filter(id => id !== product.id));
                  }, 1500);
                }}
              />
            ))}
          </div>
        </FadeInContent>
      )}
    </div>
  );
}

function ProductCard({
  product,
  justAdded,
  onAdd
}: {
  product: Product;
  justAdded: boolean;
  onAdd: () => void;
}) {
  const { addToCart, fetchProducts } = useStore();
  const [quantity, setQuantity] = useState(1);

  const availableStock = product.available_stock ?? (product.physical_stock - product.reserved_stock);
  const maxQuantity = Math.max(1, availableStock);
  const isOutOfStock = availableStock <= 0;
  const isLowStock = availableStock > 0 && availableStock <= 5;

  const handleAdd = async () => {
    if (quantity > 0 && quantity <= maxQuantity) {
      for (let i = 0; i < quantity; i++) {
        addToCart(product);
      }
      onAdd();
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
    <div className={`group bg-surface-50 rounded-2xl overflow-hidden border-2 border-transparent hover:border-primary-500 hover:shadow-lg hover:scale-[1.02] transition-all duration-300 ease-in-out ${isOutOfStock ? 'opacity-75' : ''}`}>
      {/* Product Image */}
      <div className="relative aspect-square bg-dark-100 overflow-hidden">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-dark-100 to-dark-200">
            <Package className="w-16 h-16 text-dark-300" />
          </div>
        )}

        {/* Stock Badge Overlay */}
        <div className="absolute top-3 right-3">
          {isOutOfStock ? (
            <span className="px-3 py-1.5 bg-dark-800/90 text-white text-xs font-semibold rounded-full backdrop-blur-sm">
              Out of Stock
            </span>
          ) : isLowStock ? (
            <span className="px-3 py-1.5 bg-accent-amber-500/90 text-dark-900 text-xs font-semibold rounded-full backdrop-blur-sm">
              Low Stock
            </span>
          ) : null}
        </div>

        {/* Quick Add Animation */}
        {justAdded && (
          <div className="absolute inset-0 bg-accent-green/20 flex items-center justify-center animate-pulse">
            <div className="w-16 h-16 bg-accent-green rounded-full flex items-center justify-center shadow-lg">
              <Check className="w-8 h-8 text-white" />
            </div>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="p-5">
        {/* SKU */}
        <div className="text-xs text-dark-400 font-mono mb-2">{product.sku}</div>

        {/* Product Name */}
        <h3 className="font-bold text-lg text-dark-900 mb-3 line-clamp-2 min-h-[3.5rem]">
          {product.name}
        </h3>

        {/* Price */}
        <div className="text-2xl font-extrabold text-primary-600 mb-4">
          {formatCurrency(product.price)}
        </div>

        {/* Description */}
        <p className="text-sm text-dark-500 mb-4 line-clamp-2 min-h-[2.5rem]">
          {product.description || 'Premium quality product'}
        </p>

        {/* Stock Info */}
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-dark-100">
          <div className="flex items-center gap-2">
            <span className="text-sm text-dark-500">Stock:</span>
            <span className={`font-bold text-lg ${
              isOutOfStock ? 'text-accent-red' : isLowStock ? 'text-accent-amber' : 'text-accent-green'
            }`}>
              {availableStock}
            </span>
          </div>
          {availableStock > 0 && availableStock <= 10 && (
            <span className="text-xs text-dark-400">
              {availableStock <= 3 ? 'Very low!' : 'Selling fast'}
            </span>
          )}
        </div>

        {/* Add to Cart Section */}
        <div className="flex items-center gap-3">
          <div className="flex items-center border-2 border-dark-200 rounded-xl overflow-hidden focus-within:border-primary-500">
            <button
              onClick={() => setQuantity(q => Math.max(1, q - 1))}
              className="w-10 h-10 flex items-center justify-center text-dark-500 hover:bg-dark-100 transition-colors"
            >
              -
            </button>
            <input
              type="number"
              min={1}
              max={maxQuantity}
              value={quantity}
              onChange={handleQuantityChange}
              className="w-12 h-10 text-center font-semibold text-dark-800 bg-transparent focus:outline-none"
            />
            <button
              onClick={() => setQuantity(q => Math.min(maxQuantity, q + 1))}
              className="w-10 h-10 flex items-center justify-center text-dark-500 hover:bg-dark-100 transition-colors"
            >
              +
            </button>
          </div>

          <button
            onClick={handleAdd}
            disabled={isOutOfStock}
            className={`flex-1 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all ${
              isOutOfStock
                ? 'bg-dark-200 text-dark-400 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-500/30 hover:shadow-primary-500/50'
            }`}
          >
            {isOutOfStock ? (
              'Out of Stock'
            ) : (
              <>
                <ShoppingBag className="w-5 h-5" />
                Add to Cart
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
