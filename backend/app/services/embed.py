"""Ollama Embedding 服务"""
import httpx
from typing import List
from ..config import settings


class OllamaEmbedder:
    """Ollama Embedding 客户端"""

    def __init__(self):
        pass

    @property
    def base_url(self) -> str:
        return settings.OLLAMA_BASE_URL

    @property
    def model(self) -> str:
        return settings.OLLAMA_EMBED_MODEL

    @property
    def batch_size(self) -> int:
        return settings.OLLAMA_EMBED_BATCH_SIZE

    def embed(self, texts: List[str]) -> List[List[float]]:
        """获取文本的 embedding 向量"""
        if not texts:
            return []

        # 批量处理
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = self._embed_batch(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取 embedding"""
        try:
            with httpx.Client(timeout=60.0) as client:
                if len(texts) == 1:
                    response = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={
                            "model": self.model,
                            "prompt": texts[0]
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    return [result.get("embedding", [])]
                else:
                    # 批量时逐个处理
                    embeddings = []
                    for text in texts:
                        resp = client.post(
                            f"{self.base_url}/api/embeddings",
                            json={"model": self.model, "prompt": text}
                        )
                        resp.raise_for_status()
                        embeddings.append(resp.json().get("embedding", []))
                    return embeddings

        except Exception as e:
            print(f"Embedding error: {e}")
            # 返回零向量作为降级
            dimension = self._get_embedding_dimension()
            return [[0.0] * dimension for _ in texts]

    def _get_embedding_dimension(self) -> int:
        """获取 embedding 维度"""
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": "test"}
                )
                resp.raise_for_status()
                return len(resp.json().get("embedding", []))
        except Exception:
            return 768  # 默认维度

    def embed_query(self, query: str) -> List[float]:
        """获取查询文本的 embedding"""
        embeddings = self.embed([query])
        return embeddings[0] if embeddings else []


# 全局单例
embedder = OllamaEmbedder()
