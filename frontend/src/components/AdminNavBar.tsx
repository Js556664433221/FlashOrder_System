import { useStore } from '../store';

interface AdminNavBarProps {
  onBackToShop: () => void;
}

export function AdminNavBar({ onBackToShop }: AdminNavBarProps) {
  const { user, role, setRole } = useStore();
  const isAdmin = role === 'admin';

  const handleSwitchRole = () => {
    setRole(isAdmin ? 'staff' : 'admin');
    if (!isAdmin) {
      // Switching to admin - scroll to admin section
      document.getElementById('admin-section')?.scrollIntoView({ behavior: 'smooth' });
    } else {
      // Switching to staff - scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-gray-800 text-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-bold">Admin Panel</h2>
        <span className="text-xs bg-gray-700 px-2 py-1 rounded">Admin: {user.username}</span>
      </div>
      <div className="flex gap-3">
        <button
          onClick={handleSwitchRole}
          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm font-medium transition-colors"
        >
          Switch to Staff
        </button>
        <button
          onClick={onBackToShop}
          className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm font-medium transition-colors"
        >
          Return to Shop
        </button>
      </div>
    </div>
  );
}
