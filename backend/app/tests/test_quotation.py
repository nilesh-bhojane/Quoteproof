import pytest
from app.services.quotation import validate_quote, match_description_to_sku, PRICE_LIST


# ---------------------------------------------------------------------------
# match_description_to_sku tests
# ---------------------------------------------------------------------------

class TestMatchDescriptionToSku:
    def test_exact_match(self):
        result = match_description_to_sku("Large box")
        assert result in ("BOX-L", "DEMO001"), f"Expected a Large box SKU, got {result}"
        result = match_description_to_sku("Small box")
        assert result in ("BOX-S", "SMALL001"), f"Expected a Small box SKU, got {result}"

    def test_case_insensitive(self):
        result = match_description_to_sku("large BOX")
        assert result in ("BOX-L", "DEMO001"), f"Expected a Large box SKU, got {result}"
        result = match_description_to_sku("SMALL BOX")
        assert result in ("BOX-S", "SMALL001"), f"Expected a Small box SKU, got {result}"

    def test_substring_match(self):
        assert match_description_to_sku("large") is not None
        assert match_description_to_sku("small") is not None

    def test_no_match(self):
        assert match_description_to_sku("unknown widget") is None

    def test_empty_and_none(self):
        assert match_description_to_sku("") is None
        assert match_description_to_sku(None) is None


# ---------------------------------------------------------------------------
# validate_quote tests
# ---------------------------------------------------------------------------

class TestValidateQuote:
    def test_basic_valid_quote(self):
        items = [{"sku": "BOX-L", "quantity": 500}]
        result = validate_quote(items, tax_rate=18)
        assert result["subtotal"] == 12000.0
        assert result["tax"] == 2160.0
        assert result["total"] == 14160.0
        assert len(result["items"]) == 1
        assert result["can_approve"] is True

    def test_multiple_items(self):
        items = [
            {"sku": "BOX-L", "quantity": 100},
            {"sku": "BOX-S", "quantity": 200},
        ]
        result = validate_quote(items, tax_rate=18)
        assert result["subtotal"] == 100 * 24 + 200 * 12
        assert len(result["items"]) == 2
        assert result["can_approve"] is True

    def test_unknown_sku_produces_warning(self):
        items = [{"sku": "UNKNOWN", "quantity": 10}]
        result = validate_quote(items, tax_rate=0)
        assert len(result["items"]) == 0
        assert any("Unknown SKU" in w for w in result["warnings"])
        assert result["can_approve"] is False

    def test_missing_sku_with_description_match(self):
        items = [{"description": "Large box", "quantity": 100}]
        result = validate_quote(items, tax_rate=0)
        assert len(result["items"]) == 1
        assert result["items"][0]["sku"] in PRICE_LIST

    def test_invalid_quantity(self):
        items = [{"sku": "BOX-L", "quantity": "abc"}]
        result = validate_quote(items, tax_rate=0)
        assert len(result["items"]) == 0
        assert any("Invalid quantity" in w for w in result["warnings"])

    def test_negative_quantity(self):
        items = [{"sku": "BOX-L", "quantity": -5}]
        result = validate_quote(items, tax_rate=0)
        assert len(result["items"]) == 0

    def test_zero_quantity_warning(self):
        items = [{"sku": "BOX-L", "quantity": 0}]
        result = validate_quote(items, tax_rate=0)
        assert len(result["items"]) == 0
        assert any("zero" in w for w in result["warnings"])

    def test_zero_tax_rate(self):
        items = [{"sku": "BOX-L", "quantity": 10}]
        result = validate_quote(items, tax_rate=0)
        assert result["tax"] == 0.0
        assert result["total"] == result["subtotal"]

    def test_tax_rate_clamped(self):
        items = [{"sku": "BOX-L", "quantity": 10}]
        result = validate_quote(items, tax_rate=150)
        assert result["tax_rate"] == 100.0  # clamped

    def test_empty_items(self):
        result = validate_quote([], tax_rate=18)
        assert result["subtotal"] == 0
        assert result["total"] == 0
        assert result["can_approve"] is False

    def test_blocks_approval_with_warnings(self):
        items = [
            {"sku": "BOX-L", "quantity": 500},
            {"sku": "UNKNOWN", "quantity": 100},
        ]
        result = validate_quote(items, tax_rate=18)
        # One valid item but also a warning → cannot approve
        assert len(result["items"]) == 1
        assert result["can_approve"] is False
