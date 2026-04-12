import { create } from 'zustand'
import type { Collection, RAGStats, RAGDocument } from '@/types/rag'

interface RAGState {
  collections: Collection[]
  stats: RAGStats | null
  documents: RAGDocument[]
  uploadProgress: number
  isUploading: boolean

  setCollections: (collections: Collection[]) => void
  setStats: (stats: RAGStats) => void
  setDocuments: (documents: RAGDocument[]) => void
  setUploadProgress: (progress: number) => void
  setIsUploading: (uploading: boolean) => void
  reset: () => void
}

export const useRAGStore = create<RAGState>((set) => ({
  collections: [],
  stats: null,
  documents: [],
  uploadProgress: 0,
  isUploading: false,

  setCollections: (collections) => set({ collections }),
  setStats: (stats) => set({ stats }),
  setDocuments: (documents) => set({ documents }),
  setUploadProgress: (progress) => set({ uploadProgress: progress }),
  setIsUploading: (uploading) => set({ isUploading: uploading }),
  reset: () => set({ collections: [], stats: null, documents: [], uploadProgress: 0, isUploading: false }),
}))
