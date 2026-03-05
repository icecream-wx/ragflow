"""
知识库 API：本地上传 txt/word 等文件 -> 解析 -> 分片 -> 向量化 -> 写入内存向量库
"""
from fastapi import APIRouter, UploadFile, File
from app.core.response import ResponseModel
from app.core.logger import app_logger
from app.core.rag_config import get_rag_config
from app.services.file_parser import parse_file, ALLOWED_EXTENSIONS
from app.services.vector_store_memory import get_memory_vector_store
from app.utils.text_utils import chunk_text

router = APIRouter()


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    上传本地文件（txt、docx 等）到知识库：解析 -> 分片 -> 向量化 -> 写入内存向量库。
    """
    if not files:
        return ResponseModel.error(message="请选择至少一个文件", code=400)

    cfg = get_rag_config()
    store = get_memory_vector_store()

    all_texts = []
    all_metadatas = []
    uploaded_names = []

    for upload in files:
        filename = upload.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if f".{ext}" not in ALLOWED_EXTENSIONS:
            app_logger.warning(f"跳过不支持的文件: {filename}")
            continue

        try:
            content = await upload.read()
        except Exception as e:
            app_logger.error(f"读取文件失败 {filename}: {e}")
            return ResponseModel.error(message=f"读取文件失败: {filename}", code=500)

        try:
            text = parse_file(content, filename)
        except Exception as e:
            app_logger.error(f"解析文件失败 {filename}: {e}")
            return ResponseModel.error(message=f"解析失败 {filename}: {str(e)}", code=400)

        if not text or not text.strip():
            app_logger.warning(f"文件 {filename} 内容为空，已跳过")
            continue

        chunks = chunk_text(
            text.strip(),
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
        )
        for c in chunks:
            if c and c.strip():
                all_texts.append(c.strip())
                all_metadatas.append({"source": filename[:200]})
        uploaded_names.append(filename)

    if not all_texts:
        return ResponseModel.success(
            data={"uploaded": 0, "chunks": 0, "files": []},
            message="没有可用的文本内容（或格式不支持）"
        )

    try:
        store.add_texts(texts=all_texts, metadatas=all_metadatas)
    except Exception as e:
        app_logger.error(f"写入向量库失败: {e}", exc_info=True)
        return ResponseModel.error(message=f"写入向量库失败: {str(e)}", code=500)

    return ResponseModel.success(
        data={
            "uploaded": len(uploaded_names),
            "chunks": len(all_texts),
            "files": uploaded_names,
        },
        message=f"已上传 {len(uploaded_names)} 个文件，共 {len(all_texts)} 个分片",
    )


@router.get("/stats")
async def knowledge_stats():
    """知识库统计：当前内存向量库中的片段数量。"""
    try:
        store = get_memory_vector_store()
        count = store.count()
        return ResponseModel.success(data={"chunk_count": count}, message="获取成功")
    except Exception as e:
        app_logger.error(f"知识库统计失败: {e}", exc_info=True)
        return ResponseModel.error(message=str(e), code=500)


@router.get("/allowed-extensions")
async def allowed_extensions():
    """返回支持上传的扩展名列表。"""
    return ResponseModel.success(
        data={"extensions": list(ALLOWED_EXTENSIONS)},
        message="获取成功",
    )
