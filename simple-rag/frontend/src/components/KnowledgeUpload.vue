<template>
  <div class="knowledge-page">
    <header class="page-header">
      <div class="header-content">
        <h1 class="page-title">知识库管理</h1>
        <p class="page-desc">上传本地文档，系统将自动解析、分片并建立向量索引，供智能对话检索使用。</p>
      </div>
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-value">{{ stats.chunk_count }}</span>
          <span class="stat-label">知识片段数</span>
        </div>
        <div class="stat-card stat-card-config">
          <span class="stat-label">当前分块配置</span>
          <span class="stat-config">大小 {{ stats.chunk_size ?? 500 }} · 重叠 {{ stats.chunk_overlap ?? 50 }} · {{ currentStrategyName }}</span>
        </div>
      </div>
    </header>

    <div class="upload-section">
      <el-card class="upload-card" shadow="never">
        <div class="chunk-strategy-row">
          <span class="chunk-strategy-label">本次上传分块策略</span>
          <el-select v-model="uploadChunkStrategy" placeholder="使用服务端默认" clearable class="chunk-strategy-select">
            <el-option
              v-for="s in chunkStrategies"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            >
              <span>{{ s.name }}</span>
              <span class="option-desc">{{ s.description }}</span>
            </el-option>
          </el-select>
        </div>
        <el-upload
          ref="uploadRef"
          class="upload-dragger-wrap"
          drag
          :auto-upload="false"
          :limit="20"
          multiple
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          :file-list="fileList"
          accept=".txt,.docx,.doc"
        >
          <div class="upload-inner">
            <div class="upload-icon">📄</div>
            <p class="upload-text">将文件拖到此处，或<em>点击选择</em></p>
            <p class="upload-tip">支持 .txt、.docx、.doc，单次最多 20 个文件</p>
          </div>
        </el-upload>

        <div v-if="fileList.length > 0" class="file-list">
          <div class="file-list-title">已选 {{ fileList.length }} 个文件</div>
          <ul class="file-items">
            <li v-for="(file, i) in fileList" :key="i" class="file-item">
              <el-icon class="file-type-icon"><Document /></el-icon>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatSize(file.raw?.size) }}</span>
            </li>
          </ul>
        </div>

        <div class="upload-actions">
          <el-button
            type="primary"
            size="large"
            :loading="uploadLoading"
            :disabled="fileList.length === 0"
            @click="handleUpload"
          >
            <el-icon class="mr-1"><UploadFilled /></el-icon>
            上传到知识库
          </el-button>
          <el-button
            v-if="fileList.length > 0"
            size="large"
            @click="clearFiles"
          >
            清空选择
          </el-button>
        </div>
      </el-card>

      <el-card class="strategies-card" shadow="never">
        <template #header>
          <span>当前项目支持的分块策略</span>
        </template>
        <ul class="strategies-list">
          <li v-for="s in chunkStrategies" :key="s.id" class="strategy-item">
            <span class="strategy-name">{{ s.name }}</span>
            <span class="strategy-id">（{{ s.id }}）</span>
            <p class="strategy-desc">{{ s.description }}</p>
          </li>
          <li v-if="chunkStrategies.length === 0 && !chunksLoading" class="strategy-item">加载中…</li>
        </ul>
      </el-card>
    </div>

    <!-- 知识片段列表 -->
    <div class="chunks-section">
      <el-card class="chunks-card" shadow="never">
        <template #header>
          <div class="chunks-card-header">
            <span>知识片段列表</span>
            <el-button type="primary" link :loading="chunksLoading" @click="loadChunks">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        <div v-if="chunksLoading && chunks.length === 0" class="chunks-loading">加载中...</div>
        <div v-else-if="chunks.length === 0" class="chunks-empty">暂无知识片段，请先上传文档。</div>
        <div v-else class="chunks-table-wrap">
          <el-table :data="chunks" stripe style="width: 100%">
            <el-table-column type="index" label="#" width="50" :index="(i: number) => i + 1" />
            <el-table-column prop="metadata.source" label="来源" width="140" show-overflow-tooltip>
              <template #default="{ row }">{{ row.metadata?.source ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="内容预览" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">{{ contentPreview(row.content) }}</template>
            </el-table-column>
            <el-table-column label="向量预览" width="200">
              <template #default="{ row }">
                <span class="vector-preview">{{ formatVectorPreview(row) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDetail(row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- 片段详情弹窗：分片内容 + 向量 -->
    <el-dialog
      v-model="detailVisible"
      title="知识片段详情"
      width="560px"
      class="chunk-detail-dialog"
      destroy-on-close
    >
      <div v-if="currentChunk" class="chunk-detail">
        <div class="detail-block">
          <div class="detail-label">来源</div>
          <div class="detail-value">{{ currentChunk.metadata?.source ?? '-' }}</div>
        </div>
        <div class="detail-block">
          <div class="detail-label">分片内容</div>
          <div class="detail-content">{{ currentChunk.content || '-' }}</div>
        </div>
        <div class="detail-block">
          <div class="detail-label">Embedding 向量</div>
          <div class="detail-vector">{{ formatVectorPreview(currentChunk) }}</div>
          <div v-if="currentChunk.vector_dim > vectorDisplayDims" class="detail-vector-tip">
            共 {{ currentChunk.vector_dim }} 维，仅展示前 {{ vectorDisplayDims }} 维
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadInstance } from 'element-plus'
import { Document, UploadFilled, Refresh } from '@element-plus/icons-vue'
import { uploadFilesToKnowledge, getKnowledgeStats, getKnowledgeChunks, getChunkStrategies, type KnowledgeChunkItem, type ChunkStrategyItem } from '../api/knowledge'

const uploadRef = ref<UploadInstance>()
const uploadLoading = ref(false)
const fileList = ref<UploadFile[]>([])
const stats = reactive<{ chunk_count: number; chunk_size?: number; chunk_overlap?: number; chunk_strategy?: string }>({ chunk_count: 0 })

const chunkStrategies = ref<ChunkStrategyItem[]>([])
const uploadChunkStrategy = ref<string | undefined>(undefined)

const currentStrategyName = computed(() => {
  const id = stats.chunk_strategy || 'recursive'
  const s = chunkStrategies.value.find((x) => x.id === id)
  return s ? s.name : id
})

const chunks = ref<KnowledgeChunkItem[]>([])
const chunksLoading = ref(false)
const detailVisible = ref(false)
const currentChunk = ref<KnowledgeChunkItem | null>(null)
const vectorDisplayDims = 10

function formatSize(bytes?: number): string {
  if (bytes == null || bytes === 0) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function contentPreview(content: string, maxLen = 80): string {
  if (!content) return '-'
  const t = content.trim()
  return t.length <= maxLen ? t : t.slice(0, maxLen) + '...'
}

function formatVectorPreview(row: KnowledgeChunkItem): string {
  const preview = row.vector_preview || []
  const dim = row.vector_dim || 0
  if (dim === 0 && preview.length === 0) return '-'
  const part = preview.map((x) => Number(x).toFixed(2)).join(', ')
  if (dim > preview.length) return `[${part}, ...]`
  return `[${part}]`
}

const onFileChange = (_file: UploadFile, files: UploadFile[]) => {
  fileList.value = files
}

const onFileRemove = (_file: UploadFile, files: UploadFile[]) => {
  fileList.value = files
}

const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

const loadChunks = async () => {
  chunksLoading.value = true
  try {
    const res = await getKnowledgeChunks(vectorDisplayDims)
    chunks.value = res.data?.chunks ?? []
  } catch {
    chunks.value = []
  } finally {
    chunksLoading.value = false
  }
}

const openDetail = (row: KnowledgeChunkItem) => {
  currentChunk.value = row
  detailVisible.value = true
}

const handleUpload = async () => {
  if (fileList.value.length === 0) return
  const rawFiles = fileList.value.map((f) => f.raw).filter(Boolean) as File[]
  if (rawFiles.length === 0) {
    ElMessage.warning('请重新选择文件')
    return
  }

  uploadLoading.value = true
  try {
    const res = await uploadFilesToKnowledge(rawFiles, uploadChunkStrategy.value || undefined)
    ElMessage.success(res.message || `已上传 ${res.data?.uploaded ?? 0} 个文件，共 ${res.data?.chunks ?? 0} 个分片`)
    clearFiles()
    await loadStats()
    await loadChunks()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || e.message || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await getKnowledgeStats()
    const d = res.data
    stats.chunk_count = d?.chunk_count ?? 0
    stats.chunk_size = d?.chunk_size
    stats.chunk_overlap = d?.chunk_overlap
    stats.chunk_strategy = d?.chunk_strategy
  } catch {
    // ignore
  }
}

const loadChunkStrategies = async () => {
  try {
    const res = await getChunkStrategies()
    chunkStrategies.value = res.data?.strategies ?? []
  } catch {
    chunkStrategies.value = []
  }
}

onMounted(() => {
  loadStats()
  loadChunks()
  loadChunkStrategies()
})
</script>

<style scoped>
.knowledge-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
  min-height: 100%;
}

.page-header {
  margin-bottom: 28px;
}

.header-content {
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--kb-text-primary);
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}

.page-desc {
  font-size: 14px;
  color: var(--kb-text-secondary);
  line-height: 1.6;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: var(--kb-card-bg);
  border: 1px solid var(--kb-sidebar-border);
  border-radius: var(--kb-radius);
  padding: 16px 20px;
  min-width: 140px;
  box-shadow: var(--kb-card-shadow);
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--kb-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--kb-text-muted);
  margin-top: 4px;
  display: block;
}

