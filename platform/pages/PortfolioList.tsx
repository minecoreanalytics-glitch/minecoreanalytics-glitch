import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Folder, 
  Trash2, 
  ChevronRight, 
  Search,
  Filter,
  Users,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { resolveApiBase } from '../services/apiBase';

interface Portfolio {
  id: string;
  name: string;
  description?: string;
  account_ids: string[];
  agent_id?: string | null;
  created_at: string;
  updated_at: string;
}

const API_BASE = resolveApiBase();

const PortfolioList: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioDesc, setNewPortfolioDesc] = useState('');
  const [newPortfolioAgentId, setNewPortfolioAgentId] = useState('agent-1');
  const navigate = useNavigate();

  useEffect(() => {
    fetchPortfolios();
  }, []);

  const fetchPortfolios = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/portfolios`);
      if (response.ok) {
        const data = await response.json();
        setPortfolios(data);
      }
    } catch (err) {
      console.error('Error fetching portfolios:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newPortfolioName) return;
    try {
      const response = await fetch(`${API_BASE}/portfolios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newPortfolioName,
          description: newPortfolioDesc,
          agent_id: newPortfolioAgentId || null,
        })
      });
      if (response.ok) {
        setShowCreateModal(false);
        setNewPortfolioName('');
        setNewPortfolioDesc('');
        setNewPortfolioAgentId('agent-1');
        fetchPortfolios();
      }
    } catch (err) {
      console.error('Error creating portfolio:', err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this portfolio?')) return;
    try {
      await fetch(`${API_BASE}/portfolios/${id}`, { method: 'DELETE' });
      fetchPortfolios();
    } catch (err) {
      console.error('Error deleting portfolio:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-morpheus-900">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Customer Portfolios</h1>
          <p className="text-gray-400">Organize and monitor groups of accounts</p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg transition-all shadow-lg shadow-emerald-600/20"
        >
          <Plus size={18} />
          Create Portfolio
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {portfolios.map(p => (
          <div 
            key={p.id}
            onClick={() => navigate(`/manager/portfolio/${p.id}`)}
            className="bg-morpheus-800 border border-morpheus-700 rounded-xl p-6 hover:border-emerald-500/50 transition-all cursor-pointer group relative"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
                <Folder size={24} />
              </div>
              <button 
                onClick={(e) => handleDelete(e, p.id)}
                className="text-gray-500 hover:text-red-400 transition-colors p-1"
              >
                <Trash2 size={16} />
              </button>
            </div>
            
            <h3 className="text-xl font-semibold text-white mb-1">{p.name}</h3>
            <p className="text-gray-400 text-sm mb-4 line-clamp-2">{p.description || 'No description provided.'}</p>
            
            <div className="flex items-center gap-4 mt-auto pt-4 border-t border-morpheus-700">
              <div className="flex items-center gap-1 text-gray-400 text-xs">
                <Users size={14} />
                <span>{p.account_ids.length} Accounts</span>
              </div>
              <div className="flex items-center gap-1 text-gray-400 text-xs ml-auto group-hover:text-emerald-400 transition-colors">
                <span>View Details</span>
                <ChevronRight size={14} />
              </div>
            </div>
          </div>
        ))}

        {portfolios.length === 0 && (
          <div className="col-span-full py-20 bg-morpheus-800/50 border-2 border-dashed border-morpheus-700 rounded-xl flex flex-col items-center justify-center text-gray-500">
            <Folder size={48} className="mb-4 opacity-20" />
            <p>No portfolios created yet.</p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-emerald-400 hover:text-emerald-300 font-medium"
            >
              Create your first one
            </button>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl w-full max-w-md p-8 shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-6">Create New Portfolio</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Portfolio Name</label>
                <input 
                  type="text"
                  value={newPortfolioName}
                  onChange={(e) => setNewPortfolioName(e.target.value)}
                  placeholder="e.g. High Value - North Region"
                  className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Description (Optional)</label>
                <textarea 
                  value={newPortfolioDesc}
                  onChange={(e) => setNewPortfolioDesc(e.target.value)}
                  placeholder="Describe the purpose of this portfolio..."
                  rows={3}
                  className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Assign to Agent ID</label>
                <input
                  type="text"
                  value={newPortfolioAgentId}
                  onChange={(e) => setNewPortfolioAgentId(e.target.value)}
                  placeholder="agent-1"
                  className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                />
                <p className="text-[11px] text-gray-500 mt-1">Agent will only see portfolios assigned to this ID.</p>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-8">
              <button 
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 rounded-lg border border-morpheus-700 text-gray-400 hover:bg-morpheus-700 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleCreate}
                disabled={!newPortfolioName}
                className="flex-1 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioList;
