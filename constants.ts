import { FullCustomerView, ActionItem } from './types';

export const MOCK_CUSTOMER_ID = "1000070019";

export const MOCK_CUSTOMER_DATA: FullCustomerView = {
  profile: {
    id: MOCK_CUSTOMER_ID,
    name: "HTV Group Headquarters",
    entity: "htv_group",
    status: "Active",
    address: "742 Evergreen Terrace, Springfield",
    contact_email: "admin@htvgroup.com",
    since: "2021-03-15",
    plan: "Enterprise Fibre 10G",
    mrr: 2178.50
  },
  billing: {
    balance: 0.00,
    currency: "USD",
    last_payment: "2023-10-01",
    status: "Current"
  },
  service: {
    uptime: 99.99,
    last_outage: null,
    active_devices: 142
  },
  analytics: {
    health_score: 100,
    cns_score: 98.4,
    churn_probability: 0.01,
    risk_category: "Safe",
    components: {
      billing_health: { score: 100, weight: 0.30, status: 'Safe' },
      service_stability: { score: 100, weight: 0.25, status: 'Safe' },
      equipment_health: { score: 92, weight: 0.20, status: 'Safe' },
      interaction_quality: { score: 100, weight: 0.25, status: 'Safe' }
    }
  },
  recommendations: [
    {
      id: "REC-001",
      type: "upsell",
      priority: "medium",
      title: "Suggest SLA Upgrade",
      description: "Client usage patterns indicate high dependency on uptime. Propose Premium SLA package."
    },
    {
      id: "REC-002",
      type: "retention",
      priority: "low",
      title: "Quarterly Review",
      description: "Schedule Q4 review to discuss 2024 expansion plans."
    }
  ]
};

export const SYSTEM_LOGS = [
  { id: 1, source: 'BigQuery', event: 'Billing Sync Complete', time: '10:42 AM', status: 'success' },
  { id: 2, source: 'Salesforce', event: 'Case #4922 Updated', time: '10:41 AM', status: 'info' },
  { id: 3, source: 'Morpheus Engine', event: 'Knowledge Graph Re-index', time: '10:38 AM', status: 'success' },
  { id: 4, source: 'Google Sheets', event: 'NOC Equipment Pull', time: '10:35 AM', status: 'success' },
  { id: 5, source: 'Kommo', event: 'Lead Status Change', time: '10:30 AM', status: 'warning' },
];

export const MOCK_ACTIONS: ActionItem[] = [
  {
    id: "ACT-8821",
    type: "outreach",
    priority: "high",
    title: "Initiate Retention Protocol",
    description: "Customer showing multiple churn signals. Schedule executive check-in.",
    customer: "Cyberdyne Systems",
    reason: "Usage drop (-45%) + Negative NPS",
    confidence: 92,
    status: "pending",
    timestamp: "2023-10-25 09:42:00"
  },
  {
    id: "ACT-8822",
    type: "billing",
    priority: "medium",
    title: "Review SLA Credits",
    description: "Auto-calculate downtime credits for outage #9921.",
    customer: "Tyrell Corp",
    reason: "SLA Breach > 4h",
    confidence: 88,
    status: "pending",
    timestamp: "2023-10-25 10:15:00"
  },
  {
    id: "ACT-8823",
    type: "system",
    priority: "low",
    title: "Optimization Suggestion",
    description: "Recommend bandwidth upgrade based on peak utilization.",
    customer: "Massive Dynamic",
    reason: "Link saturation > 90% for 5 days",
    confidence: 75,
    status: "executed",
    timestamp: "2023-10-24 14:20:00"
  }
];