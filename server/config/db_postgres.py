from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config.settings import settings


engine = create_async_engine(
    settings.POSTGRES_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db():
    try:
        db = AsyncSessionLocal()
        yield db
    finally:
        db.close()
   