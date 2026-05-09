import { useState } from 'react';
import { NavLink, useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useStore } from '../store';
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Tag,
  Menu,
  X,
  LogOut,
  User,
  ShieldAlert,
} from 'lucide-react';

interface AdminLayoutProps {
  onBackToShop?: () => void;
}

export function AdminLayout({ onBackToShop }: AdminLayoutProps) {
  const { user, setRole, role } = useStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    setRole('salesman');
    if (onBackToShop) {
      onBackToShop();
    } else {
      navigate('/');
    }
  };

  const handleBackToShop = () => {
    setRole('salesman');
    if (onBackToShop) {
      onBackToShop();
    } else {
      navigate('/');
    }
  };

  // Navigation items with admin-only flag
  const navItems = [
    { path: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, adminOnly: false },
    { path: 'stock', label: 'Stock Management', icon: Package, adminOnly: true },
    { path: 'orders', label: 'Order Review', icon: ShoppingCart, adminOnly: true },
    { path: 'users', label: 'User Management', icon: Users, adminOnly: true },
    { path: 'marketing', label: 'Marketing / Promo', icon: Tag, adminOnly: true },
  ];

  // Filter nav items based on role (for future flexibility)
  const visibleNavItems = navItems.filter(item => !item.adminOnly || role === 'admin');

  const getPageTitle = () => {
    const currentPath = location.pathname;
    const currentItem = navItems.find((item) =>
      currentPath.endsWith(`/${item.path}`) || currentPath === item.path
    );
    return currentItem?.label || 'Dashboard';
  };

  // Check if a nav item path matches the current URL
  const isPathActive = (itemPath: string) => {
    // Match both /admin/stock and /stock style paths
    const currentPath = location.pathname;
    return currentPath.endsWith(`/${itemPath}`) || currentPath === itemPath;
  };

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">F</span>
          </div>
          <div>
            <h1 className="text-white font-bold text-lg">FlashOrder</h1>
            <p className="text-dark-400 text-xs">Admin Portal</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-2">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={
                    isPathActive(item.path)
                      ? 'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all bg-primary-600 text-white'
                      : 'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-dark-300 hover:bg-dark-700 hover:text-white'
                  }
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="font-medium">{item.label}</span>
                  {item.adminOnly && (
                    <span className="ml-auto text-xs px-1.5 py-0.5 bg-primary-800/50 text-primary-300 rounded">
                      Admin
                    </span>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Back to Shop */}
      <div className="p-4 border-t border-dark-700">
        <button
          onClick={handleBackToShop}
          className="w-full flex items-center gap-3 px-4 py-3 text-dark-300 hover:bg-dark-700 hover:text-white rounded-lg transition-all"
        >
          <LayoutDashboard className="w-5 h-5" />
          <span className="font-medium">Back to Shop</span>
        </button>
      </div>
    </>
  );

  return (
    <div className="flex h-screen bg-surface-100">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Fixed on desktop, slide-out on mobile */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 bg-dark-900
          transform transition-transform duration-300 ease-in-out
          lg:transform-none
          flex flex-col
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Mobile close button */}
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden absolute top-4 right-4 p-2 text-dark-400 hover:text-white"
        >
          <X className="w-6 h-6" />
        </button>

        <SidebarContent />
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-screen lg:ml-0">
        {/* Glassmorphic Top Navigation Bar */}
        <header className="sticky top-0 z-30 bg-surface-50/80 backdrop-blur-md shadow-sm border-b border-primary-500/20">
          <div className="flex items-center justify-between px-4 py-3">
            {/* Mobile menu button with glass effect */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-dark-600 hover:bg-white/60 backdrop-blur-sm rounded-lg transition-colors border border-transparent hover:border-dark-200"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Page title */}
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-dark-800">{getPageTitle()}</h2>
            </div>

            {/* User info & actions */}
            <div className="flex items-center gap-3">
              {/* User badge with glass effect */}
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-white/60 backdrop-blur-sm rounded-full border border-white/50">
                <User className="w-4 h-4 text-dark-600" />
                <span className="text-sm font-medium text-dark-700">{user.username}</span>
                <span className="text-xs px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full capitalize border border-primary-200/50">
                  {user.role}
                </span>
              </div>

              {/* Logout button with glass effect */}
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 bg-white/60 backdrop-blur-sm text-dark-600 hover:bg-white/80 rounded-xl transition-all border border-white/50"
                title="Exit Admin Panel"
              >
                <LogOut className="w-5 h-5" />
                <span className="hidden sm:inline text-sm font-medium">Exit Admin</span>
              </button>
            </div>
          </div>
        </header>

        {/* Scrollable Content Area - White background */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 bg-white">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// Access Denied component for unauthorized access attempts
export function AccessDenied() {
  const { setRole } = useStore();

  const handleGoBack = () => {
    setRole('salesman');
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-4">
      <div className="bg-surface-50 rounded-xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="w-16 h-16 bg-accent-red/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-8 h-8 text-accent-red" />
        </div>
        <h1 className="text-2xl font-bold text-dark-800 mb-2">Access Denied</h1>
        <p className="text-dark-600 mb-6">
          You do not have permission to access this page.
          Only administrators can view this section.
        </p>
        <button
          onClick={handleGoBack}
          className="w-full py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors"
        >
          Return to Shop
        </button>
      </div>
    </div>
  );
}

// Protected Route wrapper that checks admin status
export function ProtectedAdminRoute({ children }: { children: React.ReactNode }) {
  const { role } = useStore();

  if (role !== 'admin') {
    return <AccessDenied />;
  }

  return <>{children}</>;
}
