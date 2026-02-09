import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Folder, ChevronRight, Activity, Users } from 'lucide-react';
import { getAuth, clearAuth } from './Login';

interface Portfolio {
  id: string;
  name: string;
  description?: string;
  account_ids: string[];
  agent_id?: string | null;
  created_at: string;
  updated_at: string;
}

const AgentHome: React.FC = () => {
  const navigate = useNavigate();
  const auth = getAuth();

  const API_BASE =
    (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL)
      ? String(import.meta.env.VITE_API_BASE_URL)
      : 'http://localhost:8000/api/v1';

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);

  const assigned = useMemo(() => {
    if (!auth) return [];
    return portfolios.filter(p => (p.agent_id || '') === auth.userId);
  }, [portfolios, auth]);

  useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/portfolios`);
        if (res.ok) {
          const data = await res.json();
          setPortfolios(data);
        }
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  if (!auth) return null;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Agent Dashboard</h1>
          <p className="text-gray-400">Welcome, {auth.displayName}. Here are your assigned portfolios.</p>
        </div>
        <button
          onClick={() => { clearAuth(); navigate('/login', { replace: true }); }}
          className="px-4 py-2 rounded-lg border border-morpheus-700 text-gray-300 hover:bg-morpheus-800 transition-colors"
        >
          Sign out
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
        </div>
      ) : (
        <>
          {assigned.length === 0 ? (
            <div className="py-16 bg-morpheus-800/40 border border-morpheus-700 rounded-2xl text-center text-gray-400">
              <Users className="mx-auto mb-4 opacity-40" size={42} />
              <div className="text-lg font-semibold text-white">No portfolios assigned</div>
              <div className="text-sm">Ask your manager to create a portfolio and assign it to Agent ID: <span className="font-mono text-emerald-300">{auth.userId}</span></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {assigned.map(p => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/agent/portfolio/${p.id}`)}
                  className="bg-morpheus-800 border border-morpheus-700 rounded-xl p-6 hover:border-emerald-500/50 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
                      <Folder size={22} />
                    </div>
                    <div className="text-gray-400 text-xs flex items-center gap-1">
                      <Activity size={14} />
                      <span>{p.account_ids?.length || 0} clients</span>
                    </div>
                  </div>

                  <h3 className="text-xl font-semibold text-white mb-1">{p.name}</h3>
                  <p className="text-gray-400 text-sm line-clamp-2">{p.description || 'No description.'}</p>

                  <div className="flex items-center gap-1 text-gray-400 text-xs mt-5 group-hover:text-emerald-400 transition-colors">
                    <span>Open Portfolio</span>
                    <ChevronRight size={14} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AgentHome;
