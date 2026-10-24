from datetime import datetime, timezone
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])

STALE_DAYS_THRESHOLD = 30


def _build_product_response(p: Product) -> ProductResponse:
    now = datetime.now(timezone.utc)
    is_stale = False
    days_diff = None

    if p.price_updated_at:
        p_time = p.price_updated_at
        if p_time.tzinfo is None:
            p_time = p_time.replace(tzinfo=timezone.utc)
        diff = now - p_time
        days_diff = diff.days
        if days_diff >= STALE_DAYS_THRESHOLD:
            is_stale = True

    available = max(0, (p.stock_on_hand or 0) - (p.reserved or 0)) if p.track_stock else 999999

    return ProductResponse(
        id=p.id if isinstance(p.id, UUID) else UUID(str(p.id)),
        name=p.name,
        aliases=p.aliases or [],
        unit=p.unit,
        sell_price=p.sell_price,
        cost_price=p.cost_price,
        min_margin_pct=p.min_margin_pct,
        bulk_tiers=p.bulk_tiers or [],
        stock_on_hand=p.stock_on_hand,
        reserved=p.reserved,
        available_stock=available,
        track_stock=p.track_stock,
        price_updated_at=p.price_updated_at,
        is_stale=is_stale,
        days_since_price_update=days_diff,
    )


@router.get("", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    """GET /api/v1/products - List catalogue with live stock and stale price warnings."""
    products = db.query(Product).order_by(Product.name.asc()).all()
    return [_build_product_response(p) for p in products]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    """POST /api/v1/products - Add a new packaging product to the catalogue."""
    new_product = Product(
        name=product_in.name.strip(),
        aliases=product_in.aliases,
        unit=product_in.unit,
        sell_price=product_in.sell_price,
        cost_price=product_in.cost_price,
        min_margin_pct=product_in.min_margin_pct,
        bulk_tiers=product_in.bulk_tiers,
        stock_on_hand=product_in.stock_on_hand,
        reserved=product_in.reserved,
        track_stock=product_in.track_stock,
        price_updated_at=datetime.now(timezone.utc),
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return _build_product_response(new_product)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, product_in: ProductUpdate, db: Session = Depends(get_db)):
    """PATCH /api/v1/products/{id} - Edit price, cost, stock; updates price_updated_at."""
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PRODUCT_NOT_FOUND", "message": f"Product {product_id} not found."},
        )

    price_changed = False
    update_data = product_in.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        if field in ("sell_price", "cost_price", "bulk_tiers"):
            price_changed = True
        setattr(prod, field, val)

    if price_changed or "sell_price" in update_data:
        prod.price_updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prod)
    return _build_product_response(prod)
