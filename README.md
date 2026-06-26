# EPC Intelligence Platform

An AI-powered project intelligence system for hyperscale data centre EPC delivery. The platform connects specifications, vendor submittals, procurement records, schedules, RFIs, commissioning documents, and quality records into a single operational intelligence layer.

Built for data centre construction teams targeting Tier III and Tier IV quality standards.

## Features (roadmap)

| Module | Description |
|--------|-------------|
| **Dashboard** | Project KPIs — non-conformances, RFIs, schedule risks, supply chain alerts, commissioning progress |
| **RFI Copilot** | RAG over project documents with citations and similar-RFI detection |
| **Spec Compliance** | Automated submittal checking against specifications with audit trail |
| **Schedule Risk** | Critical-path risk identification with mitigation options |
| **Supply Chain** | Shipment visibility and delivery risk alerts |
| **Commissioning** | Guided testing against TIA-942 / Uptime Tier standards |

## Tech stack

- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL (Docker) or SQLite (local fallback)
- **AI (planned):** Groq LLM, ChromaDB, sentence-transformers

## Getting started

See [docs/SETUP.md](docs/SETUP.md) for full installation instructions.

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (for PostgreSQL)

### Quick start

```powershell
# 1. Start database
docker compose up -d

# 2. Backend
cd backend
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and use **Seed Demo Project** to load the sample project.

API documentation: http://localhost:8000/docs

## Project structure

```
frontend/           Web application
backend/            REST API and data models
data/               Project documents and test fixtures
docs/               Setup and architecture documentation
docker-compose.yml  PostgreSQL service (host port 5433)
```

## License

MIT — see [LICENSE](LICENSE)
