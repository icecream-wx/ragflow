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
| `RAG_CHUNK_STRATEGY` | 分块策略：recursive / paragraph / sentence / fixed | `recursive` |
| `EMBEDDING_TYPE` | 嵌入方式：local / openai | `local` |
| `EMBEDDING_MODEL` | 嵌入模型名 | 见 .env.example |

**当前支持的分块策略**（可通过 `RAG_CHUNK_STRATEGY` 或上传时选择）：

| 策略 id | 说明 |
|--------|------|
| `recursive` | 递归分段（推荐）：优先按段落、换行、句号分片，兼顾中英文 |
| `paragraph` | 段落优先：优先按双换行、单换行分片，适合长文 |
| `sentence` | 句子优先：优先按句号、问号、感叹号分片，适合问答/对话 |
| `fixed` | 固定长度：严格按字符数切分，不寻找分隔符，适合无标点或代码 |

---

### 完全本地化嵌入（预下载任意 Hub 模型、可选强制离线）

思路：在 [Hugging Face](https://huggingface.co/models?pipeline_tag=sentence-similarity)（或模型官方页）选定嵌入模型，记下 **`REPO_ID`**（形如 `组织名/模型名`，与网页 URL 一致），把权重下载到本机 **`LOCAL_DIR`**，再把 `EMBEDDING_MODEL` 设为该目录的绝对路径。

1. **准备变量（自行替换）**

   - **`<REPO_ID>`**：例如轻量多语种 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`，或大模型 **`Qwen/Qwen3-Embedding-8B`**（体积与显存/内存占用大，需磁盘空间与 GPU 时请将 `EMBEDDING_DEVICE=cuda`）。
   - **`<LOCAL_DIR>`**：本机空目录，用于存放完整模型文件，例如 Linux/macOS `/path/to/my-embedding`，Windows `E:\models\my-embedding`。

   若模型为 **Gated**（需同意协议），请先在网页上申请访问，并在下载与运行环境中配置 `HF_TOKEN`（或 `huggingface-cli login`）。

2. **下载到 `<LOCAL_DIR>`**（下载阶段若直连 Hub 失败，可临时使用镜像或 VPN）：

   ```bash
   pip install huggingface_hub
   huggingface-cli download <REPO_ID> --local-dir <LOCAL_DIR>
   ```

   国内可临时指定镜像（地址以当前可用为准）：

   ```bash
   # Linux / macOS
   export HF_ENDPOINT=https://hf-mirror.com
   huggingface-cli download <REPO_ID> --local-dir <LOCAL_DIR>
   ```

   ```powershell
   # Windows PowerShell
   $env:HF_ENDPOINT="https://hf-mirror.com"
   huggingface-cli download <REPO_ID> --local-dir <LOCAL_DIR>
   ```

   等价 Python（将占位符换成实际值）：

   ```python
   from huggingface_hub import snapshot_download
   snapshot_download(
       repo_id="<REPO_ID>",
       local_dir=r"<LOCAL_DIR>",
       local_dir_use_symlinks=False,
   )
   ```

   也可从 [ModelScope](https://modelscope.cn) 等镜像站下载**同一模型或官方声明的等价权重**到 `<LOCAL_DIR>`，目录内需包含 `transformers` / `sentence-transformers` 可识别的完整文件（如 `config.json`、`*.safetensors` 或 `pytorch_model.bin`、tokenizer 相关文件等）。

3. **兼容性说明**：嵌入模型须能被本项目的 `HuggingFaceEmbeddings` 正常加载。若模型卡片要求 `trust_remote_code=True`、指定 `revision` 或额外依赖，加载失败时请按官方说明调整 [`backend/app/services/embedding_service.py`](backend/app/services/embedding_service.py) 中的 `model_kwargs` / 依赖，或换用该模型推荐的加载方式。

4. **在 `.env` 中指向本地目录**（绝对路径；Windows 建议用正斜杠）：

   ```env
   EMBEDDING_TYPE=local
   EMBEDDING_MODEL=<LOCAL_DIR>
   EMBEDDING_DEVICE=cpu
   ```

   使用 **`Qwen/Qwen3-Embedding-8B`** 且走 GPU 时，将 `EMBEDDING_DEVICE` 改为 `cuda`（并确保环境与显存满足模型要求）。

5. **（可选）强制离线**：模型已完整缓存到 `<LOCAL_DIR>` 且能稳定加载后再开启，避免运行期仍访问 Hub：

   ```env
   HF_HUB_OFFLINE=1
   TRANSFORMERS_OFFLINE=1
   ```

6. **自检**：断网或关闭 VPN 后启动后端并上传小段文本做向量化；成功即表示嵌入已完全依赖本地文件。

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/chat/send` | 发送用户消息（写入会话） |
| GET | `/api/chat/chat` | 与 AI 对话（SSE 流式，带 RAG） |
| GET | `/api/chat/history/{session_id}` | 获取会话历史 |
| GET | `/api/chat/sessions` | 获取会话列表 |
| POST | `/api/knowledge/upload` | 上传文件到知识库（multipart，可选 query `chunk_strategy`） |
| GET | `/api/knowledge/stats` | 知识库片段数及当前分块配置 |
| GET | `/api/knowledge/chunk-strategies` | 支持的分块策略列表 |
| GET | `/api/knowledge/chunks` | 知识片段详情（含向量预览） |

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
