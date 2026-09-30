# FinGuard — Financial Anomaly & Expense Prediction Portal

A production-style full-stack fintech starter with React/TypeScript, FastAPI, PostgreSQL-ready SQLAlchemy, JWT authentication, anomaly detection, expense forecasting, budgets, goals, notifications and report endpoints.

## Quick start

```bash
cp backend/.env.example backend/.env
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

```bash
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. The UI ships with realistic demo data; set `VITE_API_URL=http://localhost:8000/api/v1` to connect live APIs.

## Security baseline
- Argon2 password hashing, short-lived JWT access tokens, strict CORS allow-list
- Pydantic validation, ORM queries, ownership checks, trusted-host and security headers
- Secrets via environment only; PostgreSQL supported through `DATABASE_URL`
- Rate-limiting/revocation hooks are documented for Redis-backed production deployment

Run `pytest backend/tests` and `npm run build` before deployment.
