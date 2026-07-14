"""文本分块服务"""
from typing import List
from ..models import ParsedDocument, DocumentChunk


class TextChunker:
    """文本分块器"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: ParsedDocument) -> List[DocumentChunk]:
        """将文档分块"""
        if not doc.chunks:
            return []

        all_chunks = []
        for original_chunk in doc.chunks:
            chunks = self._split_text(original_chunk.content, original_chunk.metadata)
            all_chunks.extend(chunks)

        # 重新编号
        result = []
        for i, chunk in enumerate(all_chunks):
            result.append(DocumentChunk(
                chunk_id=f"{doc.doc_id}_{i}",
                content=chunk["content"],
                metadata={**chunk["metadata"], "doc_id": doc.doc_id, "file_name": doc.file_name}
            ))
        return result

    def _split_text(self, text: str, metadata: dict) -> List[dict]:
        """拆分文本为小块"""
        if len(text) <= self.chunk_size:
            return [{"content": text, "metadata": metadata}]

        chunks = []
        start = 0
        chunk_num = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            # 尝试在句号或换行符处分割
            if end < len(text):
                split_pos = self._find_split_point(chunk_text)
                if split_pos > 0:
                    chunk_text = chunk_text[:split_pos]
                    start = start + split_pos
                else:
                    start = end
            else:
                start = end

            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text.strip(),
                    "metadata": {**metadata, "chunk_num": chunk_num}
                })
                chunk_num += 1

            # 重叠处理
            if start < len(text):
                start = start - self.chunk_overlap
                if start < 0:
                    start = 0

        return chunks

    def _find_split_point(self, text: str) -> int:
        """找到合适的分割点"""
        # 优先在换行符处分割
        for sep in ["\n\n", "\n", "。", ". ", "！", "！", "？", "?"]:
            last_pos = text.rfind(sep)
            if last_pos > self.chunk_size * 0.5:
                return last_pos + len(sep)
        return -1

    def chunk_documents(self, docs: List[ParsedDocument]) -> List[DocumentChunk]:
        """批量分块"""
        all_chunks = []
        for doc in docs:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks
