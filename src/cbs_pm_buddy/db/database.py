"""SQLite data layer for CBS PM Buddy.

Provides connection management, schema migrations, and CRUD repositories
for Epic, Feature, and UserStory entities.

Database file: ~/.local/share/cbs-pm-buddy/data.db
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_DIR = os.path.expanduser("~/.local/share/cbs-pm-buddy")
DB_PATH = os.path.join(DB_DIR, "data.db")


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a connection with foreign keys enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_connection(db_path: str = DB_PATH):
    """Context manager that yields a connection and commits on success."""
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------

MIGRATIONS = [
    """\
CREATE TABLE IF NOT EXISTS epics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT CHECK(priority IN ('P0','P1','P2','P3')),
    status TEXT DEFAULT 'Backlog',
    tags TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    """\
CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,
    epic_id TEXT NOT NULL REFERENCES epics(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'Backlog',
    created_by TEXT CHECK(created_by IN ('PM','LLM')),
    llm_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    """\
CREATE TABLE IF NOT EXISTS user_stories (
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
);""",
    """\
CREATE INDEX IF NOT EXISTS idx_features_epic ON features(epic_id);""",
    """\
CREATE INDEX IF NOT EXISTS idx_stories_feature ON user_stories(feature_id);""",
]


def migrate(conn: sqlite3.Connection) -> None:
    """Run all pending migrations."""
    for sql in MIGRATIONS:
        conn.execute(sql)


# ---------------------------------------------------------------------------
# Data classes (in-memory representations)
# ---------------------------------------------------------------------------

class Priority(str):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Status(str):
    BACKLOG = "Backlog"
    ACTIVE = "Active"
    DONE = "Done"
    ARCHIVED = "Archived"


class Effort(str):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


@dataclass
class Epic:
    id: UUID
    title: str
    description: Optional[str] = None
    priority: str = Priority.P2
    status: str = Status.BACKLOG
    tags: list[str] = field(default_factory=list)
    created_by: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_updated(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Feature:
    id: UUID
    epic_id: UUID
    title: str
    description: Optional[str] = None
    status: str = Status.BACKLOG
    created_by: str = "PM"
    llm_confidence: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_updated(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class UserStory:
    id: UUID
    feature_id: UUID
    title: str
    description: Optional[str] = None
    acceptance_criteria: list[str] = field(default_factory=list)
    effort_estimate: Optional[str] = None
    status: str = Status.BACKLOG
    tags: list[str] = field(default_factory=list)
    created_by: str = "PM"
    llm_confidence: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_updated(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Row <-> dataclass converters
# ---------------------------------------------------------------------------

def _row_to_epic(row: sqlite3.Row) -> Epic:
    return Epic(
        id=UUID(row["id"]),
        title=row["title"],
        description=row["description"],
        priority=row["priority"] or Priority.P2,
        status=row["status"] or Status.BACKLOG,
        tags=json.loads(row["tags"]) if row["tags"] else [],
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_feature(row: sqlite3.Row) -> Feature:
    return Feature(
        id=UUID(row["id"]),
        epic_id=UUID(row["epic_id"]),
        title=row["title"],
        description=row["description"],
        status=row["status"] or Status.BACKLOG,
        created_by=row["created_by"],
        llm_confidence=row["llm_confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_user_story(row: sqlite3.Row) -> UserStory:
    return UserStory(
        id=UUID(row["id"]),
        feature_id=UUID(row["feature_id"]),
        title=row["title"],
        description=row["description"],
        acceptance_criteria=json.loads(row["acceptance_criteria"]) if row["acceptance_criteria"] else [],
        effort_estimate=row["effort_estimate"],
        status=row["status"] or Status.BACKLOG,
        tags=json.loads(row["tags"]) if row["tags"] else [],
        created_by=row["created_by"],
        llm_confidence=row["llm_confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------------------------------------------------------------------------
# CRUD Repositories
# ---------------------------------------------------------------------------

class EpicRepository:
    """CRUD operations for Epics."""

    @staticmethod
    def create(conn: sqlite3.Connection, epic: Epic) -> Epic:
        now = datetime.now(timezone.utc).isoformat()
        tags_json = json.dumps(epic.tags)
        conn.execute(
            """INSERT INTO epics (id, title, description, priority, status, tags, created_by, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(epic.id),
                epic.title,
                epic.description,
                epic.priority,
                epic.status,
                tags_json,
                epic.created_by,
                now,
                now,
            ),
        )
        return _row_to_epic(conn.execute("SELECT * FROM epics WHERE id = ?", (str(epic.id),)).fetchone())

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, epic_id: UUID) -> Optional[Epic]:
        row = conn.execute("SELECT * FROM epics WHERE id = ?", (str(epic_id),)).fetchone()
        return _row_to_epic(row) if row else None

    @staticmethod
    def get_all(conn: sqlite3.Connection) -> list[Epic]:
        rows = conn.execute("SELECT * FROM epics ORDER BY created_at DESC").fetchall()
        return [_row_to_epic(r) for r in rows]

    @staticmethod
    def update(conn: sqlite3.Connection, epic: Epic) -> Epic:
        tags_json = json.dumps(epic.tags)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """UPDATE epics SET title=?, description=?, priority=?, status=?, tags=?, updated_at=?
               WHERE id=?""",
            (epic.title, epic.description, epic.priority, epic.status, tags_json, now, str(epic.id)),
        )
        return _row_to_epic(conn.execute("SELECT * FROM epics WHERE id = ?", (str(epic.id),)).fetchone())

    @staticmethod
    def delete(conn: sqlite3.Connection, epic_id: UUID) -> None:
        conn.execute("DELETE FROM epics WHERE id = ?", (str(epic_id),))


