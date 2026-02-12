import React from 'react';
import { useNavigate } from 'react-router-dom';
import { clearAuth, getAuth } from './Login';
import PortfolioList from './PortfolioList';

const ManagerHome: React.FC = () => {
  const navigate = useNavigate();
  const auth = getAuth();

  if (!auth) return null;

  return (
    <div>
      <div className="px-8 pt-8 max-w-7xl mx-auto flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Manager Console</h1>
          <p className="text-gray-400 text-sm">Create portfolios and assign clients to agents.</p>
        </div>
        <button
          onClick={() => { clearAuth(); navigate('/login', { replace: true }); }}
          className="px-4 py-2 rounded-lg border border-morpheus-700 text-gray-300 hover:bg-morpheus-800 transition-colors"
        >
          Sign out
        </button>
      </div>
      <PortfolioList />
    </div>
  );
};

export default ManagerHome;
