import { create } from 'zustand'

interface NavState {
  activePage: string
  sidebarOpen: boolean
  setActivePage: (page: string) => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
}

export const useNavStore = create<NavState>((set) => ({
  activePage: 'dashboard',
  sidebarOpen: true,
  setActivePage: (page) => set({ activePage: page }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}))
