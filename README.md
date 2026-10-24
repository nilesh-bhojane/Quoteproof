# QuoteProof AI — Hackathon Monorepo Starter

A 3-contributor starter for a single integrated web app: AI-assisted quotation drafting with human approval, an audit trail, and an ROI dashboard.

## Team ownership
- **Contributor A — Inquiry extraction**: `frontend/src/features/inquiry/`, `backend/app/services/extraction.py`
- **Contributor B — Quote validation & approval**: `frontend/src/features/quotation/`, `backend/app/services/quotation.py`
- **Contributor C — Audit log & ROI analytics**: `frontend/src/features/analytics/`, `backend/app/services/analytics.py`
- **Integrator** owns shared app shell, API contracts, code review, and merges.

Keep each person's work in separate feature branches and merge via pull requests into `main`. Do not have everyone edit the same `App.jsx`.

## Requirements
- Node.js 20+ and npm
- Python 3.11+
- Git

## Start frontend
```bash
cd frontend
npm install
npm run dev
```

## Start backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs
Frontend: Vite will print its local URL, usually http://localhost:5173

## Environment variables
Copy `backend/.env.example` to `backend/.env`. Never commit real API keys or customer data.

## Integration rules
1. Agree on API contracts in `docs/API_CONTRACTS.md` before parallel work.
2. Each contributor commits only their assigned feature and tests.
3. Open a pull request; integrator checks it on the shared `dev` branch.
4. Merge feature branches into `dev` one by one, resolve conflicts, test the integrated app, then merge `dev` into `main`.
5. Keep `main` demo-ready. Use synthetic customer data during the hackathon.

See `docs/GIT_WORKFLOW.md` and `docs/TEAM_TASKS.md`.
