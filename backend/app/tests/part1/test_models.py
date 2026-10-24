import uuid
from decimal import Decimal
from app.models import (
    Product,
    Quote,
    QuoteItem,
    AuditLog,
    Timing,
    AiUsage,
    Setting,
)


def test_instantiate_product():
    product = Product(
        name="Carton Box 12x10x8",
        aliases=["box", "carton"],
        sell_price=Decimal("24.00"),
        cost_price=Decimal("18.00"),
        min_margin_pct=Decimal("15.00"),
        stock_on_hand=500,
        reserved=50,
        track_stock=True,
    )
    assert product.name == "Carton Box 12x10x8"
    assert product.available_stock == 450
    assert product.sell_price == Decimal("24.00")


def test_instantiate_quote_and_item():
    quote_id = uuid.uuid4()
    quote = Quote(
        id=quote_id,
        status="draft",
        inquiry_masked="Need 500 boxes to Pune",
        subtotal=Decimal("11000.00"),
        gst=Decimal("1980.00"),
        total=Decimal("12980.00"),
    )
    item = QuoteItem(
        quote_id=quote_id,
        raw_text="500 boxes",
        qty=Decimal("500.00"),
        unit="pcs",
        unit_price_snapshot=Decimal("22.00"),
        line_total=Decimal("11000.00"),
        stock_status="ok",
    )
    quote.items.append(item)
    assert quote.subtotal == Decimal("11000.00")
    assert len(quote.items) == 1
    assert quote.items[0].qty == Decimal("500.00")


def test_instantiate_audit_log_and_timing():
    audit = AuditLog(
        actor="ai",
        action="draft_created",
        before={},
        after={"items_count": 2},
    )
    timing = Timing(
        kind="assisted",
        seconds=Decimal("120.50"),
    )
    assert audit.actor == "ai"
    assert timing.seconds == Decimal("120.50")


def test_instantiate_ai_usage_and_setting():
    ai = AiUsage(
        tokens_in=350,
        tokens_out=120,
        cost_inr=Decimal("0.45"),
    )
    setting = Setting(
        id=1,
        hourly_rate=Decimal("300.00"),
        stale_days=30,
        gst_pct=Decimal("18.00"),
        basic_mode=False,
    )
    assert ai.cost_inr == Decimal("0.45")
    assert setting.gst_pct == Decimal("18.00")
