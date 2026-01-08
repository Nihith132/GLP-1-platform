import { api } from './api';
import type { Report } from '../types';

export const reportService = {
  // Get all reports
  getAllReports: async (): Promise<Report[]> => {
    const response = await api.get('/reports/');
    return response.data.reports || response.data;
  },

  // Get report by ID
  getReportById: async (id: number): Promise<Report> => {
    const response = await api.get(`/reports/${id}/`);
    return response.data;
  },

  // Get reports for a specific drug
  getReportsByDrug: async (drugId: number): Promise<Report[]> => {
    const response = await api.get(`/reports/drug/${drugId}/`);
    return response.data;
  },

  // Create a new report
  createReport: async (reportData: {
    title: string;
    content: string;
    drug_ids: number[];
  }): Promise<Report> => {
    const response = await api.post('/reports/', reportData);
    return response.data;
  },

  // Generate AI report
  generateReport: async (drugIds: number[]): Promise<Report> => {
    const response = await api.post('/reports/generate/', { drug_ids: drugIds });
    return response.data;
  },

  // Delete report
  deleteReport: async (id: number): Promise<void> => {
    await api.delete(`/reports/${id}/`);
  },
};
