"""初始化管理员账号"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session, init_db
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select


async def create_admin():
    await init_db()

    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[OK] Admin account already exists: admin (id={existing.id})")
        else:
            admin = User(
                username="admin",
                password_hash=hash_password("123456"),
                role="admin",
            )
            db.add(admin)
            await db.commit()
            print("[OK] Admin account created")
            print("     Username: admin")
            print("     Password: 123456")
            print("     WARNING: Please change the password immediately after login!")


if __name__ == "__main__":
    asyncio.run(create_admin())
