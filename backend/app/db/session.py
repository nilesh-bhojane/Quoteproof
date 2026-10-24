import os
import uuid
import json
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.core.config import settings

Base = declarative_base()


def json_dumps(obj):
    """JSON serializer for SQLAlchemy engines supporting Decimal and UUID."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    return json.dumps(obj, default=lambda o: str(o) if isinstance(o, (Decimal, uuid.UUID)) else str(o))


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's native UUID when connected to PostgreSQL,
    otherwise uses CHAR(36) on SQLite/other databases.
    """
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


db_url = settings.DATABASE_URL or ""

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Default to local SQLite database when DATABASE_URL is not set (e.g. quick tests / demo)
if not db_url:
    db_url = "sqlite:///./quoteproof.db"

if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        json_serializer=json_dumps,
    )
else:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        json_serializer=json_dumps,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Ensure tables exist and seed catalogue if empty."""
    from app.models.product import Product
    from app.services.draft_service import FALLBACK_CATALOG

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            for item in FALLBACK_CATALOG:
                # Ensure bulk_tiers has json-serializable floats/strings
                tiers = []
                for t in item.get("bulk_tiers", []):
                    tiers.append({
                        "min_qty": t.get("min_qty"),
                        "unit_price": str(t.get("unit_price")),
                    })
                p = Product(
                    id=item["id"],
                    name=item["name"],
                    aliases=item["aliases"],
                    unit=item.get("unit", "pcs"),
                    sell_price=item["sell_price"],
                    cost_price=item["cost_price"],
                    min_margin_pct=item.get("min_margin_pct", Decimal("15.00")),
                    bulk_tiers=tiers,
                    stock_on_hand=item.get("stock_on_hand", 0),
                    reserved=item.get("reserved", 0),
                    track_stock=item.get("track_stock", True),
                    price_updated_at=item.get("price_updated_at") or datetime.now(timezone.utc),
                )
                db.add(p)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


init_db()


def get_db():
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
