# CBS PM Buddy — System Design Document (v1)

> A single-user desktop app for Product Managers managing infrastructure backlogs. It organizes work into **Epics → Features → User Stories**, with a local LLM assistant that helps decompose each level into the next.

---

## 1. Problem Statement

Infrastructure Product Managers struggle to break down high-level leadership Epics into actionable User Stories. The process is manual, inconsistent, and misses context — especially when DevOps or operational concerns need to be woven in.

**CBS PM Buddy** is a local-first tool that:
- Organizes work in a three-level hierarchy: **Epic → Feature → User Story**
- Uses a **local LLM** to suggest decompositions at each level
- Lets the PM review, edit, and own every item — fully human-in-the-loop

---

## 2. Data Model

### 2.1 Hierarchy

```
Epic (strategic initiative from leadership or PM)
├── Feature (tangible capability under an Epic)
│   ├── User Story (implementable increment)
│   │   └── Acceptance Criteria (list)
│   └── User Story
└── Feature
```

### 2.2 Entities

#### Epic
| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | UUID | System | Primary key |
| `title` | str | PM / Leadership | Initiative name |
| `description` | str | PM / Leadership | Business context and outcomes |
| `priority` | Enum [P0..P3] | PM / Leadership | Priority level |
| `status` | Enum [Backlog, Active, Done, Archived] | System | Lifecycle state |
| `tags` | list[str] | PM | Free-form categorization |
| `created_by` | str | System | Who created it |
| `created_at` | datetime | System | Auto-set |
| `updated_at` | datetime | System | Last modification time |

#### Feature (belongs to Epic)
| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | UUID | System | Primary key |
| `epic_id` | UUID | System | FK → Epic |
| `title` | str | PM / LLM | Capability name |
| `description` | str | PM / LLM | What it delivers |
| `status` | Enum [Backlog, Active, Done] | System | Lifecycle state |
| `created_by` | Enum [PM, LLM] | System | Authorship tracking |
| `llm_confidence` | float \| null | System | If LLM-generated, confidence 0–1 |
| `created_at` | datetime | System | Auto-set |
| `updated_at` | datetime | System | Last modification time |

#### User Story (belongs to Feature)
| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | UUID | System | Primary key |
| `feature_id` | UUID | System | FK → Feature |
| `title` | str | PM / LLM | "As a [role], I want [goal] so that [reason]" |
| `description` | str | PM / LLM | Expanded context |
| `acceptance_criteria` | list[str] | PM / LLM | Gherkin-style or checklist |
| `effort_estimate` | Enum [XS, S, M, L, XL] \| null | PM | Story points |
| `status` | Enum [Backlog, Active, Done] | System | Lifecycle state |
| `tags` | list[str] | PM / LLM | Free-form categorization |
| `created_by` | Enum [PM, LLM] | System | Authorship tracking |
| `llm_confidence` | float \| null | System | If LLM-generated, confidence 0–1 |
| `created_at` | datetime | System | Auto-set |
| `updated_at` | datetime | System | Last modification time |

---

## 3. Decomposition Workflow

```
PM creates Epic (title, description, priority)
        │
        ▼
   Click "Decompose to Features"
        │
        ▼
   LLM suggests Features (with confidence scores)
        │
        ▼
   PM reviews: accepts / edits / rejects each
        │
        ▼
   For each Feature → Click "Decompose to Stories"
        │
        ▼
   LLM suggests User Stories + Acceptance Criteria
        │
        ▼
   PM reviews: accepts / edits / rejects each
        │
        ▼
   PM sets effort estimates, sprint targets, tags
        │
        ▼
   Done. Backlog is ready.
```

The key principle: **LLM suggests, PM decides.** Every generated item is inline-editable. The PM can regenerate any section independently.

---

## 4. LLM Integration

### 4.1 Supported Backends

| Backend | Connection | Auto-Detect | Notes |
|---------|-----------|-------------|-------|
| **Ollama** | `http://localhost:11434` | ✅ Default | Most common local LLM runner |
| **LM Studio** | `http://localhost:1234/v1` | ✅ Common | OpenAI-compatible API |
| **Any OpenAI-compatible** | Custom URL + key | Manual config | Flexibility |

### 4.2 Recommended Models

| Use Case | Model | Min VRAM |
|----------|-------|----------|
| Decomposition (primary) | `llama3.1:8b` or `mistral:7b` | 8GB |
| Complex epics | `llama3.1:70b` or `qwen2.5:32b` | 40GB+ |
| Lightweight fallback | `phi3:mini` | 4GB |

### 4.3 Prompt Template

