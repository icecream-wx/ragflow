# 简易 RAG 知识库

参考 [ragAI](https://github.com/your-org/ragAI) 的项目结构与框架，实现一个**简易 RAG 知识库**：前端上传本地 txt/word 等文本文件 → 后端解析、知识分片与索引 → **内存向量存储** → 用户提问 → **检索召回** → **重排** → **生成与融合**。

---

## 功能流程

1. **前端**：在「知识库上传」页选择本地文件（.txt、.docx、.doc），点击上传。
2. **后端**：解析上传文件（txt 按编码、docx 按段落/表格提取）→ 按配置分片（chunk_size/overlap）→ 向量化 → 写入**内存向量库**（FAISS，不落盘）。
3. **用户提问**：在「对话」页输入问题并发送。
4. **RAG 流程**：问题向量化 → 在内存向量库中**召回 top_k** → **重排取 top_n** → 将 top_n 片段与问题、历史一起拼成提示词 → 调用 LLM **流式生成**回答并融合展示。

---

## 项目结构

```
simple-rag/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py         # 聊天、会话、历史
│   │   │   └── knowledge.py   # 文件上传、知识库统计
│   │   ├── core/               # 配置与中间件
│   │   ├── models/             # RAG 对话模型
│   │   ├── services/
│   │   │   ├── embedding_service.py   # 文本向量化
│   │   │   ├── vector_store_memory.py # 内存向量库（FAISS）
│   │   │   ├── file_parser.py         # txt/docx 解析
│   │   │   ├── reranker.py            # 重排
│   │   │   └── rag_pipeline.py         # 检索召回 + 重排 + 拼上下文
│   │   └── utils/text_utils.py        # 分片、拼上下文
│   ├── main.py
│   ├── pyproject.toml
│   └── .env.example
├── frontend/                   # Vue 3 + Vite + Element Plus
│   ├── src/
│   │   ├── api/chat.ts、knowledge.ts
│   │   ├── components/ChatArea.vue、KnowledgeUpload.vue
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts          # 代理 /api -> localhost:8990
└── README.md
```

---

## 环境要求

- Python 3.10+
- Node.js 18+（前端）
- Poetry 或 pip（后端）

---

## 安装与运行

### 1. 后端

```bash
cd simple-rag/backend
poetry install
# 或：pip install -e .
```

复制并编辑环境变量：

```bash
cp .env.example .env
# 填写 LLM_API_KEY、可选 EMBEDDING_TYPE=openai 等
```

启动：

```bash
poetry run python main.py
```

默认端口 **8990**。若使用本地嵌入（`EMBEDDING_TYPE=local`），需安装：`poetry install --extras local-embedding`。

### 2. 前端

```bash
cd simple-rag/frontend
npm install
npm run dev
```

前端默认 **http://localhost:3001**，会将 `/api` 代理到后端 8990。

### 3. 使用步骤

1. 打开前端 → 「知识库上传」→ 选择 .txt / .docx 文件 → 上传到知识库。
2. 切换到「对话」→ 新建对话 → 输入问题 → 发送，即可看到基于知识库的 RAG 回答（检索召回 → 重排 → 生成与融合）。

---

## 配置说明（.env）

| 变量 | 说明 | 默认 |
|------|------|------|
| `HOST` / `PORT` | 服务地址与端口 | `0.0.0.0` / `8990` |
| `LLM_API_KEY` | 大模型 API 密钥 | 必填 |
| `LLM_MODEL_NAME` | 模型名称 | `gpt-3.5-turbo` |
| `LLM_BASE_URL` | API 基础 URL（兼容 OpenAI 的接口） | 空 |
| `RAG_TOP_K_RECALL` | 向量召回条数 | `10` |
| `RAG_TOP_N_RERANK` | 重排后保留条数 | `3` |
| `RAG_CHUNK_SIZE` | 分片大小（字符） | `500` |
| `RAG_CHUNK_OVERLAP` | 分片重叠（字符） | `50` |
| `EMBEDDING_TYPE` | 嵌入方式：local / openai | `local` |
| `EMBEDDING_MODEL` | 嵌入模型名 | 见 .env.example |

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/chat/send` | 发送用户消息（写入会话） |
| GET | `/api/chat/chat` | 与 AI 对话（SSE 流式，带 RAG） |
| GET | `/api/chat/history/{session_id}` | 获取会话历史 |
| GET | `/api/chat/sessions` | 获取会话列表 |
| POST | `/api/knowledge/upload` | 上传文件到知识库（multipart） |
| GET | `/api/knowledge/stats` | 知识库片段数统计 |

---

## 技术栈与版本（对齐 ragAI）

- **后端**：FastAPI、Uvicorn、LangChain、langchain-openai、langchain-community、FAISS（内存向量库）、python-docx
- **前端**：Vue 3、Vite、Element Plus、axios、marked

---

## 注意事项

1. **内存向量库**：使用 FAISS 仅存内存，**进程重启后数据清空**，需重新上传文件。
2. **支持格式**：.txt（UTF-8/GBK）、.docx（推荐）；.doc 仅部分可解析，建议另存为 .docx。
3. **会话存储**：会话历史存在进程内存，多实例或重启会丢失，生产环境建议改为 Redis 或数据库。

---

## 与 ragAI 的对比

- **ragAI**：从 Elasticsearch 按条件检索文档 → 分片向量化进内存/持久化 → 向量召回 + 重排 → 多轮对话。
- **本仓库**：从**本地上传** txt/word → 解析 → 分片向量化进**内存** → 向量召回 + 重排 → 多轮对话。无 ES 依赖，更适合本地文件构建知识库的简易场景。
