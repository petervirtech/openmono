# CBS PM Buddy

A local-first tool for Product Managers managing infrastructure backlogs. It organizes work into **Epics → Features → User Stories**, with a local LLM assistant that helps decompose each level into the next.

## Quick Start

```bash
cd cbs-pm-buddy
uv sync
uv run uvicorn cbs_pm_buddy:app --reload
```

Then open `http://localhost:8000` and check `/docs` for the interactive API reference.

## Prerequisites

- **Python 3.12+** (managed by `uv`)
- **Ollama** running locally with a model pulled (e.g., `ollama pull llama3.1:8b`)
  - Or **LM Studio** running locally on port 1234
  - Or any OpenAI-compatible local endpoint

## Project Structure

```
cbs-pm-buddy/
├── pyproject.toml          # uv project config
├── src/cbs_pm_buddy/       # Application source
│   ├── __init__.py         # FastAPI app export
│   ├── main.py             # API routes (FastAPI)
│   ├── db/                 # SQLite persistence layer
│   │   ├── __init__.py
│   │   └── database.py     # Connection, migrations, CRUD repos
│   ├── models/             # Data models (Pydantic) — TODO
│   ├── llm/                # LLM adapters — TODO
│   └── config/             # Configuration management — TODO
├── tests/                  # Test suite — TODO
└── docs/                   # Design & build documents
```

## Documentation

| Document | Description |
|----------|-------------|
| [DESIGN.md](docs/DESIGN.md) | System overview and architecture |
| [DATA_MODELS.md](docs/DATA_MODELS.md) | Detailed database schema and entity definitions |
| [LLM_INTEGRATION.md](docs/LLM_INTEGRATION.md) | LLM adapter specs, prompt templates, model recommendations |
| [UI_DESIGN.md](docs/UI_DESIGN.md) | UI layout and interaction design |
| [WORKFLOW.md](docs/WORKFLOW.md) | Step-by-step decomposition workflow |

## Configuration

LLM settings are stored in `~/.config/cbs-pm-buddy/llm.json`:

```json
{
  "backend": "ollama",
  "base_url": "http://localhost:11434",
  "model": "llama3.1:8b",
  "temperature": 0.7,
  "timeout_seconds": 120
}
```

## Data Storage

SQLite database at `~/.local/share/cbs-pm-buddy/data.db`. Single file — easy to back up or move. The database is excluded from version control (see `.gitignore`).

## License

Private — built for internal use.