.stat-card-config {
  flex: 1;
  min-width: 0;
}

.stat-card-config .stat-label {
  margin-top: 0;
}

.stat-config {
  display: block;
  font-size: 13px;
  color: var(--kb-text-primary);
  margin-top: 4px;
}

.chunk-strategy-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.chunk-strategy-label {
  font-size: 14px;
  color: var(--kb-text-secondary);
  flex-shrink: 0;
}

.chunk-strategy-select {
  width: 320px;
}

.chunk-strategy-select :deep(.el-select__wrapper) {
  min-height: 36px;
}

.option-desc {
  display: block;
  font-size: 12px;
  color: var(--kb-text-muted);
  margin-top: 2px;
}

.strategies-card {
  margin-top: 16px;
  border-radius: var(--kb-radius);
  border: 1px solid var(--kb-sidebar-border);
}

.strategies-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.strategy-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--kb-sidebar-border);
}

.strategy-item:last-child {
  border-bottom: none;
}

.strategy-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--kb-text-primary);
}

.strategy-id {
  font-size: 12px;
  color: var(--kb-text-muted);
}

.strategy-desc {
  font-size: 13px;
  color: var(--kb-text-secondary);
  margin: 4px 0 0;
  line-height: 1.5;
}

.upload-section {
  margin-top: 8px;
}

