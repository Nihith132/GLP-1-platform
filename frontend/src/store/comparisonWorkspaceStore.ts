import { create } from 'zustand';
import { reportService } from '@/services/reportService';
import type { Report } from '@/types';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface Highlight {
  id: string;
  text: string;
  color: string;
  position: {
    start: number;
    end: number;
  };
  sectionId?: string;
  created_at: string;
}

interface Note {
  id: string;
  content: string;
  highlightId?: string;  // If linked to a highlight (cited note)
  created_at: string;
  updated_at: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  question?: string;  // Original question for context
}

// ============================================================================
// STORE INTERFACE
// ============================================================================

interface ComparisonWorkspaceStore {
  // ========== DRUGS ==========
  sourceDrugId: number | null;
  sourceDrugName: string;
  competitorDrugIds: number[];
  competitorDrugNames: string[];
  selectedCompetitorIndex: number;
  
  // ========== HIGHLIGHTS (Source Drug Only) ==========
  sourceHighlights: Highlight[];
  
  // ========== NOTES (Quick Notes Panel) ==========
  citedNotes: Note[];      // Notes linked to highlights
  uncitedNotes: Note[];    // Standalone notes
  
  // ========== FLAGGED CHATS (RAG Chatbot) ==========
  flaggedChats: ChatMessage[];
  
  // ========== ⭐ NEW: STARRED SEMANTIC DIFFERENCES ==========
  starredDiffIds: string[];  // IDs like "34089-3_match_5"
  
  // ========== ⭐ NEW: EXECUTIVE SUMMARY HIGHLIGHTS ==========
  executiveSummaryHighlights: Highlight[];
  executiveSummaryCitedNotes: Note[];  // Notes from exec summary highlights
  
  // ========== UI STATE ==========
  activeSection: string | null;
  scrollPositions: {
    source: number;
    competitor: number;
  };
  showDifferencesPanel: boolean;
  
  // ========== ACTIONS: DRUGS ==========
  setComparisonDrugs: (
    sourceId: number,
    sourceName: string,
    competitorIds: number[],
    competitorNames: string[]
  ) => void;
  setSelectedCompetitorIndex: (index: number) => void;
  
  // ========== ACTIONS: HIGHLIGHTS ==========
  addSourceHighlight: (highlight: Highlight) => void;
  removeSourceHighlight: (id: string) => void;
  updateSourceHighlight: (id: string, updates: Partial<Highlight>) => void;
  
  // ========== ACTIONS: NOTES ==========
  addCitedNote: (note: Note, highlightId: string) => void;
  addUncitedNote: (note: Note) => void;
  updateNote: (id: string, content: string) => void;
  deleteNote: (id: string) => void;
  
  // ========== ACTIONS: CHATS ==========
  flagChat: (chat: ChatMessage) => void;
  unflagChat: (chatId: string) => void;
  
  // ========== ACTIONS: ⭐ NEW SEMANTIC DIFFS ==========
  toggleStarDiff: (diffId: string) => void;
  setStarredDiffs: (diffIds: string[]) => void;
  
  // ========== ACTIONS: ⭐ NEW EXECUTIVE SUMMARY ==========
  addExecutiveSummaryHighlight: (highlight: Highlight) => void;
  removeExecutiveSummaryHighlight: (id: string) => void;
  addExecutiveSummaryCitedNote: (note: Note, highlightId: string) => void;
  
  // ========== ACTIONS: UI STATE ==========
  setActiveSection: (section: string | null) => void;
  setScrollPositions: (positions: { source: number; competitor: number }) => void;
  setShowDifferencesPanel: (show: boolean) => void;
  
  // ========== ACTIONS: REPORTS ==========
  saveAsComparisonReport: (title: string, description?: string, tags?: string[]) => Promise<void>;
  loadComparisonReport: (report: Report) => void;
  clearComparison: () => void;
}

// ============================================================================
// STORE IMPLEMENTATION
// ============================================================================

