<template>
  <div class="app-container">
    <el-container class="h-full">
      <aside class="sidebar">
        <div class="sidebar-header">
          <div class="brand">
            <span class="brand-icon">📚</span>
            <span class="brand-name">RAG 知识库</span>
          </div>
        </div>
        <nav class="nav-menu">
          <div
            :class="['nav-item', currentPage === 'chat' && 'active']"
            @click="onMenuSelect('chat')"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span>智能对话</span>
          </div>
          <div
            :class="['nav-item', currentPage === 'knowledge' && 'active']"
            @click="onMenuSelect('knowledge')"
          >
            <el-icon><Upload /></el-icon>
            <span>知识库管理</span>
          </div>
        </nav>
        <template v-if="currentPage === 'chat'">
          <div class="sidebar-action">
            <el-button type="primary" class="btn-new-chat" @click="createNewSession">
              <el-icon><Plus /></el-icon>
              <span>新建对话</span>
            </el-button>
          </div>
          <div class="sidebar-section">
            <div class="section-title">最近对话</div>
            <el-scrollbar height="calc(100vh - 320px)" class="session-scroll">
              <div
                v-for="session in sessions"
                :key="session.session_id"
                :class="['session-item', currentSessionId === session.session_id && 'active']"
                @click="selectSession(session.session_id)"
              >
                <el-icon class="session-icon"><ChatLineRound /></el-icon>
                <div class="session-info">
                  <div class="session-title">{{ session.title || '新对话' }}</div>
                  <div class="session-preview">{{ session.last_message || '暂无消息' }}</div>
                </div>
              </div>
              <div v-if="sessions.length === 0" class="session-empty">
                暂无对话，点击上方「新建对话」开始
              </div>
            </el-scrollbar>
          </div>
        </template>
      </aside>

      <main class="main-content">
        <template v-if="currentPage === 'knowledge'">
          <KnowledgeUpload />
        </template>
        <template v-else>
          <ChatArea
            v-if="currentSessionId"
            :session-id="currentSessionId"
            @session-created="handleSessionCreated"
          />
          <div v-else class="empty-state">
            <div class="empty-icon">💬</div>
            <h2 class="empty-title">选择或新建对话</h2>
            <p class="empty-desc">从左侧选择已有对话，或点击「新建对话」开始新的问答。</p>
            <el-button type="primary" size="large" @click="createNewSession">
              <el-icon><Plus /></el-icon>
              新建对话
            </el-button>
          </div>
        </template>
      </main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, ChatDotRound, Upload, ChatLineRound } from '@element-plus/icons-vue'
import ChatArea from './components/ChatArea.vue'
import KnowledgeUpload from './components/KnowledgeUpload.vue'
import { getSessions } from './api/chat'

const currentPage = ref<'chat' | 'knowledge'>('chat')
const currentSessionId = ref<string>('')
const sessions = ref<{ session_id: string; title: string; last_message: string }[]>([])

const onMenuSelect = (index: string) => {
  currentPage.value = index === 'knowledge' ? 'knowledge' : 'chat'
}

const loadSessions = async () => {
  try {
    const res = await getSessions()
    sessions.value = res.data || []
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

const createNewSession = () => {
  currentSessionId.value = `session_${Date.now()}`
}

const selectSession = (sessionId: string) => {
  currentSessionId.value = sessionId
}

const handleSessionCreated = (sessionId: string) => {
  currentSessionId.value = sessionId
  loadSessions()
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
  display: flex;
}

.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--kb-sidebar-bg);
  border-right: 1px solid var(--kb-sidebar-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--kb-sidebar-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  font-size: 24px;
  line-height: 1;
}

.brand-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--kb-text-primary);
  letter-spacing: -0.02em;
}

.nav-menu {
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--kb-radius-sm);
  font-size: 14px;
  color: var(--kb-text-secondary);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.nav-item:hover {
  background: var(--kb-primary-light);
  color: var(--kb-primary);
}

.nav-item.active {
  background: var(--kb-primary-light);
  color: var(--kb-primary);
  font-weight: 500;
}

.nav-item .el-icon {
  font-size: 18px;
}

.sidebar-action {
  padding: 12px 16px;
}

.btn-new-chat {
  width: 100%;
  height: 42px;
  font-weight: 500;
  border-radius: var(--kb-radius-sm);
}

.btn-new-chat .el-icon {
  margin-right: 6px;
}

.sidebar-section {
  flex: 1;
  min-height: 0;
  padding: 0 16px 16px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--kb-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
  padding-left: 4px;
}

.session-scroll {
  border-radius: var(--kb-radius-sm);
}

.session-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 10px;
  border-radius: var(--kb-radius-sm);
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 2px;
}

.session-item:hover {
  background: #e2e8f0;
}

.session-item.active {
  background: var(--kb-primary-light);
}

.session-icon {
  font-size: 16px;
  color: var(--kb-text-muted);
  flex-shrink: 0;
  margin-top: 2px;
}

.session-item.active .session-icon {
  color: var(--kb-primary);
}

.session-info {
  min-width: 0;
  flex: 1;
}

.session-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--kb-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-preview {
  font-size: 12px;
  color: var(--kb-text-muted);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-empty {
  font-size: 13px;
  color: var(--kb-text-muted);
  text-align: center;
  padding: 24px 16px;
  line-height: 1.5;
}

.main-content {
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: hidden;
  background: var(--kb-main-bg);
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.9;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--kb-text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--kb-text-secondary);
  margin-bottom: 24px;
  max-width: 320px;
  line-height: 1.6;
}
</style>
