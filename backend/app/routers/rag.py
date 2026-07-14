"""RAG 查询路由"""
from fastapi import APIRouter, HTTPException
from ..models import QueryRequest, QueryResponse
from ..services.store import vector_store, library_manager
from ..services.embed import embedder

router = APIRouter(prefix="/api/rag", tags=["RAG查询"])


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """RAG 查询"""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="查询文本不能为空")

    # 确定要查询的库
    if req.library_id:
        library_ids = [req.library_id]
    else:
        libraries = library_manager.list_libraries()
        library_ids = [lib["id"] for lib in libraries]

    if not library_ids:
        return QueryResponse(query=req.query, results=[], total=0)

    # 获取 query embedding
    query_embedding = embedder.embed_query(req.query)
    if not query_embedding:
        raise HTTPException(status_code=500, detail="Embedding 服务不可用")

    # 搜索
    results = vector_store.search_all(
        query_embedding=query_embedding,
        library_ids=library_ids,
        top_k=req.top_k
    )

    return QueryResponse(
        query=req.query,
        results=results,
        total=len(results)
    )


@router.post("/query/all", response_model=QueryResponse)
async def query_all(req: QueryRequest):
    """查询所有库（与 /query 等效）"""
    return await query(req)
