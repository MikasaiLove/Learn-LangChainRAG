# Learn-LangChainRAG

基于 LangChain 的 RAG 企业级知识库问答系统，面向电商平台商品咨询场景。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **LLM** | 阿里云百炼 DashScope (`qwen-plus`) | 对话生成 |
| **Embedding** | 百炼 `text-embedding-v3` | 向量化 |
| **RAG 框架** | LangChain + LangChain Community | 检索增强生成 |
| **向量数据库** | Chroma | 嵌入式向量存储 |
| **后端** | FastAPI + SQLAlchemy 2.0 + aiosqlite | REST + SSE 流式 |
| **前端** | React 19 + TypeScript + Vite + Ant Design 5 | SPA |
| **认证** | JWT 双 Token（access + refresh）| bcrypt 密码哈希 |

## 功能

- 🔐 注册 / 登录 / 修改密码 / JWT 鉴权
- 💬 多会话管理，SSE 流式对话
- 📚 知识库文档上传（PDF / DOCX / TXT / MD / CSV / HTML）
- 🔍 自动分块 + 向量化 + 语义检索
- 📊 Token 消耗统计（input / output / total）
- 🎨 聊天背景自定义
- 👤 AI 人设：忍野忍（物语系列）

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+
- 阿里云百炼 API Key ([DashScope](https://dashscope.console.aliyun.com/))

### 1. 配置环境

```bash
# 克隆项目
git clone https://github.com/MikasaiLove/Learn-LangChainRAG.git
cd Learn-LangChainRAG

# 创建 .env 文件
echo DASHSCOPE_API_KEY=你的百炼API密钥 > .env
```

### 2. 安装依赖

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 3. 初始化管理员

```bash
cd backend
python -m app.init_admin
# 自动创建 admin / 123456
```

### 4. 启动

**一键启动：** 双击 `start.bat`

**手动启动：**

```bash
# 终端 1 — 后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 终端 2 — 前端
cd frontend
npm run dev
```

访问 http://localhost:5173 开始使用。

### 5. 其他脚本

| 脚本 | 用途 |
|------|------|
| `start.bat` | 一键启动 |
| `start-silent.bat` | 后台静默启动 |
| `stop.bat` | 停止所有服务 |
| `view-log.bat` | 查看日志 |

## 项目结构

```
Learn-LangChainRAG/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI 路由
│   │   ├── core/          # 数据库 / 安全 / 日志
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 校验
│   │   ├── services/      # 业务逻辑
│   │   ├── rag/           # RAG 管道
│   │   └── main.py        # 入口
│   ├── tests/             # pytest 单元测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios 请求封装
│   │   ├── pages/         # 页面组件
│   │   ├── stores/        # Zustand 状态
│   │   └── __tests__/     # Vitest 单元测试
│   └── package.json
├── .claude/               # Claude Code 技能与 Agent
├── start.bat
├── stop.bat
└── view-log.bat
```

## API 文档

启动后端后访问 http://localhost:8000/docs (Swagger UI)

## 运行测试

```bash
# 后端
cd backend && pytest -v

# 前端
cd frontend && npm test
```

## License

MIT
