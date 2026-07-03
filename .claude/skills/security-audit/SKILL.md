---
name: security-audit
description: 代码安全审计 — 检查敏感信息泄露、注入漏洞、配置风险、API安全等
---

# 安全审计 — 全面代码安全检查

请按以下流程逐步审计当前项目的安全隐患，最后给出一份中文报告。

---

## 审计标准

参照 OWASP Top 10 常见安全风险，结合本项目实际情况（FastAPI 后端 + LangChain RAG + React 前端 + SQLite 数据库 + 阿里云百炼 API），重点检查以下方面。

---

## 第 1 步：确定检查范围

先问用户要检查哪些文件。如果用户没指定，默认检查以下类型的文件：
- 所有 `.py`、`.ts`、`.tsx` 源码文件
- `.json`、`.yaml`、`.env`、`.env.example` 配置文件
- `pyproject.toml`、`package.json` 项目配置

跳过：`node_modules/`、`__pycache__/`、`backend/data/`、`.git/`、`*.min.js`

---

## 第 2 步：逐项检查

### 检查项 A：硬编码敏感信息

用正则和关键词搜索以下内容：

| 风险 | 搜索关键词 |
|------|-----------|
| 密码 | `password`、`passwd`、`pwd`、`密码`、`secret`、`secret_key` |
| API 密钥 | `api_key`、`apikey`、`dashscope`、`DASHSCOPE_API_KEY`、`token` |
| JWT 密钥 | `jwt_secret`、`JWT_SECRET`、`SECRET_KEY` |
| 私钥 | `PRIVATE KEY`、`-----BEGIN` |
| 数据库密码 | `database.*password`、`db_pass`、`DATABASE_URL` |
| 硬编码 URL 含凭据 | `http://user:pass@` |

判定方式：如果在代码中找到上述关键词的值是**明文字符串**（如 `api_key = "sk-abc123"`），标记为 🔴 严重。如果是环境变量引用（如 `os.getenv("DASHSCOPE_API_KEY")` 或 `get_settings().dashscope_api_key`），标记为 ✅ 安全。

### 检查项 B：SQL 注入风险

针对本项目使用 SQLAlchemy 2.0 async + aiosqlite，检查：

- ✅ **安全模式**：使用 ORM 查询（`select(Model).where(...)`）+ 参数绑定 → 安全
- 🔴 **危险模式**：使用 `text()` 或 `conn.execute()` 拼接用户输入字符串 → 严重
- 🟡 **需复核**：动态拼接表名/列名（`ORDER BY` 等无法参数化的场景）→ 需人工确认输入来源

逐文件扫描所有数据库查询，逐一标注。

### 检查项 C：配置文件敏感信息

检查以下文件是否包含明文敏感信息：

- `.env` / `.env.example` — 检查是否误提交了真实 API 密钥
- `backend/app/config.py` — 检查默认值是否包含真实密钥
- `frontend/.env` / `frontend/.env.local` — 前端环境变量
- `.claude/settings.json` — 是否包含明文 Token
- `package.json` — 检查 `scripts` 中是否嵌入了密钥

### 检查项 D：FastAPI 安全配置

| 检查点 | 说明 |
|--------|------|
| CORS 配置 | `allow_origins` 是否为 `["*"]`（生产环境应限制具体域名） |
| JWT 密钥强度 | `jwt_secret` 是否足够长（建议 ≥ 32 字符随机字符串） |
| JWT 过期时间 | access_token 过期时间是否合理（建议 15-30 分钟） |
| 文件上传校验 | 是否校验了文件类型、大小限制、文件名（防止路径遍历） |
| 错误响应 | 是否向客户端暴露了堆栈追踪、文件路径、数据库结构 |
| 请求限流 | 是否有 rate limiting 防止暴力破解和 API 滥用 |
| 依赖注入 | `get_current_user` 是否正确验证了 Token 有效性 |

### 检查项 E：LLM / RAG 安全

| 检查点 | 说明 |
|--------|------|
| API Key 存储 | DashScope API Key 是否只通过环境变量/配置文件读取，不硬编码 |
| Prompt 注入 | 用户输入是否直接拼接到 system prompt 中（可能被越权操纵） |
| 知识库权限 | 普通用户能否访问/修改知识库管理接口（应仅限 admin） |
| SSE 端点鉴权 | 流式接口是否验证了 JWT Token |
| 敏感数据泄露 | RAG 检索的知识库内容是否可能包含敏感信息返回给无权限用户 |

