import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAuth } from './Login';
import { 
  ArrowLeft, 
  Users, 
  TrendingUp, 
  Plus, 
  Trash2, 
  Search,
  Filter,
  CheckCircle2,
  XCircle
} from 'lucide-react';

interface Account {
  customer_id: string;
  name: string;
  mrr: number;
  health_score: number;
  industry: string;
  churn_probability: number;
  product_count?: number;
  last_activity?: string;
}

const PortfolioDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [portfolio, setPortfolio] = useState<any>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Account selection state
  const [showAddModal, setShowAddModal] = useState(false);
  const [availableAccounts, setAvailableAccounts] = useState<Account[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Filters for available accounts
  const [minMRR, setMinMRR] = useState<string>('');
  const [minProducts, setMinProducts] = useState<string>('');
  const [activeSince, setActiveSince] = useState<string>('');

  const API_BASE =
    (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL)
      ? String(import.meta.env.VITE_API_BASE_URL)
      : 'http://localhost:8000/api/v1';

  useEffect(() => {
    fetchPortfolioData();
  }, [id]);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      const [pRes, aRes] = await Promise.all([
        fetch(`${API_BASE}/portfolios/${id}`),
        fetch(`${API_BASE}/portfolios/${id}/accounts`)
      ]);
      
      if (pRes.ok) setPortfolio(await pRes.json());
      if (aRes.ok) setAccounts(await aRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableAccounts = async () => {
    try {
      const res = await fetch(`${API_BASE}/morpheus360/portfolio`);
      if (res.ok) {
        const data = await res.json();
        // Filter out those already in portfolio
        const existingIds = accounts.map(a => a.customer_id);
        setAvailableAccounts(data.filter((a: Account) => !existingIds.includes(a.customer_id)));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddAccount = async (accountId: string) => {
    try {
      const updatedIds = [...portfolio.account_ids, accountId];
      const res = await fetch(`${API_BASE}/portfolios/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_ids: updatedIds })
      });
      if (res.ok) {
        fetchPortfolioData();
        setShowAddModal(false);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRemoveAccount = async (accountId: string) => {
    if (!confirm('Remove this account from the portfolio?')) return;
    try {
      const updatedIds = portfolio.account_ids.filter((aid: string) => aid !== accountId);
      const res = await fetch(`${API_BASE}/portfolios/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_ids: updatedIds })
      });
      if (res.ok) {
        fetchPortfolioData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-morpheus-900">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
    </div>
  );

  const role = getAuth()?.role;

  const totalMRR = accounts.reduce((sum, a) => sum + (a.mrr || 0), 0);
  const avgHealth = accounts.length > 0 
    ? accounts.reduce((sum, a) => sum + (a.health_score || 0), 0) / accounts.length 
    : 0;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <button 
        onClick={() => navigate(getAuth()?.role === 'manager' ? '/manager' : '/agent')}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft size={18} />
        Back to Portfolios
      </button>

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-bold text-white">{portfolio?.name}</h1>
            <span className="px-3 py-1 bg-morpheus-800 border border-morpheus-700 rounded-full text-xs text-emerald-400 font-mono">
              LIVE DATA
            </span>
          </div>
          <p className="text-gray-400 max-w-2xl">{portfolio?.description || 'Strategic monitoring for selected accounts.'}</p>
          <div className="mt-2 text-xs text-gray-500">
            Assigned Agent ID: <span className="font-mono text-gray-300">{portfolio?.agent_id || '—'}</span>
          </div>
        </div>
        
        {role === 'manager' && (
          <button 
            onClick={() => {
              fetchAvailableAccounts();
              setShowAddModal(true);
            }}
            className="flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-emerald-600/20"
          >
            <Plus size={20} />
            Add Clients
          </button>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl p-6">
          <p className="text-gray-500 text-sm font-medium mb-1 uppercase tracking-wider">Total Accounts</p>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold text-white">{accounts.length}</h2>
            <Users className="text-blue-400 opacity-50" size={24} />
          </div>
        </div>
        <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl p-6">
          <p className="text-gray-500 text-sm font-medium mb-1 uppercase tracking-wider">Portfolio MRR</p>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold text-emerald-400">${totalMRR.toLocaleString()}</h2>
            <TrendingUp className="text-emerald-400 opacity-50" size={24} />
          </div>
        </div>
        <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl p-6">
          <p className="text-gray-500 text-sm font-medium mb-1 uppercase tracking-wider">Avg. Health Score</p>
          <div className="flex items-center gap-3">
            <h2 className={`text-3xl font-bold ${avgHealth > 70 ? 'text-green-400' : 'text-orange-400'}`}>
              {Math.round(avgHealth)}%
            </h2>
          </div>
        </div>
      </div>

      {/* Account Table */}
      <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-morpheus-700 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Accounts in Portfolio</h3>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input 
              type="text" 
              placeholder="Filter accounts..."
              className="bg-morpheus-900 border border-morpheus-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>
        <table className="w-full text-left">
          <thead className="bg-morpheus-900/50 text-gray-400 text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4 font-semibold">Customer</th>
              <th className="px-6 py-4 font-semibold">MRR</th>
              <th className="px-6 py-4 font-semibold">Health Score</th>
              <th className="px-6 py-4 font-semibold">Risk Status</th>
              <th className="px-6 py-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-morpheus-700">
            {accounts.map(account => (
              <tr 
                key={account.customer_id}
                className="hover:bg-morpheus-700/30 transition-colors cursor-pointer"
                onClick={() => {
                  const role = getAuth()?.role;
                  navigate(`${role === 'manager' ? '/manager' : '/agent'}/customer/360?id=${account.customer_id}`);
                }}
              >
                <td className="px-6 py-4">
                  <div className="font-semibold text-white">{account.name}</div>
                  <div className="text-xs text-gray-500">ID: {account.customer_id} • {account.industry}</div>
                </td>
                <td className="px-6 py-4 font-mono text-emerald-400">${account.mrr.toLocaleString()}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-morpheus-900 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${account.health_score > 70 ? 'bg-green-500' : account.health_score > 40 ? 'bg-orange-500' : 'bg-red-500'}`}
                        style={{ width: `${account.health_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-white">{account.health_score}%</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    account.health_score > 70 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                  }`}>
                    {account.health_score > 70 ? 'Optimal' : 'At Risk'}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  {role === 'manager' ? (
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveAccount(account.customer_id);
                      }}
                      className="text-gray-500 hover:text-red-400 p-2 transition-colors"
                      title="Remove client"
                    >
                      <Trash2 size={18} />
                    </button>
                  ) : (
                    <span className="text-xs text-gray-500">View</span>
                  )}
                </td>
              </tr>
            ))}
            {accounts.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-20 text-center text-gray-500">
                  No accounts in this portfolio. Add some to start monitoring.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add Accounts Modal */}
      {role === 'manager' && showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
            <div className="p-6 border-b border-morpheus-700 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white">Add Accounts</h2>
              <button onClick={() => setShowAddModal(false)} className="text-gray-500 hover:text-white">
                <XCircle size={24} />
              </button>
            </div>
            
            <div className="p-4 bg-morpheus-900/50 border-b border-morpheus-700 space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name or account number..."
                  className="w-full bg-morpheus-900 border border-morpheus-700 rounded-xl pl-11 pr-4 py-3 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] text-gray-400 mb-1">Min MRR</label>
                  <input
                    type="number"
                    value={minMRR}
                    onChange={(e) => setMinMRR(e.target.value)}
                    placeholder="e.g. 5000"
                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-gray-400 mb-1">Min Products</label>
                  <input
                    type="number"
                    value={minProducts}
                    onChange={(e) => setMinProducts(e.target.value)}
                    placeholder="e.g. 10"
                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-gray-400 mb-1">Active Since</label>
                  <input
                    type="date"
                    value={activeSince}
                    onChange={(e) => setActiveSince(e.target.value)}
                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => { setMinMRR(''); setMinProducts(''); setActiveSince(''); setSearchQuery(''); }}
                  className="text-xs px-3 py-2 rounded-lg border border-morpheus-700 text-gray-300 hover:bg-morpheus-800"
                >
                  Clear filters
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              <div className="grid grid-cols-1 gap-2">
                {availableAccounts
                  .filter(a => {
                    const q = searchQuery.trim().toLowerCase();
                    const matchesQuery = !q || a.name.toLowerCase().includes(q) || a.customer_id.includes(searchQuery.trim());

                    const minMrr = minMRR.trim() ? Number(minMRR) : null;
                    const minProd = minProducts.trim() ? Number(minProducts) : null;
                    const since = activeSince ? new Date(activeSince) : null;

                    const matchesMRR = minMrr === null || (a.mrr || 0) >= minMrr;
                    const matchesProducts = minProd === null || (a.product_count || 0) >= minProd;

                    const matchesDate = !since || !a.last_activity || (new Date(a.last_activity) >= since);

                    return matchesQuery && matchesMRR && matchesProducts && matchesDate;
                  })
                  .map(a => (
                    <div key={a.customer_id} className="flex items-center justify-between p-4 hover:bg-morpheus-700/50 rounded-xl transition-colors group">
                      <div>
                        <div className="font-semibold text-white">{a.name}</div>
                        <div className="text-xs text-gray-500">
                          ID: {a.customer_id}
                          {' • '}MRR: ${a.mrr.toLocaleString()}
                          {' • '}Products: {a.product_count ?? '—'}
                          {' • '}Last: {a.last_activity ? new Date(a.last_activity).toLocaleDateString() : '—'}
                          {' • '}Health: {a.health_score}%
                        </div>
                      </div>
                      <button 
                        onClick={() => handleAddAccount(a.customer_id)}
                        className="bg-emerald-600/10 text-emerald-400 border border-emerald-500/20 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-emerald-600 hover:text-white transition-all"
                      >
                        Add
                      </button>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioDetail;
