import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// ============ 类型定义 ============

export interface Library {
  id: string
  name: string
  description?: string
  source_path: string
  document_count: number
  chunk_count: number
  created_at?: string
  updated_at?: string
}

export interface QueryResult {
  content: string
  score: number
  source: string
  library_id: string
}

export interface ScanProgress {
  library_id: string
  status: 'pending' | 'scanning' | 'embedding' | 'completed' | 'failed'
  total_files: number
  processed_files: number
  message?: string
}

// ============ API 函数 ============

// 库管理
export const listLibraries = () => api.get<{ libraries: Library[] }>('/libraries').then(r => r.data)

export const createLibrary = (data: { name: string; source_path: string; description?: string }) =>
  api.post<Library>('/libraries', data).then(r => r.data)

export const getLibrary = (libraryId: string) =>
  api.get<Library>(`/libraries/${libraryId}`).then(r => r.data)

export const deleteLibrary = (libraryId: string) =>
  api.delete(`/libraries/${libraryId}`).then(r => r.data)

export const scanLibrary = (libraryId: string, forceRebuild: boolean = false) =>
  api.post<ScanProgress>(`/libraries/${libraryId}/scan`, { force_rebuild: forceRebuild }).then(r => r.data)

export const getScanProgress = (libraryId: string) =>
  api.get<ScanProgress>(`/libraries/${libraryId}/progress`).then(r => r.data)

export const getLibraryChunks = (libraryId: string) =>
  api.get<{ chunks: Array<{ chunk_id: string; content: string; metadata: any }>; total: number }>(`/libraries/${libraryId}/chunks`).then(r => r.data)

// RAG 查询
export const queryRag = (data: { query: string; library_id?: string; top_k?: number }) =>
  api.post<{ query: string; results: QueryResult[]; total: number }>('/rag/query', data).then(r => r.data)

// 配置
export const getChunkConfig = () =>
  api.get<{ chunk_size: number; chunk_overlap: number }>('/config/chunk').then(r => r.data)

export const updateChunkConfig = (data: { chunk_size: number; chunk_overlap: number }) =>
  api.post('/config/chunk', data).then(r => r.data)

export const getOllamaConfig = () =>
  api.get<{ base_url: string; embed_model: string }>('/config/ollama').then(r => r.data)

export const updateOllamaConfig = (data: { base_url: string; embed_model: string }) =>
  api.post('/config/ollama', data).then(r => r.data)
