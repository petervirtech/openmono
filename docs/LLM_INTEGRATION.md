# LLM Integration — CBS PM Buddy

## Overview

The LLM is used exclusively for **decomposition suggestions**. It takes a parent item (Epic or Feature) and generates suggested child items (Features or User Stories). The PM reviews, edits, accepts, or rejects each suggestion.

---

## Supported Backends

| Backend | Connection Method | Auto-Detect | Notes |
|---------|------------------|-------------|-------|
| **Ollama** | `http://localhost:11434` | ✅ Default | Most common local LLM runner |
| **LM Studio** | `http://localhost:1234/v1` | ✅ Common | OpenAI-compatible API |
| **Any OpenAI-compatible** | Custom URL + key | Manual config | Flexibility for other endpoints |

---

## Configuration

Stored in `~/.config/cbs-pm-buddy/llm.json`:

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

### Field Descriptions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend` | str | `"ollama"` | Which adapter to use |
| `base_url` | str | varies per backend | API endpoint URL |
| `model` | str | `"llama3.1:8b"` | Model name/identifier |
| `temperature` | float | 0.7 | Creativity (0 = deterministic, 1 = creative) |
| `max_tokens` | int | 4096 | Max output tokens per request |
| `timeout_seconds` | int | 120 | Request timeout |

---

## Recommended Models

| Use Case | Model | Min VRAM | Speed | Quality |
|----------|-------|----------|-------|---------|
| Decomposition (primary) | `llama3.1:8b` | 8GB | Fast | Good |
| Decomposition (alt) | `mistral:7b` | 8GB | Fast | Good |
| Complex epics | `llama3.1:70b` | 40GB+ | Slow | Excellent |
| Complex epics (alt) | `qwen2.5:32b` | 20GB | Medium | Very Good |
| Lightweight fallback | `phi3:mini` | 4GB | Fast | Adequate |

---

## Adapter Interface

All adapters implement a common abstract interface:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMResponse:
    """Standardized response from any LLM adapter."""
    items: list[dict]          # Generated child items
    confidence: float          # Overall confidence 0.0–1.0
    raw_response: str          # Raw text for debugging

