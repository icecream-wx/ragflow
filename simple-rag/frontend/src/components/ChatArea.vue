<template>
  <div class="chat-area">
    <div class="chat-messages">
      <div class="messages-inner">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-icon">🔍</div>
          <h2 class="welcome-title">基于知识库的智能问答</h2>
          <p class="welcome-desc">输入您的问题，系统将从已上传的文档中检索相关内容并生成回答。<br />请先在「知识库管理」中上传 txt、Word 等文件。</p>
          <div class="welcome-features">
            <span class="feature-tag">检索召回</span>
            <span class="feature-tag">重排序</span>
            <span class="feature-tag">流式输出</span>
            <span class="feature-tag">多轮对话</span>
          </div>
        </div>

        <template v-else>
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message-row', message.role === 'user' ? 'user' : 'assistant']"
          >
            <div class="message-bubble">
              <div v-if="message.role === 'assistant'" class="bubble-avatar">AI</div>
              <div class="bubble-content">
                <div v-if="message.role === 'assistant'" class="bubble-label">助手</div>
                <div v-else class="bubble-label user-label">我</div>
                <div v-if="message.role === 'assistant'" class="prose max-w-none">
                  <div v-if="message.isStreaming !== true" v-html="formatMarkdown(message.content)"></div>
                  <div v-else class="streaming-text">{{ message.content }}</div>
                </div>
                <div v-else class="user-text">{{ message.content }}</div>
              </div>
              <div v-if="message.role === 'user'" class="bubble-avatar user-avatar">我</div>
            </div>
          </div>

          <!-- 仅在没有“正在输入”的助手气泡时显示加载行，避免出现两个 AI 助手 -->
          <div
            v-if="loading && !lastMessageIsStreamingAssistant"
            class="message-row assistant"
          >
            <div class="message-bubble">
              <div class="bubble-avatar">AI</div>
              <div class="bubble-content loading-bubble">
                <div class="bubble-label">助手</div>
                <div class="typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="chat-input-wrap">
      <div class="chat-input-inner">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入您的问题，按 Ctrl+Enter 发送..."
          class="chat-textarea"
          resize="none"
          @keydown.ctrl.enter="handleSend"
          @keydown.meta.enter="handleSend"
        />
        <div class="input-footer">
          <span class="input-hint">基于知识库检索与生成，回答仅供参考</span>
          <el-button
            type="primary"
            :loading="loading"
            :disabled="!inputMessage.trim()"
            class="send-btn"
            @click="handleSend"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { sendMessage, getChatStreamUrl, getHistory } from '../api/chat'

const props = defineProps<{
  sessionId: string
}>()

const emit = defineEmits<{
  (e: 'session-created', sessionId: string): void
}>()

const messages = ref<{ role: 'user' | 'assistant'; content: string; isStreaming?: boolean }[]>([])
const inputMessage = ref('')
const loading = ref(false)

/** 最后一条是否为正在流式输出的助手消息（有则不再显示单独的加载行，避免两个 AI 助手） */
const lastMessageIsStreamingAssistant = computed(() => {
  const last = messages.value[messages.value.length - 1]
  return last?.role === 'assistant' && last?.isStreaming === true
})

const loadHistory = async () => {
  try {
    const res = await getHistory(props.sessionId)
    messages.value = res.data || []
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

const handleSend = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({ role: 'user', content: userMessage })
  scrollToBottom()

  try {
    loading.value = true
    await sendMessage({
      message: userMessage,
      session_id: props.sessionId
    })
    await startAIChat()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || error.message || '发送失败')
    loading.value = false
  }
}

const CHAT_STREAM_TIMEOUT_MS = 5 * 60 * 1000

const startAIChat = async () => {
  const aiMessage = reactive<{ role: 'assistant'; content: string; isStreaming: boolean }>({
    role: 'assistant',
    content: '',
    isStreaming: true
  })
  messages.value.push(aiMessage)

  const abortController = new AbortController()
  const timeoutId = setTimeout(() => abortController.abort(), CHAT_STREAM_TIMEOUT_MS)

  try {
    const response = await fetch(getChatStreamUrl(props.sessionId, true), {
      signal: abortController.signal
    })
    clearTimeout(timeoutId)

    if (!response.ok) throw new Error('AI 对话失败')

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) throw new Error('无法读取响应流')

    let buffer = ''
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'content') {
                aiMessage.content += data.data
                await nextTick()
                scrollToBottom()
              } else if (data.type === 'done') {
                clearTimeout(timeoutId)
                aiMessage.isStreaming = false
                loading.value = false
                return
              } else if (data.type === 'error') {
                throw new Error(data.data)
              }
            } catch (e) {
              // ignore
            }
          }
        }
      }
    } finally {
      clearTimeout(timeoutId)
      aiMessage.isStreaming = false
    }
    loading.value = false
  } catch (error: any) {
    clearTimeout(timeoutId)
    aiMessage.isStreaming = false
    if (error.name !== 'AbortError') {
      ElMessage.error(error.message || 'AI 对话失败')
    }
    loading.value = false
  }
}

