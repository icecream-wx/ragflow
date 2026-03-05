import axios from 'axios'

/** 对话相关请求超时时间：5 分钟 */
const CHAT_TIMEOUT_MS = 5 * 60 * 1000

const api = axios.create({
  baseURL: '/api',
  timeout: CHAT_TIMEOUT_MS
})

export interface MessageRequest {
  message: string
  session_id?: string
  use_rag?: boolean
}

/** 发送用户消息（写入会话） */
export const sendMessage = async (data: MessageRequest) => {
  const res = await api.post('/chat/send', data)
  return res.data
}

/** 获取 AI 流式响应 URL（GET /api/chat/chat，用于 SSE） */
export const getChatStreamUrl = (sessionId: string, useRag: boolean = true) => {
  return `/api/chat/chat?session_id=${encodeURIComponent(sessionId)}&use_rag=${useRag}`
}

export const getHistory = async (sessionId: string) => {
  const res = await api.get(`/chat/history/${sessionId}`)
  return res.data
}

export const getSessions = async () => {
  const res = await api.get('/chat/sessions')
  return res.data
}

export const deleteSession = async (sessionId: string) => {
  const res = await api.delete(`/chat/sessions/${sessionId}`)
  return res.data
}
