import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:puja%40555@localhost:5555/major",
)

# SQLAlchemy 2.0 engine with connection pooling and stale-connection checks
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session lifecycle management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verifies live PostgreSQL connection health."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            return result == 1
    except Exception:
        return False