.upload-card {
  border-radius: var(--kb-radius);
  border: 1px solid var(--kb-sidebar-border);
  overflow: hidden;
}

.upload-card :deep(.el-card__body) {
  padding: 28px;
}

.upload-dragger-wrap :deep(.el-upload-dragger) {
  padding: 40px 24px;
  border-radius: var(--kb-radius);
  border: 2px dashed var(--kb-sidebar-border);
  background: var(--kb-sidebar-bg);
  transition: border-color 0.2s, background 0.2s;
}

.upload-dragger-wrap :deep(.el-upload-dragger:hover) {
  border-color: var(--kb-primary);
  background: var(--kb-primary-light);
}

.upload-inner {
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.9;
}

.upload-text {
  font-size: 15px;
  color: var(--kb-text-primary);
  margin-bottom: 6px;
}

.upload-text em {
  color: var(--kb-primary);
  font-style: normal;
  font-weight: 500;
}

.upload-tip {
  font-size: 12px;
  color: var(--kb-text-muted);
}

.file-list {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--kb-sidebar-border);
}

.file-list-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--kb-text-secondary);
  margin-bottom: 12px;
}

.file-items {
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
  border-radius: var(--kb-radius-sm);
  background: var(--kb-sidebar-bg);
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  font-size: 13px;
  border-radius: 6px;
  transition: background 0.2s;
}

.file-item:hover {
  background: var(--kb-card-bg);
}

.file-type-icon {
  font-size: 18px;
  color: var(--kb-text-muted);
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--kb-text-primary);
}

.file-size {
  font-size: 12px;
  color: var(--kb-text-muted);
  flex-shrink: 0;
}

.upload-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  align-items: center;
}

.mr-1 {
  margin-right: 6px;
}

.chunks-section {
  margin-top: 24px;
}

.chunks-card {
  border-radius: var(--kb-radius);
  border: 1px solid var(--kb-sidebar-border);
}

.chunks-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chunks-loading,
.chunks-empty {
  padding: 24px;
  text-align: center;
  color: var(--kb-text-muted);
  font-size: 14px;
}

.chunks-table-wrap {
  max-height: min(420px, 50vh);
  overflow-y: auto;
  overflow-x: auto;
}

.vector-preview {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: var(--kb-text-secondary);
}

.chunk-detail-dialog .chunk-detail {
  padding: 0 4px;
}

.detail-block {
  margin-bottom: 20px;
}

.detail-block:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--kb-text-muted);
  margin-bottom: 6px;
}

.detail-value {
  font-size: 14px;
  color: var(--kb-text-primary);
}

.detail-content {
  font-size: 14px;
  color: var(--kb-text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  padding: 12px;
  background: var(--kb-sidebar-bg);
  border-radius: var(--kb-radius-sm);
}

.detail-vector {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  color: var(--kb-text-primary);
  word-break: break-all;
}

.detail-vector-tip {
  font-size: 12px;
  color: var(--kb-text-muted);
  margin-top: 6px;
}
</style>
