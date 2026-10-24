import pytest
from app.services.extraction import extract_inquiry

def test_basic_extraction():
    txt = "Need 500 boxes 12x10x8, 3‑ply, and 200 smaller ones."
    result = extract_inquiry(txt)
    assert isinstance(result, dict)
    assert len(result["items"]) == 2
    # first item checks
    first = result["items"][0]
    assert first["quantity"] == 500
    assert "boxes" in first["description"].lower()
    # missing field detection
    assert "dimensions/SKU for smaller item" in result["missing_fields"]
