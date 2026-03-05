"""
简易 RAG 知识库入口：本地上传 -> 解析分片索引 -> 内存向量存储 -> 检索召回 -> 重排 -> 生成
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import LoggingMiddleware, ResponseMiddleware
from app.api import chat, knowledge
from app.core.response import ResponseModel

app = FastAPI(
    title="简易 RAG 知识库 API",
    description="本地上传 txt/word -> 解析分片 -> 内存向量库 -> 检索重排 -> 生成回答",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ResponseMiddleware)

app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])


@app.get("/health")
async def health_check():
    return ResponseModel.success(data={"status": "ok"}, message="服务正常")


if __name__ == "__main__":
    import uvicorn
    import os

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8990"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=["./app"] if reload else None,
    )
