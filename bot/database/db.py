import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.database.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or "sqlite+aiosqlite:///bot.db"


def _ensure_async_driver(url: str) -> str:
    """Normalize whatever URL scheme was pasted in (e.g. straight from Supabase/Render)
    into one SQLAlchemy's async engine can actually use."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif url.startswith("sqlite://") and "+aiosqlite" not in url:
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


DATABASE_URL = _ensure_async_driver(DATABASE_URL)

# asyncpg wants "ssl", not the libpq-style "sslmode" query param some tools paste in.
connect_args = {}
if DATABASE_URL.startswith("postgresql+asyncpg://") and "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]
    connect_args = {"ssl": "require"}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Create all tables if they don't exist yet. Safe to call every startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session() -> AsyncSession:
    return async_session()
