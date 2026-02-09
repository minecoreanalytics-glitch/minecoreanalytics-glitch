import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  ArrowRight, 
  Zap,
  Filter,
  MoreHorizontal,
  Play,
  Check,
  Loader2
} from 'lucide-react';
import { DataService } from '../services/dataService';
import { ActionItem } from '../types';

const ActionExecutor: React.FC = () => {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const data = await DataService.getPendingActions();
        setActions(data);
      } catch (e) {
        console.error("Error fetching actions", e);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handleAction = (id: string, newStatus: 'approved' | 'rejected') => {
    setProcessing(id);
    // Simulate API call to execute action
    setTimeout(() => {
      setActions(prev => prev.map(a => 
        a.id === id ? { ...a, status: newStatus === 'approved' ? 'executed' : 'rejected' } : a
      ));
      setProcessing(null);
    }, 1500);
  };

  if (loading) {
     return (
        <div className="h-screen flex flex-col items-center justify-center">
           <Loader2 className="animate-spin text-purple-500 mb-4" size={32} />
           <p className="text-xs font-mono text-gray-500">Retrieving Decision Protocols...</p>
        </div>
     );
  }

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-morpheus-700 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-3">
            <Zap className="text-purple-400" /> 
            Action Executor
          </h1>
          <p className="text-gray-400 text-sm">
            Autonomous decision engine. Review and authorise Morpheus generated protocols.
          </p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-morpheus-800 border border-morpheus-700 rounded-lg text-sm text-gray-300 hover:text-white transition-colors">
            <Filter size={16} /> Filter
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 border border-purple-500/30 text-purple-400 rounded-lg text-sm font-medium hover:bg-purple-600/30 transition-colors">
            <Play size={16} /> Auto-Pilot: OFF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            <Clock size={14} /> Pending Approvals
          </h3>
          
          {actions.filter(a => a.status === 'pending').map((action) => (
            <div key={action.id} className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-5 shadow-lg relative overflow-hidden group hover:border-purple-500/50 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Zap size={100} />
              </div>

              <div className="flex justify-between items-start relative z-10">
                <div className="space-y-1">
                   <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border
                        ${action.priority === 'high' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                          action.priority === 'medium' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 
                          'bg-blue-500/10 text-blue-400 border-blue-500/20'}
                      `}>
                        {action.priority} Priority
                      </span>
                      <span className="text-xs text-gray-500 font-mono">{action.id}</span>
                   </div>
                   <h3 className="text-lg font-bold text-white">{action.title}</h3>
                   <p className="text-sm text-gray-300">{action.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-gray-500 uppercase">Confidence</div>
                  <div className="text-xl font-bold text-emerald-400 font-mono">{action.confidence}%</div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-morpheus-900/50 rounded-lg border border-morpheus-700/50 text-xs text-gray-400 flex items-start gap-2">
                 <AlertTriangle size={14} className="text-morpheus-accent mt-0.5 shrink-0" />
                 <span><span className="text-morpheus-accent font-semibold">Reasoning:</span> {action.reason}</span>
              </div>

              <div className="mt-5 flex items-center gap-3 relative z-10">
                <button 
                  onClick={() => handleAction(action.id, 'approved')}
                  disabled={processing === action.id}
                  className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2"
                >
                  {processing === action.id ? <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div> : <CheckCircle size={16} />}
                  Approve Execution
                </button>
                <button 
                  onClick={() => handleAction(action.id, 'rejected')}
                  disabled={processing === action.id}
                  className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2"
                >
                  <XCircle size={16} />
                  Reject
                </button>
              </div>
            </div>
          ))}

          {actions.filter(a => a.status === 'pending').length === 0 && (
             <div className="p-10 text-center border border-dashed border-morpheus-700 rounded-xl text-gray-500">
                <CheckCircle size={48} className="mx-auto mb-4 text-morpheus-700" />
                <p>All pending actions cleared.</p>
             </div>
          )}
        </div>

        {/* Sidebar History */}
        <div className="space-y-6">
           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Execution History</h3>
              <div className="space-y-4">
                 {actions.filter(a => a.status !== 'pending').map((action) => (
                    <div key={action.id} className="flex gap-3 relative">
                       <div className="flex flex-col items-center">
                          <div className={`w-2 h-2 rounded-full mt-1.5 ${action.status === 'executed' ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                          <div className="w-px h-full bg-morpheus-700 my-1"></div>
                       </div>
                       <div className="pb-4">
                          <div className="flex items-center gap-2 mb-1">
                             <span className="text-xs font-bold text-gray-300">{action.title}</span>
                             <span className={`text-[10px] px-1.5 py-0.5 rounded border capitalize ${
                                action.status === 'executed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'
                             }`}>{action.status}</span>
                          </div>
                          <p className="text-[10px] text-gray-500">{action.customer}</p>
                          <p className="text-[10px] text-gray-600 mt-1">{action.timestamp}</p>
                       </div>
                    </div>
                 ))}
              </div>
           </div>

           <div className="bg-gradient-to-br from-purple-900/50 to-morpheus-900 p-6 rounded-xl border border-purple-500/20">
              <h3 className="font-bold text-white mb-2">Automation Rules</h3>
              <p className="text-xs text-gray-400 mb-4">
                 Configure thresholds for auto-execution based on confidence score and risk category.
              </p>
              <button className="w-full py-2 bg-morpheus-800 border border-morpheus-700 hover:bg-morpheus-700 rounded-lg text-xs text-white transition-colors">
                 Manage Rules
              </button>
           </div>
        </div>

      </div>
    </div>
  );
};

export default ActionExecutor;