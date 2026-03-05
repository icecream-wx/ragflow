import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

/** 上传文件到知识库（multipart/form-data） */
export const uploadFilesToKnowledge = async (files: File[]) => {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const res = await api.post<{ data: { uploaded: number; chunks: number; files: string[] } }>(
    '/knowledge/upload',
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  )
  return res.data
}

/** 知识库统计（当前向量库片段数） */
export const getKnowledgeStats = async () => {
  const res = await api.get<{ data: { chunk_count: number } }>('/knowledge/stats')
  return res.data
}

/** 支持的文件扩展名 */
export const getAllowedExtensions = async () => {
  const res = await api.get<{ data: { extensions: string[] } }>('/knowledge/allowed-extensions')
  return res.data
}