const formatMarkdown = (text: string) => {
  try {
    return marked(text)
  } catch {
    return text
  }
}

const scrollToBottom = () => {
  const el = document.querySelector('.chat-messages')
  if (el) el.scrollTop = el.scrollHeight
}

watch(
  () => props.sessionId,
  (newId) => {
    if (newId) {
      messages.value = []
      loadHistory()
    }
  },
  { immediate: false }
)

onMounted(() => {
  if (props.sessionId) loadHistory()
})
</script>

<style scoped>
.chat-area {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--kb-main-bg);
}

.chat-messages {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px 24px 16px;
  -webkit-overflow-scrolling: touch;
}

.messages-inner {
  max-width: 780px;
  margin: 0 auto;
  padding-bottom: 24px; /* 底部留白，最后一条消息不被裁切 */
}

.welcome {
  text-align: center;
  padding: 48px 24px 32px;
}

.welcome-icon {
  font-size: 56px;
  margin-bottom: 20px;
  opacity: 0.9;
}

.welcome-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--kb-text-primary);
  margin-bottom: 12px;
  letter-spacing: -0.02em;
}

.welcome-desc {
  font-size: 14px;
  color: var(--kb-text-secondary);
  line-height: 1.7;
  margin-bottom: 24px;
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
}

.welcome-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.feature-tag {
  font-size: 12px;
  padding: 6px 12px;
  background: var(--kb-card-bg);
  border: 1px solid var(--kb-sidebar-border);
  border-radius: 20px;
  color: var(--kb-text-secondary);
}

.message-row {
  margin-bottom: 20px;
}

.message-row.user {
  display: flex;
  justify-content: flex-end;
}

.message-row.assistant {
  display: flex;
  justify-content: flex-start;
}

.message-bubble {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 85%;
}

.message-row.user .message-bubble {
  flex-direction: row-reverse;
}

.bubble-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--kb-primary-light);
  color: var(--kb-primary);
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar {
  background: var(--kb-primary);
  color: #fff;
}

.bubble-content {
  min-width: 0;
  flex: 1;
  background: var(--kb-card-bg);
  border: 1px solid var(--kb-sidebar-border);
  border-radius: var(--kb-radius);
  padding: 14px 16px;
  box-shadow: var(--kb-card-shadow);
}

.message-row.user .bubble-content {
  background: var(--kb-primary);
  border-color: var(--kb-primary);
  color: #fff;
}

.bubble-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--kb-text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.user-label {
  color: rgba(255, 255, 255, 0.85);
}

.prose {
  color: var(--kb-text-primary);
  font-size: 14px;
  line-height: 1.65;
}

.user-text {
  font-size: 14px;
  line-height: 1.65;
}

.streaming-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.prose p {
  margin-bottom: 0.5em;
}

.prose code {
  background: #e2e8f0;
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
}

.prose pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: var(--kb-radius-sm);
  overflow-x: auto;
  margin: 0.5em 0;
  font-size: 13px;
}

.prose pre code {
  background: transparent;
  color: inherit;
  padding: 0;
}

.loading-bubble .typing-dots {
  display: flex;
  gap: 6px;
  padding: 4px 0;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--kb-text-muted);
  animation: typing 1.4s ease-in-out infinite both;
}

.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-wrap {
  flex-shrink: 0;
  padding: 16px 24px 24px;
  background: var(--kb-main-bg);
  border-top: 1px solid var(--kb-sidebar-border);
}

.chat-input-inner {
  max-width: 780px;
  margin: 0 auto;
  background: var(--kb-card-bg);
  border: 1px solid var(--kb-sidebar-border);
  border-radius: var(--kb-radius);
  padding: 16px;
  box-shadow: var(--kb-card-shadow);
}

.chat-textarea :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  font-size: 14px;
  line-height: 1.6;
  padding: 8px 0;
  min-height: 72px;
}

.chat-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--kb-sidebar-border);
}

.input-hint {
  font-size: 12px;
  color: var(--kb-text-muted);
}

.send-btn .el-icon {
  margin-right: 4px;
}
</style>
