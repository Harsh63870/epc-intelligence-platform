# Demo Script — EPC Intelligence Platform

**Duration:** ~5 minutes  
**Project:** Mumbai Hyperscale DC-01 (Tier III)  
**Prerequisites:** Docker running, backend on :8000, frontend on :3000

---

## 1. Setup (30 seconds)

```powershell
docker compose up -d
cd backend && .venv\Scripts\uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Open http://localhost:3000

---

## 2. Seed demo project (30 seconds)

1. Go to **Dashboard**
2. Click **Seed Demo Project**
3. Confirm message shows: documents, vectors, RFIs, shipments, schedule tasks

**Talking point:** *"One click loads the full project corpus — specs, RFIs, change orders, procurement, schedule, and commissioning procedures."*

---

## 3. Document intelligence (45 seconds)

1. Navigate to **Documents**
2. Search: `UPS battery runtime`
3. Show vector search results from project specs and RFIs

**Talking point:** *"Semantic search across 23+ project documents — no manual folder digging."*

---

## 4. RFI Copilot (60 seconds)

1. Navigate to **RFI Copilot**
2. Click demo question: *"What is the approved UPS battery runtime for Tier III?"*
3. Show answer with **citations** and **similar RFIs** (RFI-014, RFI-031)
4. Ask: *"What changed in CO-014 regarding chiller redundancy?"*

**Talking point:** *"Answers cite source documents. Similar-RFI detection prevents duplicate questions — saves coordination time."*

---

## 5. Spec Compliance (60 seconds)

1. Navigate to **Spec Compliance**
2. Upload `data/submittals/generator-submittal-d.md`
3. Enter vendor: `DieselPower GmbH`
4. Show comparison table — **standby rating 3500 kW vs required 4000 kW** flagged as NC
5. Show NC audit trail panel

**Talking point:** *"Automated submittal review against owner specs. Non-conformances logged for audit — no spreadsheet tracking."*

---

## 6. Schedule Risk (45 seconds)

1. Navigate to **Schedule Risk**
2. Point out **Generator yard civil works** — high risk (+10 days delay)
3. Click **Mitigate** — show AI-generated mitigation options

**Talking point:** *"Procurement delays cross-referenced against critical path. Mitigation options generated in seconds, not hours of schedule meetings."*

---

## 7. Supply Chain (30 seconds)

1. Navigate to **Supply Chain**
2. Show **delayed Generator 4000kW** alert linked to schedule task
3. Point out shipment map with in-transit positions

**Talking point:** *"At-risk deliveries linked to schedule impact — procurement and planning on the same screen."*

---

## 8. Commissioning Copilot (45 seconds)

1. Navigate to **Commissioning Copilot**
2. Select **power** system tests
3. Record STS transfer test: measured value `3.2 ms`, click **Pass**
4. Show progress bar update

**Talking point:** *"Guided IST wizard against TIA-942 and Uptime Tier criteria. Test records auto-generated for turnover documentation."*

---

## 9. Dashboard wrap-up (15 seconds)

Return to **Dashboard** — show updated metrics:
- Schedule risks
- At-risk shipments
- Commissioning progress
- Hours saved

**Closing line:** *"Six modules, one intelligence layer — turning fragmented EPC data into actionable project decisions."*

---

## Backup: Golden tests

If compliance demo fails live:

```powershell
cd backend
.\.venv\Scripts\python scripts\run_golden_tests.py
```

Expected: **4/4 passed**

---

## API docs

http://localhost:8000/docs — full OpenAPI reference for all endpoints.
