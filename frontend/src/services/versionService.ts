import { api } from './api';
import type { VersionCheckResult, VersionHistory } from '../types';

export const versionService = {
  // Check for new versions
  checkVersions: async (drugIds?: number[]): Promise<VersionCheckResult[]> => {
    const response = await api.post('/version-check/', {
      drug_ids: drugIds,
    });
    return response.data;
  },

  // Get version history for a drug
  getVersionHistory: async (drugId: number): Promise<VersionHistory[]> => {
    const response = await api.get(`/version-check/history/${drugId}/`);
    return response.data;
  },

  // Trigger manual version check
  triggerVersionCheck: async (drugId: number): Promise<VersionCheckResult> => {
    const response = await api.post(`/version-check/trigger/${drugId}/`);
    return response.data;
  },
};
