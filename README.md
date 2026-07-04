<div align="center">

# EPC Intelligence Platform

**AI-powered project intelligence for hyperscale data centre EPC delivery.**

Unifies specifications, vendor submittals, procurement, schedule, RFIs, commissioning, and quality
records into a single operational layer aligned with **Tier III / Tier IV** standards
(TIA‑942, Uptime Institute).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](frontend/package.json)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](backend/requirements.txt)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](backend/requirements.txt)

**Demo project:** Mumbai Hyperscale DC‑01

[Quick Start](#quick-start) · [Architecture](#architecture) · [API Reference](#api-reference) · [Demo Walkthrough](#demo-walkthrough) · [Production Hardening](#production-hardening-checklist)

</div>

---

## Overview

EPC (Engineering, Procurement, Construction) delivery for hyperscale data centres generates a
sprawl of disconnected documents — specs, submittals, RFIs, change orders, schedules, and
commissioning records — that live in silos and slow decision-making. **EPC Intelligence Platform**
ingests that corpus into a single system, layers retrieval-augmented AI agents on top, and
surfaces the answers project teams actually need: *Is this submittal compliant? What's at risk on
the critical path? Which shipment is about to blow the schedule? Did this system pass IST?*

## Platform capabilities

| Module | Route | Capability |
|---|---|---|
| **Dashboard** | `/` | Live KPIs — non-conformances, open RFIs, schedule risks, at-risk shipments, commissioning progress, hours saved |
| **Documents** | `/documents` | Ingest PDF/Markdown, chunk, embed, semantic vector search |
| **RFI Copilot** | `/rfi` | RAG-based answers with document citations and similar-RFI detection |
| **Spec Compliance** | `/compliance` | Automated submittal review against specs, NC audit trail, golden-test validated |
| **Schedule Risk** | `/schedule` | Critical-path risk derived from procurement ETAs, with AI-suggested mitigations |
| **Supply Chain** | `/supply-chain` | Shipment tracking, route visibility, schedule-impact alerts |
| **Commissioning** | `/commissioning` | Guided IST (Integrated Systems Test) wizard with pass/fail/NC recording and per-system progress |

## Architecture

### Component view

```mermaid
flowchart TB
    subgraph Frontend["Next.js Frontend · port 3000"]
        Dashboard
        Documents
        RFI["RFI Copilot"]
        Compliance["Spec Compliance"]
        Schedule["Schedule Risk"]
        Supply["Supply Chain"]
        Comm["Commissioning"]
    end

    subgraph Backend["FastAPI Backend · port 8000"]
        API["REST API /api/v1"]
        Agents["AI Agents\nRFI · Compliance · Schedule · Supply Chain · Commissioning"]
        Ingestion["Document Ingestion\nchunk → embed → store"]
    end

    subgraph Storage["Data Layer"]
        PG[("PostgreSQL 16\nrelational")]
        Chroma[("ChromaDB\nvector store")]
    end

    subgraph External["External Service"]
        Groq["Groq LLM API\nllama-3.3-70b-versatile"]
    end

    Frontend -- "REST /api/v1" --> API
    API --> Agents
    API --> Ingestion
    Agents --> PG
    Agents --> Chroma
    Agents -. "optional, falls back if unset" .-> Groq
    Ingestion --> PG
    Ingestion --> Chroma
```

### Agent responsibilities

Each module in the UI maps to one backend agent, with its own data sources and output:

| Module | Agent | Data sources | Output |
|---|---|---|---|
| Documents | *(ingestion service, no agent)* | PDF/Markdown uploads, `data/` corpus | Chunked embeddings, semantic search |
| RFI Copilot | `rfi_agent` | ChromaDB RAG + `rfis` table | Cited answers, similar-RFI detection |
| Spec Compliance | `spec_compliance_agent` | `specifications` + parsed submittal | Non-conformance records, comparison table |
| Schedule Risk | `schedule_agent` | `schedule_tasks` + procurement ETAs | Risk scores, Groq-generated mitigations |
| Supply Chain | `supply_chain_agent` | `procurement_items` + schedule links | Shipment map, critical-path alerts |
| Commissioning | `commissioning_agent` | `commissioning_tests` table | Wizard progress, pass/fail/NC records |

### Request & data flow

**1. Document ingestion** — triggered on upload or demo seed:

1. File uploaded, or read from the `data/` corpus during seeding
2. PyMuPDF extracts text from PDFs; Markdown is read directly
3. Text is chunked (~500 tokens, with overlap) by the chunking service
4. `sentence-transformers/all-MiniLM-L6-v2` generates embeddings locally — no external API call
5. Chunks are stored in ChromaDB with metadata (`doc_type`, `filename`, `project_id`)
6. The document record itself is persisted to PostgreSQL

**2. RFI Copilot query:**

1. The user's question is embedded and matched against ChromaDB
2. Top-k relevant chunks are retrieved as context
3. Previously resolved RFIs are surfaced via embedding similarity on the `rfis` table
4. Groq (`llama-3.3-70b-versatile`) generates a cited answer from the retrieved context
5. If `GROQ_API_KEY` is unset, the agent falls back to returning the retrieved chunks directly, un-summarized
6. An audit event is logged for the dashboard's "hours saved" metric

**3. Spec compliance check:**

1. A submittal (Markdown/PDF) is uploaded
2. Key attributes are extracted via regex rules, optionally refined with Groq JSON extraction
3. Extracted attributes are compared against each linked specification, rule by rule
4. Any failing rule creates a `NonConformance` record with a severity level
5. The golden-test suite re-runs this logic against 4 planted deviations in `data/submittals/` to guard against regressions

**4. Schedule risk scoring:**

1. Schedule tasks are linked to procurement items via `depends_on_procurement_id`
2. A risk score is computed from the gap between a shipment's ETA and the task's planned start date
3. Tasks scoring ≥ 0.5 are surfaced as high-risk on the dashboard and Schedule Risk page
4. Mitigation options are generated via Groq, or a rule-based fallback if no key is set

**5. Supply chain tracking:** procurement items carry origin, current, and destination coordinates; at-risk or delayed shipments raise alerts, which are cross-linked back to the critical-path schedule tasks they threaten.

**6. Commissioning:** tests are seeded from TIA-942 / Uptime Institute Tier procedures; the wizard walks a witness through pass/fail/NC recording per test, with progress rolled up by system type (power, cooling, etc.).

### Database schema

Core PostgreSQL entities:

| Table | Purpose |
|---|---|
| `projects` | Project metadata — tier, location, status |
| `documents` | Ingested file records with parsed text |
| `specifications` | Structured requirement rules |
| `submittals` / `non_conformances` | Compliance workflow and audit trail |
| `rfis` | Request-for-information records |
| `procurement_items` | Equipment shipments with geo coordinates |
| `schedule_tasks` | Planned tasks with procurement dependencies |
| `commissioning_tests` | IST procedures and recorded results |
| `audit_events` | Action log used for hours-saved metrics |

### Design rationale

| Choice | Reason |
|---|---|
| Next.js + Tailwind | Fast iteration, clean industrial dark theme |
| FastAPI | Async-ready, automatic OpenAPI docs, native fit with the Python ML stack |
| PostgreSQL | Relational integrity across EPC workflow entities |
| ChromaDB | Local vector store — zero cloud dependency for the demo |
| sentence-transformers | Free, local embeddings with no per-call API cost |
| Groq | Fast, generous free tier for RAG generation and mitigation suggestions |
| Dockerized Postgres on 5433 | Avoids clashing with a locally installed Postgres on 5432 |

Full design notes: [`docs/architecture.md`](docs/architecture.md)

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| API | FastAPI, Pydantic, SQLAlchemy 2 |
| Database | PostgreSQL 16 (Dockerized) |
| Vector store | ChromaDB (local, persistent on disk) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local inference, no API cost) |
| Document parsing | PyMuPDF |
| LLM | Groq `llama-3.3-70b-versatile` (OpenAI-compatible API) |

