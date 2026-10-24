# Inquiry Extraction (Contributor A)

## Overview
The **InquiryPanel** component lets a user paste a raw customer message, calls the backend `/api/extract` endpoint, and displays a deterministic extraction preview.

## Features
- Paste‑inquiry UI with a sample loader.
- Live extraction via `fetch('/api/extract')`.
- UI states: loading, error, and empty‑result handling.
- Missing‑field detection – highlighted for reviewer action.

## Screenshot (placeholder)
> *Insert a screenshot of the panel after a successful extraction here.*

## Development
```bash
# Frontend
npm run dev   # serves on http://localhost:3000

# Backend
uvicorn backend.app.main:app --reload
```

Run the tests:
```bash
# Backend
pytest backend/app/tests

# Frontend
npm test
```
