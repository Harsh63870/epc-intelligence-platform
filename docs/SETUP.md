# Development Setup

This guide walks through running the EPC Intelligence Platform locally on Windows. Use three separate terminals for database, backend, and frontend.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- Node.js 20 or later
- Python 3.11 or later

## 1. Start PostgreSQL

From the repository root:

```powershell
docker compose up -d
docker compose ps
```

The `epc-postgres` container should report **healthy**. PostgreSQL is exposed on host port **5433** (not 5432) to avoid conflicts with a local PostgreSQL installation.

## 2. Environment configuration

**Backend** (required):

```powershell
cd backend
copy .env.example .env
```

Default connection string:

```
DATABASE_URL=postgresql://epc:epc_secret@127.0.0.1:5433/epc_intelligence
```

Set `GROQ_API_KEY` when using AI features. Other variables are optional for initial setup.

**Frontend** (optional):

```powershell
cd frontend
copy .env.local.example .env.local
```

## 3. Backend API

First-time setup:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Run the server:

```powershell
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- Interactive API docs: http://localhost:8000/docs
- Health check: `Invoke-RestMethod http://localhost:8000/api/v1/health`  
  Expect `database: connected`.

## 4. Frontend

First-time setup:

```powershell
cd frontend
npm install
```

Run the dev server:

```powershell
npm run dev
```

Open http://localhost:3000

## 5. Demo data

On the Dashboard, click **Seed Demo Project**, or run:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/seed" -Method POST
```

This creates the sample project **Mumbai Hyperscale DC-01**.

## Verification checklist

- [ ] `docker compose ps` shows postgres as healthy
- [ ] http://localhost:8000/docs loads
- [ ] Health endpoint reports `database: connected`
- [ ] http://localhost:3000 loads
- [ ] All navigation items are accessible
- [ ] Demo project appears in the project selector

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Docker will not start | Ensure Docker Desktop is running |
| Port 5432 already in use | Expected if local PostgreSQL is installed; use port **5433** as configured |
| `password authentication failed for user epc` | Confirm `backend/.env` uses `127.0.0.1:5433`, restart the API |
| Frontend cannot reach API | Confirm backend is on port 8000; check `NEXT_PUBLIC_API_URL` in `.env.local` |
| Seed request fails | Backend or database not running |

## SQLite fallback

If Docker is unavailable, remove or rename `backend/.env`. The API falls back to SQLite (`backend/epc_dev.db`) automatically.

## Stopping services

Press `Ctrl+C` in the backend and frontend terminals, then:

```powershell
docker compose down
```

Database files are stored in the Docker volume `postgres_data`. Run `docker compose down -v` only if you need to reset the database.
