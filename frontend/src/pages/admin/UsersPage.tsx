import { useState, useEffect } from 'react';
import { Search, Edit2, UserCheck, UserX, Shield, ShoppingBag, Loader2, Crown, X } from 'lucide-react';
import { api } from '../../api';
import type { UserResponse } from '../../api';
import { useStore } from '../../store';

interface CreateAdminFormData {
  username: string;
  email: string;
  password: string;
}

export function UsersPage() {
  const { user } = useStore();
  const isSuperAdmin = (user as any).is_superadmin === 1;

  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [promotingId, setPromotingId] = useState<number | null>(null);

  // Modal states
  const [showPromoteModal, setShowPromoteModal] = useState(false);
  const [showCreateAdminModal, setShowCreateAdminModal] = useState(false);
  const [promoteTargetUser, setPromoteTargetUser] = useState<UserResponse | null>(null);
  const [createAdminForm, setCreateAdminForm] = useState<CreateAdminFormData>({
    username: '',
    email: '',
    password: ''
  });
  const [createAdminError, setCreateAdminError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getUsers('admin');
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (userId: number) => {
    try {
      setTogglingId(userId);
      await api.toggleUserStatus(userId, 'admin');
      await fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to toggle user status');
    } finally {
      setTogglingId(null);
    }
  };

  const handlePromoteClick = (user: UserResponse) => {
    setPromoteTargetUser(user);
    setShowPromoteModal(true);
  };

  const handlePromoteConfirm = async () => {
    if (!promoteTargetUser) return;

    try {
      setPromotingId(promoteTargetUser.id);
      setShowPromoteModal(false);
      await api.promoteUser(promoteTargetUser.id, 'admin');
      await fetchUsers();
      setPromoteTargetUser(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to promote user');
    } finally {
      setPromotingId(null);
    }
  };

  const handleCreateAdminChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCreateAdminForm(prev => ({ ...prev, [name]: value }));
    setCreateAdminError(null);
  };

  const handleCreateAdminSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateAdminError(null);

    if (!createAdminForm.username.trim()) {
      setCreateAdminError('Username is required');
      return;
    }
    if (!createAdminForm.email.trim() || !createAdminForm.email.includes('@')) {
      setCreateAdminError('Valid email is required');
      return;
    }
    if (createAdminForm.password.length < 6) {
      setCreateAdminError('Password must be at least 6 characters');
      return;
    }

    try {
      setSubmitting(true);
      await api.createAdmin(createAdminForm, 'admin');
      setShowCreateAdminModal(false);
      setCreateAdminForm({ username: '', email: '', password: '' });
      await fetchUsers();
    } catch (err) {
      setCreateAdminError(err instanceof Error ? err.message : 'Failed to create admin');
    } finally {
      setSubmitting(false);
    }
  };

  const closePromoteModal = () => {
    setShowPromoteModal(false);
    setPromoteTargetUser(null);
  };

  const closeCreateAdminModal = () => {
    setShowCreateAdminModal(false);
    setCreateAdminForm({ username: '', email: '', password: '' });
    setCreateAdminError(null);
  };

  const filteredUsers = users.filter((user) =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Promotion Confirmation Modal */}
      {showPromoteModal && promoteTargetUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
            <div className="bg-amber-50 px-6 py-4 border-b border-amber-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <Crown className="w-5 h-5 text-amber-600" />
                </div>
                <h3 className="text-lg font-bold text-amber-800">Confirm Promotion</h3>
              </div>
            </div>
            <div className="p-6">
              <p className="text-gray-700 mb-4">
                This action will grant <strong>{promoteTargetUser.username}</strong> full administrative access.
              </p>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                <p className="text-amber-800 text-sm">
                  The user will be able to access all admin features including product management,
                  order processing, and user management.
                </p>
              </div>
              <p className="text-gray-600 mb-6">Proceed?</p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={closePromoteModal}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handlePromoteConfirm}
                  disabled={promotingId === promoteTargetUser.id}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {promotingId === promoteTargetUser.id && <Loader2 className="w-4 h-4 animate-spin" />}
                  Promote to Admin
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Admin Modal */}
      {showCreateAdminModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
            <div className="bg-purple-50 px-6 py-4 border-b border-purple-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Crown className="w-5 h-5 text-purple-600" />
                  </div>
                  <h3 className="text-lg font-bold text-purple-800">Create Admin Account</h3>
                </div>
                <button onClick={closeCreateAdminModal} className="p-1 hover:bg-purple-100 rounded-lg transition-colors">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
            <form onSubmit={handleCreateAdminSubmit} className="p-6 space-y-4">
              {createAdminError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {createAdminError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  name="username"
                  value={createAdminForm.username}
                  onChange={handleCreateAdminChange}
                  placeholder="Enter username"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={createAdminForm.email}
                  onChange={handleCreateAdminChange}
                  placeholder="Enter email address"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  name="password"
                  value={createAdminForm.password}
                  onChange={handleCreateAdminChange}
                  placeholder="Enter password (min 6 characters)"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                />
              </div>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-purple-800 text-sm">
                  This user will be created with Admin role and full administrative access.
                </p>
              </div>
              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={closeCreateAdminModal}
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
                  Create Admin
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">User Management</h2>
          <p className="text-sm text-gray-500">Manage user accounts and roles</p>
        </div>
        {isSuperAdmin && (
          <button
            onClick={() => setShowCreateAdminModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors"
          >
            <Crown className="w-4 h-4" />
            <span className="font-medium">Create Admin</span>
          </button>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ShoppingBag className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-700">{users.filter(u => u.role === 'salesman').length}</div>
              <div className="text-sm text-blue-600">Salesmen</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-xl border border-purple-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Shield className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-700">{users.filter(u => u.role === 'admin').length}</div>
              <div className="text-sm text-purple-600">Admins</div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl border border-red-200 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <UserX className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-red-700">{users.filter(u => u.status === 'Suspended').length}</div>
              <div className="text-sm text-red-600">Suspended</div>
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
            placeholder="Search by username or email..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
          />
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <p className="text-red-500">{error}</p>
              <button
                onClick={fetchUsers}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Username</th>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Email</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Role</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Status</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${user.role === 'admin' ? 'bg-purple-100' : 'bg-blue-100'}`}>
                          <span className={`text-sm font-medium ${user.role === 'admin' ? 'text-purple-600' : 'text-blue-600'}`}>
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="font-medium text-gray-800">{user.username}</span>
                        {user.is_superadmin === 1 && (
                          <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 text-xs font-medium rounded">
                            Super
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{user.email}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                        user.role === 'admin'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {user.role === 'admin' ? <Shield className="w-3 h-3" /> : <ShoppingBag className="w-3 h-3" />}
                        {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                        user.status === 'Active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {user.status === 'Active' ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                        {user.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors" title="Edit">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        {/* Promote to Admin button - only visible to Initial Admin */}
                        {isSuperAdmin && user.role === 'salesman' && (
                          <button
                            onClick={() => handlePromoteClick(user)}
                            disabled={promotingId === user.id}
                            className="p-2 text-amber-500 hover:bg-amber-50 rounded-lg transition-colors disabled:opacity-50"
                            title="Promote to Admin"
                          >
                            {promotingId === user.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Crown className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        <button
                          onClick={() => handleToggleStatus(user.id)}
                          disabled={togglingId === user.id || user.is_superadmin === 1}
                          className={`p-2 rounded-lg transition-colors disabled:opacity-30 ${
                            user.status === 'Active'
                              ? 'text-red-500 hover:bg-red-50'
                              : 'text-green-500 hover:bg-green-50'
                          }`}
                          title={user.is_superadmin === 1 ? 'Cannot suspend Super Admin' : user.status === 'Active' ? 'Suspend' : 'Activate'}
                        >
                          {togglingId === user.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : user.status === 'Active' ? (
                            <UserX className="w-4 h-4" />
                          ) : (
                            <UserCheck className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}