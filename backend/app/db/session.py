from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

db_url = settings.DATABASE_URL or ""

# Normalize Postgres driver scheme for SQLAlchemy if standard postgres:// is provided
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Configure connection engine
if db_url:
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()


def get_db():
    """Dependency for obtaining a database session per request."""
    if SessionLocal is None:
        raise RuntimeError(
            "Database session is unconfigured. Please ensure DATABASE_URL is set in backend/.env"
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
