# Evidence Ledger & ROI Dashboard (Contributor C)

## Overview
The **AnalyticsPanel** provides an audit trail ("Evidence Ledger") and productivity/ROI calculator for the quotation system.

## Key Features
- **Key Event Tracking:** Captures audit events including:
  - `inquiry_received`: Raw message recorded
  - `draft_created`: Extracted line items drafted
  - `fields_edited`: Human reviewer modified item details
  - `warning_resolved`: Gaps or missing specifications cleared
  - `approved` / `rejected`: Human reviewer final decision
- **Duration & Efficiency Gain:**
  - Measures manual vs. AI-assisted quotation cycle duration.
  - Automatically computes time saved (in minutes) and percentage cycle reduction.
- **Strict Labour Value Rule:**
  - Financial value of saved labour is calculated **strictly** when an explicit, positive hourly rate is input.
  - If no hourly cost is entered, the metric displays an uncomputed dash (`—`) rather than inventing numbers.
- **Clear Illustrative Disclaimers:**
  - Notice clearly identifies demo values as illustrative baselines pending live field measurement.

## Service & Endpoints
- `backend/app/services/analytics.py`
  - `record_event(quote_id, event_type, details)`
  - `get_events(quote_id)`
  - `calculate_roi(manual_seconds, assisted_seconds, hourly_labour_cost)`
  - `summary()`
- **API Endpoints:**
  - `POST /api/events` — log an event
  - `GET /api/events` — fetch recorded events
  - `POST /api/analytics/calculate` — calculate ROI metrics
  - `GET /api/analytics/summary` — retrieve analytics baseline

## Running Tests
```bash
# Backend pytest
cd backend
python -m pytest app/tests/test_analytics.py -v
```
