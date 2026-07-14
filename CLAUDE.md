# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

X-RAG 是一个本地文档 RAG（检索增强生成）系统，支持多知识库管理和跨库查询。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python + FastAPI |
| 文档解析 | PDF (pdfplumber)、Markdown、TXT |
| 向量存储 | ChromaDB |
| Embedding | Ollama (nomic-embed-text) |
| 前端 | React 18 + TypeScript + Ant Design + Vite |

## 目录结构

```
x-rag/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── main.py       # 应用入口
│   │   ├── config.py     # 配置 (ChromaDB、Ollama、分块参数)
│   │   ├── models.py     # Pydantic 数据模型
│   │   ├── routers/      # API 路由
│   │   │   ├── libraries.py  # 库管理接口
│   │   │   └── rag.py         # RAG 查询接口
│   │   └── services/    # 核心服务
│   │       ├── parser.py      # 文档解析
│   │       ├── chunker.py    # 文本分块
│   │       ├── embed.py      # Ollama Embedding
│   │       └── store.py      # ChromaDB 存储 + 库管理
│   └── run.py            # 启动脚本
├── frontend/             # React 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Libraries.tsx  # 知识库管理页面
│   │   │   └── Chat.tsx      # RAG 查询页面
│   │   ├── services/api.ts   # API 调用封装
│   │   └── App.tsx           # 路由配置
│   └── vite.config.ts        # Vite 配置 (API 代理)
├── data/                 # RAG 库存储 (ChromaDB + libraries.json)
└── CLAUDE.md
```

## 常用命令

```bash
# 安装后端依赖
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt

# 启动后端 (端口 8000)
python run.py

# 安装前端依赖
cd frontend
npm install

# 启动前端开发服务器 (端口 3000)
npm run dev

# 前端构建生产版本
npm run build
```

## 前置条件

- **Ollama**: 必须运行在 `localhost:11434`，且加载 `nomic-embed-text` 模型
  ```bash
  ollama serve
  ollama pull nomic-embed-text
  ```

## API 接口

### 库管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/libraries` | 列出所有知识库 |
| POST | `/api/libraries` | 创建知识库 |
| GET | `/api/libraries/{id}` | 获取库详情 |
| DELETE | `/api/libraries/{id}` | 删除知识库 |
| POST | `/api/libraries/{id}/scan` | 扫描并建立索引 |
| GET | `/api/libraries/{id}/progress` | 获取扫描进度 |

### RAG 查询

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/rag/query` | 执行 RAG 查询 |

### 查询参数

```json
{
  "query": "查询文本",
  "library_id": "可选，指定库ID",
  "top_k": 5
}
```

## 数据流

1. **创建库**: 指定文件夹路径 → 系统注册库信息
2. **扫描索引**: 遍历文件夹 → 解析 PDF/MD/TXT → 文本分块 → Ollama Embedding → 存入 ChromaDB
3. **查询**: 用户输入 → Embedding → ChromaDB 相似度检索 → 返回结果

## 配置项 (backend/app/config.py)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `CHUNK_SIZE` | `500` | 文本分块大小 |
| `CHUNK_OVERLAP` | `50` | 分块重叠大小 |
| `CHROMA_PERSIST_DIR` | `data/chroma_db` | ChromaDB 持久化目录 |

## 多库设计

- 每个顶级文件夹 = 一个独立知识库
- 库 ID = 文件夹名称
- ChromaDB 中每个库对应一个 collection
- 查询可指定单个库或搜索所有库
