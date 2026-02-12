import React, { useState, useEffect } from 'react';
import {
  Database,
  Activity,
  Zap,
  Server,
  ArrowUpRight,
  Share2,
  Cpu,
  GitBranch,
  Layers,
  RefreshCw,
  Trash2,
  Play,
  Loader2
} from 'lucide-react';
import { DataService } from '../services/dataService';

const StatCard: React.FC<{
  title: string;
  value: string;
  sub: string;
  icon: React.ReactNode;
  color?: string;
}> = ({ title, value, sub, icon, color = "blue" }) => {
  // Fix: Use proper conditional classes instead of template literal interpolation
  const bgColorClass = color === "blue" ? "bg-blue-500/5" :
                        color === "green" ? "bg-green-500/5" :
                        color === "purple" ? "bg-purple-500/5" : "bg-blue-500/5";

  return (
    <div className="bg-morpheus-800 p-6 rounded-xl border border-morpheus-700 hover:border-morpheus-500/50 transition-all group relative overflow-hidden">
      <div className={`absolute top-0 right-0 w-24 h-24 ${bgColorClass} rounded-full blur-2xl -mr-10 -mt-10 transition-opacity group-hover:opacity-100 opacity-50`}></div>
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className="p-3 bg-morpheus-900 rounded-lg text-morpheus-500 group-hover:text-morpheus-accent transition-colors border border-morpheus-700">
          {icon}
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded border border-emerald-400/20">
          {sub}
        </span>
      </div>
      <div className="text-3xl font-bold text-white mb-1 tracking-tight relative z-10">{value}</div>
      <div className="text-sm text-gray-400 relative z-10">{title}</div>
    </div>
  );
};

const ModuleStatus: React.FC<{ name: string; status: string; latency: string; active: boolean; icon?: React.ReactNode }> = ({ name, status, latency, active, icon }) => (
  <div className="flex items-center justify-between p-3 bg-morpheus-900/50 rounded-lg border border-morpheus-700/50 hover:border-morpheus-700 transition-colors">
    <div className="flex items-center gap-3">
      <div className={`w-2 h-2 rounded-full ${active ? 'bg-emerald-500 animate-pulse' : 'bg-gray-500'}`} />
      <div>
         <div className="text-sm font-medium text-gray-200 flex items-center gap-2">
            {name}
            {icon && <span className="text-gray-500">{icon}</span>}
         </div>
         <div className="text-[10px] text-gray-500">{status}</div>
      </div>
    </div>
    <div className="text-right">
      <div className="text-[10px] font-mono text-emerald-500/80 bg-emerald-500/5 px-2 py-0.5 rounded">{latency}</div>
    </div>
  </div>
);

interface LogEntry {
  id: number;
  source: string;
  event: string;
  time: string;
  status: string;
}

