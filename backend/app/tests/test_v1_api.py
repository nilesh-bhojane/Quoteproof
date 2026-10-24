from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "v1"


def test_v1_products_list():
    res = client.get("/api/v1/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 3
    assert any("Corrugated Box" in p["name"] for p in products)


def test_v1_quotes_draft():
    payload = {
        "inquiry_text": "Need 500 boxes 12x10x8, 3-ply, delivery to Pune next week.",
        "mode": "basic",
    }
    res = client.post("/api/v1/quotes/draft", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) >= 1
    assert float(data["subtotal"]) > 0
    assert float(data["gst"]) > 0
    assert float(data["total"]) > float(data["subtotal"])


def test_v1_approve_quote():
    payload = {"approved_by": "Karan Sapate"}
    res = client.post("/api/v1/quotes/demo-quote-1/approve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "Karan Sapate"


def test_v1_reject_quote():
    payload = {"reason": "Customer cancelled requirement"}
    res = client.post("/api/v1/quotes/demo-quote-2/reject", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rejected"


def test_v1_timings_and_roi():
    timing_payload = {
        "quote_id": "demo-quote-1",
        "kind": "assisted",
        "seconds": 180,
    }
    res = client.post("/api/v1/timings", json=timing_payload)
    assert res.status_code == 200

    roi_res = client.get("/api/v1/roi?hourly_rate=400")
    assert roi_res.status_code == 200
    roi = roi_res.json()
    assert roi["time_saved_seconds"] > 0
    assert roi["estimated_labour_value_saved"] is not None


def test_v1_trust_test_runner():
    res = client.post("/api/v1/trust-test/run")
    assert res.status_code == 200
    report = res.json()
    assert report["total_inquiries_tested"] >= 10
    assert report["masking_leak_rate_pct"] == 0.0
    assert report["pricing_error_rate_pct"] == 0.0
    assert report["status"] == "passed_benchmark"
