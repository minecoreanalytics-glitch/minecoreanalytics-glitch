import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Users, LayoutGrid, Shield, Database, Share2 } from 'lucide-react';
import { clearAuth, getAuth } from '../pages/Login';

const M360Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const auth = getAuth();

  return (
    <div className="min-h-screen bg-morpheus-900 text-gray-100">
      <header className="sticky top-0 z-20 border-b border-morpheus-700 bg-morpheus-900/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <div className="flex items-center gap-3 mr-4">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/15 flex items-center justify-center">
              <Users className="text-emerald-400" size={18} />
            </div>
            <div>
              <div className="font-bold leading-4">M360</div>
              <div className="text-[11px] text-gray-400">CS Management</div>
            </div>
          </div>

          {auth && (
            <nav className="flex items-center gap-2 text-sm">
              {auth.role === 'manager' ? (
                <>
                  <NavLink to="/manager" className={({ isActive }) => isActive ? 'px-3 py-2 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'px-3 py-2 rounded-lg text-gray-300 hover:bg-morpheus-800'}>
                    <span className="inline-flex items-center gap-2"><Shield size={16}/>Manager</span>
                  </NavLink>
                  <NavLink to="/manager/data-nexus" className={({ isActive }) => isActive ? 'px-3 py-2 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'px-3 py-2 rounded-lg text-gray-300 hover:bg-morpheus-800'}>
                    <span className="inline-flex items-center gap-2"><Database size={16}/>Data</span>
                  </NavLink>
                  <NavLink to="/manager/graph" className={({ isActive }) => isActive ? 'px-3 py-2 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'px-3 py-2 rounded-lg text-gray-300 hover:bg-morpheus-800'}>
                    <span className="inline-flex items-center gap-2"><Share2 size={16}/>Graph</span>
                  </NavLink>
                </>
              ) : (
                <NavLink to="/agent" className={({ isActive }) => isActive ? 'px-3 py-2 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'px-3 py-2 rounded-lg text-gray-300 hover:bg-morpheus-800'}>
                  <span className="inline-flex items-center gap-2"><LayoutGrid size={16}/>Agent</span>
                </NavLink>
              )}
            </nav>
          )}

          <div className="ml-auto flex items-center gap-3">
            {auth && (
              <div className="text-xs text-gray-400">
                Signed in as <span className="text-gray-200">{auth.displayName}</span> <span className="font-mono">({auth.role}:{auth.userId})</span>
              </div>
            )}
            {auth && (
              <button
                onClick={() => { clearAuth(); navigate('/login', { replace: true }); }}
                className="px-3 py-2 rounded-lg border border-morpheus-700 text-gray-300 hover:bg-morpheus-800 transition-colors text-sm"
              >
                Sign out
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="min-h-[calc(100vh-72px)]">
        {children}
      </main>
    </div>
  );
};

export default M360Shell;
