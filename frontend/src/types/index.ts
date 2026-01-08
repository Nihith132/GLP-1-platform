// Drug Label Types
export interface Drug {
  id: number;
  name: string;
  set_id: string;
  manufacturer: string | null;
  version: number;
  last_updated: string;
  version_check_enabled?: boolean;
  last_version_check?: string | null;
  is_current_version?: boolean;
  generic_name?: string | null;
}

export interface DrugLabel {
  drug_id: number;
  drug_name: string;
  set_id: string;
  version: number;
  sections: LabelSection[];
}

export interface LabelSection {
  section_name: string;
  content: string;
  entities?: Entity[];
}

export interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
  score?: number;
}

// Search Types
export interface SearchResult {
  drug_id: number;
  drug_name: string;
  section_name: string;
  content: string;
  score: number;
  entities?: Entity[];
}

// Analytics Types
export interface PlatformAnalytics {
  total_drugs: number;
  total_sections: number;
  total_entities: number;
  last_updated: string;
  entity_distribution: { [key: string]: number };
}

export interface AnalyticsSummary {
  total_drugs: number;
  total_versions: number;
  recent_updates: number;
  enabled_monitoring: number;
}

export interface TrendData {
  date: string;
  count: number;
  drug_name?: string;
}

// Comparison Types
export interface ComparisonResult {
  drug1_id: number;
  drug2_id: number;
  drug1_name: string;
  drug2_name: string;
  differences: SectionDifference[];
  similarity_score: number;
}

export interface SectionDifference {
  section_name: string;
  drug1_content: string;
  drug2_content: string;
  diff_type: 'added' | 'removed' | 'modified' | 'unchanged';
  similarity: number;
}

// Report Types
export interface Report {
  id: number;
  title: string;
  report_type: 'comparison' | 'analysis' | 'search';
  created_at: string;
  updated_at: string;
  data: any;
  tags?: string[];
  notes?: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  response: string;
  sources?: {
    drug_name: string;
    section_name: string;
    relevance_score: number;
  }[];
}

// Version Checker Types
export interface VersionCheckResult {
  drug_id: number;
  drug_name: string;
  set_id: string;
  current_version: string;
  new_version?: string;
  status: 'up_to_date' | 'new_version' | 'error';
  publish_date?: string;
  error?: string;
  has_update?: boolean;
  changes?: string;
}

export interface VersionHistory {
  id: number;
  drug_id: number;
  old_version: string;
  new_version: string;
  detected_at: string;
  publish_date?: string;
  s3_key?: string;
  processed: boolean;
}