class LLMAdapter(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    async def decompose_features(self, epic_title: str, epic_description: str, priority: str) -> LLMResponse:
        """Generate suggested Features from an Epic."""
        ...

    @abstractmethod
    async def decompose_stories(self, feature_title: str, feature_description: str) -> LLMResponse:
        """Generate suggested User Stories from a Feature."""
        ...
```

---

## Ollama Adapter

### Connection Details

- **Base URL:** `http://localhost:11434`
- **API endpoint:** `/api/generate` (legacy) or `/api/chat` (chat format)
- **Model format:** Named by tag, e.g., `llama3.1:8b`

### Implementation Notes

```python
import httpx

class OllamaAdapter(LLMAdapter):
    def __init__(self, config: dict):
        self.base_url = config["base_url"]  # default: http://localhost:11434
        self.model = config["model"]
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout_seconds", 120)

    async def decompose_features(self, epic_title: str, epic_description: str, priority: str) -> LLMResponse:
        prompt = build_feature_decomposition_prompt(epic_title, epic_description, priority)
        response = await self._send_request(prompt)
        return parse_json_response(response)
```

### Ollama API Call Format (Chat)

```json
{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 4096
  }
}
```

---

## LM Studio Adapter

### Connection Details

- **Base URL:** `http://localhost:1234/v1` (default)
- **API format:** OpenAI-compatible chat completions
- **Model format:** Full model identifier, e.g., `TheBloke/Llama-2-7B-Chat-GGUF`

### Implementation Notes

```python
import httpx

class LMStudioAdapter(LLMAdapter):
    def __init__(self, config: dict):
        self.base_url = config["base_url"]  # default: http://localhost:1234/v1
        self.model = config["model"]
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout_seconds", 120)

    async def decompose_features(self, epic_title: str, epic_description: str, priority: str) -> LLMResponse:
        messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(epic_title, epic_description, priority)}
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload)
            resp.raise_for_status()
            return parse_openai_response(resp.json())
```

---

## Prompt Templates

### System Prompt (shared across all adapters)

```
You are an expert Infrastructure Product Manager's assistant.
Your job is to decompose parent items into actionable child items.

Rules:
- Output ONLY valid JSON, no markdown wrapping, no explanations.
- Each item must have a "title", "description", and "confidence" (0.0–1.0).
- For User Stories, include "acceptance_criteria" as an array of strings.
- Keep titles concise (under 80 characters).
- Be specific to infrastructure context unless told otherwise.
```

### Decompose to Features Prompt

```
Decompose the following Epic into actionable Features.

Epic Title: {title}
Description: {description}
Priority: {priority}

Output format:
[
  {
    "title": "...",
    "description": "...",
    "confidence": 0.95
  },
  ...
]
```

### Decompose to User Stories Prompt

```
Decompose the following Feature into actionable User Stories.

Feature Title: {title}
Description: {description}

Output format:
[
  {
    "title": "As a [role], I want [goal] so that [reason]",
    "description": "...",
    "acceptance_criteria": ["Given X, When Y, Then Z"],
    "confidence": 0.87
  },
  ...
]
```

---

## Error Handling

### No LLM Available

When the configured backend is unreachable:
1. The "Decompose" button is **disabled** (grayed out)
2. A tooltip explains: "LLM not available. Configure Ollama or LM Studio in Settings."
3. The PM can still manually create Features and User Stories

### LLM Timeout / Error

```python
async def decompose_with_retry(self, ...):
    for attempt in range(2):  # 1 retry max
        try:
            return await self.decompose_features(...)
        except httpx.TimeoutException:
            if attempt == 0:
                continue  # retry once
            raise LLMTimeoutError("Request timed out. Try a smaller model or larger timeout.")
        except httpx.HTTPStatusError as e:
            raise LLMAPIError(f"LLM returned error {e.response.status_code}: {e.response.text}")
```

### Partial Results

If the LLM returns malformed JSON, attempt to extract JSON from the response using regex fallback. If that fails, show the raw output in a collapsible section and let the PM copy-paste or retry.

---

## Auto-Detection Logic

On app startup, check for common backends:

```python
async def detect_available_backends() -> dict[str, bool]:
    results = {}

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            results["ollama"] = resp.status_code == 200
    except Exception:
        results["ollama"] = False

    # Check LM Studio
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://localhost:1234/v1/models")
            results["lmstudio"] = resp.status_code == 200
    except Exception:
        results["lmstudio"] = False

    return results
```

The sidebar shows a status indicator:
- 🟢 **Ollama ready** (if detected)
- 🔴 **No LLM detected** — configure in Settings
- 🟡 **Configured but unreachable**

---

## Usage in the Application

```python
# In the orchestrator layer
class DecompositionOrchestrator:
    def __init__(self, llm_adapter: LLMAdapter, db_repo: DatabaseRepository):
        self.llm = llm_adapter
        self.db = db_repo

    async def decompose_epic(self, epic_id: uuid.UUID) -> list[Feature]:
        epic = self.db.get_epic(epic_id)
        response = await self.llm.decompose_features(
            epic.title,
            epic.description,
            epic.priority.value,
        )
        features = []
        for item in response.items:
            feature = Feature(
                epic_id=epic_id,
                title=item["title"],
                description=item["description"],
                created_by="LLM",
                llm_confidence=item.get("confidence"),
            )
            self.db.save_feature(feature)
            features.append(feature)
        return features

    async def decompose_feature(self, feature_id: uuid.UUID) -> list[UserStory]:
        feature = self.db.get_feature(feature_id)
        response = await self.llm.decompose_stories(
            feature.title,
            feature.description,
        )
        stories = []
        for item in response.items:
            story = UserStory(
                feature_id=feature_id,
                title=item["title"],
                description=item.get("description"),
                acceptance_criteria=item.get("acceptance_criteria", []),
                created_by="LLM",
                llm_confidence=item.get("confidence"),
            )
            self.db.save_user_story(story)
            stories.append(story)
        return stories
```
