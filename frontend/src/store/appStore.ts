import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  isDarkMode: boolean;
  isSidebarCollapsed: boolean;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      isDarkMode: false,
      isSidebarCollapsed: false,
      toggleDarkMode: () =>
        set((state) => {
          const newMode = !state.isDarkMode;
          if (newMode) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
          return { isDarkMode: newMode };
        }),
      toggleSidebar: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      setSidebarCollapsed: (collapsed) =>
        set({ isSidebarCollapsed: collapsed }),
    }),
    {
      name: 'app-storage',
      onRehydrateStorage: () => (state) => {
        if (state?.isDarkMode) {
          document.documentElement.classList.add('dark');
        }
      },
    }
  )
);
