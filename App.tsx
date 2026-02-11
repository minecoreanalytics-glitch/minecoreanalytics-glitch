import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';

import Login, { getAuth } from './pages/Login';
import ManagerHome from './pages/ManagerHome';
import AgentHome from './pages/AgentHome';
import PortfolioDetail from './pages/PortfolioDetail';
import Customer360 from './pages/Customer360';
import DataNexus from './pages/DataNexus';
import KnowledgeGraphExplorer from './pages/KnowledgeGraphExplorer';
import M360Shell from './components/M360Shell';

const RequireAuth: React.FC<{ role?: 'manager' | 'agent'; children: React.ReactNode }> = ({ role, children }) => {
  const auth = getAuth();
  if (!auth) return <Navigate to="/login" replace />;
  if (role && auth.role !== role) return <Navigate to={auth.role === 'manager' ? '/manager' : '/agent'} replace />;
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <HashRouter>
      <M360Shell>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/manager"
            element={
              <RequireAuth role="manager">
                <ManagerHome />
              </RequireAuth>
            }
          />

          <Route
            path="/manager/portfolio/:id"
            element={
              <RequireAuth role="manager">
                <PortfolioDetail />
              </RequireAuth>
            }
          />

          <Route
            path="/manager/data-nexus"
            element={
              <RequireAuth role="manager">
                <DataNexus />
              </RequireAuth>
            }
          />

          <Route
            path="/manager/graph"
            element={
              <RequireAuth role="manager">
                <KnowledgeGraphExplorer />
              </RequireAuth>
            }
          />

          <Route
            path="/agent"
            element={
              <RequireAuth role="agent">
                <AgentHome />
              </RequireAuth>
            }
          />

          <Route
            path="/agent/portfolio/:id"
            element={
              <RequireAuth role="agent">
                <PortfolioDetail />
              </RequireAuth>
            }
          />

          <Route
            path="/agent/customer/360"
            element={
              <RequireAuth role="agent">
                <Customer360 />
              </RequireAuth>
            }
          />

          <Route
            path="/manager/customer/360"
            element={
              <RequireAuth role="manager">
                <Customer360 />
              </RequireAuth>
            }
          />

          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </M360Shell>
    </HashRouter>
  );
};

export default App;
