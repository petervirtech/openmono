# System Design — CBS PM Buddy

## 1. Problem Statement

Infrastructure Product Managers struggle to break down high-level leadership Epics into actionable User Stories. The process is manual, inconsistent, and misses context.

**CBS PM Buddy** is a local-first tool that:
- Organizes work in a three-level hierarchy: **Epic → Feature → User Story**
- Uses a **local LLM** to suggest decompositions at each level
- Lets the PM review, edit, and own every item — fully human-in-the-loop

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│              CBS PM Buddy API                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌──────────────────┐               │
│  │ FastAPI  │    │ Business Logic   │               │
│  │ Routes   │◄──►│ Orchestrator     │               │
│  └──────────┘    └───────┬──────────┘               │
│                          │                           │
│                   ┌──────▼───────┐    ┌────────────┐│
│                   │  SQLite DB   │◄──►│ LLM Adapter││
│                   │ (data.db)    │    │ (Ollama /  ││
│                   └──────────────┘    │ LM Studio) ││
│                                       └────────────┘│
└─────────────────────────────────────────────────────┘
```

### Design Principles

1. **Local-first, single-user** — No cloud dependency. All data and AI inference run on the PM's machine.
2. **Zero-config LLM integration** — Auto-detects Ollama, LM Studio, or any OpenAI-compatible local endpoint.
3. **Human-in-the-loop** — The LLM *suggests*; the PM *decides*. Every generated item is editable.
4. **Audit trail** — Track who (PM vs LLM) authored each backlog item and when it was modified.

## 3. Data Model Overview

```
Epic (strategic initiative from leadership or PM)
├── Feature (tangible capability under an Epic)
│   ├── User Story (implementable increment)
│   │   └── Acceptance Criteria (list of strings)
│   └── User Story
└── Feature
```

Each entity tracks `created_by` (PM or LLM) and, for LLM-generated items, an `llm_confidence` score (0.0–1.0).

## 4. Persistence

Single SQLite database at `~/.local/share/cbs-pm-buddy/data.db`. Three tables: `epics`, `features`, `user_stories`. See [DATA_MODELS.md](DATA_MODELS.md) for full schema.

## 5. LLM Integration

The LLM is used exclusively for decomposition suggestions. Supported backends: Ollama (default), LM Studio, or any OpenAI-compatible endpoint. See [LLM_INTEGRATION.md](LLM_INTEGRATION.md).

## 6. API

FastAPI-based REST API with auto-generated OpenAPI/Swagger docs at `/docs`. Endpoints for CRUD operations on Epics, Features, and User Stories.

### Current Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/items` | List items (legacy) |
| `POST` | `/items` | Create item (legacy) |
| `GET` | `/items/{id}` | Get item by ID (legacy) |
| `DELETE` | `/items/{id}` | Delete item (legacy) |

Full entity endpoints (Epic/Feature/UserStory) to be added as the API layer is extended.

## 7. Workflow

PM creates Epic → clicks "Decompose" → LLM suggests Features → PM reviews → for each Feature, clicks "Decompose to Stories" → LLM suggests User Stories → PM finalizes. See [WORKFLOW.md](WORKFLOW.md).

## 8. Dependencies

| Package | Purpose | Status |
|---------|---------|--------|
| `fastapi` | REST API framework | ✅ Installed |
| `uvicorn` | ASGI server | ✅ Installed |
| `pydantic` | Data validation & models | ✅ Installed |
| `sqlite3` (stdlib) | Local database | ✅ Used — see `src/cbs_pm_buddy/db/database.py` |
| `streamlit` | Desktop UI | 📋 Planned |
| `httpx` | Async HTTP client for LLM APIs | 📋 Planned |
| `pyyaml` | Config file handling | 📋 Planned |

## 9. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| Startup time | < 3s from `streamlit run` |
| LLM response time | < 30s for full decomposition (configurable) |
| Data portability | Single SQLite file, easy to backup/restore |
| Privacy | Zero data leaves the machine |
| Offline-first | Fully works without internet (LLM is local) |
