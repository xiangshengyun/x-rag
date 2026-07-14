"""库管理路由"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime
from ..models import LibraryCreate, LibraryInfo, LibraryListResponse, ScanRequest, ScanProgress
from ..services.store import vector_store, library_manager
from ..services.parser import DocumentParser
from ..services.chunker import TextChunker
from ..services.embed import embedder
from ..config import settings

router = APIRouter(prefix="/api/libraries", tags=["库管理"])

# 进度存储（内存中）
_scan_progress: dict = {}


@router.get("", response_model=LibraryListResponse)
async def list_libraries():
    """列出所有RAG库"""
    libraries = library_manager.list_libraries()
    result = []
    for lib in libraries:
        stats = vector_store.get_library_stats(lib["id"])
        result.append(LibraryInfo(
            id=lib["id"],
            name=lib["name"],
            description=lib.get("description"),
            source_path=lib["source_path"],
            document_count=lib.get("document_count", 0),
            chunk_count=stats.get("chunk_count", 0),
            created_at=lib.get("created_at"),
            updated_at=lib.get("updated_at")
        ))
    return LibraryListResponse(libraries=result)


@router.post("", response_model=LibraryInfo)
async def create_library(req: LibraryCreate):
    """创建新RAG库（仅注册，不扫描）"""
    source_path = Path(req.source_path)
    if not source_path.exists():
        raise HTTPException(status_code=400, detail="源路径不存在")

    if not source_path.is_dir():
        raise HTTPException(status_code=400, detail="源路径必须是目录")

    # 使用文件夹名作为库ID
    library_id = source_path.name

    if library_manager.get_library(library_id):
        raise HTTPException(status_code=400, detail="库已存在")

    now = datetime.now().isoformat()
    library_manager.create_library(
        library_id=library_id,
        name=req.name,
        source_path=str(source_path),
        description=req.description
    )
    library_manager.update_library(library_id, created_at=now, updated_at=now)

    return LibraryInfo(
        id=library_id,
        name=req.name,
        description=req.description,
        source_path=str(source_path),
        document_count=0,
        chunk_count=0,
        created_at=now,
        updated_at=now
    )


@router.get("/{library_id}", response_model=LibraryInfo)
async def get_library(library_id: str):
    """获取库详情"""
    lib = library_manager.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="库不存在")

    stats = vector_store.get_library_stats(library_id)
    return LibraryInfo(
        id=lib["id"],
        name=lib["name"],
        description=lib.get("description"),
        source_path=lib["source_path"],
        document_count=lib.get("document_count", 0),
        chunk_count=stats.get("chunk_count", 0),
        created_at=lib.get("created_at"),
        updated_at=lib.get("updated_at")
    )


@router.delete("/{library_id}")
async def delete_library(library_id: str):
    """删除RAG库"""
    lib = library_manager.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="库不存在")

    vector_store.delete_library(library_id)
    library_manager.delete_library(library_id)

    return {"message": "库已删除"}


@router.get("/{library_id}/chunks")
async def get_library_chunks(library_id: str):
    """获取库的所有分块内容"""
    lib = library_manager.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="库不存在")

    chunks = vector_store.get_chunks(library_id)
    return {"chunks": chunks, "total": len(chunks)}


@router.post("/{library_id}/scan", response_model=ScanProgress)
async def scan_library(library_id: str, req: ScanRequest = None):
    """扫描库文件夹，建立向量索引"""
    lib = library_manager.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="库不存在")

    source_path = Path(lib["source_path"])
    if not source_path.exists():
        raise HTTPException(status_code=400, detail="源路径不存在")

    # 设置进度
    _scan_progress[library_id] = ScanProgress(
        library_id=library_id,
        status="scanning",
        total_files=0,
        processed_files=0,
        message="正在扫描文件..."
    )

    try:
        # 解析文档
        documents = DocumentParser.scan_directory(source_path)
        _scan_progress[library_id].total_files = len(documents)
        _scan_progress[library_id].message = f"发现 {len(documents)} 个文档"

        if not documents:
            _scan_progress[library_id].status = "completed"
            _scan_progress[library_id].message = "没有找到支持的文档"
            return _scan_progress[library_id]

        # 分块
        chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        all_chunks = chunker.chunk_documents(documents)

        _scan_progress[library_id].status = "embedding"
        _scan_progress[library_id].message = f"正在向量化 {len(all_chunks)} 个文本块..."

        # 如果强制重建，先清空现有数据
        if req and req.force_rebuild:
            vector_store.delete_library(library_id)

        # 向量化
        texts = [chunk.content for chunk in all_chunks]
        embeddings = embedder.embed(texts)

        # 存储
        vector_store.add_chunks(library_id, all_chunks, embeddings)

        # 更新库信息
        library_manager.update_library(
            library_id,
            document_count=len(documents),
            chunk_count=len(all_chunks),
            updated_at=datetime.now().isoformat()
        )

        _scan_progress[library_id].status = "completed"
        _scan_progress[library_id].processed_files = len(documents)
        _scan_progress[library_id].message = f"完成！已索引 {len(documents)} 个文档，{len(all_chunks)} 个文本块"

    except Exception as e:
        _scan_progress[library_id].status = "failed"
        _scan_progress[library_id].message = f"错误: {str(e)}"

    return _scan_progress[library_id]


@router.get("/{library_id}/progress", response_model=ScanProgress)
async def get_scan_progress(library_id: str):
    """获取扫描进度"""
    if library_id in _scan_progress:
        return _scan_progress[library_id]
    return ScanProgress(
        library_id=library_id,
        status="pending",
        total_files=0,
        processed_files=0,
        message=""
    )
