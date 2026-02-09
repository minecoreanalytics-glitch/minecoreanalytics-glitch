
import { MOCK_CUSTOMER_DATA, SYSTEM_LOGS, MOCK_ACTIONS } from '../constants';
import { FullCustomerView, ActionItem, Integration, DataSourceConfig } from '../types';

// Storage keys for persisting configuration across reloads
const STORAGE_KEY_URL = 'morpheus_core_url';
const STORAGE_KEY_MODE = 'morpheus_live_mode';

// Resolve API base URL with environment override and Cloud Run fallback
const DEFAULT_API_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL)
    ? String(import.meta.env.VITE_API_BASE_URL)
    : (typeof window !== 'undefined' && window.location.host.includes('morpheus-frontend-78704783250.us-central1.run.app'))
      ? 'https://morpheus-backend-78704783250.us-central1.run.app/api/v1'
      : 'http://localhost:8000/api/v1';

/**
 * The DataService now acts as a full HTTP Client Proxy.
 * It manages the connection to the Python Morpheus Core.
 */
export const DataService = {

  // --- Configuration Management ---

  getApiUrl: (): string => {
    return localStorage.getItem(STORAGE_KEY_URL) || DEFAULT_API_URL;
  },

  setApiUrl: (url: string) => {
    localStorage.setItem(STORAGE_KEY_URL, url);
  },

  isLiveMode: (): boolean => {
    // Always use live mode when BigQuery is connected
    const mode = localStorage.getItem(STORAGE_KEY_MODE);
    return mode === null ? true : mode === 'true';
  },

  setLiveMode: (isLive: boolean) => {
    localStorage.setItem(STORAGE_KEY_MODE, String(isLive));
  },

  // --- Core Request Engine ---

  /**
   * Universal request handler with Fallback Logic.
   * 1. If Live Mode is OFF: Returns Mock Data immediately (with simulated latency).
   * 2. If Live Mode is ON: Attempts to fetch from API.
   * 3. If API fails: Logs warning and returns Mock Data (Graceful Degradation).
   */
  async request<T>(endpoint: string, mockFallback: T, method: string = 'GET', body?: any): Promise<T> {
    const baseUrl = this.getApiUrl();
    const url = `${baseUrl}${endpoint}`;

    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-Morpheus-Client': 'Web-Dashboard-v2.1'
      };

      const config: RequestInit = {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      };

      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`Morpheus Core Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data as T;

    } catch (error) {
      if (this.isLiveMode()) {
        console.warn(`[Morpheus DataService] Live mode enabled; suppressing mock fallback for ${endpoint}.`, error);
        throw error;
      }
      console.warn(`[Morpheus DataService] Connection to Core failed for ${endpoint}. Using cached/mock data.`, error);
      const delay = Math.random() * 400 + 300;
      await new Promise(resolve => setTimeout(resolve, delay));
      return mockFallback;
    }
  },

  // --- Connection Testing ---

  /**
   * Pings the Morpheus Core to verify connectivity.
   */
  testConnection: async (): Promise<{ success: boolean; message: string; latency?: number }> => {
    const start = Date.now();
    try {
      const baseUrl = DataService.getApiUrl();
      // Assuming a health endpoint exists. If not, we can catch the 404 which still proves connectivity.
      const res = await fetch(`${baseUrl}/health`, { method: 'GET', signal: AbortSignal.timeout(3000) });
      const latency = Date.now() - start;

      if (res.ok) {
        return { success: true, message: 'Morpheus Core Online', latency };
      } else {
        return { success: false, message: `Server Error: ${res.status}`, latency };
      }
    } catch (err) {
      return { success: false, message: 'Unreachable', latency: 0 };
    }
  },

  // --- Integration Management ---

  /**
   * Connects a new Data Source (like BigQuery) to the backend.
   * Sends credentials to the backend API for actual connection.
   */
  connectSource: async (config: DataSourceConfig): Promise<Integration> => {
    if (config.type === 'bigquery') {
      try {
        const connectionId = `bq-${Date.now()}`;
        // Always use live API for connections (not mock mode)
        const baseUrl = DataService.getApiUrl();
        const url = `${baseUrl}/integrations/bigquery/connect`;

        const creds = config.credentials as any;
        const hasToken = Boolean(creds?.accessToken);
        const hasKey = Boolean(creds?.serviceAccountKey);
        const credentialsPayload = hasToken
          ? {
            accessToken: creds.accessToken,
            service_account: {
              client_email: creds.serviceAccount || 'token-only@morpheus.local',
              token_uri: 'https://oauth2.googleapis.com/token'
            }
          }
          : hasKey
            ? { serviceAccountKey: creds.serviceAccountKey }
            : {
              service_account: {
                client_email: creds.serviceAccount || 'token-only@morpheus.local',
                token_uri: 'https://oauth2.googleapis.com/token'
              }
            };

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Morpheus-Client': 'Web-Dashboard-v2.1'
          },
          body: JSON.stringify({
            id: connectionId,
            projectId: creds?.projectId,
            datasetId: creds?.dataset,
            credentials: credentialsPayload,
            name: config.name
          })
        });

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Connection failed' }));
          throw new Error(error.detail || `Failed to connect: ${response.statusText}`);
        }

        const result = await response.json();

        // Return integration object
        return {
          id: connectionId,
          name: config.name,
          type: 'Data Warehouse',
          status: 'healthy',
          lastSync: 'Just now',
          records: '0',
          latency: 45,
          config: {
            project: config.credentials.projectId,
            dataset: config.credentials.dataset
          },
          metadata: {
            tables: [],
            datasetSize: "0 GB"
          }
        };
      } catch (error) {
        console.error('[Morpheus] BigQuery connection failed:', error);
        throw error;
      }
    }

    throw new Error("Unsupported Source Type");
  },

  // --- Domain Methods ---

  /**
   * GET /customer/{id}/360
   * Aggregates Billing, Salesforce, and Usage data.
   */
  getCustomer360: async (customerId: string): Promise<FullCustomerView> => {
    return DataService.request<FullCustomerView>(
      `/customer/${customerId}/360`,
      MOCK_CUSTOMER_DATA
    );
  },

  /**
   * GET /system/logs
   * Real-time logs from the ingestion pipeline.
   */
  getSystemLogs: async () => {
    return DataService.request(
      '/system/logs',
      SYSTEM_LOGS
    );
  },

  /**
   * GET /actions/pending
   * Decisions waiting for human approval.
   */
  getPendingActions: async () => {
    return DataService.request<ActionItem[]>(
      '/actions/pending',
      MOCK_ACTIONS
    );
  },

  /**
   * POST /actions/{id}/execute
   * Trigger an automated action.
   */
  executeAction: async (actionId: string, decision: 'approved' | 'rejected') => {
    // We don't need a mock return for this void/status operation, 
    // but we simulate success for the fallback.
    return DataService.request(
      `/actions/${actionId}/execute`,
      { success: true, timestamp: new Date().toISOString() },
      'POST',
      { decision }
    );
  },

  /**
   * GET /integrations/status
   * Health check for downstream adapters.
   */
  getIntegrationStatus: async () => {
    // Detailed Mock for fallback with Schema and Metadata
    const mockIntegrations: Integration[] = [
      {
        id: 'bq-main',
        name: 'Google BigQuery',
        type: 'Data Warehouse',
        status: 'healthy',
        lastSync: '45s ago',
        records: '45.2M',
        latency: 120,
        metadata: {
          datasetSize: "142.5 GB",
          location: "US-CENTRAL1",
          tables: [
            {
              id: 'customers_v2',
              rows: 25553,
              size: "124 MB",
              lastModified: "Today 10:45 AM",
              schema: [
                { name: 'customer_id', type: 'STRING', mode: 'REQUIRED' },
                { name: 'entity_name', type: 'STRING', mode: 'NULLABLE' },
                { name: 'status', type: 'STRING', mode: 'NULLABLE' },
                { name: 'mrr_amount', type: 'FLOAT', mode: 'NULLABLE' }
              ]
            },
            {
              id: 'billing_ledger_2023',
              rows: 1240500,
              size: "2.4 GB",
              lastModified: "Yesterday 11:00 PM",
              schema: [
                { name: 'transaction_id', type: 'STRING', mode: 'REQUIRED' },
                { name: 'amount', type: 'FLOAT', mode: 'REQUIRED' },
                { name: 'currency', type: 'STRING', mode: 'REQUIRED' },
                { name: 'timestamp', type: 'TIMESTAMP', mode: 'REQUIRED' }
              ]
            }
          ]
        }
      },
      {
        id: 'sf-crm',
        name: 'Salesforce CRM',
        type: 'CRM',
        status: 'healthy',
        lastSync: '2m ago',
        records: '128K',
        latency: 240,
        metadata: {
          datasetSize: "450 MB",
          tables: [
            {
              id: 'Cases',
              rows: 15420,
              size: "45 MB",
              lastModified: "Live",
              schema: [
                { name: 'CaseNumber', type: 'STRING', mode: 'REQUIRED' },
                { name: 'Status', type: 'STRING', mode: 'REQUIRED' },
                { name: 'Priority', type: 'STRING', mode: 'NULLABLE' }
              ]
            }
          ]
        }
      },
      {
        id: 'gs-ops',
        name: 'Google Sheets (NOC)',
        type: 'Spreadsheet',
        status: 'syncing',
        lastSync: 'Now',
        records: '4.2K',
        latency: 850
      },
      {
        id: 'kom-crm',
        name: 'Kommo CRM',
        type: 'Sales Pipeline',
        status: 'warning',
        lastSync: '15m ago',
        records: '12K',
        latency: 45
      },
      {
        id: 'omni-ch',
        name: 'OmniChannel Adapters',
        type: 'Communication',
        status: 'healthy',
        lastSync: 'Live',
        records: 'Stream',
        latency: 28
      },
    ];

    return DataService.request(
      '/integrations/status',
      mockIntegrations
    );
  },

  /**
   * GET /integrations/connection-status
   * Check the current BigQuery connection status
   */
  checkConnection: async () => {
    // Try to fetch from platform API first
    try {
      const datasources = await DataService.request(
        '/platform/catalog/datasources',
        []
      );

      if (datasources && datasources.length > 0) {
        const ds = datasources[0];
        return {
          connected: true,
          project_id: 'looker-studio-htv', // Hardcoded for now
          connection_name: ds.name,
          connection_id: ds.id,
          active_dataset: 'billing_data_dataset' // Hardcoded for now
        };
      }
    } catch (error) {
      console.warn('Platform API failed for connection status:', error);
    }

    // Fallback to mock
    const mockStatus = {
      connected: false,
      project_id: null,
      connection_name: "Google BigQuery",
      connection_id: "bigquery-main",
      active_dataset: null
    };

    return mockStatus;
  },

  /**
   * Get detailed connection status information
   */
  getConnectionStatus: async () => {
    try {
      const status = await DataService.checkConnection();
      return {
        isConnected: status.connected,
        projectId: status.project_id,
        connectionName: status.connection_name,
        activeDataset: status.active_dataset
      };
    } catch (error) {
      console.error('[Morpheus] Failed to get connection status:', error);
      return {
        isConnected: false,
        projectId: null,
        connectionName: null,
        activeDataset: null
      };
    }
  },

  /**
   * GET /integrations/bigquery/datasets
   * Lists all datasets in the connected BigQuery project
   */
  listBigQueryDatasets: async () => {
    // Use the new platform catalog API
    const mockDatasets = {
      projectId: 'looker-studio-htv',
      datasets: [
        {
          datasetId: 'HTVallproductssales',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'All products sales data'
        },
        {
          datasetId: 'billing_data_dataset',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'Billing data'
        },
        {
          datasetId: 'data_integration',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'Data integration'
        },
        {
          datasetId: 'htv_analytics',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'HTV analytics'
        },
        {
          datasetId: 'kommo_data',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'Kommo CRM data'
        },
        {
          datasetId: 'prepaid_alez',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'Prepaid data'
        },
        {
          datasetId: 'revenue_hainet',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'Revenue data'
        },
        {
          datasetId: 'revenue_htv',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'HTV revenue data'
        },
        {
          datasetId: 'telehaiti_dataset',
          projectId: 'looker-studio-htv',
          location: 'US',
          created: new Date().toISOString(),
          description: 'Tele Haiti data'
        }
      ],
      count: 9
    };

    // Try to fetch from platform API first
    try {
      const platformDatasets = await DataService.request(
        '/platform/catalog/datasources/bq-1764622453743/datasets',
        []
      );

      // Transform platform response to expected format
      const transformedDatasets = platformDatasets.map((ds: any) => ({
        datasetId: ds.name,
        projectId: 'looker-studio-htv',
        location: 'US',
        created: new Date().toISOString(),
        description: ds.name
      }));

      return {
        projectId: 'looker-studio-htv',
        datasets: transformedDatasets,
        count: transformedDatasets.length
      };
    } catch (error) {
      console.warn('Platform API failed, using mock data:', error);
      return mockDatasets;
    }
  },

  /**
   * GET /integrations/bigquery/datasets/{dataset_id}/tables
   * Lists all tables in a specific BigQuery dataset
   */
  listBigQueryTables: async (datasetId: string) => {
    const mockTables = {
      datasetId,
      projectId: 'looker-studio-htv',
      tables: [
        {
          tableId: 'customer_data',
          numRows: 25553,
          numBytes: 130023424,
          createdAt: new Date().toISOString(),
          modifiedAt: new Date().toISOString(),
          type: 'TABLE'
        },
        {
          tableId: 'transactions',
          numRows: 1240500,
          numBytes: 2580234240,
          createdAt: new Date().toISOString(),
          modifiedAt: new Date().toISOString(),
          type: 'TABLE'
        }
      ],
      count: 2
    };

    // Try to fetch from platform API first
    try {
      const platformTables = await DataService.request(
        `/platform/catalog/datasets/${datasetId}/tables`,
        []
      );

      // Transform platform response to expected format
      const transformedTables = platformTables.map((table: any) => ({
        tableId: table.name,
        numRows: table.num_rows || 0,
        numBytes: table.num_bytes || 0,
        createdAt: new Date().toISOString(),
        modifiedAt: new Date().toISOString(),
        type: table.type || 'TABLE'
      }));

      return {
        datasetId,
        projectId: 'looker-studio-htv',
        tables: transformedTables,
        count: transformedTables.length
      };
    } catch (error) {
      console.warn('Platform API failed, using mock data:', error);
      return mockTables;
    }
  },

  /**
   * POST /integrations/bigquery/set-dataset
   * Set the active dataset for queries
   */
  setActiveDataset: async (datasetId: string) => {
    try {
      const baseUrl = DataService.getApiUrl();
      const url = `${baseUrl}/integrations/bigquery/set-dataset`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Morpheus-Client': 'Web-Dashboard-v2.1'
        },
        body: JSON.stringify({ datasetId })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to set dataset' }));
        throw new Error(error.detail || `Failed to set dataset: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[Morpheus] Failed to set active dataset:', error);
      throw error;
    }
  },

  /**
   * GET /api/v1/customers?search={query}
   * Search for customers by name or ID.
   */
  searchCustomers: async (query: string) => {
    // Determine endpoint based on whether we are searching or listing
    // The current backend `list_customers` supports limit/offset, but maybe not search.
    // For MVP, if we don't have a search endpoint, we might have to filter client-side or add one.
    // Let's assume we can utilize listing and filter, or a new search param if we add it.
    // For now, let's use the existing list endpoint and we will rely on finding by ID if exact match.
    // OR, we can add a search query param to `list_customers` in backend later.
    return DataService.request(
      `/customers?limit=100`,
      []
    );
  },

  /**
   * GET /api/v1/graph/{id}/nodes
   */
  getGraphNodes: async (customerId: string) => {
    return DataService.request(
      `/graph/${customerId}/nodes`,
      [
        { id: "Porta", type: "concept", label: "Porta", properties: { description: "Billing System" } },
        { id: "Customer", type: "customer", label: customerId, properties: { name: "Customer" } }
      ]
    );
  },

  /**
   * GET /api/v1/graph/{id}/edges
   */
  getGraphEdges: async (customerId: string) => {
    return DataService.request(
      `/graph/${customerId}/edges`,
      [
        { from_node: "Customer", to_node: "Porta", type: "usage", strength: 0.8 }
      ]
    );
  },

  /**
  * GET /api/v1/graph/{id}/stats
  */
  getGraphStats: async (customerId: string) => {
    return DataService.request(
      `/graph/${customerId}/stats`,
      { node_count: 2, edge_count: 1, by_entity_type: { customer: 1, concept: 1 } }
    );
  }
};

