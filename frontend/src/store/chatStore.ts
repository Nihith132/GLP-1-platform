import { create } from 'zustand';
import type { ChatMessage } from '../types';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  toggleFlag: (messageId: string) => void;
  getFlaggedMessages: () => ChatMessage[];
  restoreMessages: (messages: ChatMessage[]) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  clearMessages: () => set({ messages: [] }),
  setLoading: (loading) => set({ isLoading: loading }),
  toggleFlag: (messageId) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, isFlagged: !msg.isFlagged } : msg
      ),
    })),
  getFlaggedMessages: () => {
    return get().messages.filter((msg) => msg.isFlagged);
  },
  restoreMessages: (messages) => set({ messages }),
}));
