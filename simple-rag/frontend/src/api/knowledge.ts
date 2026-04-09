import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

/** 上传文件到知识库（multipart/form-data），可选指定本次上传的分块策略 */
export const uploadFilesToKnowledge = async (files: File[], chunkStrategy?: string) => {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const params = chunkStrategy ? { chunk_strategy: chunkStrategy } : {}
  const res = await api.post<{ data: { uploaded: number; chunks: number; files: string[] } }>(
    '/knowledge/upload',
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      params
    }
  )
  return res.data
}

/** 知识库统计（片段数 + 当前分块配置） */
export interface KnowledgeStatsData {
  chunk_count: number
  chunk_size?: number
  chunk_overlap?: number
  chunk_strategy?: string
}

export const getKnowledgeStats = async () => {
  const res = await api.get<{ data: KnowledgeStatsData }>('/knowledge/stats')
  return res.data
}

/** 分块策略项 */
export interface ChunkStrategyItem {
  id: string
  name: string
  description: string
}

/** 获取当前项目支持的知识分块策略列表 */
export const getChunkStrategies = async () => {
  const res = await api.get<{ data: { strategies: ChunkStrategyItem[] } }>('/knowledge/chunk-strategies')
  return res.data
}

/** 知识片段项（含向量预览） */
export interface KnowledgeChunkItem {
  index: number
  id: string
  content: string
  metadata: Record<string, unknown>
  vector_preview: number[]
  vector_dim: number
}

/** 获取知识库所有片段详情（含分片内容与向量预览） */
export const getKnowledgeChunks = async (vectorDisplayDims: number = 10) => {
  const res = await api.get<{
    data: { chunks: KnowledgeChunkItem[]; total: number }
  }>('/knowledge/chunks', {
    params: { vector_display_dims: vectorDisplayDims }
  })
  return res.data
}

/** 支持的文件扩展名 */
export const getAllowedExtensions = async () => {
  const res = await api.get<{ data: { extensions: string[] } }>('/knowledge/allowed-extensions')
  return res.data
}