### 检查项 F：不安全的动态代码执行

搜索以下危险模式：

**Python：**
| 风险 | 模式 |
|------|------|
| 🔴 `eval()` | 执行任意字符串为 Python 代码 |
| 🔴 `exec()` | 执行任意代码块 |
| 🔴 `compile()` + `exec` | 等价于 eval |
| 🟡 `__import__()` | 动态导入可能被利用 |
| 🟡 `pickle.load()` | 反序列化不受信任的数据 |

**TypeScript/React：**
| 风险 | 模式 |
|------|------|
| 🔴 `eval()` | 执行任意字符串为代码 |
| 🔴 `new Function()` | 等价于 eval |
| 🟡 `innerHTML` | 可能造成 XSS（react-markdown 的 rehype 插件需检查） |
| 🟡 `dangerouslySetInnerHTML` | React 中明确标记为危险的 API |

### 检查项 G：其他常见隐患

| 检查点 | 说明 |
|--------|------|
| 调试信息泄露 | `console.log` / `print()` / `logger.debug()` 是否打印了密码、完整 Token、数据库内容 |
| 路径遍历 | 文件上传保存路径是否过滤了 `../`（`upload_document` 中的 `stored_name`） |
| 依赖漏洞 | Python: `pip-audit` 或检查 `pyproject.toml`；Node: `npm audit` |
| 密码哈希 | 是否使用 bcrypt（已确认 ✅），是否有 salt |
| Token 黑名单 | 登出时 Token 是否加入撤销列表（`revoked_tokens` 表） |
| 会话隔离 | 用户 A 能否通过修改 session_id 访问用户 B 的会话 |

---

## 第 3 步：生成报告

用以下格式输出：

```
🔒 安全审计报告
══════════════════════════════════
审计时间：YYYY-MM-DD HH:MM
审计范围：X 个文件
风险等级：🔴 严重 / 🟡 警告 / 🔵 建议 / ✅ 安全
══════════════════════════════════

📊 总览
┌──────────────────────┬────┬────┬────┬────┐
│ 检查项               │ 🔴 │ 🟡 │ 🔵 │ ✅ │
├──────────────────────┼────┼────┼────┼────┤
│ A. 硬编码敏感信息    │  0 │  0 │  0 │  5 │
│ B. SQL 注入          │  0 │  1 │  0 │  8 │
│ C. 配置文件明文      │  0 │  0 │  1 │  3 │
│ D. FastAPI 安全配置  │  0 │  1 │  1 │  4 │
│ E. LLM/RAG 安全      │  0 │  0 │  1 │  4 │
│ F. 动态代码执行      │  0 │  1 │  0 │  5 │
│ G. 其他隐患          │  0 │  0 │  1 │  5 │
└──────────────────────┴────┴────┴────┴────┘

────────────────────────────────

🔴 严重风险（需立即修复）

1. [A-001] 文件：backend/app/config.py:15
   问题：JWT 密钥使用弱密码
   代码：jwt_secret: str = "changeme"
   建议：生成随机强密钥，通过环境变量注入

2. [E-001] 文件：backend/app/api/knowledge.py:25
   问题：知识库删除接口缺少 admin 权限校验
   建议：添加 `dependencies=[Depends(require_admin)]`

────────────────────────────────

🟡 警告（建议修复）

1. [D-001] 文件：backend/app/main.py:30
   问题：CORS allow_origins=["*"] 允许任意来源
   建议：生产环境改为具体域名列表

────────────────────────────────

🔵 改进建议（可选）

1. [G-001] 建议对聊天接口添加 rate limiting

────────────────────────────────

✅ 安全项（无需处理）

- A 项：所有 API 密钥均通过环境变量/配置文件读取 ✅
- B 项：所有数据库查询均使用 SQLAlchemy ORM ✅
```

---

## 第 4 步：询问是否修复

报告生成后，问用户：
- "要我帮你修复这些安全问题吗？"

按照 🔴 严重 → 🟡 警告 → 🔵 建议 的顺序修复，修改前先让用户确认每项改动。
