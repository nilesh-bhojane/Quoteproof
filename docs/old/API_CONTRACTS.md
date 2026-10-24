# Shared API contracts (initial proposal)

Keep these contracts stable while features are developed in parallel.

## POST `/api/extract`
Request: `{ "inquiry_text": "Need 500 boxes..." }`
Response:
```json
{
  "items": [
    {"description": "large box", "quantity": 500, "unit": "pcs", "specifications": {"size": "12x10x8"}, "sku": null}
  ],
  "missing_fields": ["price/specification for smaller box"],
  "warnings": []
}
```

## POST `/api/quotes/validate`
Request: `{ "items": [{"sku":"BOX-L","quantity":500}] }`
Response: `{ "items": [], "subtotal": 0, "tax_rate": 0, "tax": 0, "total": 0, "warnings": [] }`

## POST `/api/events`
Request: `{ "quote_id":"demo-1", "event_type":"draft_created", "details": {} }`
Response: `{ "ok": true }`

## GET `/api/analytics/summary`
Response: `{ "manual_seconds": 600, "assisted_seconds": 240, "quotes_tested": 1, "hourly_labour_cost": null, "estimated_labour_value_saved": null }`

Numbers above are examples only. Implementations must validate input and avoid claiming illustrative values are real measured results.