class FeatureRepository:
    """CRUD operations for Features."""

    @staticmethod
    def create(conn: sqlite3.Connection, feature: Feature) -> Feature:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO features (id, epic_id, title, description, status, created_by, llm_confidence, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(feature.id),
                str(feature.epic_id),
                feature.title,
                feature.description,
                feature.status,
                feature.created_by,
                feature.llm_confidence,
                now,
                now,
            ),
        )
        return _row_to_feature(conn.execute("SELECT * FROM features WHERE id = ?", (str(feature.id),)).fetchone())

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, feature_id: UUID) -> Optional[Feature]:
        row = conn.execute("SELECT * FROM features WHERE id = ?", (str(feature_id),)).fetchone()
        return _row_to_feature(row) if row else None

    @staticmethod
    def get_by_epic(conn: sqlite3.Connection, epic_id: UUID) -> list[Feature]:
        rows = conn.execute(
            "SELECT * FROM features WHERE epic_id = ? ORDER BY created_at DESC", (str(epic_id),)
        ).fetchall()
        return [_row_to_feature(r) for r in rows]

    @staticmethod
    def update(conn: sqlite3.Connection, feature: Feature) -> Feature:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """UPDATE features SET epic_id=?, title=?, description=?, status=?, created_by=?, llm_confidence=?, updated_at=?
               WHERE id=?""",
            (
                str(feature.epic_id),
                feature.title,
                feature.description,
                feature.status,
                feature.created_by,
                feature.llm_confidence,
                now,
                str(feature.id),
            ),
        )
        return _row_to_feature(conn.execute("SELECT * FROM features WHERE id = ?", (str(feature.id),)).fetchone())

    @staticmethod
    def delete(conn: sqlite3.Connection, feature_id: UUID) -> None:
        conn.execute("DELETE FROM features WHERE id = ?", (str(feature_id),))


class UserStoryRepository:
    """CRUD operations for User Stories."""

    @staticmethod
    def create(conn: sqlite3.Connection, story: UserStory) -> UserStory:
        now = datetime.now(timezone.utc).isoformat()
        ac_json = json.dumps(story.acceptance_criteria)
        tags_json = json.dumps(story.tags)
        conn.execute(
            """INSERT INTO user_stories (id, feature_id, title, description, acceptance_criteria, effort_estimate,
               status, tags, created_by, llm_confidence, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(story.id),
                str(story.feature_id),
                story.title,
                story.description,
                ac_json,
                story.effort_estimate,
                story.status,
                tags_json,
                story.created_by,
                story.llm_confidence,
                now,
                now,
            ),
        )
        return _row_to_user_story(
            conn.execute("SELECT * FROM user_stories WHERE id = ?", (str(story.id),)).fetchone()
        )

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, story_id: UUID) -> Optional[UserStory]:
        row = conn.execute("SELECT * FROM user_stories WHERE id = ?", (str(story_id),)).fetchone()
        return _row_to_user_story(row) if row else None

    @staticmethod
    def get_by_feature(conn: sqlite3.Connection, feature_id: UUID) -> list[UserStory]:
        rows = conn.execute(
            "SELECT * FROM user_stories WHERE feature_id = ? ORDER BY created_at DESC", (str(feature_id),)
        ).fetchall()
        return [_row_to_user_story(r) for r in rows]

    @staticmethod
    def update(conn: sqlite3.Connection, story: UserStory) -> UserStory:
        now = datetime.now(timezone.utc).isoformat()
        ac_json = json.dumps(story.acceptance_criteria)
        tags_json = json.dumps(story.tags)
        conn.execute(
            """UPDATE user_stories SET feature_id=?, title=?, description=?, acceptance_criteria=?, effort_estimate=?,
               status=?, tags=?, created_by=?, llm_confidence=?, updated_at=?
               WHERE id=?""",
            (
                str(story.feature_id),
                story.title,
                story.description,
                ac_json,
                story.effort_estimate,
                story.status,
                tags_json,
                story.created_by,
                story.llm_confidence,
                now,
                str(story.id),
            ),
        )
        return _row_to_user_story(
            conn.execute("SELECT * FROM user_stories WHERE id = ?", (str(story.id),)).fetchone()
        )

    @staticmethod
    def delete(conn: sqlite3.Connection, story_id: UUID) -> None:
        conn.execute("DELETE FROM user_stories WHERE id = ?", (str(story_id),))


# ---------------------------------------------------------------------------
# Database manager
# ---------------------------------------------------------------------------

class Database:
    """Manages the SQLite connection and runs migrations on init."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def init_db(self) -> None:
        """Create tables if they don't exist (run migrations)."""
        with get_connection(self.db_path) as conn:
            migrate(conn)

    @contextmanager
    def connection(self):
        """Yield a connection and handle commit/rollback."""
        with get_connection(self.db_path) as conn:
            yield conn

    # Convenience properties for quick access
    @property
    def epics(self) -> EpicRepository:
        return EpicRepository()

    @property
    def features(self) -> FeatureRepository:
        return FeatureRepository()

    @property
    def user_stories(self) -> UserStoryRepository:
        return UserStoryRepository()


# Singleton — call init_db() before first use (e.g. at app startup)
_database: Optional[Database] = None


def get_database(db_path: str = DB_PATH) -> Database:
    """Return the singleton Database instance."""
    global _database
    if _database is None:
        _database = Database(db_path)
    return _database
