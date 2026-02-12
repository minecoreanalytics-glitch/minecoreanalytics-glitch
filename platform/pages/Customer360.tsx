
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import { 
  Building2, 
  CreditCard, 
  Signal, 
  MessageSquare, 
  ArrowRight,
  BrainCircuit,
  Link2,
  Layers,
  History,
  FileText,
  Download,
  Phone,
  Siren,
  TrendingUp,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { DataService } from '../services/dataService';
import { FullCustomerView } from '../types';

const Customer360: React.FC = () => {
  const [searchParams] = useSearchParams();
  const customerId = searchParams.get('id') || "1000070019"; // Default ID if none provided
  
  const [data, setData] = useState<FullCustomerView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<{
    isConnected: boolean;
    projectId: string | null;
    activeDataset: string | null;
  } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Check connection (optional) so we can show a clean error message
        const status = await DataService.getConnectionStatus();
        setConnectionStatus(status);

        // Fetch customer data using the ID from URL
        const customerData = await DataService.getCustomer360(customerId);
        setData(customerData);
      } catch (err) {
        setError("Failed to load customer data.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [customerId]); // Reload when customer ID changes

  if (loading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center space-y-4">
        <Loader2 className="animate-spin text-emerald-500" size={48} />
        <div className="text-sm font-mono text-gray-400 animate-pulse">Loading customer profile...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="h-screen flex flex-col items-center justify-center space-y-6 p-6">
        <div className="bg-morpheus-800 border border-morpheus-700 rounded-xl p-8 max-w-md text-center space-y-4">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto">
            <AlertTriangle className="text-red-400" size={32} />
          </div>
          <h2 className="text-xl font-bold text-white">
            {!connectionStatus?.isConnected ? 'Connect to BigQuery' : 'Connection Error'}
          </h2>
          <p className="text-gray-400 text-sm">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-morpheus-700 hover:bg-morpheus-600 text-white rounded-lg text-sm font-medium transition-colors w-full"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const metrics = data.metrics;
  const cnsScore = Math.max(0, Math.min(100, Number(metrics?.cns ?? 0)));
  
  // CNS breakdown must be grounded in real signals.
  // If a signal is missing, keep it at 0 (no simulation).
  const hf = ((data as any)?.health_factors || {}) as {
    payment_method_score?: number;
    failed_payments_10m?: number;
    service_count?: number;
    plan_tier?: string;
    account_age_months?: number;
    timing_points?: number;
    billing_health_score?: number;
    network_health_score?: number;
    customer_experience_score?: number;
    equipment_health_score?: number;
    tenure_score?: number;
    domain_breakdown?: {
      billing?: {
        score?: number;
        weight?: number;
        components?: Array<{ id: string; label: string; score: number; weight: number }>;
      };
      network?: {
        score?: number;
        weight?: number;
        components?: Array<{ id: string; label: string; score: number; weight: number }>;
      };
      customer_experience?: {
        score?: number;
        weight?: number;
        components?: Array<{ id: string; label: string; score: number; weight: number }>;
      };
      equipment?: {
        score?: number;
        weight?: number;
        components?: Array<{ id: string; label: string; score: number; weight: number }>;
      };
    };
  };

  const billingScore = typeof hf.billing_health_score === 'number'
    ? Math.max(0, Math.min(100, hf.billing_health_score))
    : 0;

  const networkScore = typeof hf.network_health_score === 'number'
    ? Math.max(0, Math.min(100, hf.network_health_score))
    : 0;

  const experienceScore = typeof hf.customer_experience_score === 'number'
    ? Math.max(0, Math.min(100, hf.customer_experience_score))
    : 0;

  const equipmentScore = typeof hf.equipment_health_score === 'number'
    ? Math.max(0, Math.min(100, hf.equipment_health_score))
    : 0;

  const domainBreakdown = hf.domain_breakdown;

  const componentStatus = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 65) return 'Good';
    if (score >= 45) return 'Watch';
    return 'At Risk';
  };

  const domainCards = [
    {
      key: 'billing' as const,
      title: 'Billing Health',
      score: billingScore,
      weight: domainBreakdown?.billing?.weight ?? 30,
      icon: CreditCard,
      iconColor: 'text-blue-400',
      barColor: 'bg-blue-500',
      components: domainBreakdown?.billing?.components ?? [{ id: 'billing_core', label: 'Billing Core', score: billingScore, weight: 100 }],
    },
    {
      key: 'network' as const,
      title: 'Network Health',
      score: networkScore,
      weight: domainBreakdown?.network?.weight ?? 25,
      icon: Signal,
      iconColor: 'text-purple-400',
      barColor: 'bg-purple-500',
      components: domainBreakdown?.network?.components ?? [{ id: 'network_core', label: 'Network Core', score: networkScore, weight: 100 }],
    },
    {
      key: 'customer_experience' as const,
      title: 'Customer Experience',
      score: experienceScore,
      weight: domainBreakdown?.customer_experience?.weight ?? 25,
      icon: MessageSquare,
      iconColor: 'text-pink-400',
      barColor: 'bg-pink-500',
      components: domainBreakdown?.customer_experience?.components ?? [{ id: 'experience_core', label: 'Experience Core', score: experienceScore, weight: 100 }],
    },
    {
      key: 'equipment' as const,
      title: 'Equipment Health',
      score: equipmentScore,
      weight: domainBreakdown?.equipment?.weight ?? 20,
      icon: TrendingUp,
      iconColor: 'text-amber-400',
      barColor: 'bg-amber-500',
      components: domainBreakdown?.equipment?.components ?? [{ id: 'equipment_core', label: 'Equipment Core', score: equipmentScore, weight: 100 }],
    },
  ];

  // Churn Gauge Data
  const churnRisk = metrics.churn_probability;
  const churnData = [
    { name: 'Risk', value: churnRisk },
    { name: 'Safe', value: 100 - churnRisk },
  ];
  const CHURN_COLORS = ['#EF4444', '#1F2937']; // Red for risk, dark for remaining

  const recentActivity = (((data as any)?.recent_activity ?? []) as Array<{
    type?: string;
    channel?: string;
    subject?: string;
    sentiment?: string;
    timestamp?: string;
  }>).slice(0, 5);

  const recommendedActions = [
    ...domainCards
      .filter((domain) => domain.score < 60)
      .map((domain) => ({
        key: `stabilize-${domain.key}`,
        tag: 'STABILIZE',
        title: `Improve ${domain.title}`,
        description: `${domain.title} is ${Math.round(domain.score)}/100. Focus on lowest sub-components first.`,
      })),
    ...(churnRisk >= 40
      ? [
          {
            key: 'churn-escalation',
            tag: 'RETENTION',
            title: 'Escalate Churn Mitigation',
            description: `Churn probability is ${churnRisk.toFixed(1)}%. Trigger retention workflow and agent outreach.`,
          },
        ]
      : []),
    ...((String((data as any)?.status || '').toLowerCase() === 'on-hold')
      ? [
          {
            key: 'on-hold-recovery',
            tag: 'RECOVERY',
            title: 'Resolve On-Hold Account State',
            description: 'Account is currently On-Hold. Prioritize payment and service unblock sequence.',
          },
        ]
      : []),
  ].slice(0, 4);

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6 animate-fade-in">
      
      {/* Module Branding / Header */}
      <div className="bg-morpheus-800/80 p-4 rounded-xl border border-morpheus-700 flex flex-col md:flex-row items-center justify-between gap-4 backdrop-blur-md sticky top-0 z-20 shadow-lg">
        <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-emerald-500 to-green-400 p-2.5 rounded-lg shadow-lg shadow-emerald-500/20">
                <Layers className="text-white" size={24} />
            </div>
            <div>
                <h2 className="text-xl font-bold text-white tracking-wide leading-none">MORPHEUS 360</h2>
                <p className="text-xs text-emerald-400 font-medium mt-1">Customer Success & Account Management Module</p>
            </div>
        </div>
        <div className="flex items-center gap-3">
             <div className="flex items-center gap-2 text-[10px] text-gray-400 bg-morpheus-900 px-3 py-1.5 rounded-full border border-morpheus-700 shadow-inner">
                <Link2 size={12} />
                <span className="font-mono">DATA_SOURCE: {connectionStatus?.isConnected ? connectionStatus.projectId : 'MORPHEUS_KG_v2.1'}</span>
            </div>
            {connectionStatus?.isConnected && (
              <div className="flex items-center gap-2 text-[10px] text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                  <span className="font-bold tracking-wider">BIGQUERY LIVE</span>
              </div>
            )}
        </div>
      </div>

      {/* Customer Header */}
      <div className="bg-morpheus-800 p-6 rounded-xl border border-morpheus-700 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-full flex items-center justify-center border border-blue-500/30">
            <Building2 className="text-blue-400" size={32} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-white">{data.name}</h1>
              <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 tracking-wider">
                {data.status}
              </span>
            </div>
            <p className="text-gray-400 font-mono text-sm mt-1">ID: <span className="text-gray-300">{data.customer_id}</span> • {data.industry}</p>
          </div>
        </div>
        
        <div className="flex gap-4 items-center">
            {/* Action Bar */}
            <div className="flex items-center gap-2 mr-4">
                 <button className="flex items-center gap-2 px-3 py-2 bg-morpheus-700 hover:bg-morpheus-600 text-gray-200 text-xs font-medium rounded-lg transition-colors">
                    <Download size={14} /> Report
                 </button>
                 <button className="flex items-center gap-2 px-3 py-2 bg-morpheus-700 hover:bg-morpheus-600 text-gray-200 text-xs font-medium rounded-lg transition-colors">
                    <Phone size={14} /> Call
                 </button>
                 <button className="flex items-center gap-2 px-3 py-2 bg-red-900/30 hover:bg-red-900/50 text-red-400 border border-red-500/30 text-xs font-medium rounded-lg transition-colors">
                    <Siren size={14} /> Escalate
                 </button>
            </div>

            <div className="h-8 w-px bg-morpheus-700 hidden lg:block"></div>
            
            <div className="flex gap-6 bg-morpheus-900/50 p-4 rounded-lg border border-morpheus-700/50">
                <div className="text-right">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Monthly Revenue</div>
                    <div className="text-xl font-bold text-white font-mono">${metrics.mrr?.toLocaleString() || '0'}</div>
                </div>
                <div className="h-8 w-px bg-morpheus-700"></div>
                <div className="text-right">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">CNS Score</div>
                    <div className="text-xl font-bold text-emerald-400 font-mono">{Math.round(cnsScore)}/100</div>
                </div>
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Details */}
        <div className="space-y-6">
           {/* Profile Card */}
           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-5">
              <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                <FileText size={14} /> Profile Details
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between border-b border-morpheus-700/50 pb-2">
                    <span className="text-gray-500">Customer ID</span>
                    <span className="text-gray-200 text-right font-mono">{data.customer_id}</span>
                </div>
                <div className="flex justify-between border-b border-morpheus-700/50 pb-2">
                    <span className="text-gray-500">Industry</span>
                    <span className="text-gray-200">{data.industry}</span>
                </div>
                <div className="flex justify-between border-b border-morpheus-700/50 pb-2">
                    <span className="text-gray-500">Status</span>
                    <span className="text-gray-200">{data.status}</span>
                </div>
                <div className="flex justify-between items-center pt-2">
                    <span className="text-gray-500">CNS Score</span>
                    <span className="text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded text-xs">{Math.round(cnsScore)}/100</span>
                </div>
              </div>
           </div>

           {/* Billing Card */}
           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-5">
              <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                <CreditCard size={14} /> Revenue Metrics
              </h3>
              <div className="grid grid-cols-2 gap-4">
                  <div className="bg-morpheus-900/50 p-3 rounded-lg border border-morpheus-700/50">
                      <div className="text-xs text-gray-500">Monthly Revenue</div>
                      <div className="text-lg font-bold text-white mt-1">${metrics.mrr?.toLocaleString() || '0'}</div>
                  </div>
                  <div className="bg-morpheus-900/50 p-3 rounded-lg border border-morpheus-700/50">
                      <div className="text-xs text-gray-500">CNS Score</div>
                      <div className="text-lg font-bold text-emerald-400 mt-1">{Math.round(cnsScore)}/100</div>
                  </div>
              </div>
              <div className="mt-4 text-xs text-gray-500 flex justify-between">
                  <span>Data Source</span>
                  <span className="text-gray-300">{connectionStatus?.isConnected ? 'BigQuery Live' : 'Not Connected'}</span>
              </div>
           </div>

           {/* Recommendations */}
           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-5 flex flex-col h-[300px]">
              <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                 <BrainCircuit size={14} className="text-morpheus-accent" />
                 Recommended Actions
              </h3>
              <div className="space-y-3 overflow-y-auto pr-1">
                 {recommendedActions.length === 0 && (
                   <div className="bg-morpheus-900/50 border border-morpheus-700/60 p-3 rounded-lg">
                     <p className="text-xs text-gray-400 leading-relaxed">No high-priority actions generated from current live signals.</p>
                   </div>
                 )}
                 {recommendedActions.map((action) => (
                   <div key={action.key} className="bg-morpheus-900/50 border-l-2 border-morpheus-accent p-3 rounded-r-lg">
                     <div className="flex justify-between items-start mb-1">
                       <span className="text-xs font-bold text-morpheus-accent">{action.tag}</span>
                       <ArrowRight size={12} className="text-gray-500" />
                     </div>
                     <h4 className="text-sm font-semibold text-white mb-1">{action.title}</h4>
                     <p className="text-xs text-gray-400 leading-relaxed">{action.description}</p>
                   </div>
                 ))}
              </div>
           </div>
        </div>

        {/* Middle: CNS & Churn Analysis */}
        <div className="space-y-6">
            <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6 flex flex-col items-center">
                 <h3 className="text-xs font-bold text-gray-400 mb-6 uppercase tracking-widest w-full text-left">Customer CNS Score</h3>
                 <div className="relative w-64 h-64 flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={[
                                    { name: 'CNS', value: cnsScore },
                                    { name: 'Gap', value: 100 - cnsScore }
                                ]}
                                innerRadius={80}
                                outerRadius={110}
                                paddingAngle={2}
                                dataKey="value"
                                startAngle={90}
                                endAngle={-270}
                                stroke="none"
                            >
                                <Cell fill="#10B981" />
                                <Cell fill="#1F2937" />
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-6xl font-bold text-emerald-400">{Math.round(cnsScore)}</span>
                        <span className="text-sm text-gray-400 mt-2">CNS Score</span>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4 w-full mt-6">
                    <div className="text-center p-3 bg-morpheus-900 rounded-lg">
                        <div className="text-2xl font-bold text-emerald-400">{Math.round(cnsScore)}</div>
                        <div className="text-[10px] text-gray-500 uppercase">CNS Score</div>
                    </div>
                    <div className="text-center p-3 bg-morpheus-900 rounded-lg">
                        <div className="text-2xl font-bold text-emerald-400">{churnRisk < 30 ? 'LOW' : churnRisk < 50 ? 'MED' : 'HIGH'}</div>
                        <div className="text-[10px] text-gray-500 uppercase">Risk Category</div>
                    </div>
                </div>
           </div>

           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6">
                <h3 className="text-xs font-bold text-gray-400 mb-6 uppercase tracking-widest">Churn Probability</h3>
                <div className="flex items-center gap-6">
                    <div className="relative w-24 h-24">
                        <ResponsiveContainer width="100%" height="100%">
                           <PieChart>
                               <Pie
                                   data={churnData}
                                   innerRadius={35}
                                   outerRadius={45}
                                   paddingAngle={5}
                                   dataKey="value"
                                   startAngle={90}
                                   endAngle={-270}
                                   stroke="none"
                               >
                                   {churnData.map((entry, index) => (
                                       <Cell key={`cell-${index}`} fill={CHURN_COLORS[index % CHURN_COLORS.length]} />
                                   ))}
                               </Pie>
                           </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-bold text-white">{churnRisk.toFixed(1)}%</span>
                        </div>
                    </div>
                    <div className="flex-1">
                        <div className="text-sm text-gray-300 mb-2">Churn Risk Analysis</div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            Probability is provided by live backend signals for this account and recalculates as source data updates.
                        </p>
                        <div className="mt-3 flex items-center gap-2">
                            <div className={`h-2 rounded-full flex-1 ${churnRisk < 5 ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                            <span className="text-xs font-mono text-gray-400">{churnRisk < 5 ? 'SAFE' : 'CRITICAL'}</span>
                        </div>
                    </div>
                </div>
           </div>
        </div>

        {/* Right Column: Component Breakdown */}
        <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6">
             <h3 className="text-xs font-bold text-gray-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                <Signal size={14} /> CNS Breakdown
             </h3>
             <div className="space-y-4">
                {domainCards.map((domain) => {
                  const DomainIcon = domain.icon;
                  return (
                    <div key={domain.key} className="bg-morpheus-900/40 border border-morpheus-700/50 rounded-lg p-3">
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center gap-2">
                          <DomainIcon size={14} className={domain.iconColor} />
                          <span className="text-sm font-medium text-gray-200">{domain.title}</span>
                        </div>
                        <span className="text-sm font-mono text-emerald-400">{Math.round(domain.score)}/100</span>
                      </div>
                      <div className="w-full bg-morpheus-900 h-1.5 rounded-full overflow-hidden mb-1">
                        <div className={`${domain.barColor} h-full rounded-full`} style={{ width: `${Math.max(0, Math.min(100, domain.score))}%` }}></div>
                      </div>
                      <p className="text-[10px] text-gray-500 mb-3">Weight: {domain.weight}% • Status: {componentStatus(domain.score)}</p>

                      <div className="space-y-2">
                        {(domain.key === 'customer_experience' ? domain.components : domain.components.slice(0, 5)).map((component) => (
                          <div key={component.id}>
                            <div className="flex justify-between text-[11px] mb-1">
                              <span className="text-gray-400">{component.label}</span>
                              <span className="text-gray-300 font-mono">{Math.round(component.score)}/100</span>
                            </div>
                            <div className="w-full bg-morpheus-900 h-1 rounded-full overflow-hidden">
                              <div
                                className={`${domain.barColor} h-full rounded-full`}
                                style={{ width: `${Math.max(0, Math.min(100, component.score))}%` }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
             </div>

             <div className="mt-8 pt-6 border-t border-morpheus-700">
                 <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                    <History size={14} /> Recent Events
                 </h3>
                 <div className="space-y-4">
                     {recentActivity.length === 0 && (
                       <div className="text-xs text-gray-500">No recent activity events available from connected sources.</div>
                     )}
                     {recentActivity.map((event, index) => (
                       <div key={`${event.timestamp || 'event'}-${index}`} className="flex gap-3 items-start">
                         <div className={`w-1.5 h-1.5 rounded-full mt-1.5 ${
                           event.sentiment === 'positive'
                             ? 'bg-emerald-500'
                             : event.sentiment === 'negative'
                               ? 'bg-red-500'
                               : 'bg-gray-600'
                         }`}></div>
                         <div>
                           <p className="text-xs text-gray-300">{event.subject || event.type || 'Activity event'}</p>
                           <span className="text-[10px] text-gray-500">
                             {event.timestamp || 'Unknown time'}{event.channel ? ` • ${event.channel}` : ''}
                           </span>
                         </div>
                       </div>
                     ))}
                 </div>
             </div>
        </div>

      </div>
    </div>
  );
};

export default Customer360;
