import React, { useState } from 'react';
import { HashRouter, Routes, Route, Navigate, NavLink, useLocation } from 'react-router-dom';
import { 
  Network, 
  Users, 
  Activity, 
  BrainCircuit, 
  Database, 
  Menu,
  X,
  Layers,
  Cpu,
  Share2
} from 'lucide-react';

// Pages
import PlatformOverview from './pages/PlatformOverview';
import Customer360 from './pages/Customer360';
import AgentPortfolio from './pages/AgentPortfolio';
import PortfolioList from './pages/PortfolioList';
import PortfolioDetail from './pages/PortfolioDetail';
import ActionExecutor from './pages/ActionExecutor';
import DataNexus from './pages/DataNexus';
import KnowledgeGraphExplorer from './pages/KnowledgeGraphExplorer';

const Sidebar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  // Helper for consistent NavLink styling
  const getLinkClass = (isActive: boolean, color: 'blue' | 'emerald' | 'purple') => {
    const base = "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 text-sm group";
    
    if (!isActive) {
      return `${base} text-gray-400 hover:bg-morpheus-800 hover:text-gray-200`;
    }

    // Active styles based on color theme
    if (color === 'blue') {
      return `${base} bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]`;
    }
    if (color === 'emerald') {
      return `${base} bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]`;
    }
    if (color === 'purple') {
      return `${base} bg-purple-500/10 text-purple-400 border border-purple-500/20`;
    }
    return base;
  };

  return (
    <>
      {/* Mobile Trigger */}
      <button 
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 right-4 z-50 p-2 bg-morpheus-800 rounded-md border border-morpheus-700"
      >
        {mobileOpen ? <X /> : <Menu />}
      </button>

      {/* Sidebar Container */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-morpheus-900 border-r border-morpheus-700 z-40 transition-transform duration-300 flex flex-col
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Brand Header */}
        <div className="p-6 border-b border-morpheus-700 flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <BrainCircuit className="text-white" size={18} />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight text-white">MORPHEUS</h1>
            <p className="text-[10px] text-morpheus-accent font-mono uppercase tracking-wider">Intelligence Core</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
          
          {/* Section: MORPHEUS CORE */}
          <div>
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-2 flex items-center gap-2">
              <Cpu size={10} /> Morpheus Core
            </div>
            <nav className="space-y-1">
              <NavLink
                to="/"
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => getLinkClass(isActive, 'blue')}
              >
                <Network size={18} />
                <span>Neural Hub</span>
              </NavLink>
              <NavLink
                to="/integration"
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => getLinkClass(isActive, 'blue')}
              >
                <Database size={18} />
                <span>Data Nexus</span>
              </NavLink>
              <NavLink
                to="/knowledge-graph"
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => getLinkClass(isActive, 'blue')}
              >
                <Share2 size={18} />
                <span>Knowledge Graph</span>
              </NavLink>
            </nav>
          </div>

          {/* Section: MODULES */}
          <div>
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-2 flex items-center gap-2">
              <Layers size={10} /> Active Modules
            </div>
            <nav className="space-y-1">
              <NavLink
                to="/morpheus360"
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => getLinkClass(isActive, 'emerald')}
              >
                {({ isActive }) => (
                  <>
                    <Users size={18} className={isActive ? "text-emerald-400" : "group-hover:text-emerald-400 transition-colors"} />
                    <span>Morpheus 360</span>
                  </>
                )}
              </NavLink>
              <NavLink
                to="/actions"
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => getLinkClass(isActive, 'purple')}
              >
                {({ isActive }) => (
                  <>
                     <Activity size={18} className={isActive ? "text-purple-400" : "group-hover:text-purple-400 transition-colors"} />
                     <span>Action Executor</span>
                  </>
                )}
              </NavLink>
            </nav>
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-morpheus-700 bg-morpheus-800/50">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              <div className="w-2 h-2 rounded-full bg-emerald-500 absolute top-0 left-0 animate-ping opacity-75"></div>
            </div>
            <span className="text-xs text-emerald-500 font-mono tracking-wide">SYSTEM OPTIMAL</span>
          </div>
          <div className="mt-2 text-[10px] text-gray-500 font-mono">
            Morpheus Engine v2.1.0
          </div>
        </div>
      </aside>
    </>
  );
};

const App: React.FC = () => {
  return (
    <HashRouter>
      <div className="min-h-screen bg-morpheus-900 text-gray-100 font-sans selection:bg-morpheus-accent/30">
        <Sidebar />
        <main className="lg:ml-64 min-h-screen transition-all duration-300">
          <Routes>
            <Route path="/" element={<PlatformOverview />} />
            <Route path="/morpheus360" element={<PortfolioList />} />
            <Route path="/morpheus360/portfolio/:id" element={<PortfolioDetail />} />
            <Route path="/customer/360" element={<Customer360 />} />
            <Route path="/integration" element={<DataNexus />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraphExplorer />} />
            <Route path="/actions" element={<ActionExecutor />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
};

export default App;