# EPC Intelligence Platform

Production-ready AI project intelligence for hyperscale data centre EPC delivery. The platform unifies specifications, vendor submittals, procurement, schedules, RFIs, commissioning, and quality records into a single operational layer aligned with **Tier III / Tier IV** standards (TIA-942, Uptime Institute).

**Demo project:** Mumbai Hyperscale DC-01

---

## Platform capabilities

| Module | Route | Capability |
|--------|-------|------------|
| **Dashboard** | `/` | Live KPIs — NCs, RFIs, schedule risks, at-risk shipments, commissioning progress, hours saved |
| **Documents** | `/documents` | Ingest PDF/Markdown, chunk, embed, semantic vector search |
| **RFI Copilot** | `/rfi` | RAG + Groq answers with document citations and similar-RFI detection |
| **Spec Compliance** | `/compliance` | Automated submittal review, NC audit trail, golden-test validated |
| **Schedule Risk** | `/schedule` | Critical-path risk from procurement ETAs + AI mitigation options |
| **Supply Chain** | `/supply-chain` | Shipment tracking, route visibility, schedule-impact alerts |
| **Commissioning** | `/commissioning` | Guided IST wizard with pass/fail/NC recording and progress by system |

---

## Architecture

```
┌─────────────────┐     REST /api/v1      ┌──────────────────────────────────┐
│  Next.js 16     │ ◄──────────────────► │  FastAPI                         │
│  TypeScript     │                      │  Agents: RFI, Compliance,        │
│  Tailwind CSS   │                      │  Schedule, Supply Chain, Comm.   │
└─────────────────┘                      └──────────┬───────────────┬────────┘
                                                    │               │
                                         ┌──────────▼───┐   ┌───────▼────────┐
                                         │ PostgreSQL   │   │ ChromaDB       │
                                         │ (relational) │   │ (vectors)      │
                                         └──────────────┘   └────────────────┘
                                                    │
                                         ┌──────────▼───┐
                                         │ Groq LLM     │
                                         │ (optional)   │
                                         └──────────────┘
```

Full design: [docs/architecture.md](docs/architecture.md)

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS |
| API | FastAPI, Pydantic, SQLAlchemy 2 |
| Database | PostgreSQL 16 (Docker) |
| Vector store | ChromaDB (local persistent) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, no API cost) |
| Document parsing | PyMuPDF |
| LLM | Groq `llama-3.3-70b-versatile` (OpenAI-compatible API) |

---

## Requirements

- **Node.js** 20+
- **Python** 3.11+
- **Docker Desktop** (PostgreSQL)
- **Groq API key** (recommended; RFI and mitigations fall back without it)

---

## Production deployment (local / staging)

### 1. Database

```powershell
docker compose up -d
docker compose ps   # epc-postgres should be healthy
```

PostgreSQL listens on host port **5433** (avoids conflict with local Postgres on 5432).

### 2. Backend

```powershell
cd backend
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Required environment variables** (`backend/.env`):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | `postgresql://epc:epc_secret@127.0.0.1:5433/epc_intelligence` |
| `GROQ_API_KEY` | Groq API key for RFI answers and schedule mitigations |
| `CORS_ORIGINS` | Comma-separated frontend origins (default `http://localhost:3000`) |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path (default `./chroma_data`) |

### 3. Frontend

```powershell
cd frontend
npm install
npm run build
npm start
```

For development: `npm run dev`

**Frontend environment** (`frontend/.env.local`):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Initialize demo data

1. Open http://localhost:3000
2. Click **Seed Demo Project** on the Dashboard

This loads:

- 23+ project documents (specs, RFIs, COs, commissioning procedures)
- Vector embeddings in ChromaDB
- 5 specifications, 10 RFIs, 6 commissioning tests
- 5 procurement shipments + 7 schedule tasks (with planted delay scenarios)
- 4 demo submittals in `data/submittals/` for compliance testing

---

## API reference

- **Interactive docs:** http://localhost:8000/docs
- **Health check:** `GET /api/v1/health`

| Endpoint group | Prefix | Purpose |
|----------------|--------|---------|
| Core | `/api/v1/projects`, `/api/v1/dashboard/metrics` | Projects and KPIs |
| Documents | `/api/v1/documents/*` | Ingest, list, vector search |
| RFI | `/api/v1/rfi/*` | Chat, similar RFIs |
| Compliance | `/api/v1/compliance/*` | Submittal check, NC management |
| Schedule | `/api/v1/schedule/*` | Tasks, risks, mitigations |
| Supply chain | `/api/v1/supply-chain/*` | Shipments, alerts |
| Commissioning | `/api/v1/commissioning/*` | Tests, progress, record results |
| Seed | `POST /api/v1/seed` | Load demo project |

---

## Quality assurance

### Golden compliance tests

Automated regression against planted submittal deviations:

```powershell
cd backend
.\.venv\Scripts\python scripts\run_golden_tests.py
```

Expected: **4/4 passed** (UPS runtime, chiller redundancy, switchgear standard, generator rating).

### Frontend build

```powershell
cd frontend
npm run build
```

All routes compile: `/`, `/documents`, `/rfi`, `/compliance`, `/schedule`, `/supply-chain`, `/commissioning`.

---

## Demo walkthrough

5-minute guided demo for stakeholders: [docs/demo-script.md](docs/demo-script.md)

| Step | Action |
|------|--------|
| 1 | Seed demo project from Dashboard |
| 2 | Documents → search *"UPS battery runtime"* |
| 3 | RFI Copilot → ask about CO-014 chiller redundancy |
| 4 | Compliance → upload `data/submittals/generator-submittal-d.md` |
| 5 | Schedule Risk → mitigate generator yard delay |
| 6 | Supply Chain → review delayed generator alert |
| 7 | Commissioning → record STS transfer test as passed |

---

## Repository layout

```
frontend/src/app/          Next.js pages (all modules)
frontend/src/lib/api.ts      Typed API client
backend/app/agents/          AI agents (RFI, compliance, schedule, supply, commissioning)
backend/app/api/             REST route handlers
backend/app/models/          SQLAlchemy ORM (11 entities)
backend/app/services/        Ingestion, embeddings, ChromaDB, seed, Groq client
backend/scripts/             seed_corpus.py, run_golden_tests.py
data/                        Specs, RFIs, submittals, commissioning, golden fixtures
docs/                        SETUP.md, architecture.md, demo-script.md
docker-compose.yml           PostgreSQL 16 on port 5433
```

Detailed setup: [docs/SETUP.md](docs/SETUP.md)

---

## Production hardening checklist

Before exposing beyond staging:

- [ ] Replace demo seed with real project ingestion pipeline
- [ ] Add authentication (OAuth2 / JWT) and project-level RBAC
- [ ] Store secrets in a vault (not `.env` on disk)
- [ ] Persist ChromaDB to a mounted volume or migrate to pgvector / Pinecone
- [ ] Enable HTTPS reverse proxy (nginx / Caddy)
- [ ] Configure structured logging and health monitoring
- [ ] Rate-limit Groq API calls and add retry/backoff
- [ ] Back up PostgreSQL on a schedule

---

## License

MIT — see [LICENSE](LICENSE)
