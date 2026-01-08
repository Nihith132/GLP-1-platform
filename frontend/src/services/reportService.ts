import { api } from './api';
import type { Report, WorkspaceState } from '../types';

export const reportService = {
  // Get all reports
  getAllReports: async (): Promise<Report[]> => {
    const response = await api.get('/reports/');
    return response.data.reports || response.data;
  },

  // Get report by ID
  getReportById: async (id: number | string): Promise<Report> => {
    const response = await api.get(`/reports/${id}/`);
    return response.data;
  },

  // Get reports for a specific drug
  getReportsByDrug: async (drugId: number | string): Promise<Report[]> => {
    const response = await api.get(`/reports/drug/${drugId}/`);
    return response.data;
  },

  // Create a new analysis workspace report
  createReport: async (reportData: {
    title: string;
    description?: string;
    report_type: 'analysis' | 'comparison';
    workspace_state: WorkspaceState;
    tags?: string[];
  }): Promise<Report> => {
    const payload = {
      report_type: reportData.report_type,
      metadata: {
        title: reportData.title,
        type_category: 'general_analysis', // Changed to match backend validation
        description: reportData.description || '',
        tags: reportData.tags || [],
      },
      workspace_state: reportData.workspace_state,
    };
    
    const response = await api.post('/reports/create', payload);
    return response.data;
  },

  // Generate AI report (old functionality)
  generateReport: async (drugIds: number[]): Promise<Report> => {
    const response = await api.post('/reports/generate/', { drug_ids: drugIds });
    return response.data;
  },

  // Delete report
  deleteReport: async (id: number | string): Promise<void> => {
    await api.delete(`/reports/${id}/`);
  },
};