## Requirements

- **Node.js** 20+
- **Python** 3.11+
- **Docker Desktop** (PostgreSQL)
- **Groq API key** — recommended; RFI answers and schedule mitigations fall back to
  non-generative behavior without it

## Quick start

### 1. Database

```bash
docker compose up -d
docker compose ps   # epc-postgres should be "healthy"
```

PostgreSQL listens on host port **5433** (avoids clashing with a local Postgres on 5432).

### 2. Backend

```bash
cd backend
cp .env.example .env          # Windows: copy .env.example .env
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Backend environment** (`backend/.env`):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://epc:epc_secret@127.0.0.1:5433/epc_intelligence` |
| `GROQ_API_KEY` | Groq API key for RFI answers and schedule mitigations | *(empty — features fall back)* |
| `CHROMA_PATH` | ChromaDB persistence directory | `./chroma_data` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` |

### 3. Frontend

```bash
cd frontend
npm install
npm run build
npm start
```

For local development with hot reload, use `npm run dev` instead of `build` + `start`.

**Frontend environment** (`frontend/.env.local`):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Seed the demo project

1. Open **http://localhost:3000**
2. Click **Seed Demo Project** on the Dashboard

This loads:

- 23+ project documents (specs, RFIs, change orders, commissioning procedures)
- Vector embeddings into ChromaDB
- 5 specifications, 10 RFIs, 6 commissioning tests
- 5 procurement shipments and 7 schedule tasks (with planted delay scenarios)
- 4 demo submittals in `data/submittals/` for compliance testing

## API reference

- **Interactive docs (Swagger UI):** http://localhost:8000/docs
- **Health check:** `GET /api/v1/health`

| Endpoint group | Prefix | Purpose |
|---|---|---|
| Core | `/api/v1/projects`, `/api/v1/dashboard/metrics` | Projects and dashboard KPIs |
| Documents | `/api/v1/documents/*` | Ingest, list, vector search |
| RFI | `/api/v1/rfi/*` | Chat, similar-RFI detection |
| Compliance | `/api/v1/compliance/*` | Submittal review, NC management |
| Schedule | `/api/v1/schedule/*` | Tasks, risk scoring, AI mitigations |
| Supply chain | `/api/v1/supply-chain/*` | Shipments, schedule-impact alerts |
| Commissioning | `/api/v1/commissioning/*` | Tests, progress, result recording |
| Seed | `POST /api/v1/seed` | Load the demo project |

## Quality assurance

### Golden compliance tests

Automated regression tests validate the compliance agent against planted submittal deviations,
running against an isolated SQLite database (no Docker required):

```bash
cd backend
python scripts/run_golden_tests.py
```

Expected result: **4/4 passed** — UPS runtime, chiller redundancy, switchgear standard, and
generator rating cases.

### Frontend build

```bash
cd frontend
npm run build
```

All routes must compile cleanly: `/`, `/documents`, `/rfi`, `/compliance`, `/schedule`,
`/supply-chain`, `/commissioning`.

## Demo walkthrough

A 5-minute guided demo for stakeholders — full script at [`docs/demo-script.md`](docs/demo-script.md):

| Step | Action |
|---|---|
| 1 | Seed the demo project from the Dashboard |
| 2 | **Documents** → search *"UPS battery runtime"* |
| 3 | **RFI Copilot** → ask about CO‑014 chiller redundancy |
| 4 | **Compliance** → upload `data/submittals/generator-submittal-d.md` |
| 5 | **Schedule Risk** → mitigate the generator yard delay |
| 6 | **Supply Chain** → review the delayed generator alert |
| 7 | **Commissioning** → record the STS transfer test as passed |

## Repository layout

```
frontend/src/app/            Next.js pages (all modules)
frontend/src/lib/api.ts      Typed API client
backend/app/agents/          AI agents — RFI, compliance, schedule, supply chain, commissioning
backend/app/api/             REST route handlers
backend/app/models/          SQLAlchemy ORM entities (projects, documents, specs, RFIs, etc.)
backend/app/services/        Ingestion, chunking, embeddings, ChromaDB, seeding, Groq client
backend/scripts/             seed_corpus.py, run_golden_tests.py
data/                        Specs, RFIs, submittals, commissioning, procurement, golden fixtures
docs/                        SETUP.md, architecture.md, demo-script.md
docker-compose.yml           PostgreSQL 16 on host port 5433
```

Detailed local setup: [`docs/SETUP.md`](docs/SETUP.md)

## Production hardening checklist

This repository ships as a fully working local/staging build. Before exposing it beyond staging:

- [ ] Replace the demo seed with a real project ingestion pipeline
- [ ] Add authentication (OAuth2 / JWT) and project-level RBAC
- [ ] Store secrets in a vault, not in a `.env` file on disk
- [ ] Persist ChromaDB to a mounted volume, or migrate to `pgvector` / Pinecone
- [ ] Put the app behind an HTTPS reverse proxy (nginx / Caddy)
- [ ] Add structured logging and health/metrics monitoring
- [ ] Rate-limit Groq API calls and add retry/backoff
- [ ] Schedule automated PostgreSQL backups
- [ ] Add CI (lint, golden tests, frontend build) before merging to `main`

## License

MIT — see [LICENSE](LICENSE).
