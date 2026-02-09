import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface CustomerSummary {
  customer_id: string;
  name: string;
  status: string;
  mrr: number;
  lifetime_value: number;
  health_score: number;
  churn_probability: number;
  industry: string;
  last_activity?: string;
}

const AgentPortfolio: React.FC = () => {
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'health' | 'mrr' | 'name'>('health');
  const [filterStatus, setFilterStatus] = useState<'all' | 'healthy' | 'at-risk' | 'critical'>('all');
  const navigate = useNavigate();

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      // Fetch top customers with their health metrics
      const response = await fetch('http://localhost:8000/api/v1/morpheus360/portfolio');
      
      if (!response.ok) {
        throw new Error('Failed to fetch portfolio');
      }
      
      const data = await response.json();
      setCustomers(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching portfolio:', err);
      setError('Failed to load portfolio. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (score: number): string => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    if (score >= 40) return 'text-orange-500';
    return 'text-red-500';
  };

  const getHealthBadge = (score: number): { color: string; label: string } => {
    if (score >= 80) return { color: 'bg-green-500/20 text-green-400', label: 'Healthy' };
    if (score >= 60) return { color: 'bg-yellow-500/20 text-yellow-400', label: 'Monitor' };
    if (score >= 40) return { color: 'bg-orange-500/20 text-orange-400', label: 'At Risk' };
    return { color: 'bg-red-500/20 text-red-400', label: 'Critical' };
  };

  const getRiskBadge = (probability: number): { color: string; label: string } => {
    if (probability < 20) return { color: 'bg-green-500/20 text-green-400', label: 'Low Risk' };
    if (probability < 40) return { color: 'bg-yellow-500/20 text-yellow-400', label: 'Medium' };
    if (probability < 70) return { color: 'bg-orange-500/20 text-orange-400', label: 'High Risk' };
    return { color: 'bg-red-500/20 text-red-400', label: 'Urgent' };
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleCustomerClick = (customerId: string) => {
    navigate(`/customer/360?id=${customerId}`);
  };

  // Calculate portfolio stats
  const portfolioStats = {
    totalCustomers: customers.length,
    totalMRR: customers.reduce((sum, c) => sum + (c.mrr || 0), 0),
    avgHealth: customers.length > 0 
      ? customers.reduce((sum, c) => sum + (c.health_score || 0), 0) / customers.length 
      : 0,
    atRisk: customers.filter(c => c.health_score < 60).length,
    healthy: customers.filter(c => c.health_score >= 80).length,
  };

  // Filter and sort customers
  let filteredCustomers = [...customers];
  
  if (filterStatus !== 'all') {
    filteredCustomers = filteredCustomers.filter(c => {
      if (filterStatus === 'healthy') return c.health_score >= 80;
      if (filterStatus === 'at-risk') return c.health_score >= 40 && c.health_score < 80;
      if (filterStatus === 'critical') return c.health_score < 40;
      return true;
    });
  }

  filteredCustomers.sort((a, b) => {
    if (sortBy === 'health') return (b.health_score || 0) - (a.health_score || 0);
    if (sortBy === 'mrr') return (b.mrr || 0) - (a.mrr || 0);
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    return 0;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading your portfolio...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-6 max-w-md">
          <h3 className="text-red-400 font-semibold mb-2">Error Loading Portfolio</h3>
          <p className="text-slate-400 mb-4">{error}</p>
          <button
            onClick={fetchPortfolio}
            className="px-4 py-2 bg-cyan-500 text-white rounded hover:bg-cyan-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Agent Portfolio</h1>
            <p className="text-slate-400">Manage and monitor your client relationships</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
              BIGQUERY LIVE
            </span>
            <button
              onClick={fetchPortfolio}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded transition-colors"
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Portfolio Stats */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">Total Clients</p>
            <p className="text-2xl font-bold text-white">{portfolioStats.totalCustomers}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">Monthly Revenue</p>
            <p className="text-2xl font-bold text-cyan-400">{formatCurrency(portfolioStats.totalMRR)}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">Lifetime Value</p>
            <p className="text-2xl font-bold text-emerald-400">{formatCurrency(customers.reduce((sum, c) => sum + (c.lifetime_value || 0), 0))}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">Avg Health</p>
            <p className={`text-2xl font-bold ${getHealthColor(portfolioStats.avgHealth)}`}>
              {portfolioStats.avgHealth.toFixed(0)}%
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">Healthy</p>
            <p className="text-2xl font-bold text-green-400">{portfolioStats.healthy}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">At Risk</p>
            <p className="text-2xl font-bold text-orange-400">{portfolioStats.atRisk}</p>
          </div>
        </div>
      </div>

      {/* Filters and Sort */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setFilterStatus('all')}
            className={`px-4 py-2 rounded transition-colors ${
              filterStatus === 'all'
                ? 'bg-cyan-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            All ({customers.length})
          </button>
          <button
            onClick={() => setFilterStatus('healthy')}
            className={`px-4 py-2 rounded transition-colors ${
              filterStatus === 'healthy'
                ? 'bg-green-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            Healthy ({portfolioStats.healthy})
          </button>
          <button
            onClick={() => setFilterStatus('at-risk')}
            className={`px-4 py-2 rounded transition-colors ${
              filterStatus === 'at-risk'
                ? 'bg-orange-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            At Risk ({portfolioStats.atRisk})
          </button>
          <button
            onClick={() => setFilterStatus('critical')}
            className={`px-4 py-2 rounded transition-colors ${
              filterStatus === 'critical'
                ? 'bg-red-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            Critical ({customers.filter(c => c.health_score < 40).length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-slate-800 text-white border border-slate-700 rounded px-3 py-2"
          >
            <option value="health">Health Score</option>
            <option value="mrr">MRR (Highest)</option>
            <option value="name">Name (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Customer List */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-800">
            <tr>
              <th className="text-left px-6 py-3 text-slate-300 font-semibold">Customer</th>
              <th className="text-left px-6 py-3 text-slate-300 font-semibold">Industry</th>
              <th className="text-right px-6 py-3 text-slate-300 font-semibold">MRR</th>
              <th className="text-right px-6 py-3 text-slate-300 font-semibold">Lifetime</th>
              <th className="text-center px-6 py-3 text-slate-300 font-semibold">Health Score</th>
              <th className="text-center px-6 py-3 text-slate-300 font-semibold">Churn Risk</th>
              <th className="text-center px-6 py-3 text-slate-300 font-semibold">Status</th>
              <th className="text-center px-6 py-3 text-slate-300 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map((customer, index) => {
              const healthBadge = getHealthBadge(customer.health_score);
              const riskBadge = getRiskBadge(customer.churn_probability);
              
              return (
                <tr
                  key={customer.customer_id}
                  className="border-t border-slate-800 hover:bg-slate-800/50 transition-colors cursor-pointer"
                  onClick={() => handleCustomerClick(customer.customer_id)}
                >
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-white font-medium">{customer.name}</p>
                      <p className="text-slate-400 text-sm">ID: {customer.customer_id}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-300">{customer.industry}</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-cyan-400 font-semibold">
                      {formatCurrency(customer.mrr || 0)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-emerald-400 font-medium">
                      {formatCurrency(customer.lifetime_value || 0)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-16 bg-slate-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            customer.health_score >= 80 ? 'bg-green-500' :
                            customer.health_score >= 60 ? 'bg-yellow-500' :
                            customer.health_score >= 40 ? 'bg-orange-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${customer.health_score}%` }}
                        />
                      </div>
                      <span className={`font-bold ${getHealthColor(customer.health_score)}`}>
                        {customer.health_score}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${riskBadge.color}`}>
                      {riskBadge.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${healthBadge.color}`}>
                      {healthBadge.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCustomerClick(customer.customer_id);
                      }}
                      className="px-3 py-1 bg-cyan-500 hover:bg-cyan-600 text-white rounded text-sm transition-colors"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredCustomers.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p>No customers found matching the selected filter.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentPortfolio;
