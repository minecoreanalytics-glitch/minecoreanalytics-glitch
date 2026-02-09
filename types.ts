
export interface CNSComponents {
  billing_health: { score: number; weight: number; status: 'Safe' | 'Watchlist' | 'At Risk' | 'Critical' };
  service_stability: { score: number; weight: number; status: 'Safe' | 'Watchlist' | 'At Risk' | 'Critical' };
  equipment_health: { score: number; weight: number; status: 'Safe' | 'Watchlist' | 'At Risk' | 'Critical' };
  interaction_quality: { score: number; weight: number; status: 'Safe' | 'Watchlist' | 'At Risk' | 'Critical' };
}

export interface CustomerProfile {
  id: string;
  name: string;
  entity: string;
  status: 'Active' | 'Suspended' | 'Churned';
  address: string;
  contact_email: string;
  since: string;
  plan: string;
  mrr: number;
}

export interface CustomerAnalytics {
  health_score: number;
  cns_score: number;
  churn_probability: number;
  risk_category: 'Safe' | 'Watchlist' | 'At Risk' | 'Critical';
  components: CNSComponents;
}

export interface CustomerRecommendation {
  id: string;
  type: 'upsell' | 'retention' | 'support' | 'billing';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
}

export interface FullCustomerView {
  profile: CustomerProfile;
  analytics: CustomerAnalytics;
  recommendations: CustomerRecommendation[];
  billing: {
    balance: number;
    currency: string;
    last_payment: string;
    status: 'Current' | 'Overdue';
  };
  service: {
    uptime: number; // percentage
    last_outage: string | null;
    active_devices: number;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: number;
  // Optional enhanced fields for SQL/Data responses
  sql?: string;
  data?: any[];
}

export interface ActionItem {
  id: string;
  type: 'outreach' | 'ticket' | 'system' | 'billing';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  customer: string;
  reason: string;
  confidence: number;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
  timestamp: string;
}

export interface SchemaField {
  name: string;
  type: string;
  mode: 'NULLABLE' | 'REQUIRED' | 'REPEATED';
}

export interface TableMetadata {
  id: string;
  rows: number;
  size: string;
  lastModified: string;
  schema: SchemaField[];
}

export interface IntegrationMetadata {
  tables: TableMetadata[];
  datasetSize?: string;
  location?: string;
}

export interface Integration {
  id: string;
  name: string;
  type: string;
  status: string;
  lastSync: string;
  records: string;
  latency: number;
  config?: any;
  metadata?: IntegrationMetadata;
}

export interface BigQueryCredentials {
  projectId?: string;
  dataset?: string;
  serviceAccount?: string;
  serviceAccountKey?: any;
  accessToken?: string;
}

export interface DataSourceConfig {
  type: 'bigquery' | 'salesforce' | 'postgres' | 'sheets';
  name: string;
  credentials: BigQueryCredentials | Record<string, any>;
}
