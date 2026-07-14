"""配置文件"""
import json
from pathlib import Path
from typing import Optional


class Config:
    """应用配置（支持运行时修改）"""

    _instance: Optional['Config'] = None

    def __init__(self):
        self.BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
        self.DATA_DIR: Path = self.BASE_DIR / "data"
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Ollama 配置
        self.OLLAMA_BASE_URL: str = "http://localhost:11434"
        self.OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
        self.OLLAMA_EMBED_BATCH_SIZE: int = 32

        # 文档处理配置（可运行时修改）
        self.CHUNK_SIZE: int = 500
        self.CHUNK_OVERLAP: int = 50

        # API 配置
        self.API_HOST: str = "0.0.0.0"
        self.API_PORT: int = 8000

        # 配置文件路径
        self.config_file = self.DATA_DIR / "config.json"
        self._load_config()

    @classmethod
    def get_instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_config(self):
        """从文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.CHUNK_SIZE = data.get("chunk_size", 500)
                    self.CHUNK_OVERLAP = data.get("chunk_overlap", 50)
                    self.OLLAMA_BASE_URL = data.get("ollama_base_url", self.OLLAMA_BASE_URL)
                    self.OLLAMA_EMBED_MODEL = data.get("ollama_embed_model", self.OLLAMA_EMBED_MODEL)
            except Exception as e:
                print(f"Error loading config: {e}")

    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "chunk_size": self.CHUNK_SIZE,
                    "chunk_overlap": self.CHUNK_OVERLAP,
                    "ollama_base_url": self.OLLAMA_BASE_URL,
                    "ollama_embed_model": self.OLLAMA_EMBED_MODEL,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._save_config()

    def get_chunk_config(self) -> dict:
        """获取分块配置"""
        return {
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
        }


# 全局单例
settings = Config.get_instance()
