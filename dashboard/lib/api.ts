const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'demo-key-123';

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Stats
export interface PlatformStats {
  total_wallets: number;
  total_transactions: number;
  total_volume_avax: number;
  whale_count: number;
  bot_count: number;
  dex_user_count: number;
  blocks_indexed: number;
}

export const getStats = () => fetchAPI<PlatformStats>('/api/v1/stats');

// Wallets
export interface WalletProfile {
  wallet_address: string;
  total_txs: number;
  volume_avax: number;
  is_whale: boolean;
  is_bot: boolean;
  is_dex_user: boolean;
  first_seen: string;
  last_seen: string;
}

export interface WalletsResponse {
  wallets: WalletProfile[];
  total: number;
  page: number;
  limit: number;
}

export const getWallets = (page = 1, limit = 20, filters?: { whale?: boolean; bot?: boolean; dex_user?: boolean }) => {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (filters?.whale) params.append('whale', 'true');
  if (filters?.bot) params.append('bot', 'true');
  if (filters?.dex_user) params.append('dex_user', 'true');
  return fetchAPI<WalletsResponse>(`/api/v1/wallets?${params}`);
};

export const getWallet = (address: string) => fetchAPI<{ wallet: WalletProfile }>(`/api/v1/wallets/${address}`);

interface Transaction {
  hash: string;
  value: string;
  from_address: string;
  to_address: string;
  timestamp: string;
}

export const getWalletTransactions = (address: string, limit = 20) => 
  fetchAPI<{ transactions: Transaction[] }>(`/api/v1/wallets/${address}/transactions?limit=${limit}`);

// Cohorts
export interface Cohort {
  cohort_name: string;
  wallet_count: number;
  avg_volume_avax: number;
  avg_txs: number;
  whale_count?: number;
}

export interface CohortsResponse {
  cohorts: Cohort[];
  total_cohorts: number;
}

export const getCohorts = () => fetchAPI<CohortsResponse>('/api/v1/cohorts');

export const getCohortWallets = (cohortName: string, limit = 50) =>
  fetchAPI<{ cohort: string; wallets: WalletProfile[] }>(`/api/v1/cohorts/${encodeURIComponent(cohortName)}/wallets?limit=${limit}`);

// Patterns
export interface PatternData {
  period_days: number;
  analyzed_at: string;
  patterns: {
    accumulators: Array<{ address: string; net_flow_avax: number; receive_count: number; send_count: number }>;
    distributors: Array<{ address: string; net_flow_avax: number; send_count: number; receive_count: number }>;
    high_frequency: Array<{ address: string; tx_count: number; volume_avax: number }>;
    new_whales: Array<{ address: string; volume_avax: number; tx_count: number; first_seen: string }>;
  };
  summary: {
    accumulators_count: number;
    distributors_count: number;
    high_frequency_count: number;
    new_whales_count: number;
  };
}

export const analyzePatterns = (days = 7) =>
  fetchAPI<PatternData>(`/api/v1/patterns/analyze?days=${days}`, { method: 'POST' });

export interface HeatmapData {
  period_days: number;
  total_transactions: number;
  heatmap: {
    data: number[][];
    rows: string[];
    columns: string[];
  };
  insights: {
    peak_day: string;
    peak_hour: string;
    peak_activity: number;
    busiest_day: string;
    busiest_hour: string;
    best_posting_times: Array<{ day: string; hour: string; activity: number }>;
  };
}

export const getHeatmap = (days = 30) => fetchAPI<HeatmapData>(`/api/v1/patterns/heatmap?days=${days}`);

export interface TrendsData {
  period_days: number;
  comparison: string;
  trends: Array<{
    metric: string;
    current: number;
    previous: number;
    change_percent: number;
    direction: 'up' | 'down';
  }>;
  insights: string[];
  summary: {
    active_whales: number;
    total_trends_up: number;
    total_trends_down: number;
  };
}

export const getTrends = (days = 7) => fetchAPI<TrendsData>(`/api/v1/patterns/trends?days=${days}`);

// ICP Generator
export interface ICPRequest {
  protocol_name: string;
  protocol_description: string;
  target_audience?: string;
}

export interface ICPResponse {
  protocol: string;
  icp: {
    name: string;
    description: string;
    criteria: {
      min_transaction_count: number;
      min_volume_usd: number;
      wallet_age_days: number;
      required_behaviors: string[];
      excluded_behaviors: string[];
    };
    outreach_strategy: string;
  };
  matching_wallets: number;
  generated_at: string;
}

export const generateICP = (data: ICPRequest) =>
  fetchAPI<ICPResponse>('/api/v1/icp/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// ICP Campaign Post
export interface ICPCampaignRequest {
  protocol_name: string;
  icp_name: string;
  icp_description: string;
  outreach_strategy: string;
  matching_wallets: number;
  required_behaviors: string[];
  post_type: string;
}

export interface ICPCampaignPost {
  content: string;
  character_count: number;
  intent_url: string;
  ready_to_post: boolean;
  post_type: string;
  protocol: string;
  target_audience: string;
  generated_at: string;
}

export const generateICPCampaignPost = (data: ICPCampaignRequest) =>
  fetchAPI<ICPCampaignPost>('/api/v1/icp/campaign-post', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Natural Language Search
export interface SearchRequest {
  query: string;
}

export interface SearchResponse {
  query: string;
  interpretation: {
    intent: string;
    filters: string[];
  };
  results: WalletProfile[];
  total_matches: number;
}

export const searchWallets = (query: string) =>
  fetchAPI<SearchResponse>('/api/v1/search/natural', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });

// Social Media
export interface PostTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export const getPostTemplates = () => fetchAPI<{ templates: PostTemplate[] }>('/api/v1/social/templates');

export interface GeneratePostRequest {
  post_type: string;
  custom_prompt?: string;
}

export interface GeneratedPost {
  post_type: string;
  generated: {
    content: string;
    tweets: string[];
    is_thread: boolean;
    character_count: number;
  };
  ready: {
    content: string;
    character_count: number;
    intent_url: string;
    ready_to_post: boolean;
  };
}

export const generatePost = (postType: string) =>
  fetchAPI<GeneratedPost>(`/api/v1/social/generate-ready?post_type=${postType}`, {
    method: 'POST',
  });

// Chain Stats
export interface ChainStats {
  rpc_url: string;
  chain_id: number;
  latest_block: number;
  gas_price_gwei: number;
  synced: boolean;
}

export const getChainStats = () => fetchAPI<ChainStats>('/api/v1/chain/stats');
