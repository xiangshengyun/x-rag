"""配置路由"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..config import settings

router = APIRouter(prefix="/api/config", tags=["配置"])


class ChunkConfig(BaseModel):
    """分块配置"""
    chunk_size: int = Field(500, ge=100, le=2000, description="分块大小")
    chunk_overlap: int = Field(50, ge=0, le=500, description="分块重叠大小")


class OllamaConfig(BaseModel):
    """Ollama配置"""
    base_url: str = Field("http://localhost:11434", description="Ollama 服务地址")
    embed_model: str = Field("nomic-embed-text", description="Embedding 模型")


@router.get("/chunk")
async def get_chunk_config():
    """获取分块配置"""
    return settings.get_chunk_config()


@router.post("/chunk")
async def update_chunk_config(config: ChunkConfig):
    """更新分块配置"""
    settings.update(
        CHUNK_SIZE=config.chunk_size,
        CHUNK_OVERLAP=config.chunk_overlap
    )
    return {"message": "配置已更新", "config": settings.get_chunk_config()}


@router.get("/ollama")
async def get_ollama_config():
    """获取Ollama配置"""
    return {
        "base_url": settings.OLLAMA_BASE_URL,
        "embed_model": settings.OLLAMA_EMBED_MODEL,
    }


@router.post("/ollama")
async def update_ollama_config(config: OllamaConfig):
    """更新Ollama配置"""
    settings.update(
        OLLAMA_BASE_URL=config.base_url,
        OLLAMA_EMBED_MODEL=config.embed_model
    )
    return {"message": "配置已更新"}
