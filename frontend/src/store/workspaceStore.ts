import { create } from 'zustand';
import type { Highlight, Note, WorkspaceState, ChatMessage } from '../types';
import { reportService } from '../services/reportService';

interface WorkspaceStoreState extends WorkspaceState {
  // Actions
  addHighlight: (highlight: Omit<Highlight, 'id' | 'createdAt'>) => string;
  removeHighlight: (id: string) => void;
  updateHighlightColor: (id: string, color: 'red' | 'blue') => void;
  
  addNote: (note: Omit<Note, 'id' | 'createdAt'>) => void;
  updateNote: (id: string, content: string) => void;
  removeNote: (id: string) => void;
  
  setDrug: (drugId: number, drugName: string) => void;
  updateScrollPosition: (position: number) => void;
  
  saveAsReport: (title: string, description?: string, tags?: string[]) => Promise<void>;
  loadReport: (workspaceState: WorkspaceState) => void;
  clearWorkspace: () => void;
  syncFlaggedChats: (flaggedMessages: ChatMessage[]) => void;
  
  // UI State
  isNotesModalOpen: boolean;
  setNotesModalOpen: (open: boolean) => void;
  selectedHighlightId: string | null;
  setSelectedHighlightId: (id: string | null) => void;
}

const generateId = () => `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export const useWorkspaceStore = create<WorkspaceStoreState>((set, get) => ({
  // Initial State
  drugId: 0,
  drugName: '',
  highlights: [],
  notes: [],
  flaggedChats: [],
  scrollPosition: 0,
  isNotesModalOpen: false,
  selectedHighlightId: null,

  // Highlight Actions
  addHighlight: (highlightData) => {
    const id = generateId();
    set((state) => ({
      highlights: [
        ...state.highlights,
        {
          ...highlightData,
          id,
          createdAt: new Date().toISOString(),
        },
      ],
    }));
    return id;
  },

  removeHighlight: (id) =>
    set((state) => ({
      highlights: state.highlights.filter((h) => h.id !== id),
      notes: state.notes.filter((n) => n.highlightId !== id),
    })),

  updateHighlightColor: (id, color) =>
    set((state) => ({
      highlights: state.highlights.map((h) =>
        h.id === id ? { ...h, color } : h
      ),
    })),

  // Note Actions
  addNote: (noteData) =>
    set((state) => ({
      notes: [
        ...state.notes,
        {
          ...noteData,
          id: generateId(),
          createdAt: new Date().toISOString(),
        },
      ],
    })),

  updateNote: (id, content) =>
    set((state) => ({
      notes: state.notes.map((n) => (n.id === id ? { ...n, content } : n)),
    })),

  removeNote: (id) =>
    set((state) => ({
      notes: state.notes.filter((n) => n.id !== id),
    })),

  // Drug & Scroll
  setDrug: (drugId, drugName) => set({ drugId, drugName }),
  
  updateScrollPosition: (position) => set({ scrollPosition: position }),

  // Save/Load/Clear
  saveAsReport: async (title, description, tags) => {
    const state = get();
    
    // Convert to snake_case for backend API (backend expects snake_case)
    const workspaceState: any = {
      drug_id: state.drugId,
      drug_name: state.drugName,
      highlights: state.highlights,
      notes: state.notes,
      flaggedChats: state.flaggedChats,
      scrollPosition: state.scrollPosition,
    };

    await reportService.createReport({
      title,
      report_type: 'analysis',
      workspace_state: workspaceState,
      description: description || `Analysis report for ${state.drugName}`,
      tags: tags || [state.drugName, 'analysis'],
    });
  },

  loadReport: (workspaceState: any) => {
    // Handle both snake_case (from backend) and camelCase (internal)
    set({
      drugId: workspaceState.drug_id || workspaceState.drugId,
      drugName: workspaceState.drug_name || workspaceState.drugName,
      highlights: workspaceState.highlights || [],
      notes: workspaceState.notes || [],
      flaggedChats: workspaceState.flaggedChats || [],
      scrollPosition: workspaceState.scrollPosition || 0,
    });
  },

  clearWorkspace: () =>
    set({
      highlights: [],
      notes: [],
      flaggedChats: [],
      scrollPosition: 0,
      selectedHighlightId: null,
    }),

  // Sync flagged chats from chat store
  syncFlaggedChats: (flaggedMessages) =>
    set({ flaggedChats: flaggedMessages }),

  // UI State
  setNotesModalOpen: (open) => set({ isNotesModalOpen: open }),
  setSelectedHighlightId: (id) => set({ selectedHighlightId: id }),
}));
