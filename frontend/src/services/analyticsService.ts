import { api } from './api';
import type { TrendData } from '../types';

export interface PlatformAnalytics {
  total_drugs: number;
  total_manufacturers: number;
  total_drug_types: number;
  active_labels: number;
  manufacturers: Array<{ name: string; count: number }>;
  drug_types: Array<{ name: string; count: number }>;
  last_updated: string;
}

export interface EntityStatistics {
  entity_type: string;
  count: number;
  percentage: number;
}

export interface DrugAnalytics {
  drug_id: number;
  drug_name: string;
  total_sections: number;
  total_entities: number;
  entity_breakdown: EntityStatistics[];
  most_common_entities: Array<{
    entity_type: string;
    count: number;
  }>;
}

export const analyticsService = {
  // Get platform analytics
  getPlatformAnalytics: async (): Promise<PlatformAnalytics> => {
    const response = await api.get('/analytics/platform');
    return response.data;
  },

  // Get drug-specific analytics
  getDrugAnalytics: async (drugId: number): Promise<DrugAnalytics> => {
    const response = await api.get(`/analytics/drug/${drugId}`);
    return response.data;
  },

  // Get drug trends
  getDrugTrends: async (drugId?: number): Promise<TrendData[]> => {
    const response = await api.get('/analytics/trends/', {
      params: drugId ? { drug_id: drugId } : undefined,
    });
    return response.data;
  },

  // Get version change statistics
  getVersionStats: async (): Promise<any> => {
    const response = await api.get('/analytics/version-stats/');
    return response.data;
  },

  // Get most changed sections
  getMostChangedSections: async (): Promise<any> => {
    const response = await api.get('/analytics/changed-sections/');
    return response.data;
  },
};
