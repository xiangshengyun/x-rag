"""数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from pathlib import Path


# ============ 库管理模型 ============

class LibraryCreate(BaseModel):
    """创建库请求"""
    name: str = Field(..., description="库名称")
    description: Optional[str] = Field(None, description="库描述")
    source_path: str = Field(..., description="源文件夹路径")


class LibraryInfo(BaseModel):
    """库信息"""
    id: str = Field(..., description="库ID (文件夹名)")
    name: str = Field(..., description="库名称")
    description: Optional[str] = Field(None, description="库描述")
    source_path: str = Field(..., description="源文件夹路径")
    document_count: int = Field(0, description="文档数量")
    chunk_count: int = Field(0, description="分块数量")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class LibraryListResponse(BaseModel):
    """库列表响应"""
    libraries: List[LibraryInfo] = Field(default_factory=list)


# ============ 文档解析模型 ============

class DocumentChunk(BaseModel):
    """文档分块"""
    chunk_id: str = Field(..., description="分块ID")
    content: str = Field(..., description="分块内容")
    metadata: dict = Field(default_factory=dict, description="元数据")


class ParsedDocument(BaseModel):
    """解析后的文档"""
    doc_id: str = Field(..., description="文档ID")
    file_name: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型: pdf, md, txt")
    chunks: List[DocumentChunk] = Field(default_factory=list)


# ============ RAG 查询模型 ============

class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="查询文本")
    library_id: Optional[str] = Field(None, description="指定库ID，不指定则搜索所有库")
    top_k: int = Field(5, description="返回结果数量")


class QueryResult(BaseModel):
    """查询结果"""
    content: str = Field(..., description="相关文本内容")
    score: float = Field(..., description="相似度分数")
    source: str = Field(..., description="来源文件")
    library_id: str = Field(..., description="所属库ID")


class QueryResponse(BaseModel):
    """查询响应"""
    query: str = Field(..., description="原始查询")
    results: List[QueryResult] = Field(default_factory=list)
    total: int = Field(0, description="结果总数")


# ============ 扫描任务模型 ============

class ScanRequest(BaseModel):
    """扫描文件夹请求"""
    force_rebuild: bool = Field(False, description="是否强制重建")


class ScanProgress(BaseModel):
    """扫描进度"""
    library_id: str = Field(..., description="库ID")
    status: str = Field(..., description="状态: pending, scanning, embedding, completed, failed")
    total_files: int = Field(0, description="总文件数")
    processed_files: int = Field(0, description="已处理文件数")
    message: Optional[str] = Field(None, description="状态消息")
