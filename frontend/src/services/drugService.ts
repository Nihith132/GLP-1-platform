import { api } from './api';
import type { Drug, DrugLabel } from '../types';

export const drugService = {
  // Get all drugs
  getAllDrugs: async (): Promise<Drug[]> => {
    const response = await api.get('/drugs/');
    return response.data.drugs || response.data;
  },

  // Get drug by ID
  getDrugById: async (id: number): Promise<Drug> => {
    const response = await api.get(`/drugs/${id}/`);
    return response.data;
  },

  // Get drug by name
  getDrugByName: async (name: string): Promise<Drug> => {
    const response = await api.get(`/drugs/name/${name}/`);
    return response.data;
  },

  // Get drug label (latest version)
  getDrugLabel: async (drugId: number): Promise<DrugLabel> => {
    const response = await api.get(`/drugs/${drugId}/label/`);
    return response.data;
  },

  // Get drug label by version
  getDrugLabelVersion: async (drugId: number, version: string): Promise<DrugLabel> => {
    const response = await api.get(`/drugs/${drugId}/label/${version}/`);
    return response.data;
  },

  // Get all versions for a drug
  getDrugVersions: async (drugId: number): Promise<string[]> => {
    const response = await api.get(`/drugs/${drugId}/versions/`);
    return response.data;
  },

  // Get enabled drugs for monitoring
  getEnabledDrugs: async (): Promise<Drug[]> => {
    const response = await api.get('/drugs/enabled/');
    return response.data.drugs || response.data;
  },
};