export const useComparisonWorkspaceStore = create<ComparisonWorkspaceStore>((set, get) => ({
  // ========== INITIAL STATE ==========
  sourceDrugId: null,
  sourceDrugName: '',
  competitorDrugIds: [],
  competitorDrugNames: [],
  selectedCompetitorIndex: 0,
  
  sourceHighlights: [],
  citedNotes: [],
  uncitedNotes: [],
  flaggedChats: [],
  starredDiffIds: [],
  executiveSummaryHighlights: [],
  executiveSummaryCitedNotes: [],
  
  activeSection: null,
  scrollPositions: {
    source: 0,
    competitor: 0,
  },
  showDifferencesPanel: false,
  
  // ========== DRUG ACTIONS ==========
  setComparisonDrugs: (sourceId, sourceName, competitorIds, competitorNames) =>
    set({
      sourceDrugId: sourceId,
      sourceDrugName: sourceName,
      competitorDrugIds: competitorIds,
      competitorDrugNames: competitorNames,
    }),
  
  setSelectedCompetitorIndex: (index) =>
    set({ selectedCompetitorIndex: index }),
  
  // ========== HIGHLIGHT ACTIONS ==========
  addSourceHighlight: (highlight) =>
    set((state) => ({
      sourceHighlights: [...state.sourceHighlights, highlight],
    })),
  
  removeSourceHighlight: (id) =>
    set((state) => ({
      sourceHighlights: state.sourceHighlights.filter((h) => h.id !== id),
      // Also remove associated cited notes
      citedNotes: state.citedNotes.filter((n) => n.highlightId !== id),
    })),
  
  updateSourceHighlight: (id, updates) =>
    set((state) => ({
      sourceHighlights: state.sourceHighlights.map((h) =>
        h.id === id ? { ...h, ...updates } : h
      ),
    })),
  
  // ========== NOTE ACTIONS ==========
  addCitedNote: (note, highlightId) =>
    set((state) => ({
      citedNotes: [...state.citedNotes, { ...note, highlightId }],
    })),
  
  addUncitedNote: (note) =>
    set((state) => ({
      uncitedNotes: [...state.uncitedNotes, note],
    })),
  
  updateNote: (id, content) =>
    set((state) => {
      const updatedCitedNotes = state.citedNotes.map((n) =>
        n.id === id ? { ...n, content, updated_at: new Date().toISOString() } : n
      );
      const updatedUncitedNotes = state.uncitedNotes.map((n) =>
        n.id === id ? { ...n, content, updated_at: new Date().toISOString() } : n
      );
      const updatedExecNotes = state.executiveSummaryCitedNotes.map((n) =>
        n.id === id ? { ...n, content, updated_at: new Date().toISOString() } : n
      );
      
      return {
        citedNotes: updatedCitedNotes,
        uncitedNotes: updatedUncitedNotes,
        executiveSummaryCitedNotes: updatedExecNotes,
      };
    }),
  
  deleteNote: (id) =>
    set((state) => ({
      citedNotes: state.citedNotes.filter((n) => n.id !== id),
      uncitedNotes: state.uncitedNotes.filter((n) => n.id !== id),
      executiveSummaryCitedNotes: state.executiveSummaryCitedNotes.filter((n) => n.id !== id),
    })),
  
  // ========== CHAT ACTIONS ==========
  flagChat: (chat) =>
    set((state) => ({
      flaggedChats: [...state.flaggedChats, chat],
    })),
  
  unflagChat: (chatId) =>
    set((state) => ({
      flaggedChats: state.flaggedChats.filter((c) => c.id !== chatId),
    })),
  
  // ========== ⭐ NEW: SEMANTIC DIFF ACTIONS ==========
  toggleStarDiff: (diffId) =>
    set((state) => {
      const isStarred = state.starredDiffIds.includes(diffId);
      return {
        starredDiffIds: isStarred
          ? state.starredDiffIds.filter((id) => id !== diffId)  // Unstar
          : [...state.starredDiffIds, diffId],  // Star
      };
    }),
  
  setStarredDiffs: (diffIds) =>
    set({ starredDiffIds: diffIds }),
  
  // ========== ⭐ NEW: EXECUTIVE SUMMARY ACTIONS ==========
  addExecutiveSummaryHighlight: (highlight) =>
    set((state) => ({
      executiveSummaryHighlights: [...state.executiveSummaryHighlights, highlight],
    })),
  
  removeExecutiveSummaryHighlight: (id) =>
    set((state) => ({
      executiveSummaryHighlights: state.executiveSummaryHighlights.filter((h) => h.id !== id),
      // Also remove associated cited notes
      executiveSummaryCitedNotes: state.executiveSummaryCitedNotes.filter((n) => n.highlightId !== id),
    })),
  
  addExecutiveSummaryCitedNote: (note, highlightId) =>
    set((state) => ({
      executiveSummaryCitedNotes: [...state.executiveSummaryCitedNotes, { ...note, highlightId }],
    })),
  
  // ========== UI STATE ACTIONS ==========
  setActiveSection: (section) =>
    set({ activeSection: section }),
  
  setScrollPositions: (positions) =>
    set({ scrollPositions: positions }),
  
  setShowDifferencesPanel: (show) =>
    set({ showDifferencesPanel: show }),
  
  // ========== REPORT ACTIONS ==========
  
  /**
   * ⭐ CRITICAL: Save Comparison Report
   * Converts all state to snake_case for backend compatibility
   */
  saveAsComparisonReport: async (title, description, tags) => {
    const state = get();
    
    // ⚠️ CRITICAL: Convert to snake_case for backend
    const workspaceState: any = {
      // Drugs
      source_drug_id: state.sourceDrugId,
      source_drug_name: state.sourceDrugName,
      competitor_drug_ids: state.competitorDrugIds,
      competitor_drug_names: state.competitorDrugNames,
      selected_competitor_index: state.selectedCompetitorIndex,
      
      // User Interactions (What we save)
      source_highlights: state.sourceHighlights,
      cited_notes: state.citedNotes,
      uncited_notes: state.uncitedNotes,
      flagged_chats: state.flaggedChats,
      
      // ⭐ NEW: Starred differences (only IDs, not full data)
      starred_diff_ids: state.starredDiffIds,
      
      // ⭐ NEW: Executive summary highlights
      executive_summary_highlights: state.executiveSummaryHighlights,
      executive_summary_cited_notes: state.executiveSummaryCitedNotes,
      
      // UI State
      active_section: state.activeSection,
      scroll_positions: state.scrollPositions,
      show_differences_panel: state.showDifferencesPanel,
    };

    await reportService.createReport({
      title,
      description: description || undefined,
      report_type: 'comparison',  // ⭐ Important!
      workspace_state: workspaceState,
    });
  },
  
  /**
   * ⭐ CRITICAL: Load Comparison Report
   * Handles both snake_case and camelCase with fallbacks
   */
  loadComparisonReport: (report) => {
    const ws = report.workspace_state as any;
    
    set({
      // Drugs (handle both naming conventions)
      sourceDrugId: ws.source_drug_id ?? ws.sourceDrugId ?? null,
      sourceDrugName: ws.source_drug_name ?? ws.sourceDrugName ?? '',
      competitorDrugIds: ws.competitor_drug_ids ?? ws.competitorDrugIds ?? [],
      competitorDrugNames: ws.competitor_drug_names ?? ws.competitorDrugNames ?? [],
      selectedCompetitorIndex: ws.selected_competitor_index ?? ws.selectedCompetitorIndex ?? 0,
      
      // User Interactions
      sourceHighlights: ws.source_highlights ?? ws.sourceHighlights ?? [],
      citedNotes: ws.cited_notes ?? ws.citedNotes ?? [],
      uncitedNotes: ws.uncited_notes ?? ws.uncitedNotes ?? [],
      flaggedChats: ws.flagged_chats ?? ws.flaggedChats ?? [],
      
      // ⭐ NEW: Starred differences
      starredDiffIds: ws.starred_diff_ids ?? ws.starredDiffIds ?? [],
      
      // ⭐ NEW: Executive summary highlights
      executiveSummaryHighlights: ws.executive_summary_highlights ?? ws.executiveSummaryHighlights ?? [],
      executiveSummaryCitedNotes: ws.executive_summary_cited_notes ?? ws.executiveSummaryCitedNotes ?? [],
      
      // UI State
      activeSection: ws.active_section ?? ws.activeSection ?? null,
      scrollPositions: ws.scroll_positions ?? ws.scrollPositions ?? { source: 0, competitor: 0 },
      showDifferencesPanel: ws.show_differences_panel ?? ws.showDifferencesPanel ?? false,
    });
  },
  
  /**
   * Clear all comparison state
   */
  clearComparison: () =>
    set({
      sourceDrugId: null,
      sourceDrugName: '',
      competitorDrugIds: [],
      competitorDrugNames: [],
      selectedCompetitorIndex: 0,
      sourceHighlights: [],
      citedNotes: [],
      uncitedNotes: [],
      flaggedChats: [],
      starredDiffIds: [],
      executiveSummaryHighlights: [],
      executiveSummaryCitedNotes: [],
      activeSection: null,
      scrollPositions: { source: 0, competitor: 0 },
      showDifferencesPanel: false,
    }),
}));
