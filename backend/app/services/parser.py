"""文档解析服务"""
import hashlib
import pdfplumber
from pathlib import Path
from typing import List, Optional
import markdown
from ..models import ParsedDocument, DocumentChunk


class DocumentParser:
    """文档解析器"""

    SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".markdown"}

    @classmethod
    def get_doc_id(cls, file_path: Path) -> str:
        """生成文档唯一ID"""
        return hashlib.md5(str(file_path).encode()).hexdigest()[:12]

    @classmethod
    def get_file_type(cls, file_path: Path) -> str:
        """获取文件类型"""
        ext = file_path.suffix.lower()
        if ext == ".markdown":
            return "md"
        return ext.lstrip(".")

    @classmethod
    def parse_file(cls, file_path: Path) -> Optional[ParsedDocument]:
        """解析单个文件"""
        if not file_path.exists():
            return None

        ext = file_path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            return None

        doc_id = cls.get_doc_id(file_path)
        file_type = cls.get_file_type(file_path)

        try:
            if ext == ".pdf":
                content = cls._parse_pdf(file_path)
            elif ext in {".md", ".markdown"}:
                content = cls._parse_markdown(file_path)
            else:  # .txt
                content = cls._parse_txt(file_path)

            if not content.strip():
                return None

            return ParsedDocument(
                doc_id=doc_id,
                file_name=file_path.name,
                file_type=file_type,
                chunks=[DocumentChunk(chunk_id=f"{doc_id}_{0}", content=content)]
            )
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    @classmethod
    def _parse_pdf(cls, file_path: Path) -> str:
        """解析 PDF 文件"""
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    @classmethod
    def _parse_markdown(cls, file_path: Path) -> str:
        """解析 Markdown 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        # 转换为纯文本
        md = markdown.Markdown()
        html = md.convert(md_content)
        # 简单去除 HTML 标签
        import re
        text = re.sub(r'<[^>]+>', '', html)
        return text

    @classmethod
    def _parse_txt(cls, file_path: Path) -> str:
        """解析 TXT 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def scan_directory(cls, directory: Path) -> List[ParsedDocument]:
        """扫描目录下的所有支持的文件"""
        documents = []
        for ext in cls.SUPPORTED_EXTENSIONS:
            for file_path in directory.rglob(f"*{ext}"):
                doc = cls.parse_file(file_path)
                if doc:
                    documents.append(doc)
        return documents
