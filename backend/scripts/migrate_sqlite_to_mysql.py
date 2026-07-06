"""将 SQLite 数据迁移到 MySQL"""
import asyncio
import os
import sys

# 先设置 SQLite 连接读取旧数据
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/app.db"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# 1. 从 SQLite 读取所有数据
async def read_sqlite():
    engine = create_async_engine("sqlite+aiosqlite:///./data/app.db", echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 读取所有表的数据
        tables = ["users", "sessions", "messages", "documents", "revoked_tokens"]
        data = {}
        for table in tables:
            result = await session.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            columns = result.keys()
            data[table] = [dict(zip(columns, row)) for row in rows]
            print(f"  [SQLite] {table}: {len(data[table])} 条记录")

    await engine.dispose()
    return data


# 2. 写入 MySQL
async def write_mysql(data):
    # 切换到 MySQL
    engine = create_async_engine(
        "mysql+aiomysql://root:123456@localhost:3306/langchain_rag",
        echo=False,
        pool_recycle=3600,
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 按依赖顺序插入：先 users，再 sessions，再 messages，再 documents，最后 revoked_tokens
        table_order = ["users", "sessions", "messages", "documents", "revoked_tokens"]

        for table in table_order:
            rows = data.get(table, [])
            if not rows:
                continue

            for row in rows:
                columns = ", ".join(row.keys())
                placeholders = ", ".join([f":{k}" for k in row.keys()])
                sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
                try:
                    await session.execute(text(sql), row)
                except Exception as e:
                    print(f"  [WARN] {table} 插入失败: {e} | row: {row.get('id', '?')}")

        await session.commit()
        print("  [OK] 全部写入完成")

    await engine.dispose()


async def main():
    print("=" * 50)
    print("SQLite → MySQL 数据迁移")
    print("=" * 50)

    # 读取
    print("\n[1/2] 读取 SQLite 数据...")
    data = await read_sqlite()

    # 写入
    print("\n[2/2] 写入 MySQL...")
    await write_mysql(data)

    print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(main())
