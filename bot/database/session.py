from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.config.settings import config

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False, # Поставьте True для вывода SQL-запросов в консоль при отладке
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """Генератор для получения сессии БД (может использоваться в DI)."""
    async with async_session_maker() as session:
        yield session