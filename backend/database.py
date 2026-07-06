from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
# Railway provides postgres:// but asyncpg needs postgresql+asyncpg://
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1).replace(
    "postgresql://", "postgresql+asyncpg://", 1
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
