import { api } from './api';
import type { SearchResult } from '../types';

export const searchService = {
  // Semantic search across all drug labels
  semanticSearch: async (query: string, topK: number = 10): Promise<SearchResult[]> => {
    const response = await api.post('/search/semantic/', null, {
      params: { query, top_k: topK },
    });
    return response.data;
  },

  // Keyword search
  keywordSearch: async (query: string): Promise<SearchResult[]> => {
    const response = await api.post('/search/keyword/', null, {
      params: { query },
    });
    return response.data;
  },

  // Hybrid search (semantic + keyword)
  hybridSearch: async (query: string, topK: number = 10): Promise<SearchResult[]> => {
    const response = await api.post('/search/hybrid/', null, {
      params: { query, top_k: topK },
    });
    return response.data;
  },

  // Search within specific drug
  searchInDrug: async (drugId: number, query: string): Promise<SearchResult[]> => {
    const response = await api.post(`/search/drug/${drugId}/`, null, {
      params: { query },
    });
    return response.data;
  },
};
