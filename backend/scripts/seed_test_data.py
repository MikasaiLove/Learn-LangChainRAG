"""压力测试数据种子脚本 — 创建 100 用户 + 会话 + 消息"""

import asyncio
import json
import os
import sys
import uuid
import shutil

# === MUST be before any app.* imports ===
TEST_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_stress_test"
)
TEST_CREDENTIALS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tests", "stress", "test_data.json",
)

# Override DB path BEFORE importing from app
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DATA_DIR}/app.db"
os.environ["CHROMA_PERSIST_DIR"] = os.path.join(TEST_DATA_DIR, "chroma")
os.environ["UPLOAD_DIR"] = os.path.join(TEST_DATA_DIR, "uploads")

# Ensure project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, async_sessionmaker, init_db
from app.core.security import hash_password
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from sqlalchemy import select

NUM_USERS = 100
SESSIONS_PER_USER = 3
MESSAGES_PER_SESSION = 4


async def seed():
    """创建测试数据"""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    data = {"users": [], "sessions": {}}

    async with session_factory() as db:
        result = await db.execute(select(User).where(User.username == "testuser_001"))
        if result.scalar_one_or_none():
            print("[SKIP] Test data already exists. Delete data_stress_test/ to rebuild.")
            return

        common_hash = hash_password("Test@123456")

        for i in range(1, NUM_USERS + 1):
            username = f"testuser_{i:03d}"
            role = "admin" if i <= 10 else "user"

            user = User(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=common_hash,
                role=role,
            )
            db.add(user)
            await db.flush()

            data["users"].append({
                "username": username,
                "password": "Test@123456",
                "role": role,
            })

            user_sessions = []
            titles = ["商品咨询", "规格对比", "售后问题"]
            questions = ["这个产品有什么颜色？", "价格是多少？"]
            answers = [
                "该产品有黑色、白色、蓝色三种颜色可选。",
                "价格在299-599元之间，具体取决于配置和颜色。",
            ]

            for s in range(SESSIONS_PER_USER):
                session_id = str(uuid.uuid4())
                session = Session(
                    id=session_id,
                    user_id=user.id,
                    title=f"测试会话{s+1} - {titles[s % 3]}",
                )
                db.add(session)
                await db.flush()

                for m in range(MESSAGES_PER_SESSION):
                    is_user = m % 2 == 0
                    msg = Message(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        role="user" if is_user else "assistant",
                        content=questions[m // 2] if is_user else answers[m // 2],
                        citations=[],
                    )
                    db.add(msg)

                user_sessions.append(session_id)

            data["sessions"][username] = user_sessions

            if i % 20 == 0:
                print(f"  Created {i}/{NUM_USERS} users...")

        await db.commit()

    os.makedirs(os.path.dirname(TEST_CREDENTIALS_FILE), exist_ok=True)
    with open(TEST_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Done!")
    print(f"   Users: {NUM_USERS} (10 admin + 90 user)")
    print(f"   Sessions: {NUM_USERS * SESSIONS_PER_USER}")
    print(f"   Messages: {NUM_USERS * SESSIONS_PER_USER * MESSAGES_PER_SESSION}")
    print(f"   Credentials: {TEST_CREDENTIALS_FILE}")


def setup_test_dir():
    """复制正式数据目录到测试目录（保留 chroma 向量）"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(base_dir, "data")
    dst = TEST_DATA_DIR

    if os.path.exists(dst):
        print(f"[SKIP] {dst} already exists.")
        return

    os.makedirs(dst, exist_ok=True)

    # 复制 chroma 和 uploads 目录结构
    for sub in ["chroma", "uploads"]:
        sub_src = os.path.join(src, sub)
        sub_dst = os.path.join(dst, sub)
        if os.path.exists(sub_src) and not os.path.exists(sub_dst):
            shutil.copytree(sub_src, sub_dst)
            print(f"  Copied {sub}/")

    print(f"  Created test data directory: {dst}")


def main():
    setup_test_dir()

    # 初始化测试数据库表结构
    init_db_sync()
    # 创建种子数据
    asyncio.run(seed())


def init_db_sync():
    """同步初始化测试数据库表（调用数据库模块的 init_db）"""
    import asyncio as _a
    _a.run(init_db())


if __name__ == "__main__":
    main()
