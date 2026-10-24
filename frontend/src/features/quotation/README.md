# Quotation Validation & Approval (Contributor B)

## Overview
The **QuotationPanel** component provides an editable quote table with a review / approve / reject workflow. It matches extracted item descriptions to known SKUs from a sample price list, calculates subtotal, tax, and total in code (never in an LLM), and blocks approval when any required field is unresolved.

## Features
- **Editable quote table** — each line item has editable Quantity and Unit Price inputs.
- **SKU / price-list matching** — on load, item descriptions are matched (case-insensitive) against `priceList.json` to auto-fill SKU and unit price.
- **In-code calculation** — subtotal, tax (configurable rate), and grand total are computed in JavaScript, not delegated to an LLM.
- **Approval gating** — the Approve button is disabled until every line item has a quantity > 0 and a unit price > 0.
- **Reject flow** — a dedicated Reject button sets the quote status to "Rejected".
- **Validation notice** — a warning banner shows when unresolved items remain.

## Files
| File | Purpose |
|---|---|
| `frontend/src/features/quotation/QuotationPanel.jsx` | React component — editable table, approve/reject UI |
| `frontend/src/features/quotation/QuotationPanel.test.jsx` | Frontend tests (Jest + React Testing Library) |
| `frontend/src/data/priceList.json` | Sample price list (2 demo SKUs) |
| `frontend/src/services/priceListService.js` | Helper service for price-list lookup |
| `backend/app/services/quotation.py` | Backend validation service with description→SKU matching |
| `backend/app/tests/test_quotation.py` | Backend tests (pytest) |

## Sample Price List
```json
[
  { "sku": "DEMO001", "description": "Large box", "unitPrice": 24 },
  { "sku": "SMALL001", "description": "Small box", "unitPrice": 12 }
]
```

## API Contract
**POST `/api/quotes/validate`**
```json
{
  "items": [{ "sku": "BOX-L", "quantity": 500 }],
  "tax_rate": 18
}
```
Response:
```json
{
  "items": [{ "sku": "BOX-L", "name": "Large box", "quantity": 500, "unit": "pcs", "unit_price": 24, "line_total": 12000 }],
  "subtotal": 12000, "tax_rate": 18, "tax": 2160, "total": 14160,
  "warnings": [], "can_approve": true
}
```

## Development
```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Running Tests
```bash
# Backend
cd backend
pytest app/tests/test_quotation.py -v

# Frontend
cd frontend
npm test
```
