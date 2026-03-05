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
      </div>
    </header>

    <div class="upload-section">
      <el-card class="upload-card" shadow="never">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadInstance } from 'element-plus'
import { Document, UploadFilled } from '@element-plus/icons-vue'
import { uploadFilesToKnowledge, getKnowledgeStats } from '../api/knowledge'

const uploadRef = ref<UploadInstance>()
const uploadLoading = ref(false)
const fileList = ref<UploadFile[]>([])
const stats = reactive({ chunk_count: 0 })

function formatSize(bytes?: number): string {
  if (bytes == null || bytes === 0) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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

const handleUpload = async () => {
  if (fileList.value.length === 0) return
  const rawFiles = fileList.value.map((f) => f.raw).filter(Boolean) as File[]
  if (rawFiles.length === 0) {
    ElMessage.warning('请重新选择文件')
    return
  }

  uploadLoading.value = true
  try {
    const res = await uploadFilesToKnowledge(rawFiles)
    ElMessage.success(res.message || `已上传 ${res.data?.uploaded ?? 0} 个文件，共 ${res.data?.chunks ?? 0} 个分片`)
    clearFiles()
    await loadStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || e.message || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await getKnowledgeStats()
    stats.chunk_count = res.data?.chunk_count ?? 0
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadStats()
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
</style>
