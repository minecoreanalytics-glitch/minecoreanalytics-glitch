
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
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

  const invoices = data.invoices || [];
  const recentPayments = invoices
    .filter(i => i.amount)
    .slice(0, 12)
    .map((i, idx) => ({ name: i.paid_date || i.due_date || String(idx+1), amount: i.amount }));

  const kpi = [
    { label: 'Status', value: (data as any).status || '—' },
    { label: 'Activity', value: (data as any).activity_level ? `${(data as any).activity_level}${typeof (data as any).days_since_last_activity === 'number' ? ` (${(data as any).days_since_last_activity}d)` : ''}` : '—' },
    { label: 'MRR', value: metrics.mrr ? `$${Math.round(metrics.mrr).toLocaleString()}` : '—' },
    { label: 'Health', value: `${Math.round(metrics.health_score)}%` },
    { label: 'Churn', value: `${Math.round(metrics.churn_probability)}%` },
    { label: 'Products', value: String((data as any).product_count ?? '—') },
  ];
  
  // CNS breakdown must be grounded in real signals.
  // If a signal is missing, keep it at 0 (no simulation).
  const hf = ((data as any)?.health_factors || {}) as {
    payment_method_score?: number;
    failed_payments_10m?: number;
    service_count?: number;
    plan_tier?: string;
    account_age_months?: number;
    timing_points?: number;
  };

  const billingScore = typeof hf.payment_method_score === 'number'
    ? Math.max(0, Math.min(100, (hf.payment_method_score / 50) * 100))
    : 0;

  const adoptionScore = typeof hf.service_count === 'number'
    ? Math.max(0, Math.min(100, (hf.service_count / 25) * 100))
    : 0;

  const stabilityScore = typeof hf.failed_payments_10m === 'number'
    ? Math.max(0, Math.min(100, 100 - (hf.failed_payments_10m * 20)))
    : 0;

  const timingScore = typeof hf.timing_points === 'number'
    ? Math.max(0, Math.min(100, (hf.timing_points / 10) * 100))
    : 0;

  const tenureScore = typeof hf.account_age_months === 'number'
    ? Math.max(0, Math.min(100, (hf.account_age_months / 24) * 100))
    : 0;

  const radarData = [
    { subject: 'Billing', A: billingScore, fullMark: 100 },
    { subject: 'Adoption', A: adoptionScore, fullMark: 100 },
    { subject: 'Stability', A: stabilityScore, fullMark: 100 },
    { subject: 'Timing', A: timingScore, fullMark: 100 },
    { subject: 'Tenure', A: tenureScore, fullMark: 100 },
  ];

  // --- Customer 360 KPIs + mini charts (portfolio-style) ---
  const healthColor = metrics.health_score >= 80 ? 'text-green-400' : metrics.health_score >= 70 ? 'text-emerald-300' : metrics.health_score >= 40 ? 'text-orange-300' : 'text-red-400';

  const invoiceChartData = (data.invoices || []).slice(0, 12).map((inv, i) => ({
    name: inv.paid_date || inv.due_date || String(i + 1),
    amount: inv.amount || 0,
  })).reverse();

  // Churn Gauge Data
  const churnRisk = metrics.churn_probability;
  const churnData = [
    { name: 'Risk', value: churnRisk },
    { name: 'Safe', value: 100 - churnRisk },
  ];
  const CHURN_COLORS = ['#EF4444', '#1F2937']; // Red for risk, dark for remaining

  return (
    <>
      {/* Customer 360 KPI Grid */}
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">{data.name}</h1>
            <div className="text-sm text-gray-400">Account ID: <span className="font-mono text-gray-200">{data.customer_id}</span></div>
            {(data as any).health_explanation && (
              <div className="text-xs text-gray-500 mt-2">Why: <span className="text-gray-300">{(data as any).health_explanation}</span></div>
            )}
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Health</div>
            <div className={`text-3xl font-bold ${healthColor}`}>{Math.round(metrics.health_score)}%</div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {kpi.map((k) => (
            <div key={k.label} className="bg-morpheus-800 border border-morpheus-700 rounded-xl p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wider">{k.label}</div>
              <div className="text-lg font-semibold text-white mt-1">{k.value}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl p-6">
            <div className="text-sm font-semibold text-white mb-3">Health Breakdown (CNS)</div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                  <Radar name="CNS" dataKey="A" stroke="#34d399" fill="#34d399" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-morpheus-800 border border-morpheus-700 rounded-2xl p-6">
            <div className="text-sm font-semibold text-white mb-3">Recent Invoice Amounts</div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={invoiceChartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="amount" fill="#60a5fa" radius={[6,6,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
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
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Health Score</div>
                    <div className="text-xl font-bold text-emerald-400 font-mono">{metrics.health_score}/100</div>
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
                    <span className="text-gray-500">Health Score</span>
                    <span className="text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded text-xs">{metrics.health_score}/100</span>
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
                      <div className="text-lg font-bold text-emerald-400 mt-1">{Math.round(metrics.cns)}/100</div>
                  </div>
              </div>
              <div className="mt-4 text-xs text-gray-500 flex justify-between">
                  <span>Data Source</span>
                  <span className="text-gray-300">BigQuery Live</span>
              </div>
           </div>

           {/* Recommendations */}
           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-5 flex flex-col h-[300px]">
              <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                 <BrainCircuit size={14} className="text-morpheus-accent" />
                 Recommended Actions
              </h3>
              <div className="space-y-3 overflow-y-auto pr-1">
                 {/* Mock recommendations for MVP - will be replaced with ML-driven insights */}
                 <div className="bg-morpheus-900/50 border-l-2 border-morpheus-accent p-3 rounded-r-lg hover:bg-morpheus-700/30 transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-bold text-morpheus-accent">UPSELL</span>
                        <ArrowRight size={12} className="text-gray-600 group-hover:text-morpheus-accent transition-colors" />
                    </div>
                    <h4 className="text-sm font-semibold text-white mb-1">High-Value Customer</h4>
                    <p className="text-xs text-gray-400 leading-relaxed">Customer shows strong engagement with MRR ${metrics.mrr?.toLocaleString()}. Consider premium tier upgrade.</p>
                 </div>
                 <div className="bg-morpheus-900/50 border-l-2 border-blue-500 p-3 rounded-r-lg hover:bg-morpheus-700/30 transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-bold text-blue-400">RETENTION</span>
                        <ArrowRight size={12} className="text-gray-600 group-hover:text-blue-400 transition-colors" />
                    </div>
                    <h4 className="text-sm font-semibold text-white mb-1">Schedule Check-In</h4>
                    <p className="text-xs text-gray-400 leading-relaxed">Health score at {Math.round(metrics.health_score)}. Proactive outreach recommended.</p>
                 </div>
              </div>
           </div>
        </div>

        {/* Middle: Health Score & Churn Analysis */}
        <div className="space-y-6">
            <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6 flex flex-col items-center">
                 <h3 className="text-xs font-bold text-gray-400 mb-6 uppercase tracking-widest w-full text-left">Customer Health Score</h3>
                 <div className="relative w-64 h-64 flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={[
                                    { name: 'Health', value: metrics.health_score },
                                    { name: 'Risk', value: 100 - metrics.health_score }
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
                        <span className="text-6xl font-bold text-emerald-400">{Math.round(metrics.health_score)}</span>
                        <span className="text-sm text-gray-400 mt-2">Health Score</span>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4 w-full mt-6">
                    <div className="text-center p-3 bg-morpheus-900 rounded-lg">
                        <div className="text-2xl font-bold text-emerald-400">{Math.round(metrics.cns)}</div>
                        <div className="text-[10px] text-gray-500 uppercase">CNS Score</div>
                    </div>
                    <div className="text-center p-3 bg-morpheus-900 rounded-lg">
                        <div className="text-2xl font-bold text-emerald-400">{churnRisk < 30 ? 'LOW' : churnRisk < 50 ? 'MED' : 'HIGH'}</div>
                        <div className="text-[10px] text-gray-500 uppercase">Risk Category</div>
                    </div>
                </div>
           </div>

           <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6 flex flex-col items-center">
                 <h3 className="text-xs font-bold text-gray-400 mb-6 uppercase tracking-widest w-full text-left">Score Breakdown (CNS)</h3>
                 <div className="h-[280px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                            <PolarGrid stroke="#374151" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                            <Radar
                                name="Score"
                                dataKey="A"
                                stroke="#10B981"
                                strokeWidth={2}
                                fill="#10B981"
                                fillOpacity={0.2}
                            />
                        </RadarChart>
                    </ResponsiveContainer>
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
                            Probability calculated via Logistic Regression on 248 historical churn events. Key factors: Balance, MRR, Revenue.
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
             <div className="space-y-6">
                 {/* Item 1 - Derived from overall CNS */}
                 <div className="group">
                     <div className="flex justify-between items-center mb-1">
                         <div className="flex items-center gap-2">
                             <CreditCard size={14} className="text-blue-400" />
                             <span className="text-sm font-medium text-gray-200">Billing Health</span>
                         </div>
                         <span className="text-sm font-mono text-emerald-400">{Math.round(cnsScore * 1.1)}/100</span>
                     </div>
                     <div className="w-full bg-morpheus-900 h-1.5 rounded-full overflow-hidden">
                         <div className="bg-blue-500 h-full rounded-full" style={{ width: `${Math.min(100, cnsScore * 1.1)}%` }}></div>
                     </div>
                     <p className="text-[10px] text-gray-500 mt-1 pl-6">Weight: 30% • Status: Good</p>
                 </div>

                 {/* Item 2 */}
                 <div className="group">
                     <div className="flex justify-between items-center mb-1">
                         <div className="flex items-center gap-2">
                             <Signal size={14} className="text-purple-400" />
                             <span className="text-sm font-medium text-gray-200">Service Stability</span>
                         </div>
                         <span className="text-sm font-mono text-emerald-400">{Math.round(cnsScore * 0.95)}/100</span>
                     </div>
                     <div className="w-full bg-morpheus-900 h-1.5 rounded-full overflow-hidden">
                         <div className="bg-purple-500 h-full rounded-full" style={{ width: `${Math.min(100, cnsScore * 0.95)}%` }}></div>
                     </div>
                     <p className="text-[10px] text-gray-500 mt-1 pl-6">Weight: 25% • Status: Stable</p>
                 </div>

                 {/* Item 3 */}
                 <div className="group">
                     <div className="flex justify-between items-center mb-1">
                         <div className="flex items-center gap-2">
                             <TrendingUp size={14} className="text-amber-400" />
                             <span className="text-sm font-medium text-gray-200">Equipment Health</span>
                         </div>
                         <span className="text-sm font-mono text-emerald-400">{Math.round(cnsScore * 1.05)}/100</span>
                     </div>
                     <div className="w-full bg-morpheus-900 h-1.5 rounded-full overflow-hidden">
                         <div className="bg-amber-500 h-full rounded-full" style={{ width: `${Math.min(100, cnsScore * 1.05)}%` }}></div>
                     </div>
                     <p className="text-[10px] text-gray-500 mt-1 pl-6">Weight: 20% • Status: Optimal</p>
                 </div>

                 {/* Item 4 */}
                 <div className="group">
                     <div className="flex justify-between items-center mb-1">
                         <div className="flex items-center gap-2">
                             <MessageSquare size={14} className="text-pink-400" />
                             <span className="text-sm font-medium text-gray-200">Interaction Quality</span>
                         </div>
                         <span className="text-sm font-mono text-emerald-400">{Math.round(cnsScore * 0.9)}/100</span>
                     </div>
                     <div className="w-full bg-morpheus-900 h-1.5 rounded-full overflow-hidden">
                         <div className="bg-pink-500 h-full rounded-full" style={{ width: `${Math.min(100, cnsScore * 0.9)}%` }}></div>
                     </div>
                     <p className="text-[10px] text-gray-500 mt-1 pl-6">Weight: 25% • Status: Positive</p>
                 </div>
             </div>

             <div className="mt-8 pt-6 border-t border-morpheus-700">
                 <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                    <History size={14} /> Recent Events
                 </h3>
                 <div className="space-y-4">
                     {[1,2,3].map((i) => (
                         <div key={i} className="flex gap-3 items-start">
                             <div className="w-1.5 h-1.5 rounded-full bg-gray-600 mt-1.5"></div>
                             <div>
                                 <p className="text-xs text-gray-300">Ticket #4829 closed with positive feedback.</p>
                                 <span className="text-[10px] text-gray-500">2 hours ago • Salesforce</span>
                             </div>
                         </div>
                     ))}
                 </div>
             </div>
        </div>

      </div>
    </div>
    </>
  );
};

export default Customer360;
