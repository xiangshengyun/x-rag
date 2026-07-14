# X-RAG

本地文档 RAG 系统，支持多知识库管理和跨库查询。

## 功能特性

- 📁 **多知识库管理**: 每个文件夹独立建库
- 📄 **支持多种格式**: PDF、Markdown、TXT
- 🔍 **向量检索**: 基于 FAISS + Ollama
- 🌐 **Web UI**: React 前端，易于使用
- 🔌 **RESTful API**: 方便集成和扩展
- ⚙️ **分块策略可调**: 支持配置分块大小和重叠

## 快速开始

### 1. 启动 Ollama

```bash
ollama serve
ollama pull nomic-embed-text
```

### 2. 验证 Ollama

```powershell
# Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:11434/api/embeddings" -Method Post -ContentType "application/json" -Body '{"model":"nomic-embed-text","prompt":"罗胖在2016年跨年演讲中"}'
```

### 3. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 5. 使用

1. 打开 http://localhost:3000
2. 添加知识库（指定文件夹路径）
3. 点击"建立索引"扫描文档
4. 进入"查询"页面搜索

## 技术栈

- **后端**: Python + FastAPI
- **向量存储**: FAISS
- **Embedding**: Ollama (nomic-embed-text)
- **前端**: React + Ant Design + Vite
