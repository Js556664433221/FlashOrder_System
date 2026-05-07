import { useStore } from '../store';

interface AdminNavBarProps {
  onBackToShop: () => void;
}

export function AdminNavBar({ onBackToShop }: AdminNavBarProps) {
  const { user } = useStore();

  return (
    <div className="bg-gray-800 text-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-bold">Admin Panel / 管理中心</h2>
        <span className="text-xs bg-gray-700 px-2 py-1 rounded">Admin: {user?.username}</span>
      </div>
      <button
        onClick={onBackToShop}
        className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm font-medium transition-colors"
      >
        ← Return to Shop
      </button>
    </div>
  );
}