
import React, { useState, useEffect, useRef } from 'react';
import {
    Database,
    Cloud,
    Table,
    MessageSquare,
    RefreshCcw,
    CheckCircle2,
    AlertCircle,
    ArrowUpRight,
    Loader2,
    Settings,
    Server,
    ToggleLeft,
    ToggleRight,
    Wifi,
    WifiOff,
    Plus,
    X,
    Shield,
    Key,
    FileJson,
    Upload,
    Code2,
    List,
    Box,
    ChevronRight,
    ChevronDown,
    Folder,
    FolderOpen,
    HardDrive
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { DataService } from '../services/dataService';
import { Integration } from '../types';

const LATENCY_DATA = [
    { time: '10:00', ms: 120 },
    { time: '10:05', ms: 132 },
    { time: '10:10', ms: 101 },
    { time: '10:15', ms: 145 },
    { time: '10:20', ms: 180 },
    { time: '10:25', ms: 130 },
    { time: '10:30', ms: 115 },
];

// Dataset and Table Types
interface BigQueryDataset {
    datasetId: string;
    projectId: string;
    location: string;
    created: string;
    description?: string;
}

interface BigQueryTable {
    tableId: string;
    numRows: number;
    numBytes: number;
    createdAt: string;
    modifiedAt: string;
    type: string;
}

const DataNexus: React.FC = () => {
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [loading, setLoading] = useState(true);

    // Connection Settings State
    const [showSettings, setShowSettings] = useState(false);
    const [apiUrl, setApiUrl] = useState(DataService.getApiUrl());
    const [isLive, setIsLive] = useState(DataService.isLiveMode());
    const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'failed'>('idle');
    const [statusMsg, setStatusMsg] = useState('');

    // Add Source Modal State
    const [showAddModal, setShowAddModal] = useState(false);
    const [newSourceStep, setNewSourceStep] = useState(1);
    const [bqConfig, setBqConfig] = useState({
        name: 'Marketing Data Warehouse',
        projectId: '',
        dataset: '',
        serviceAccount: '',
        serviceAccountKey: null as any,
        accessToken: ''
    });
    const [isConnecting, setIsConnecting] = useState(false);

    // Inspector Panel State
    const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
    const [inspectorTab, setInspectorTab] = useState<'tables' | 'schema'>('tables');

    // File Upload State
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [keyFileName, setKeyFileName] = useState<string | null>(null);

    // Dataset Discovery State
    const [datasets, setDatasets] = useState<BigQueryDataset[]>([]);
    const [loadingDatasets, setLoadingDatasets] = useState(false);
    const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
    const [datasetTables, setDatasetTables] = useState<Record<string, BigQueryTable[]>>({});
    const [expandedDatasets, setExpandedDatasets] = useState<Set<string>>(new Set());
    const [loadingTables, setLoadingTables] = useState<Set<string>>(new Set());

    const handleSyncAll = async () => {
        setLoading(true);
        try {
            // Trigger scan for all known sources (mocking ID for now or fetching list first)
            // For MVP, we assume 'bigquery-main' or we fetch list first.
            // Let's just fetch status which is what it was doing, but maybe add a specific scan call if needed.
            // The backend `getIntegrationStatus` does a lightweight check.
            // To force a scan, we should call /catalog/scan/{id}

            const status = await DataService.getIntegrationStatus();
            setIntegrations(status);

            // Trigger background scan for each connected source
            status.forEach(async (source) => {
                if (source.status === 'healthy' || source.status === 'connected') {
                    await DataService.request(`/platform/catalog/scan/${source.id}`, {});
                }
            });

        } catch (e) {
            console.error("Error syncing integrations", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        handleSyncAll();
    }, []);

    const handleSaveSettings = async () => {
        DataService.setApiUrl(apiUrl);
        DataService.setLiveMode(isLive);

        if (isLive) {
            setConnectionStatus('testing');
            const result = await DataService.testConnection();
            if (result.success) {
                setConnectionStatus('success');
                setStatusMsg(`Connected (${result.latency}ms)`);
            } else {
                setConnectionStatus('failed');
                setStatusMsg(result.message);
            }
        } else {
            setConnectionStatus('idle');
            setStatusMsg('');
        }

        // Reload data with new settings
        handleSyncAll();
    };

    const handleConnectBigQuery = async () => {
        setIsConnecting(true);
        try {
            await DataService.connectSource({
                type: 'bigquery',
                name: bqConfig.name,
                credentials: bqConfig
            });
            // Refresh integrations from backend to get authoritative state
            await handleSyncAll();

            // Automatically fetch datasets after successful connection
            await fetchDatasets();

            setShowAddModal(false);
            setNewSourceStep(1);
            setBqConfig({ name: 'Marketing Data Warehouse', projectId: '', dataset: '', serviceAccount: '', serviceAccountKey: null, accessToken: '' });
            setKeyFileName(null);
        } catch (e) {
            console.error(e);
        } finally {
            setIsConnecting(false);
        }
    };

    // Fetch available datasets
    const fetchDatasets = async () => {
        setLoadingDatasets(true);
        try {
            const response = await DataService.listBigQueryDatasets();
            setDatasets(response.datasets || []);
        } catch (error) {
            console.error('Failed to fetch datasets:', error);
        } finally {
            setLoadingDatasets(false);
        }
    };

    // Fetch tables for a specific dataset
    const fetchTablesForDataset = async (datasetId: string) => {
        if (datasetTables[datasetId]) {
            // Already loaded, just toggle expansion
            toggleDatasetExpansion(datasetId);
            return;
        }

        setLoadingTables(prev => new Set(prev).add(datasetId));
        try {
            const response = await DataService.listBigQueryTables(datasetId);
            setDatasetTables(prev => ({
                ...prev,
                [datasetId]: response.tables || []
            }));
            // Expand after loading
            setExpandedDatasets(prev => new Set(prev).add(datasetId));
        } catch (error) {
            console.error(`Failed to fetch tables for dataset ${datasetId}:`, error);
        } finally {
            setLoadingTables(prev => {
                const newSet = new Set(prev);
                newSet.delete(datasetId);
                return newSet;
            });
        }
    };

    // Handle dataset selection
    const handleDatasetSelect = async (datasetId: string) => {
        setSelectedDataset(datasetId);
        try {
            await DataService.setActiveDataset(datasetId);
            console.log(`✓ Active dataset set to: ${datasetId}`);
        } catch (error) {
            console.error('Failed to set active dataset:', error);
        }
    };

    // Toggle dataset expansion
    const toggleDatasetExpansion = (datasetId: string) => {
        setExpandedDatasets(prev => {
            const newSet = new Set(prev);
            if (newSet.has(datasetId)) {
                newSet.delete(datasetId);
            } else {
                newSet.add(datasetId);
            }
            return newSet;
        });
    };

    // Format bytes to human readable
    const formatBytes = (bytes: number): string => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
    };

    // Format date to relative time
    const formatRelativeTime = (dateString: string): string => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    // --- File Handling Logic ---

    const processFile = (file: File) => {
        if (!file) return;

        if (file.type === "application/json" || file.name.endsWith('.json')) {
            setKeyFileName(file.name);
            const reader = new FileReader();

            reader.onload = (e) => {
                try {
                    const content = e.target?.result as string;
                    const json = JSON.parse(content);

                    // Validate it's a service account key
                    if (!json.type || json.type !== 'service_account') {
                        alert("This doesn't appear to be a valid GCP service account key file.");
                        setKeyFileName(null);
                        return;
                    }

                    // Store the complete JSON key and auto-fill fields
                    setBqConfig(prev => ({
                        ...prev,
                        projectId: json.project_id || prev.projectId,
                        serviceAccount: json.client_email || prev.serviceAccount,
                        serviceAccountKey: json
                    }));

                } catch (err) {
                    console.error("Invalid JSON content", err);
                    alert("The file content is not valid JSON.");
                    setKeyFileName(null);
                }
            };

            reader.onerror = () => {
                alert("Failed to read file.");
                setKeyFileName(null);
            };

            reader.readAsText(file);
        } else {
            alert("Please upload a valid .json key file.");
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) processFile(file);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        const file = e.dataTransfer.files?.[0];
        if (file) processFile(file);
    };

    const getIcon = (type: string) => {
        if (type === 'Data Warehouse') return <Database className="text-blue-400" />;
        if (type === 'CRM') return <Cloud className="text-blue-300" />;
        if (type === 'Spreadsheet') return <Table className="text-emerald-400" />;
        if (type === 'Sales Pipeline') return <Database className="text-purple-400" />;
        return <MessageSquare className="text-pink-400" />;
    };

    if (loading && integrations.length === 0) {
        return (
            <div className="h-screen flex flex-col items-center justify-center">
                <Loader2 className="animate-spin text-blue-500 mb-4" size={32} />
                <p className="text-xs font-mono text-gray-500">Scanning Data Pipelines...</p>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-[1600px] mx-auto space-y-6 animate-fade-in relative flex gap-6">

            {/* Main Content Area */}
            <div className={`flex-1 space-y-6 transition-all duration-300 ${selectedIntegration ? 'pr-[400px]' : ''}`}>
                {/* Modal Overlay */}
                {showAddModal && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                        <div className="bg-morpheus-800 border border-morpheus-700 rounded-xl w-full max-w-2xl shadow-2xl animate-fade-in overflow-hidden">
                            {/* Modal Header */}
                            <div className="p-6 border-b border-morpheus-700 flex justify-between items-center bg-morpheus-900/50">
                                <h2 className="text-lg font-bold text-white flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                                        <Database size={20} />
                                    </div>
                                    Connect New Data Source
                                </h2>
                                <button onClick={() => setShowAddModal(false)} className="text-gray-400 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Modal Content */}
                            <div className="p-6">
                                {/* Step 1: Selection (Simplified to just BQ for this demo) */}
                                {newSourceStep === 1 && (
                                    <div className="grid grid-cols-3 gap-4">
                                        <div
                                            onClick={() => setNewSourceStep(2)}
                                            className="border border-blue-500 bg-blue-500/10 p-4 rounded-xl cursor-pointer hover:bg-blue-500/20 transition-all text-center group"
                                        >
                                            <Database size={32} className="mx-auto text-blue-400 mb-3 group-hover:scale-110 transition-transform" />
                                            <h3 className="font-bold text-white text-sm">Google BigQuery</h3>
                                            <p className="text-[10px] text-blue-300 mt-1">Data Warehouse</p>
                                        </div>
                                        <div className="border border-morpheus-700 bg-morpheus-900/50 p-4 rounded-xl cursor-not-allowed opacity-50 text-center">
                                            <Cloud size={32} className="mx-auto text-gray-500 mb-3" />
                                            <h3 className="font-bold text-gray-400 text-sm">Salesforce</h3>
                                            <p className="text-[10px] text-gray-600 mt-1">CRM Adapter</p>
                                        </div>
                                        <div className="border border-morpheus-700 bg-morpheus-900/50 p-4 rounded-xl cursor-not-allowed opacity-50 text-center">
                                            <Table size={32} className="mx-auto text-gray-500 mb-3" />
                                            <h3 className="font-bold text-gray-400 text-sm">PostgreSQL</h3>
                                            <p className="text-[10px] text-gray-600 mt-1">SQL Database</p>
                                        </div>
                                    </div>
                                )}

                                {/* Step 2: Configuration */}
                                {newSourceStep === 2 && (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-2 text-sm text-blue-400 bg-blue-500/10 p-3 rounded-lg border border-blue-500/20 mb-4">
                                            <Shield size={16} />
                                            Credentials are encrypted using AES-256 before transmission.
                                        </div>

                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Source Name</label>
                                                <input
                                                    type="text"
                                                    value={bqConfig.name}
                                                    onChange={e => setBqConfig({ ...bqConfig, name: e.target.value })}
                                                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                                />
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="block text-xs font-bold text-gray-400 uppercase mb-1">GCP Project ID</label>
                                                    <input
                                                        type="text"
                                                        value={bqConfig.projectId}
                                                        onChange={e => setBqConfig({ ...bqConfig, projectId: e.target.value })}
                                                        placeholder="htv-data-warehouse-prod"
                                                        className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none font-mono"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Dataset Location</label>
                                                    <input
                                                        type="text"
                                                        value={bqConfig.dataset}
                                                        onChange={e => setBqConfig({ ...bqConfig, dataset: e.target.value })}
                                                        placeholder="US (multi-region)"
                                                        className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                                    />
                                                </div>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Service Account Email</label>
                                                <input
                                                    type="text"
                                                    value={bqConfig.serviceAccount}
                                                    onChange={e => setBqConfig({ ...bqConfig, serviceAccount: e.target.value })}
                                                    placeholder="morpheus-connector@htv-group.iam.gserviceaccount.com"
                                                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none font-mono"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Access Token (optional)</label>
                                                <input
                                                    type="text"
                                                    value={bqConfig.accessToken}
                                                    onChange={e => setBqConfig({ ...bqConfig, accessToken: e.target.value })}
                                                    placeholder="ya29..."
                                                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none font-mono"
                                                />
                                                <p className="text-[10px] text-gray-500 mt-1">Use a short-lived OAuth access token if no JSON key is provided.</p>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Service Account Key (JSON)</label>
                                                <div
                                                    onClick={() => fileInputRef.current?.click()}
                                                    onDragOver={handleDragOver}
                                                    onDrop={handleDrop}
                                                    className={`w-full border border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-all cursor-pointer group
                                                ${keyFileName
                                                            ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400'
                                                            : 'border-morpheus-600 bg-morpheus-900/30 text-gray-500 hover:text-gray-300 hover:border-gray-500'}
                                            `}
                                                >
                                                    <input
                                                        type="file"
                                                        ref={fileInputRef}
                                                        onChange={handleFileChange}
                                                        accept=".json"
                                                        className="hidden"
                                                    />
                                                    {keyFileName ? (
                                                        <>
                                                            <CheckCircle2 size={32} className="mb-2 text-emerald-400" />
                                                            <span className="text-xs font-bold">{keyFileName}</span>
                                                            <span className="text-[10px] text-emerald-400/70 mt-1">Credentials Parsed & Ready</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <div className="p-3 bg-morpheus-800 rounded-full mb-3 group-hover:scale-110 transition-transform">
                                                                <Upload size={20} className="text-blue-400" />
                                                            </div>
                                                            <span className="text-xs font-medium">Click to Upload or Drag .json Key</span>
                                                            <span className="text-[10px] text-gray-600 mt-1">Supports standard GCP Service Account keys</span>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Modal Footer */}
                            <div className="p-6 border-t border-morpheus-700 bg-morpheus-900/50 flex justify-between items-center">
                                {newSourceStep === 2 && (
                                    <button
                                        onClick={() => setNewSourceStep(1)}
                                        className="text-sm text-gray-400 hover:text-white"
                                    >
                                        Back
                                    </button>
                                )}
                                {newSourceStep === 1 && <span></span>}

                                {newSourceStep === 1 && (
                                    <button
                                        onClick={() => setNewSourceStep(2)}
                                        className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
                                    >
                                        Next Step
                                    </button>
                                )}

                                {newSourceStep === 2 && (
                                    <button
                                        onClick={handleConnectBigQuery}
                                        disabled={isConnecting}
                                        className="flex items-center gap-2 px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-wait"
                                    >
                                        {isConnecting ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                                        {isConnecting ? 'Verifying Handshake...' : 'Test & Connect'}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Header */}
                <div className="flex justify-between items-end border-b border-morpheus-700 pb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-3">
                            <Database className="text-blue-500" />
                            Data Nexus
                        </h1>
                        <p className="text-gray-400 text-sm">
                            Integration health monitoring and data ingestion pipelines.
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setShowSettings(!showSettings)}
                            className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium transition-colors
                        ${showSettings ? 'bg-morpheus-700 border-morpheus-600 text-white' : 'bg-morpheus-800 border-morpheus-700 text-gray-400 hover:text-white'}
                    `}
                        >
                            <Settings size={16} /> Connection
                        </button>
                        <button
                            onClick={handleSyncAll}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-600/20"
                        >
                            <RefreshCcw size={16} /> Sync All
                        </button>
                    </div>
                </div>

                {/* Connection Settings Panel */}
                {showSettings && (
                    <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6 animate-slide-down">
                        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                            <Server size={16} className="text-purple-400" />
                            Morpheus Core Connection
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                            <div className="space-y-2">
                                <label className="text-xs text-gray-400 uppercase font-bold">API Gateway URL</label>
                                <input
                                    type="text"
                                    value={apiUrl}
                                    onChange={(e) => setApiUrl(e.target.value)}
                                    className="w-full bg-morpheus-900 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                    placeholder="http://localhost:8000/api/v1"
                                />
                            </div>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setIsLive(!isLive)}
                                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors border
                                ${isLive
                                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                            : 'bg-gray-800 text-gray-400 border-gray-700'}
                            `}
                                >
                                    {isLive ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
                                    {isLive ? 'Live Production Mode' : 'Simulation Mode'}
                                </button>
                                <button
                                    onClick={handleSaveSettings}
                                    disabled={connectionStatus === 'testing'}
                                    className="flex-1 bg-morpheus-700 hover:bg-morpheus-600 text-white py-2 rounded-lg text-sm font-medium transition-colors"
                                >
                                    {connectionStatus === 'testing' ? 'Connecting...' : 'Save & Connect'}
                                </button>
                            </div>
                        </div>

                        {/* Connection Feedback */}
                        {isLive && connectionStatus !== 'idle' && (
                            <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-xs font-mono
                        ${connectionStatus === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                                    connectionStatus === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}
                    `}>
                                {connectionStatus === 'success' ? <Wifi size={14} /> : connectionStatus === 'failed' ? <WifiOff size={14} /> : <Loader2 size={14} className="animate-spin" />}
                                {statusMsg || 'Verifying handshake...'}
                            </div>
                        )}
                    </div>
                )}

                {/* Operational Dashboard */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {integrations.map((source) => (
                        <div
                            key={source.id}
                            onClick={() => setSelectedIntegration(source)}
                            className={`bg-morpheus-800 rounded-xl border p-5 transition-all group cursor-pointer relative overflow-hidden
                    ${selectedIntegration?.id === source.id ? 'border-blue-500 ring-1 ring-blue-500 shadow-lg shadow-blue-500/10' : 'border-morpheus-700 hover:border-blue-500/50'}
                `}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-morpheus-900 rounded-lg border border-morpheus-700 group-hover:border-morpheus-600 transition-colors">
                                    {getIcon(source.type)}
                                </div>
                                <div className={`px-2 py-1 rounded text-[10px] uppercase font-bold flex items-center gap-1.5 border
                        ${source.status === 'healthy' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                        source.status === 'warning' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                            'bg-blue-500/10 text-blue-400 border-blue-500/20'}
                    `}>
                                    {source.status === 'healthy' && <CheckCircle2 size={12} />}
                                    {source.status === 'warning' && <AlertCircle size={12} />}
                                    {source.status === 'syncing' && <RefreshCcw size={12} className="animate-spin" />}
                                    {source.status}
                                </div>
                            </div>

                            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
                                {source.name}
                                <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity text-blue-400" />
                            </h3>
                            <p className="text-xs text-gray-500 mb-6">{source.type}</p>

                            <div className="grid grid-cols-2 gap-4 border-t border-morpheus-700 pt-4">
                                <div>
                                    <div className="text-[10px] text-gray-500 uppercase mb-1">Last Sync</div>
                                    <div className="text-sm font-mono text-gray-200">{source.lastSync}</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-[10px] text-gray-500 uppercase mb-1">Records/Stream</div>
                                    <div className="text-sm font-mono text-gray-200">{source.records}</div>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Add New Source */}
                    <div
                        onClick={() => setShowAddModal(true)}
                        className="bg-morpheus-800/50 rounded-xl border border-dashed border-morpheus-700 p-5 flex flex-col items-center justify-center text-center hover:bg-morpheus-800 transition-colors cursor-pointer group"
                    >
                        <div className="w-12 h-12 rounded-full bg-morpheus-900 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                            <Plus className="text-gray-400 group-hover:text-white" />
                        </div>
                        <h3 className="text-sm font-bold text-gray-300 group-hover:text-white">Connect Source</h3>
                        <p className="text-xs text-gray-500 mt-1">BigQuery, REST API, or SQL</p>
                    </div>
                </div>

                {/* Available Datasets Section */}
                {datasets.length > 0 && (
                    <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <HardDrive size={16} className="text-blue-400" />
                                Available Datasets
                                <span className="text-xs font-normal text-gray-500 ml-2">
                                    ({datasets.length} dataset{datasets.length !== 1 ? 's' : ''})
                                </span>
                            </h3>
                            <button
                                onClick={fetchDatasets}
                                disabled={loadingDatasets}
                                className="flex items-center gap-2 px-3 py-1.5 bg-morpheus-700 hover:bg-morpheus-600 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                            >
                                <RefreshCcw size={14} className={loadingDatasets ? 'animate-spin' : ''} />
                                Refresh
                            </button>
                        </div>

                        {loadingDatasets ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="animate-spin text-blue-500 mr-3" size={24} />
                                <span className="text-sm text-gray-400">Loading datasets...</span>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {datasets.map((dataset) => {
                                    const isExpanded = expandedDatasets.has(dataset.datasetId);
                                    const isLoading = loadingTables.has(dataset.datasetId);
                                    const tables = datasetTables[dataset.datasetId] || [];

                                    return (
                                        <div key={dataset.datasetId} className="border border-morpheus-700 rounded-lg overflow-hidden">
                                            {/* Dataset Header */}
                                            <div
                                                onClick={() => fetchTablesForDataset(dataset.datasetId)}
                                                className="flex items-center justify-between p-4 bg-morpheus-900/50 hover:bg-morpheus-900 cursor-pointer transition-colors group"
                                            >
                                                <div className="flex items-center gap-3 flex-1">
                                                    <div className="p-2 bg-morpheus-800 rounded-lg border border-morpheus-700 group-hover:border-blue-500/30 transition-colors">
                                                        {isExpanded ? (
                                                            <FolderOpen size={16} className="text-blue-400" />
                                                        ) : (
                                                            <Folder size={16} className="text-gray-400 group-hover:text-blue-400 transition-colors" />
                                                        )}
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="text-sm font-mono font-bold text-white group-hover:text-blue-400 transition-colors">
                                                                {dataset.datasetId}
                                                            </h4>
                                                            {selectedDataset === dataset.datasetId && (
                                                                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] font-bold uppercase rounded border border-blue-500/30">
                                                                    Selected
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-3 mt-1">
                                                            <span className="text-xs text-gray-500">
                                                                📍 {dataset.location}
                                                            </span>
                                                            <span className="text-xs text-gray-600">•</span>
                                                            <span className="text-xs text-gray-500">
                                                                Created {formatRelativeTime(dataset.created)}
                                                            </span>
                                                            {dataset.description && (
                                                                <>
                                                                    <span className="text-xs text-gray-600">•</span>
                                                                    <span className="text-xs text-gray-500 italic">
                                                                        {dataset.description}
                                                                    </span>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    {!isExpanded && tables.length > 0 && (
                                                        <span className="text-xs text-gray-500 bg-morpheus-800 px-2 py-1 rounded border border-morpheus-700">
                                                            {tables.length} table{tables.length !== 1 ? 's' : ''}
                                                        </span>
                                                    )}
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDatasetSelect(dataset.datasetId);
                                                        }}
                                                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${selectedDataset === dataset.datasetId
                                                            ? 'bg-blue-500 text-white'
                                                            : 'bg-morpheus-700 text-gray-300 hover:bg-blue-500/20 hover:text-blue-400'
                                                            }`}
                                                    >
                                                        {selectedDataset === dataset.datasetId ? 'Selected' : 'Select'}
                                                    </button>
                                                    {isLoading ? (
                                                        <Loader2 size={16} className="animate-spin text-blue-400" />
                                                    ) : (
                                                        <ChevronDown
                                                            size={16}
                                                            className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                                        />
                                                    )}
                                                </div>
                                            </div>

                                            {/* Tables List */}
                                            {isExpanded && tables.length > 0 && (
                                                <div className="bg-morpheus-900/30 divide-y divide-morpheus-700/50">
                                                    {tables.map((table) => (
                                                        <div
                                                            key={table.tableId}
                                                            className="flex items-center justify-between p-3 pl-16 hover:bg-morpheus-800/50 transition-colors group"
                                                        >
                                                            <div className="flex items-center gap-3 flex-1">
                                                                <Table size={14} className="text-gray-500 group-hover:text-emerald-400 transition-colors" />
                                                                <div>
                                                                    <div className="text-sm font-mono text-gray-200 group-hover:text-white transition-colors">
                                                                        {table.tableId}
                                                                    </div>
                                                                    <div className="flex items-center gap-3 mt-0.5">
                                                                        <span className="text-[10px] text-gray-600">
                                                                            {table.numRows.toLocaleString()} rows
                                                                        </span>
                                                                        <span className="text-[10px] text-gray-700">•</span>
                                                                        <span className="text-[10px] text-gray-600">
                                                                            {formatBytes(table.numBytes)}
                                                                        </span>
                                                                        <span className="text-[10px] text-gray-700">•</span>
                                                                        <span className="text-[10px] text-gray-600">
                                                                            Modified {formatRelativeTime(table.modifiedAt)}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <span className="px-2 py-0.5 bg-morpheus-800 text-gray-400 text-[10px] font-mono rounded border border-morpheus-700">
                                                                    {table.type}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {isExpanded && tables.length === 0 && !isLoading && (
                                                <div className="p-6 text-center text-gray-500 text-sm bg-morpheus-900/30">
                                                    No tables found in this dataset
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* Latency Graph */}
                <div className="bg-morpheus-800 rounded-xl border border-morpheus-700 p-6">
                    <h3 className="text-sm font-bold text-white mb-6 flex items-center gap-2">
                        <RefreshCcw size={16} className="text-gray-400" />
                        Ingestion Latency (Global)
                    </h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={LATENCY_DATA}>
                                <defs>
                                    <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                                    itemStyle={{ color: '#E5E7EB' }}
                                />
                                <XAxis dataKey="time" stroke="#4B5563" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#4B5563" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}ms`} />
                                <Area type="monotone" dataKey="ms" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorLatency)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* --- Source Inspector Side Panel --- */}
            <div className={`fixed top-0 right-0 h-full w-[400px] bg-morpheus-800 border-l border-morpheus-700 shadow-2xl z-30 transform transition-transform duration-300 ${selectedIntegration ? 'translate-x-0' : 'translate-x-full'}`}>
                {selectedIntegration && (
                    <div className="h-full flex flex-col">
                        {/* Panel Header */}
                        <div className="p-6 border-b border-morpheus-700 bg-morpheus-900/80">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-morpheus-800 rounded-lg border border-morpheus-700">
                                        {getIcon(selectedIntegration.type)}
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-bold text-white leading-tight">{selectedIntegration.name}</h2>
                                        <p className="text-xs text-gray-400">{selectedIntegration.type}</p>
                                    </div>
                                </div>
                                <button onClick={() => setSelectedIntegration(null)} className="text-gray-500 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>
                            <div className="flex gap-2 text-xs">
                                <div className="flex-1 bg-morpheus-800 p-2 rounded border border-morpheus-700 text-center">
                                    <div className="text-gray-500 uppercase text-[10px]">Latency</div>
                                    <div className="font-mono text-emerald-400">{selectedIntegration.latency}ms</div>
                                </div>
                                <div className="flex-1 bg-morpheus-800 p-2 rounded border border-morpheus-700 text-center">
                                    <div className="text-gray-500 uppercase text-[10px]">Size</div>
                                    <div className="font-mono text-blue-400">{selectedIntegration.metadata?.datasetSize || 'N/A'}</div>
                                </div>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-morpheus-700">
                            <button
                                onClick={() => setInspectorTab('tables')}
                                className={`flex-1 py-3 text-xs font-bold uppercase tracking-wide transition-colors ${inspectorTab === 'tables' ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-500/5' : 'text-gray-500 hover:text-gray-300'}`}
                            >
                                <List size={14} className="inline mr-2 mb-0.5" /> Tables
                            </button>
                            <button
                                onClick={() => setInspectorTab('schema')}
                                className={`flex-1 py-3 text-xs font-bold uppercase tracking-wide transition-colors ${inspectorTab === 'schema' ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-500/5' : 'text-gray-500 hover:text-gray-300'}`}
                            >
                                <Code2 size={14} className="inline mr-2 mb-0.5" /> Schema
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-0">
                            {inspectorTab === 'tables' && (
                                <div className="divide-y divide-morpheus-700">
                                    {selectedIntegration.metadata?.tables.map((table) => (
                                        <div key={table.id} className="p-4 hover:bg-morpheus-700/30 transition-colors group cursor-pointer">
                                            <div className="flex justify-between items-center mb-1">
                                                <div className="flex items-center gap-2">
                                                    <Table size={14} className="text-gray-500 group-hover:text-blue-400" />
                                                    <span className="text-sm font-mono text-gray-200 group-hover:text-white">{table.id}</span>
                                                </div>
                                                <span className="text-xs text-gray-500">{table.size}</span>
                                            </div>
                                            <div className="flex justify-between items-center pl-6">
                                                <span className="text-[10px] text-gray-600">{table.rows.toLocaleString()} rows</span>
                                                <span className="text-[10px] text-gray-600">Updated: {table.lastModified}</span>
                                            </div>
                                        </div>
                                    ))}
                                    {(!selectedIntegration.metadata?.tables || selectedIntegration.metadata.tables.length === 0) && (
                                        <div className="p-8 text-center text-gray-500 text-sm">
                                            No tables detected in metadata stream.
                                        </div>
                                    )}
                                </div>
                            )}

                            {inspectorTab === 'schema' && (
                                <div className="p-4 space-y-4">
                                    {selectedIntegration.metadata?.tables.map((table) => (
                                        <div key={table.id} className="bg-morpheus-900/50 rounded-lg border border-morpheus-700 overflow-hidden">
                                            <div className="px-3 py-2 bg-morpheus-800 border-b border-morpheus-700 flex items-center gap-2">
                                                <Box size={12} className="text-blue-400" />
                                                <span className="text-xs font-bold text-gray-300">{table.id}</span>
                                            </div>
                                            <div className="divide-y divide-morpheus-700/50">
                                                {table.schema.map((field) => (
                                                    <div key={field.name} className="px-3 py-2 flex justify-between items-center">
                                                        <span className="text-xs font-mono text-emerald-400/80">{field.name}</span>
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-[10px] text-gray-500 uppercase">{field.type}</span>
                                                            {field.mode === 'REQUIRED' && <span className="w-1.5 h-1.5 rounded-full bg-red-500" title="Required"></span>}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

        </div>
    );
};

export default DataNexus;
