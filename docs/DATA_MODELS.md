# Data Models — CBS PM Buddy

## Overview

Three entities in a parent-child hierarchy: **Epic → Feature → User Story**. All data is stored in a single SQLite database.

---

## Entity: Epic

A strategic initiative from leadership or the PM. The top-level container for all work.

### Fields

| Field | Type | Constraint | Source | Description |
|-------|------|-----------|--------|-------------|
| `id` | TEXT (UUID) | PK, NOT NULL | System | Primary key |
| `title` | TEXT | NOT NULL | PM / Leadership | Initiative name |
| `description` | TEXT | — | PM / Leadership | Business context and outcomes |
| `priority` | TEXT | CHECK IN ('P0','P1','P2','P3') | PM / Leadership | Priority level (P0 = highest) |
| `status` | TEXT | DEFAULT 'Backlog' | System | Lifecycle state |
| `tags` | TEXT (JSON array) | — | PM | Free-form categorization, e.g. `["infrastructure", "migration"]` |
| `created_by` | TEXT | NOT NULL | System | Who created it ("Leadership" or PM name) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | System | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | System | Last modification time |

### Status Values

`Backlog` → `Active` → `Done` → `Archived`

---

## Entity: Feature

A tangible capability or deliverable under an Epic. Bridges the gap between strategic intent and implementation.

### Fields

| Field | Type | Constraint | Source | Description |
|-------|------|-----------|--------|-------------|
| `id` | TEXT (UUID) | PK, NOT NULL | System | Primary key |
| `epic_id` | TEXT (UUID) | FK → epics(id), NOT NULL | System | Parent Epic |
| `title` | TEXT | NOT NULL | PM / LLM | Capability name |
| `description` | TEXT | — | PM / LLM | What it delivers and why |
| `status` | TEXT | DEFAULT 'Backlog' | System | Lifecycle state |
| `created_by` | TEXT | CHECK IN ('PM','LLM') | System | Authorship tracking |
| `llm_confidence` | REAL | — | System | If LLM-generated, confidence score 0.0–1.0 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | System | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | System | Last modification time |

### Status Values

`Backlog` → `Active` → `Done`

---

## Entity: User Story

An implementable increment of work. The smallest unit in the backlog hierarchy.

### Fields

| Field | Type | Constraint | Source | Description |
|-------|------|-----------|--------|-------------|
| `id` | TEXT (UUID) | PK, NOT NULL | System | Primary key |
| `feature_id` | TEXT (UUID) | FK → features(id), NOT NULL | System | Parent Feature |
| `title` | TEXT | NOT NULL | PM / LLM | Standard format: "As a [role], I want [goal] so that [reason]" |
| `description` | TEXT | — | PM / LLM | Expanded context, technical notes |
| `acceptance_criteria` | TEXT (JSON array) | — | PM / LLM | Concrete, testable criteria. e.g. `["Given X, When Y, Then Z"]` |
| `effort_estimate` | TEXT | CHECK IN ('XS','S','M','L','XL') | PM | Story points (Fibonacci-like scale) |
| `status` | TEXT | DEFAULT 'Backlog' | System | Lifecycle state |
| `tags` | TEXT (JSON array) | — | PM / LLM | Free-form categorization, e.g. `["frontend", "api"]` |
| `created_by` | TEXT | CHECK IN ('PM','LLM') | System | Authorship tracking |
| `llm_confidence` | REAL | — | System | If LLM-generated, confidence score 0.0–1.0 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | System | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | System | Last modification time |

### Status Values

`Backlog` → `Active` → `Done`

### Effort Estimates

| Value | Meaning |
|-------|---------|
| XS | Trivial, < 1 hour of work |
| S | Small, half a day or less |
| M | Medium, 1–2 days |
| L | Large, multiple days, needs splitting consideration |
| XL | Epic-sized — should be decomposed further |

---

## SQL Schema

```sql
CREATE TABLE epics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT CHECK(priority IN ('P0','P1','P2','P3')),
    status TEXT DEFAULT 'Backlog',
    tags TEXT,
    created_by TEXT NOT NULL,
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
    acceptance_criteria TEXT,
    effort_estimate TEXT CHECK(effort_estimate IN ('XS','S','M','L','XL')),
    status TEXT DEFAULT 'Backlog',
    tags TEXT,
    created_by TEXT CHECK(created_by IN ('PM','LLM')),
    llm_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient queries
CREATE INDEX idx_features_epic ON features(epic_id);
CREATE INDEX idx_stories_feature ON user_stories(feature_id);
```

---

## Pydantic Models (Python)

These are the in-memory representations used by the application. They mirror the SQL schema but add validation and serialization helpers.

### Epic Model

```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
import uuid

class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

class Status(str, Enum):
    BACKLOG = "Backlog"
    ACTIVE = "Active"
    DONE = "Done"
    ARCHIVED = "Archived"

class Epic(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.P2
    status: Status = Status.BACKLOG
    tags: list[str] = Field(default_factory=list)
    created_by: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_updated(self):
        from datetime import datetime
        self.updated_at = datetime.utcnow().isoformat()
```

### Feature Model

```python
class Feature(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    epic_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: Status = Status.BACKLOG
    created_by: str = "PM"           # "PM" or "LLM"
    llm_confidence: Optional[float] = None  # 0.0–1.0 if LLM-generated
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_updated(self):
        from datetime import datetime
        self.updated_at = datetime.utcnow().isoformat()
```

### User Story Model

```python
class Effort(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

class UserStory(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    feature_id: uuid.UUID
    title: str
    description: Optional[str] = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    effort_estimate: Optional[Effort] = None
    status: Status = Status.BACKLOG
    tags: list[str] = Field(default_factory=list)
    created_by: str = "PM"           # "PM" or "LLM"
    llm_confidence: Optional[float] = None  # 0.0–1.0 if LLM-generated
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_updated(self):
        from datetime import datetime
        self.updated_at = datetime.utcnow().isoformat()
```

---

## Relationships

```
epics (1) ────< features (N)
features (1) ────< user_stories (N)
```

- Deleting an Epic cascades to its Features and their Stories.
- A Feature always belongs to exactly one Epic.
- A User Story always belongs to exactly one Feature.
- No cross-references between siblings — the hierarchy is strict parent-child.