The LLM receives a structured prompt based on the parent item:

```
You are an Infrastructure Product Manager's assistant.
Decompose the following into actionable items.

---
Parent: {title}
Description: {description}
Priority: {priority}
---

Generate {target_type}s that break this down into implementable work.

For each {target_type}, provide:
- title: short, clear name
- description: expanded context
- acceptance_criteria: (for User Stories only) concrete, testable criteria
- tags: relevant categories

Output as JSON array. Include a confidence score (0.0–1.0) for each item.
```

### 4.4 Error Handling

- **No LLM available** → "Generate" button disabled; PM can still create items manually
- **LLM error/timeout** → Retry once, then show partial results + message to retry
- **Poor output** → PM adjusts context and re-generates just that section

---

## 5. Persistence

### Storage: Single SQLite database

Location: `~/.local/share/cbs-pm-buddy/data.db`

```sql
CREATE TABLE epics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT CHECK(priority IN ('P0','P1','P2','P3')),
    status TEXT DEFAULT 'Backlog',
    tags TEXT,           -- JSON array
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE features (
    id TEXT PRIMARY KEY,
    epic_id TEXT NOT NULL REFERENCES epics(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'Backlog',
    created_by TEXT CHECK(created_by IN ('PM','LLM')),
    llm_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_stories (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL REFERENCES features(id),
    title TEXT NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,  -- JSON array
    effort_estimate TEXT,
    status TEXT DEFAULT 'Backlog',
    tags TEXT,                 -- JSON array
    created_by TEXT CHECK(created_by IN ('PM','LLM')),
    llm_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. UI (Streamlit)

```
┌──────────────────────────────────────────────────────────┐
│  CBS PM Buddy                              [Settings]   │
├──────────────────────┬───────────────────────────────────┤
│  Sidebar             │  Main Area                        │
│                      │                                   │
│  📋 Epics            │  Epic View                        │
│  ├── Epic A         │                                   │
│  ├── Epic B         │  Title: Migrate to Kubernetes       │
│  └── + New Epic     │  Desc: Move legacy apps...          │
│                      │  Priority: P1                     │
│  ⚡ Actions          │                                   │
│  └── 🤖 Decompose   │  ─── Features ──────────────       │
│                      │  [✓] Container orchestration      │
│  📊 Summary          │  [ ] Networking & ingress         │
│                      │  [✓] Monitoring & logging         │
│                      │  [+ Add Feature]                  │
│                      │                                   │
│                      │  ─── User Stories ─────────────   │
│                      │  [✓] As a DevOps eng, I want...   │
│                      │  [ ] As a Platform owner...       │
│                      │  [+ Add Story]                    │
└──────────────────────┴───────────────────────────────────┘
```

**Interaction model:**
1. Create Epic → fill title, description, priority
2. Click **"Decompose"** → LLM suggests Features (streaming)
3. PM accepts / edits / rejects each Feature
4. For a Feature → click **"Decompose to Stories"** → LLM suggests User Stories + acceptance criteria
5. PM reviews and finalizes

---

## 7. Configuration

```
~/.config/cbs-pm-buddy/
├── llm.json              # LLM backend config
└── preferences.json      # PM name, default priority, etc.
```

`llm.json`:
```json
{
  "backend": "ollama",
  "base_url": "http://localhost:11434",
  "model": "llama3.1:8b",
  "temperature": 0.7,
  "max_tokens": 4096,
  "timeout_seconds": 120
}
```

---

## 8. Project Structure

```
cbs-pm-buddy/
├── pyproject.toml
├── uv.lock
├── .python-version
├── README.md
│
├── src/
│   └── cbs_pm_buddy/
│       ├── __init__.py
│       ├── app.py              # Streamlit entry point
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── epic.py
│       │   ├── feature.py
│       │   └── user_story.py
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   └── database.py     # SQLite connection + CRUD
│       │
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── adapter.py      # LLM interface (ABC)
│       │   ├── ollama_adapter.py
│       │   └── prompt_templates.py
│       │
│       └── config/
│           ├── __init__.py
│           └── llm_config.py
│
└── tests/
```

---

## 9. Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Desktop UI |
| `pydantic` | Data validation & models |
| `sqlite3` (stdlib) | Local database |
| `httpx` | Async HTTP client for LLM APIs |
| `pyyaml` | Config file handling |

---

## 10. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| Startup time | < 3s from `streamlit run` |
| LLM response time | < 30s for full decomposition (configurable) |
| Data portability | Single SQLite file, easy to backup/restore |
| Privacy | Zero data leaves the machine |
| Offline-first | Fully works without internet (LLM is local) |