const PlatformOverview: React.FC = () => {
  const [syncing, setSyncing] = useState(false);

  // Hardcode logs for now to avoid async issues
  const logs: LogEntry[] = [
    { id: 1, source: 'BigQuery', event: 'Billing Sync Complete', time: '10:42 AM', status: 'success' },
    { id: 2, source: 'Salesforce', event: 'Case #4922 Updated', time: '10:41 AM', status: 'info' },
    { id: 3, source: 'Morpheus Engine', event: 'Knowledge Graph Re-index', time: '10:38 AM', status: 'success' },
  ];

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 2000);
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 border-b border-morpheus-700 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-3">
            <Cpu className="text-morpheus-accent" />
            Morpheus Intelligence Hub
          </h1>
          <p className="text-gray-400 text-sm max-w-2xl">
            Central Intelligence Platform orchestrating data injection, correlation, and logic distribution to downstream modules.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <div className="text-xs text-gray-500">Global System Load</div>
            <div className="text-sm font-mono text-morpheus-accent">34% OPTIMAL</div>
          </div>
          <div className="w-px h-8 bg-morpheus-700 mx-2 hidden md:block"></div>
          <div className="flex items-center gap-2 text-xs font-mono text-morpheus-accent bg-morpheus-accent/10 px-3 py-1.5 rounded-full border border-morpheus-accent/20">
            <div className="w-1.5 h-1.5 rounded-full bg-morpheus-accent animate-pulse" />
            MORPHEUS ENGINE v2.0 ONLINE
          </div>
        </div>
      </div>

      {/* Core Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Correlated Entities"
          value="25,553"
          sub="KG GROUNDS"
          icon={<GitBranch size={24} />}
        />
        <StatCard
          title="Data Ingestion"
          value="2.4 GB/s"
          sub="5 STREAMS"
          icon={<Database size={24} />}
        />
        <StatCard
          title="Inference/Sec"
          value="142"
          sub="99.9% VALID"
          icon={<Zap size={24} />}
        />
        <StatCard
          title="Module Uptime"
          value="100%"
          sub="HEALTHY"
          icon={<Server size={24} />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Vis - Left 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Logs Panel - Now taking prominence as the main feed */}
          <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 overflow-hidden h-full flex flex-col">
            <div className="p-4 border-b border-morpheus-700 flex justify-between items-center bg-morpheus-800/50">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Activity size={16} className="text-morpheus-500" />
                Ingestion & Correlation Logs
              </h3>
              <div className="flex gap-2">
                <span className="text-[10px] bg-morpheus-900 text-gray-500 px-2 py-1 rounded">Live Stream</span>
              </div>
            </div>
            <div className="divide-y divide-morpheus-700 bg-black/20 flex-1 overflow-y-auto min-h-[400px]">
              {logs.map((log) => (
                <div key={log.id} className="p-4 flex items-center justify-between hover:bg-morpheus-700/30 transition-colors group">
                  <div className="flex items-center gap-4">
                    <span className={`w-2 h-2 rounded-full ${
                      log.status === 'success' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' :
                      log.status === 'warning' ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 'bg-blue-500'
                    }`} />
                    <div>
                      <div className="text-sm text-gray-200 font-mono group-hover:text-white transition-colors">{log.event}</div>
                      <div className="text-[10px] text-gray-500 uppercase tracking-wide flex items-center gap-2">
                         {log.source}
                         {log.status === 'success' && <span className="text-emerald-500/50">●</span>}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs font-mono text-gray-500">{log.time}</div>
                </div>
              ))}
              {/* Additional Mock Logs to fill space */}
              <div className="p-4 flex items-center justify-between hover:bg-morpheus-700/30 transition-colors group opacity-50">
                  <div className="flex items-center gap-4">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    <div>
                      <div className="text-sm text-gray-200 font-mono">Routine Health Check</div>
                      <div className="text-[10px] text-gray-500 uppercase tracking-wide">System Core</div>
                    </div>
                  </div>
                  <div className="text-xs font-mono text-gray-500">10:25 AM</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar - Right 1/3 */}
        <div className="space-y-6">

          {/* Control Plane (Operational) */}
          <div className="bg-morpheus-800 p-5 rounded-xl border border-morpheus-700 shadow-xl">
             <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
               <Cpu size={16} className="text-morpheus-accent" />
               Control Plane
             </h3>
             <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleSync}
                  className={`flex items-center justify-center gap-2 bg-morpheus-900 border border-morpheus-700 rounded-lg p-2 text-xs font-medium text-gray-300 hover:bg-morpheus-700 hover:text-white transition-all ${syncing ? 'opacity-70 cursor-wait' : ''}`}
                >
                   <RefreshCw size={12} className={syncing ? "animate-spin" : ""} />
                   {syncing ? 'Syncing...' : 'Force Sync'}
                </button>
                <button className="flex items-center justify-center gap-2 bg-morpheus-900 border border-morpheus-700 rounded-lg p-2 text-xs font-medium text-gray-300 hover:bg-morpheus-700 hover:text-white transition-all">
                   <Trash2 size={12} />
                   Purge Cache
                </button>
                <button className="col-span-2 flex items-center justify-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-lg p-2 text-xs font-medium text-blue-400 hover:bg-blue-600/20 transition-all">
                   <Play size={12} />
                   Run Diagnostics (Level 3)
                </button>
             </div>
          </div>

          {/* Module Health Panel */}
          <div className="bg-morpheus-800 p-5 rounded-xl border border-morpheus-700 shadow-xl">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Share2 size={16} className="text-morpheus-accent" />
              Active Modules
            </h3>
            <p className="text-xs text-gray-400 mb-4">
                Applications currently consuming data from Morpheus Core.
            </p>
            <div className="space-y-3">
              <ModuleStatus
                name="Morpheus 360"
                status="Feeding Live Customer Intelligence"
                latency="12ms"
                active={true}
                icon={<Layers size={12} />}
              />
              <ModuleStatus
                name="Action Executor"
                status="Standby - Ready for trigger"
                latency="8ms"
                active={true}
                icon={<Zap size={12} />}
              />
              <ModuleStatus
                name="Analytics Engine"
                status="Batch Processing"
                latency="45ms"
                active={true}
              />
            </div>
            <div className="mt-4 pt-4 border-t border-morpheus-700">
               <div className="flex justify-between items-center text-xs text-gray-400">
                 <span>Total API Throughput</span>
                 <span className="font-mono text-white">452 req/min</span>
               </div>
               <div className="w-full bg-morpheus-900 rounded-full h-1.5 mt-2">
                 <div className="bg-blue-500 h-1.5 rounded-full w-[35%]"></div>
               </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default PlatformOverview;
