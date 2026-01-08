import { create } from 'zustand';
import type { Drug } from '../types';

interface DrugState {
  drugs: Drug[];
  selectedDrugs: number[];
  setDrugs: (drugs: Drug[]) => void;
  addSelectedDrug: (drugId: number) => void;
  removeSelectedDrug: (drugId: number) => void;
  clearSelectedDrugs: () => void;
  toggleDrugSelection: (drugId: number) => void;
}

export const useDrugStore = create<DrugState>((set) => ({
  drugs: [],
  selectedDrugs: [],
  setDrugs: (drugs) => set({ drugs }),
  addSelectedDrug: (drugId) =>
    set((state) => ({
      selectedDrugs: [...state.selectedDrugs, drugId],
    })),
  removeSelectedDrug: (drugId) =>
    set((state) => ({
      selectedDrugs: state.selectedDrugs.filter((id) => id !== drugId),
    })),
  clearSelectedDrugs: () => set({ selectedDrugs: [] }),
  toggleDrugSelection: (drugId) =>
    set((state) => {
      const isSelected = state.selectedDrugs.includes(drugId);
      return {
        selectedDrugs: isSelected
          ? state.selectedDrugs.filter((id) => id !== drugId)
          : [...state.selectedDrugs, drugId],
      };
    }),
}));
