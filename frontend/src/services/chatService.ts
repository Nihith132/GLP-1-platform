import { api } from './api';
import type { ChatMessage } from '../types';

export interface Citation {
  section_id: number;
  drug_name: string;
  section_title: string;
  loinc_code: string;
  chunk_text: string;
}

export interface ChatResponse {
  response: string;
  citations: Citation[];
  conversation_id?: string;
}

export const chatService = {
  // Ask question using RAG
  ask: async (request: {
    message: string;
    drug_id?: number;
    conversation_history?: any[];
  }): Promise<{ answer: string; citations: Array<{ section_name: string; drug_name: string }> }> => {
    const response = await api.post('/chat/ask', request);
    return {
      answer: response.data.response,
      citations: response.data.citations.map((c: Citation) => ({
        section_name: c.section_title,
        drug_name: c.drug_name
      }))
    };
  },

  // Send chat message and get AI response
  sendMessage: async (
    message: string,
    drugIds?: number[],
    conversationHistory?: ChatMessage[]
  ): Promise<ChatMessage> => {
    const response = await api.post('/chat/', {
      message,
      drug_ids: drugIds,
      conversation_history: conversationHistory,
    });
    return response.data;
  },

  // Ask question about specific drug
  askAboutDrug: async (
    drugId: number,
    question: string,
    conversationHistory?: ChatMessage[]
  ): Promise<ChatMessage> => {
    const response = await api.post(`/chat/drug/${drugId}/`, {
      question,
      conversation_history: conversationHistory,
    });
    return response.data;
  },
};

