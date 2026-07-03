---
name: unit-test
description: 为项目创建单元测试、执行测试、生成测试报告
---

# 单元测试 — 创建、执行、报告

请按以下流程逐步操作，每步完成后简要告诉用户进展。

---

## 第 1 步：评估项目

先搞清楚三个问题：

1. **这是什么类型的项目？**（Electron / React / Vue / Node.js / Python / 纯前端 / 其他）
2. **有没有现成的测试框架？**（检查 `package.json` 里有没有 jest、vitest、mocha、pytest 等）
3. **适合用什么测试工具？**（根据项目类型推荐，用通俗语言告诉用户为什么选它）

常用推荐（按项目类型）：

| 项目类型 | 推荐框架 | 一句话理由 |
|----------|---------|-----------|
| Electron / Node.js | Vitest | 快、简单、零配置 |
| React | Vitest + Testing Library | 业界标配 |
| Vue | Vitest | Vue 官方推荐 |
| 纯前端 JS | Vitest + jsdom | 模拟浏览器环境 |
| Python | pytest | Python 界最流行 |
| TypeScript | Vitest | 原生支持 TS |
| FastAPI 全栈 | pytest + Vitest | 后端 pytest，前端 vitest |

## 第 2 步：安装测试框架

如果项目还没有测试框架：
- 告诉用户要装什么
- 安装命令由用户确认后执行
- 安装完成后，在对应配置中加入测试命令

如果已有测试框架，跳过安装，直接说"已检测到 XXX，跳过安装"。

## 第 3 步：找出可测试的代码

扫描项目源码，列出哪些函数 / 模块适合写单元测试。优先选择：

- **纯函数**（输入确定 → 输出确定，不依赖外部状态）
- **工具函数**（格式化、计算、校验类）
- **业务逻辑**（和数据、计算相关的核心代码）
- **API 端点**（使用 TestClient 测试 FastAPI 路由）

跳过这些：
- 直接操作 DOM 的函数（需要额外配置）
- 调用外部 API 的函数（需要 mock）
- 需要真实数据库连接的函数（需要 mock session）

告诉用户大概可以测几个模块，挑最有价值的开始。

## 第 4 步：编写测试

### Python 后端（pytest）

在 `backend/tests/` 创建测试文件。

命名规则：`tests/test_模块名.py`

每条测试遵循 AAA 模式：
- **安排（Arrange）**：准备好测试数据和环境
- **执行（Act）**：调用要测试的函数
- **断言（Assert）**：检查结果是否符合预期

```python
import pytest
from app.core.security import hash_password, verify_password

def test_hash_and_verify_password():
    """测试密码哈希和验证"""
    password = "test123456"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False
```

关键规则：
- 正常情况（happy path）至少测 1 个
- 边界情况至少测 1 个（空值、负数、零、超大值等）
- 用中文写测试描述
- 使用 pytest fixtures 管理测试依赖

### TypeScript 前端（vitest）

在 `frontend/src/__tests__/` 创建测试文件。

命名规则：`__tests__/模块名.test.ts`

```typescript
import { describe, it, expect } from 'vitest';

describe('工具函数', () => {
  it('应该正确计算', () => {
    expect(1 + 1).toBe(2);
  });
});
```

## 第 5 步：执行测试

### Python 后端
```bash
cd backend && python -m pytest tests/ -v
```

### TypeScript 前端
```bash
cd frontend && npx vitest run
```

捕获输出结果。

## 第 6 步：测试报告

用清晰的中文向用户报告结果，格式如下：

```
📊 测试报告
══════════════════════════
  ✅ 通过：X 个
  ❌ 失败：X 个
  ⏭ 跳过：X 个
  ⏱ 耗时：Xms
══════════════════════════

【通过的测试】
✅ 安全模块 — 密码哈希和验证正确
✅ 安全模块 — 拒绝错误密码

【失败的测试】（如果有）
❌ 某测试
   期望结果：XXX
   实际结果：YYY
```

- 如果有失败的测试，帮用户分析原因并询问是否要修复
- 如果全部通过，恭喜用户
