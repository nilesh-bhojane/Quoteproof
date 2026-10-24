# Inquiry Extraction (Contributor A)

## Overview
The **InquiryPanel** component enables intake of raw customer messages, parses them into structured line items (description, quantity, unit, specifications), detects ambiguous or missing fields, and enforces the core principle: **never invent prices**.

## Features
- **Sample Inquiry Selector:** Dropdown with multiple realistic business scenarios (standard mix, large bulk, ambiguous specs).
- **Structured Extraction:** Parses line items with quantities, units, and optional specifications.
- **Missing Field Detection:** Flags missing dimensions/SKUs (e.g. "smaller ones") for human review.
- **Workflow Handoff:** Provides seamless "Send to Quotation Review" handoff into Contributor B's validation table.
- **States:** Handles empty text, parsing progress, and error/offline conditions.

## API Contract
**POST `/api/extract`**
```json
{
  "inquiry_text": "Need 500 boxes 12x10x8, 3-ply, and 200 smaller ones."
}
```
Response:
```json
{
  "items": [
    {"description": "boxes 12x10x8", "quantity": 500, "unit": "pcs", "specifications": {"note": "3-ply"}, "sku": null},
    {"description": "smaller ones", "quantity": 200, "unit": "pcs", "specifications": {}, "sku": null}
  ],
  "missing_fields": ["dimensions/SKU for smaller item"],
  "warnings": ["Starter parser only: verify every extracted field."]
}
```

## Running Tests
```bash
# Backend pytest
cd backend
python -m pytest app/tests/test_extraction.py -v
```
