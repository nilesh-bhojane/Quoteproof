from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from app.services.product_matching_service import match_product
from app.services.stock_service import check_item_stock

CATALOG = [
    {
        "id": "p1",
        "name": "Corrugated Box 12x10x8 (3-Ply)",
        "aliases": ["box 12x10x8", "3-ply box", "standard shipping box"],
        "unit": "pcs",
        "sell_price": Decimal("24.00"),
        "stock_on_hand": 5000,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": datetime.now(timezone.utc),
    },
    {
        "id": "p2",
        "name": "Heavy Duty Box 18x14x12 (5-Ply)",
        "aliases": ["5-ply box", "heavy duty carton", "large box"],
        "unit": "pcs",
        "sell_price": Decimal("48.00"),
        "stock_on_hand": 120,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": datetime.now(timezone.utc),
    },
    {
        "id": "p3",
        "name": "Die-Cut Mailer Box 10x8x3 (White E-Flute)",
        "aliases": ["white mailer", "mailer box", "die cut box"],
        "unit": "pcs",
        "sell_price": Decimal("32.00"),
        "stock_on_hand": 0,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": datetime.now(timezone.utc),
    },
    {
        "id": "p4",
        "name": "Air Bubble Roll 100m x 1m (50 GSM)",
        "aliases": ["bubble wrap", "bubble roll"],
        "unit": "roll",
        "sell_price": Decimal("850.00"),
        "stock_on_hand": 80,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": datetime.now(timezone.utc) - timedelta(days=60),  # Stale price
    },
    {
        "id": "p5",
        "name": "Custom Brand Logo Printing",
        "aliases": ["logo printing", "screen print"],
        "unit": "job",
        "sell_price": Decimal("1200.00"),
        "stock_on_hand": 0,
        "reserved": 0,
        "track_stock": False,  # Untracked service
        "price_updated_at": datetime.now(timezone.utc),
    },
]


def test_exact_name_matching():
    res = match_product("Corrugated Box 12x10x8 (3-Ply)", CATALOG)
    assert res["match_type"] == "exact"
    assert res["product"]["id"] == "p1"
    assert len(res["flags"]) == 0


def test_alias_matching():
    res = match_product("bubble wrap", CATALOG)
    assert res["match_type"] == "alias"
    assert res["product"]["id"] == "p4"
    # p4 has a 60-day old price -> should trigger STALE_PRICE warning
    assert any(f["code"] == "STALE_PRICE" for f in res["flags"])
    assert not any(f["blocks_approval"] for f in res["flags"])


def test_unknown_product_flag():
    res = match_product("Wooden Pallet 48x40", CATALOG)
    assert res["match_type"] == "none"
    assert res["product"] is None
    assert any(f["code"] == "UNKNOWN_PRODUCT" and f["blocks_approval"] for f in res["flags"])


def test_stock_case_1_full_availability():
    prod = CATALOG[0]  # 5000 in stock
    stock_res = check_item_stock(prod, Decimal("500"))
    assert stock_res["stock_status"] == "ok"
    assert stock_res["available"] == 5000
    assert not stock_res["decision_required"]
    assert len(stock_res["flags"]) == 0


def test_stock_case_2_partial_shortage():
    # 500 requested, only 120 available (Section 14 demo scenario)
    prod = CATALOG[1]  # 120 in stock
    stock_res = check_item_stock(prod, Decimal("500"))
    assert stock_res["stock_status"] == "short"
    assert stock_res["available"] == 120
    assert stock_res["decision_required"] is True
    assert any(f["code"] == "STOCK_SHORT" and f["blocks_approval"] for f in stock_res["flags"])


def test_stock_case_3_out_of_stock_with_copyable_reply():
    prod = CATALOG[2]  # 0 in stock
    stock_res = check_item_stock(prod, Decimal("200"))
    assert stock_res["stock_status"] == "out_of_stock"
    assert stock_res["available"] == 0
    assert stock_res["decision_required"] is True
    assert any(f["code"] == "OUT_OF_STOCK" and f["blocks_approval"] for f in stock_res["flags"])
    assert stock_res["copyable_reply"] is not None
    assert "Expected Date" in stock_res["copyable_reply"]


def test_stock_untracked_service():
    prod = CATALOG[4]  # track_stock = False
    stock_res = check_item_stock(prod, Decimal("1"))
    assert stock_res["stock_status"] == "untracked"
    assert stock_res["available"] is None
    assert not stock_res["decision_required"]
    assert len(stock_res["flags"]) == 0
