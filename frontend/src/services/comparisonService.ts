import { api } from './api';
import type { ComparisonResult } from '../types';

interface DrugSection {
  id: number;
  loinc_code: string;
  title: string;
  order: number;
  content: string;
  ner_entities: any[];
}

interface DrugWithSections {
  id: number;
  name: string;
  generic_name: string;
  manufacturer: string;
  set_id: string;
  version: number;
  is_current_version: boolean;
  status: string;
  last_updated: string;
  created_at: string;
  ner_summary: any;
  source_file: string;
  sections: DrugSection[];
}

interface CompareLoadResponse {
  source_drug: DrugWithSections;
  competitors: DrugWithSections[];
}

interface TextChange {
  change_type: 'addition' | 'deletion';
  text: string;
  start_char: number;
  end_char: number;
}

interface LexicalDiffResult {
  section_loinc: string;
  section_title: string;
  source_text: string;
  competitor_text: string;
  additions: TextChange[];
  deletions: TextChange[];
}

interface LexicalDiffResponse {
  source_drug_name: string;
  competitor_drug_name: string;
  diffs: LexicalDiffResult[];
}

interface SemanticSegment {
  text: string;
  start_char: number;
  end_char: number;
  highlight_color: 'green' | 'yellow' | 'red' | 'blue';
  underline_style?: 'wavy';
  diff_type: 'high_similarity' | 'partial_match' | 'unique_to_source' | 'omission' | 'conflict';
}

interface SemanticMatch {
  source_segment: SemanticSegment | null;
  competitor_segment: SemanticSegment | null;
  similarity_score: number | null;
  explanation: string;
}

interface SemanticDiffResult {
  section_loinc: string;
  section_title: string;
  matches: SemanticMatch[];
}

interface SemanticDiffSummary {
  total_matches: number;
  high_similarity: number;
  partial_matches: number;
  unique_to_source: number;
  omissions: number;
  conflicts: number;
}

interface SemanticDiffResponse {
  source_drug_name: string;
  competitor_drug_name: string;
  diffs: SemanticDiffResult[];
  summary: SemanticDiffSummary;
}

interface ExplainSegmentResponse {
  explanation: string;
  clinical_significance: string;
  marketing_implication: string;
  action_items: string[];
}

interface DiffCategorySummary {
  category: string;
  advantages: string[];
  gaps: string[];
  conflicts: string[];
}

interface SummarizeDiffsResponse {
  source_drug_name: string;
  competitor_drug_name: string;
  executive_summary: string;
  category_summaries: DiffCategorySummary[];
  overall_statistics: SemanticDiffSummary;
}

export const comparisonService = {
  // Load drugs for comparison workspace
  loadComparison: async (
    sourceDrugId: number,
    competitorDrugIds: number[]
  ): Promise<CompareLoadResponse> => {
    const response = await api.post('/compare/load', {
      source_drug_id: sourceDrugId,
      competitor_drug_ids: competitorDrugIds,
    });
    return response.data;
  },

  // Get lexical (text-based) differences
  getLexicalDiff: async (
    sourceDrugId: number,
    competitorDrugId: number,
    sectionLoinc?: string
  ): Promise<LexicalDiffResponse> => {
    const response = await api.post('/compare/lexical', {
      source_drug_id: sourceDrugId,
      competitor_drug_id: competitorDrugId,
      section_loinc: sectionLoinc,
    });
    return response.data;
  },

  // Get semantic (meaning-based) differences
  getSemanticDiff: async (
    sourceDrugId: number,
    competitorDrugId: number,
    sectionLoinc?: string,
    similarityThreshold: number = 0.65
  ): Promise<SemanticDiffResponse> => {
    const response = await api.post('/compare/semantic', {
      source_drug_id: sourceDrugId,
      competitor_drug_id: competitorDrugId,
      section_loinc: sectionLoinc,
      similarity_threshold: similarityThreshold,
    });
    return response.data;
  },

  // Get detailed explanation for a specific segment difference
  explainSegment: async (
    sourceDrugId: number,
    competitorDrugId: number,
    sectionLoinc: string,
    sourceText?: string,
    competitorText?: string
  ): Promise<ExplainSegmentResponse> => {
    const response = await api.post('/compare/semantic/explain', {
      source_drug_id: sourceDrugId,
      competitor_drug_id: competitorDrugId,
      section_loinc: sectionLoinc,
      source_text: sourceText,
      competitor_text: competitorText,
    });
    return response.data;
  },

  // Get executive summary of all differences
  getDiffSummary: async (
    sourceDrugId: number,
    competitorDrugId: number
  ): Promise<SummarizeDiffsResponse> => {
    const response = await api.post('/compare/semantic/summary', {
      source_drug_id: sourceDrugId,
      competitor_drug_id: competitorDrugId,
    });
    return response.data;
  },

  // Legacy methods (kept for backward compatibility)
  // Compare two drug labels
  compareDrugs: async (drugId1: number, drugId2: number): Promise<ComparisonResult> => {
    const response = await api.get('/compare/drugs/', {
      params: { drug_id_1: drugId1, drug_id_2: drugId2 },
    });
    return response.data;
  },

  // Compare specific versions of a drug
  compareVersions: async (
    drugId: number,
    version1: string,
    version2: string
  ): Promise<ComparisonResult> => {
    const response = await api.get('/compare/versions/', {
      params: {
        drug_id: drugId,
        version_1: version1,
        version_2: version2,
      },
    });
    return response.data;
  },

  // Compare multiple drugs
  compareMultipleDrugs: async (drugIds: number[]): Promise<ComparisonResult[]> => {
    const response = await api.post('/compare/multiple/', { drug_ids: drugIds });
    return response.data;
  },
};
