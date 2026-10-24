# Team task split

## Contributor A — Inquiry intake & extraction
**Branch:** `feat/inquiry-extraction`
- Build paste-inquiry UI and sample inquiry selector.
- Extract customer request into structured line items (description, quantity, unit, requested specs).
- Return missing/ambiguous fields; never invent prices.
- Add loading, error, and empty states.
- Deliver: component, service, tests, short README note, screenshot if possible.

## Contributor B — Quotation validation & approval
**Branch:** `feat/quotation-approval`
- Build editable quote table and review/approve/reject flow.
- Match extracted descriptions to known SKUs/price-list entries.
- Calculate subtotal, configured tax and total in code, not in the LLM.
- Block approval when required fields are unresolved.
- Deliver: component, service, tests, sample price list, short README note.

## Contributor C — Evidence Ledger & ROI dashboard
**Branch:** `feat/audit-roi`
- Record key events: draft created, fields edited, warning resolved, approved/rejected.
- Capture manual and assisted workflow duration with clear labels.
- Show time difference and percentage reduction; label demo values as illustrative.
- Estimate labour value only when an explicit hourly cost is entered.
- Deliver: dashboard, analytics service, tests, short README note.

## Integrator
- Own `App.jsx`, global layout, routing, API contract and final integration.
- Review PRs; do not merge untested code directly to `main`.
- Run a complete end-to-end scenario before final demo.
