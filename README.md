# Learn-LangChainRAG

基于 LangChain 的 RAG 企业级知识库问答系统，面向电商平台商品咨询场景。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **LLM** | 阿里云百炼 DashScope (`qwen-plus`) | 对话生成 |
| **Embedding** | 百炼 `text-embedding-v3` | 向量化 |
| **RAG 框架** | LangChain + LangChain Community | 检索增强生成 |
| **向量数据库** | Chroma | 嵌入式向量存储 |
| **后端** | FastAPI + SQLAlchemy 2.0 + aiomysql | REST + SSE 流式 |
| **数据库** | MySQL 8.0 | 支持高并发读写 |
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
- MySQL 8.0+
- 阿里云百炼 API Key ([DashScope](https://dashscope.console.aliyun.com/))

### 1. 配置环境

```bash
# 克隆项目
git clone https://github.com/MikasaiLove/Learn-LangChainRAG.git
cd Learn-LangChainRAG
```

**MySQL 数据库：**

```sql
-- 在 Navicat 或 MySQL 命令行中创建数据库
CREATE DATABASE IF NOT EXISTS langchain_rag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**配置 .env 文件：**

```bash
cd backend
cp .env.example .env   # 如果存在模板文件
# 编辑 .env，填入你的 API Key 和 MySQL 连接信息
```

`.env` 关键配置：

```ini
DASHSCOPE_API_KEY=你的百炼API密钥
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/langchain_rag
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

### 单元测试

```bash
# 后端 (pytest)
cd backend && pytest -v

# 前端 (vitest)
cd frontend && npm test
```

### 压力测试 (Locust)

模拟高并发场景，验证系统吞吐与瓶颈。

```bash
pip install locust
cd backend/tests/stress
```

**分阶段运行：**

| 阶段 | 场景 | 命令 |
|------|------|------|
| Phase 1 | Health Check 基准 | `export LOCUST_PHASE=health && locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 2m --host http://localhost:8000` |
| Phase 2 | 认证 + 会话列表 | `export LOCUST_PHASE=auth && locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 3m --host http://localhost:8000` |
| Phase 3 | 知识库管理 | `export LOCUST_PHASE=kb && locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m --host http://localhost:8000` |
| Phase 4 | RAG 对话 (Mock LLM) | `export LOCUST_PHASE=chat && locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --host http://localhost:8000` |
| Phase 5 | 真实 LLM (少量) | `export LOCUST_PHASE=chat_real && locust -f locustfile.py --headless --users 5 --spawn-rate 2 --run-time 2m --host http://localhost:8000` |

**Web UI 模式（实时图表）：**

```bash
export LOCUST_PHASE=chat && locust -f locustfile.py --host http://localhost:8000
# 打开 http://localhost:8089 查看实时面板
```

**Mock 模式（不消耗 API 额度）：**

```bash
export STRESS_TEST_MOCK_LLM=true
# 压力测试使用独立数据库，避免污染正式数据
export DATABASE_URL="mysql+aiomysql://root:密码@localhost:3306/langchain_rag_stress_test"
export CHROMA_PERSIST_DIR="./data_stress_test/chroma"
# 先在 Navicat 中创建 langchain_rag_stress_test 库，再运行以下命令
python scripts/seed_test_data.py          # 生成 100 用户 + 300 会话
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 200
```

### 压力测试结果

| Phase | 场景 | 并发 | 请求数 | 失败 | 平均延迟 | P95 | 结论 |
|-------|------|:--:|------|:--:|------|------|------|
| 1 | Health Check | 100 | 36,810 | 0 | 8ms | 7ms | ✅ FastAPI 层无瓶颈 |
| 4 | RAG Mock (18并发) | 18 | 13 | 0 | 6,078ms | 8,100ms | ✅ 稳定，零失败 |
| 5 | 真实 LLM | 5 | 6 | 0 | 5,540ms | 7,400ms | ✅ 百炼免费额度够用 |

**发现的瓶颈：**
1. **首字延迟偏高** (5-6s) — Mock 和真实 LLM 接近，说明瓶颈在 Chroma 检索 + DB 写入，不在 LLM
2. **bcrypt CPU 消耗** — 登录时 bcrypt.checkpw 约 250ms/次，高并发会饱和所有核心
3. **Chroma 线程池** — 嵌入式向量检索受限于 `asyncio.to_thread` 默认线程数

> 已从 SQLite 迁移到 MySQL 解决了单写者锁问题，高并发写入不再排队阻塞。

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
│   │   ├── rag/           # RAG 管道 (含 Mock LLM 开关)
│   │   └── main.py        # 入口
│   ├── scripts/           # 工具脚本 (种子数据等)
│   ├── tests/
│   │   ├── stress/        # Locust 压力测试
│   │   │   ├── locustfile.py
│   │   │   ├── scenarios/ # 5 阶段场景
│   │   │   └── helpers/   # SSE 客户端 / Token 缓存
│   │   ├── test_config.py
│   │   ├── test_security.py
│   │   └── test_prompts.py
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

## License

MIT
