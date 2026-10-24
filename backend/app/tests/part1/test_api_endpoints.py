"""API Endpoint Tests for Part 1 (Inquiry to Draft pipeline & Catalogue).

Tests Section 11 API contract:
- GET /api/v1/health
- GET /api/v1/products
- POST /api/v1/products
- PATCH /api/v1/products/{id}
- POST /api/v1/quotes/draft
- GET /api/v1/quotes/{id}
- PATCH /api/v1/quotes/{id}
- POST /api/v1/quotes/{id}/stock-decision
"""

import uuid
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.quote import Quote, QuoteItem

client = TestClient(app)


def test_health_v1():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "v1"


def test_list_products():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) >= 8

    box = next((p for p in products if "12x10x8" in p["name"]), None)
    assert box is not None
    assert Decimal(str(box["sell_price"])) == Decimal("24.00")
    assert box["available_stock"] == 5000


def test_create_and_patch_product():
    new_prod_payload = {
        "name": f"Test Corrugated Sheet {uuid.uuid4().hex[:6]}",
        "aliases": ["test sheet", "flute sheet"],
        "unit": "pcs",
        "sell_price": "15.50",
        "cost_price": "11.00",
        "min_margin_pct": "15.00",
        "bulk_tiers": [{"min_qty": 100, "unit_price": "14.00"}],
        "stock_on_hand": 300,
        "reserved": 0,
        "track_stock": True,
    }
    create_res = client.post("/api/v1/products", json=new_prod_payload)
    assert create_res.status_code == 201
    prod = create_res.json()
    prod_id = prod["id"]
    assert Decimal(str(prod["sell_price"])) == Decimal("15.50")
    assert prod["available_stock"] == 300

    # PATCH product price and stock
    patch_payload = {
        "sell_price": "17.00",
        "stock_on_hand": 450,
    }
    patch_res = client.patch(f"/api/v1/products/{prod_id}", json=patch_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert Decimal(str(updated["sell_price"])) == Decimal("17.00")
    assert updated["available_stock"] == 450


def test_create_draft_endpoint():
    inquiry_text = "Need 100 pcs of 3-ply box and 50 rolls brown tape. Please send quotation."
    payload = {
        "inquiry_text": inquiry_text,
        "mode": "basic",
    }
    res = client.post("/api/v1/quotes/draft", json=payload)
    assert res.status_code == 200
    draft = res.json()

    assert draft["status"] == "draft"
    assert len(draft["items"]) >= 2
    assert Decimal(str(draft["subtotal"])) > Decimal("0.00")
    assert Decimal(str(draft["gst"])) > Decimal("0.00")
    assert Decimal(str(draft["total"])) > Decimal(str(draft["subtotal"]))

    # Verify persistence
    quote_id = draft["id"]
    get_res = client.get(f"/api/v1/quotes/{quote_id}")
    assert get_res.status_code == 200
    saved_quote = get_res.json()
    assert saved_quote["id"] == quote_id
    assert len(saved_quote["items"]) == len(draft["items"])


def test_patch_quote_items_recalculates_decimal():
    # 1. Create a draft first
    res = client.post(
        "/api/v1/quotes/draft",
        json={"inquiry_text": "Need 50 pcs box 12x10x8", "mode": "basic"},
    )
    assert res.status_code == 200
    draft = res.json()
    quote_id = draft["id"]
    item_id = draft["items"][0]["id"]
    old_total = Decimal(str(draft["total"]))

    # 2. Patch item quantity to 100 and override unit price to 25.00
    patch_payload = {
        "items": [
            {
                "item_id": item_id,
                "qty": "100.00",
                "unit_price_snapshot": "25.00",
            }
        ]
    }
    patch_res = client.patch(f"/api/v1/quotes/{quote_id}", json=patch_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()

    # 100 * 25.00 = 2500.00 subtotal. GST 18% = 450.00. Total = 2950.00
    assert Decimal(str(updated["subtotal"])) == Decimal("2500.00")
    assert Decimal(str(updated["gst"])) == Decimal("450.00")
    assert Decimal(str(updated["total"])) == Decimal("2950.00")
    assert Decimal(str(updated["total"])) != old_total


def test_patch_approved_quote_blocked():
    # Create draft
    res = client.post(
        "/api/v1/quotes/draft",
        json={"inquiry_text": "Need 10 pcs 3-ply box", "mode": "basic"},
    )
    draft = res.json()
    quote_id = draft["id"]

    # Manually mark quote as approved in db to simulate Handshake
    db = SessionLocal()
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    quote.status = "approved"
    db.commit()
    db.close()

    # Attempt to edit approved quote
    patch_res = client.patch(
        f"/api/v1/quotes/{quote_id}",
        json={"items": [{"item_id": draft["items"][0]["id"], "qty": "50.00"}]},
    )
    assert patch_res.status_code == 400
    err = patch_res.json()
    assert err["detail"]["error"] == "IMMUTABLE_APPROVED_QUOTE"


def test_stock_decision_endpoint():
    # Inquiry requesting 500 pcs of Heavy Duty Box (only 120 available in seed)
    res = client.post(
        "/api/v1/quotes/draft",
        json={"inquiry_text": "Need 500 pcs 5-ply box 18x14x12 urgently", "mode": "basic"},
    )
    draft = res.json()
    quote_id = draft["id"]
    item = draft["items"][0]
    item_id = item["id"]

    assert item["stock_status"] == "short"

    # Owner applies partial decision: quote 120 now
    decision_payload = {
        "item_id": item_id,
        "decision": "partial",
        "qty": "120.00",
        "note": "Quote available 120 units immediately",
    }
    decision_res = client.post(f"/api/v1/quotes/{quote_id}/stock-decision", json=decision_payload)
    assert decision_res.status_code == 200
    updated_quote = decision_res.json()

    updated_item = updated_quote["items"][0]
    assert Decimal(str(updated_item["qty"])) == Decimal("120.00")
    assert updated_item["stock_status"] == "ok"
    # Blocking stock flag cleared
    assert not any(f["code"] == "STOCK_SHORT" for f in updated_quote["blocking_flags"])
