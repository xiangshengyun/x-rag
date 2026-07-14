"""FAISS 向量存储服务"""
import faiss
import numpy as np
import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from ..config import settings
from ..models import DocumentChunk, QueryResult


class VectorStore:
    """FAISS 向量存储管理"""

    def __init__(self):
        self.data_dir = settings.DATA_DIR / "faiss_index"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_lib_path(self, library_id: str) -> tuple:
        """获取库的索引文件和元数据路径"""
        lib_dir = self.data_dir / library_id
        lib_dir.mkdir(parents=True, exist_ok=True)
        return lib_dir / "index.bin", lib_dir / "metadata.json"

    def _load_metadata(self, library_id: str) -> Dict:
        """加载元数据"""
        _, meta_path = self._get_lib_path(library_id)
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"chunks": [], "dimension": 768}

    def _save_metadata(self, library_id: str, metadata: Dict):
        """保存元数据"""
        _, meta_path = self._get_lib_path(library_id)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _load_index(self, library_id: str, dimension: int) -> faiss.IndexFlatIP:
        """加载或创建索引"""
        index_path, _ = self._get_lib_path(library_id)
        if index_path.exists():
            return faiss.read_index(str(index_path))
        # 创建新索引 (内积 cosine similarity)
        # 归一化后内积 = cosine similarity
        return faiss.IndexFlatIP(dimension)

    def _save_index(self, library_id: str, index: faiss.IndexFlatIP):
        """保存索引"""
        index_path, _ = self._get_lib_path(library_id)
        faiss.write_index(index, str(index_path))

    def add_chunks(self, library_id: str, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """添加文档块到向量库"""
        if not chunks or not embeddings:
            return

        dimension = len(embeddings[0])
        index = self._load_index(library_id, dimension)
        metadata = self._load_metadata(library_id)

        # 归一化向量 (FAISS IP 需要)
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)

        # 添加到索引
        index.add(vectors)

        # 更新元数据
        existing_ids = set(m["chunk_id"] for m in metadata["chunks"])
        for i, chunk in enumerate(chunks):
            if chunk.chunk_id not in existing_ids:
                metadata["chunks"].append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "metadata": chunk.metadata
                })

        # 保存
        self._save_index(library_id, index)
        self._save_metadata(library_id, metadata)

    def search(
        self,
        library_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[QueryResult]:
        """搜索向量库"""
        try:
            metadata = self._load_metadata(library_id)
            if not metadata["chunks"]:
                return []
        except Exception:
            return []

        try:
            index = self._load_index(library_id, len(query_embedding))
            if index.ntotal == 0:
                return []
        except Exception:
            return []

        # 归一化查询向量
        query_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vec)

        # 搜索
        k = min(top_k, index.ntotal)
        distances, indices = index.search(query_vec, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            chunk_info = metadata["chunks"][idx]
            # 转换距离为相似度分数
            score = float(distances[0][i])
            score = (score + 1) / 2  # 转换到 0-1 范围

            results.append(QueryResult(
                content=chunk_info["content"],
                score=score,
                source=chunk_info["metadata"].get("file_name", "unknown"),
                library_id=library_id
            ))

        return results

    def search_all(
        self,
        query_embedding: List[float],
        library_ids: List[str],
        top_k: int = 5
    ) -> List[QueryResult]:
        """搜索所有指定库"""
        all_results = []
        for library_id in library_ids:
            results = self.search(library_id, query_embedding, top_k)
            all_results.extend(results)

        # 按分数排序
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

    def delete_library(self, library_id: str):
        """删除库"""
        lib_dir = self.data_dir / library_id
        if lib_dir.exists():
            for f in lib_dir.glob("*"):
                f.unlink()
            lib_dir.rmdir()

    def get_library_stats(self, library_id: str) -> Dict:
        """获取库统计信息"""
        try:
            metadata = self._load_metadata(library_id)
            return {"chunk_count": len(metadata.get("chunks", []))}
        except Exception:
            return {"chunk_count": 0}

    def get_chunks(self, library_id: str) -> List[Dict]:
        """获取库的所有分块"""
        try:
            metadata = self._load_metadata(library_id)
            return metadata.get("chunks", [])
        except Exception:
            return []


class LibraryManager:
    """RAG 库管理器"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.libraries_file = self.data_dir / "libraries.json"
        self._libraries: Dict[str, dict] = {}
        self._load_libraries()

    def _load_libraries(self):
        """加载库列表"""
        if self.libraries_file.exists():
            try:
                with open(self.libraries_file, "r", encoding="utf-8") as f:
                    self._libraries = json.load(f)
            except Exception as e:
                print(f"Error loading libraries: {e}")
                self._libraries = {}

    def _save_libraries(self):
        """保存库列表"""
        with open(self.libraries_file, "w", encoding="utf-8") as f:
            json.dump(self._libraries, f, ensure_ascii=False, indent=2)

    def create_library(self, library_id: str, name: str, source_path: str, description: str = None) -> dict:
        """创建新库"""
        self._libraries[library_id] = {
            "id": library_id,
            "name": name,
            "source_path": source_path,
            "description": description,
            "created_at": "",
            "updated_at": "",
            "document_count": 0,
            "chunk_count": 0
        }
        self._save_libraries()
        return self._libraries[library_id]

    def get_library(self, library_id: str) -> Optional[dict]:
        """获取库信息"""
        return self._libraries.get(library_id)

    def list_libraries(self) -> List[dict]:
        """列出所有库"""
        return list(self._libraries.values())

    def update_library(self, library_id: str, **kwargs):
        """更新库信息"""
        if library_id in self._libraries:
            self._libraries[library_id].update(kwargs)
            self._save_libraries()

    def delete_library(self, library_id: str):
        """删除库"""
        if library_id in self._libraries:
            del self._libraries[library_id]
            self._save_libraries()


# 全局单例
vector_store = VectorStore()
library_manager = LibraryManager(settings.DATA_DIR)
