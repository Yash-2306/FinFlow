export interface Transaction {
  id: string;
  customer_id: string;
  amount: number;
  currency: string;
  merchant_category: string;
  merchant_name: string;
  transaction_type: string;
  location_city: string;
  location_country: string;
  timestamp: string;
  risk_score: number;
  is_flagged: boolean;
  flag_reasons: string[];
}

export interface Stats {
  total_transactions: number;
  total_flagged: number;
  total_volume: number;
  flag_rate: number;
  avg_amount: number;
}

export interface CategoryStat {
  category: string;
  count: number;
  total_volume: number;
  avg_amount: number;
  anomaly_count: number;
}

export interface RollingStats {
  last_60s: { count: number; flagged: number };
  last_5min: { count: number; flagged: number };
  last_1hr: { count: number; flagged: number };
}

export interface RiskBucket {
  range: string;
  count: number;
}
