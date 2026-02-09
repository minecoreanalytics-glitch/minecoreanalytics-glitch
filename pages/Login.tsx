import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users } from 'lucide-react';

type Role = 'manager' | 'agent';

const STORAGE_KEY = 'm360_auth_v1';

export function getAuth(): { role: Role; userId: string; displayName: string } | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!obj?.role || !obj?.userId) return null;
    return obj;
  } catch {
    return null;
  }
}

export function setAuth(auth: { role: Role; userId: string; displayName: string }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
}

export function clearAuth() {
  localStorage.removeItem(STORAGE_KEY);
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [role, setRole] = useState<Role>('agent');
  const [userId, setUserId] = useState('agent-1');
  const [displayName, setDisplayName] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const dn = displayName.trim() || (role === 'manager' ? 'Manager' : 'Agent');
    setAuth({ role, userId: userId.trim() || (role === 'manager' ? 'manager-1' : 'agent-1'), displayName: dn });
    navigate(role === 'manager' ? '/manager' : '/agent', { replace: true });
  };

  return (
    <div className="min-h-screen bg-morpheus-900 text-gray-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-morpheus-800 border border-morpheus-700 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/15 flex items-center justify-center">
            <Users className="text-emerald-400" size={20} />
          </div>
          <div>
            <div className="text-xl font-bold">M360</div>
            <div className="text-xs text-gray-400">CS Management</div>
          </div>
        </div>

        <h1 className="text-2xl font-bold mb-2">Sign in</h1>
        <p className="text-gray-400 text-sm mb-6">Demo login (no password). Choose a role to continue.</p>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="manager">Manager</option>
              <option value="agent">Agent</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">User ID</label>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder={role === 'manager' ? 'manager-1' : 'agent-1'}
              className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
            <p className="text-[11px] text-gray-500 mt-1">Use a stable ID (e.g., agent-1) so portfolios can be assigned.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Display name</label>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder={role === 'manager' ? 'Thierry (Manager)' : 'Agent Name'}
              className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
