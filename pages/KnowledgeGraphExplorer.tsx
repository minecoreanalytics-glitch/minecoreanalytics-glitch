
import React, { useState, useEffect } from 'react';
import {
  Share2,
  Search,
  Filter,
  ZoomIn,
  ZoomOut,
  Maximize,
  Grid,
  RefreshCcw,
  RotateCcw,
  Layout,
  BookOpen,
  Settings,
  MoreVertical,
  X,
  Edit2,
  ExternalLink,
  ChevronRight,
  Loader2,
  AlertTriangle,
  Database,
  Sparkles
} from 'lucide-react';
import NetworkGraph from '../components/NetworkGraph';
import { DataService } from '../services/dataService';

// Mock data based on Screenshot 1
const MOCK_NODE_DETAILS = {
  id: "Porta",
  labels: "Porta",
  degree: 149,
  properties: {
    description: "Porta is a critical system used for billing and switching management within the core infrastructure.",
    name: "Porta",
    type: "concept",
    file: "bigquery_batch_1; bigquery_batch_3; bigquery_log_stream_active",
    c_id: "chunk-ec78342f919ac59858f25dfb648"
  },
  neighbors: [
    "Pierre Depestre",
    "Belifka Blaise",
    "Junior Fernando Sylla",
    "Banabe Mose",
    "Leconte Brunel",
    "Patrick Ganthier",
    "Jose Mickel Merise",
    "Vladimir Durandis",
    "Lafrance Lyndon Guerrier",
    "Edrice Jean",
    "Lucien Pierre",
    "Solon Paul",
    "Kerly Blain",
    "Jean Rene Lochard",
    "Cinthia Edouard",
    "Beauvais Tania"
  ]
};

const LayoutOption: React.FC<{ label: string; active?: boolean }> = ({ label, active }) => (
  <div className={`px-4 py-2 text-sm cursor-pointer transition-colors ${active ? 'bg-morpheus-700 text-white' : 'text-gray-400 hover:text-gray-200 hover:bg-morpheus-800'}`}>
    {label}
  </div>
);

const ToolbarButton: React.FC<{ icon: React.ReactNode; onClick?: () => void; active?: boolean }> = ({ icon, onClick, active }) => (
  <button
    onClick={onClick}
    className={`p-2.5 rounded-lg transition-all duration-200 border ${active
      ? 'bg-morpheus-700 text-white border-morpheus-600 shadow-[0_0_10px_rgba(59,130,246,0.2)]'
      : 'bg-morpheus-800 text-gray-400 border-morpheus-700 hover:bg-morpheus-700 hover:text-gray-200'
      }`}
  >
    {icon}
  </button>
);

const KnowledgeGraphExplorer: React.FC = () => {
  const [showLayoutMenu, setShowLayoutMenu] = useState(false);
  const [selectedLayout, setSelectedLayout] = useState('Force Directed');
  const [showNodePanel, setShowNodePanel] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<{
    isConnected: boolean;
    projectId: string | null;
    activeDataset: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<any>(null);
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [buildError, setBuildError] = useState<string | null>(null);

  // State for search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);

  useEffect(() => {
    checkConnection();
  }, []);

  // When a customer is selected, fetch their specific graph
  useEffect(() => {
    if (selectedCustomer) {
      loadGraphData(selectedCustomer);
    }
  }, [selectedCustomer]);

  const checkConnection = async () => {
    try {
      const status = await DataService.getConnectionStatus();
      setConnectionStatus(status);
    } catch (error) {
      console.error('Failed to check connection:', error);
    }
  };

  const loadGraphData = async (customerId: string) => {
    setLoading(true);
    try {
      // 1. Fetch Nodes
      const nodes = await DataService.getGraphNodes(customerId);
      // 2. Fetch Edges
      const edges = await DataService.getGraphEdges(customerId);
      // 3. Fetch Stats
      const stats = await DataService.getGraphStats(customerId);

      setGraphData({
        nodes,
        edges,
        stats
      });
      console.log(`Graph loaded for ${customerId}`, stats);
    } catch (error) {
      console.error('Failed to load graph data:', error);
      // Fallback to mock if API fails? Or just show error?
      // For now, let's show error
      setBuildError('Failed to load graph data from backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      try {
        setLoading(true);
        // For MVP, we list customers and filter or use the first one if exact match?
        // Let's assume search returns a list
        const customers = await DataService.searchCustomers(searchQuery);

        // Simple client-side Filter for MVP if backend doesn't support search param yet
        const matches = customers.filter((c: any) =>
          c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.customer_id.includes(searchQuery)
        );

        if (matches.length > 0) {
          console.log("Found customer:", matches[0]);
          setSelectedCustomer(matches[0].customer_id);
          setSearchResults(matches);
        } else {
          console.warn("No customer found");
          setBuildError(`No customer found matching "${searchQuery}"`);
          setGraphData(null); // Clear graph
        }
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setLoading(false);
      }
    }
  };


  if (loading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center space-y-4">
        <Loader2 className="animate-spin text-morpheus-accent" size={48} />
        <div className="text-sm font-mono text-gray-400 animate-pulse">Loading Knowledge Graph...</div>
      </div>
    );
  }

  if (!connectionStatus?.isConnected) {
    return (
      <div className="h-screen flex flex-col items-center justify-center space-y-6 p-6">
        <div className="bg-morpheus-800 border border-morpheus-700 rounded-xl p-8 max-w-md text-center space-y-4">
          <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto">
            <Database className="text-amber-400" size={32} />
          </div>
          <h2 className="text-xl font-bold text-white">Connect to BigQuery</h2>
          <p className="text-gray-400 text-sm">
            The Knowledge Graph Explorer requires an active BigQuery connection to visualize your data relationships.
          </p>
          <button
            onClick={() => window.location.href = '/#/data-nexus'}
            className="px-6 py-3 bg-morpheus-accent hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors w-full"
          >
            Go to Data Nexus to Connect
          </button>
        </div>
      </div>
    );
  }

  const nodeDetails = graphData || MOCK_NODE_DETAILS;

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6 animate-fade-in h-screen flex flex-col">
      {/* Page Header */}
      <div className="flex justify-between items-end border-b border-morpheus-700 pb-6 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-3">
            <Share2 className="text-morpheus-accent" />
            Morpheus Knowledge Graph
          </h1>
          <div className="flex items-center gap-3">
            <p className="text-gray-400 text-sm">
              Interactive visualization of the neural data ontology and entity relationships.
            </p>
            {connectionStatus?.isConnected && (
              <div className="flex items-center gap-2 text-[10px] text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                <span className="font-bold tracking-wider">LIVE: {connectionStatus.projectId}</span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Top Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input
              type="text"
              placeholder="Search entities (e.g. Pierre)..."
              className="bg-morpheus-800 border border-morpheus-700 text-sm rounded-lg pl-9 pr-4 py-2 text-gray-200 focus:outline-none focus:border-morpheus-accent w-64"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
            />
          </div>
        </div>
      </div>

      {/* Build Error Alert */}
      {buildError && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={20} />
          <div className="flex-1">
            <h4 className="text-red-400 font-medium text-sm mb-1">Failed to Build Graph</h4>
            <p className="text-red-300/80 text-xs">{buildError}</p>
          </div>
          <button
            onClick={() => setBuildError(null)}
            className="text-red-400 hover:text-red-300 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main Graph Container */}
      <div className="flex-1 min-h-0 bg-morpheus-900 rounded-xl border border-morpheus-700 relative overflow-hidden flex flex-col shadow-2xl">

        <NetworkGraph height={800} className="flex-1 border-0 rounded-none shadow-none" data={graphData} />

        {/* --- LEFT TOOLBAR (Screenshot 2) --- */}
        <div className="absolute top-6 left-6 flex flex-col gap-3 z-10">
          <div className="bg-morpheus-800/90 backdrop-blur-sm p-1.5 rounded-xl border border-morpheus-700 shadow-xl flex flex-col gap-2">
            <div className="relative">
              <ToolbarButton
                icon={<Grid size={20} />}
                active={showLayoutMenu}
                onClick={() => setShowLayoutMenu(!showLayoutMenu)}
              />
              {/* Layout Popup Menu */}
              {showLayoutMenu && (
                <div className="absolute left-full top-0 ml-3 w-48 bg-morpheus-800 border border-morpheus-700 rounded-lg shadow-2xl overflow-hidden py-1 z-50">
                  {['Circular', 'Circlepack', 'Random', 'Noverlaps', 'Force Directed', 'Force Atlas'].map(l => (
                    <div key={l} onClick={() => { setSelectedLayout(l); setShowLayoutMenu(false); }}>
                      <LayoutOption label={l} active={selectedLayout === l} />
                    </div>
                  ))}
                </div>
              )}
            </div>
            <ToolbarButton icon={<RefreshCcw size={20} />} />
            <ToolbarButton icon={<RotateCcw size={20} />} />
            <div className="h-px bg-morpheus-700 mx-2"></div>
            <ToolbarButton icon={<Maximize size={20} />} />
            <ToolbarButton icon={<ZoomIn size={20} />} />
            <ToolbarButton icon={<ZoomOut size={20} />} />
            <div className="h-px bg-morpheus-700 mx-2"></div>
            <ToolbarButton icon={<BookOpen size={20} />} />
            <ToolbarButton icon={<Settings size={20} />} />
          </div>
        </div>

        {/* Status Indicator (Screenshot 2 Bottom) */}
        <div className="absolute bottom-6 left-6 z-10">
          <div className="text-xs font-mono text-gray-500 bg-morpheus-900/80 px-3 py-1.5 rounded border border-morpheus-700">
            D: 3 <span className="mx-2 text-morpheus-700">|</span> Max: 1000
          </div>
        </div>

        {/* --- RIGHT NODE DETAILS PANEL (Screenshot 1) --- */}
        {showNodePanel && (
          <div className="absolute top-6 right-6 w-[380px] bg-morpheus-800/95 backdrop-blur-md border border-morpheus-700 rounded-xl shadow-2xl flex flex-col max-h-[calc(100%-3rem)] z-10 animate-fade-in">
            {/* Header */}
            <div className="p-4 border-b border-morpheus-700 flex justify-between items-center bg-morpheus-800/50 rounded-t-xl">
              <h3 className="font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                Node
              </h3>
              <div className="flex items-center gap-2">
                <button className="p-1.5 hover:bg-morpheus-700 rounded-lg text-gray-400 transition-colors">
                  <Share2 size={16} />
                </button>
                <button className="p-1.5 hover:bg-morpheus-700 rounded-lg text-gray-400 transition-colors" onClick={() => setShowNodePanel(false)}>
                  <X size={16} />
                </button>
              </div>
            </div>

            <div className="overflow-y-auto flex-1 p-0 custom-scrollbar">
              {/* Basic Info */}
              <div className="p-5 space-y-3 border-b border-morpheus-700/50">
                <div className="flex gap-4">
                  <span className="text-xs font-mono text-purple-400 w-16 uppercase">ID</span>
                  <span className="text-sm text-white font-medium">: {nodeDetails.id}</span>
                </div>
                <div className="flex gap-4">
                  <span className="text-xs font-mono text-purple-400 w-16 uppercase">Labels</span>
                  <span className="text-sm text-white font-medium">: {nodeDetails.labels}</span>
                </div>
                <div className="flex gap-4">
                  <span className="text-xs font-mono text-purple-400 w-16 uppercase">Degree</span>
                  <span className="text-sm text-white font-medium">: {nodeDetails.degree}</span>
                </div>
              </div>

              {/* Properties */}
              <div className="p-5 border-b border-morpheus-700/50">
                <h4 className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4">Properties</h4>
                <div className="space-y-4">
                  <div className="space-y-1">
                    <div className="flex justify-between items-center text-xs text-purple-400 font-mono">
                      <span>Description</span>
                      <Edit2 size={10} className="text-gray-600 cursor-pointer hover:text-white" />
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed bg-morpheus-900/50 p-2 rounded border border-morpheus-700/50">
                      {nodeDetails.properties.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    <div className="flex gap-2 items-center">
                      <span className="text-xs text-purple-400 font-mono w-16">Name</span>
                      <span className="text-xs text-gray-400">:</span>
                      <span className="text-sm text-white">{nodeDetails.properties.name}</span>
                    </div>
                    <div className="flex gap-2 items-center">
                      <span className="text-xs text-purple-400 font-mono w-16">Type</span>
                      <span className="text-xs text-gray-400">:</span>
                      <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {nodeDetails.properties.type}
                      </span>
                    </div>
                    <div className="flex gap-2 items-start">
                      <span className="text-xs text-purple-400 font-mono w-16 mt-0.5">File</span>
                      <span className="text-xs text-gray-400 mt-0.5">:</span>
                      <span className="text-xs text-gray-400 break-words flex-1">
                        {nodeDetails.properties.file}
                      </span>
                    </div>
                    <div className="flex gap-2 items-center">
                      <span className="text-xs text-purple-400 font-mono w-16">C-ID</span>
                      <span className="text-xs text-gray-400">:</span>
                      <span className="text-xs text-gray-500 font-mono truncate w-40">
                        {nodeDetails.properties.c_id}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Relations */}
              <div className="p-5 pb-8">
                <h4 className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-4">Relations (within subgraph)</h4>
                <div className="space-y-1 bg-morpheus-900/30 rounded-lg p-1">
                  {nodeDetails.neighbors.map((neighbor: string, idx: number) => (
                    <div key={idx} className="flex gap-3 items-center p-2 hover:bg-morpheus-700/50 rounded transition-colors cursor-pointer group">
                      <span className="text-xs font-mono text-purple-400 opacity-60 group-hover:opacity-100">Neigh</span>
                      <span className="text-xs text-gray-500">:</span>
                      <span className="text-sm text-gray-300 group-hover:text-white truncate flex-1">{neighbor}</span>
                      <ChevronRight size={12} className="text-gray-700 group-hover:text-gray-400 opacity-0 group-hover:opacity-100" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraphExplorer;
