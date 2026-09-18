# UI Design — CBS PM Buddy

## Framework

**Streamlit** — runs locally in the browser, data-display focused, fast to build. The PM opens a terminal, runs `streamlit run app.py`, and gets a full desktop-like experience at `http://localhost:8501`.

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CBS PM Buddy                                        [⚙️] [📤] │
├──────────────────────┬──────────────────────────────────────────┤
│  Sidebar (280px)     │  Main Content Area                       │
│                      │                                          │
│  ── Epics ──         │  ┌───────────────────────────────────┐   │
│  🔍 Search...        │  │                                   │   │
│                      │  │  Epic Detail View                 │   │
│  📋 Active           │  │                                   │   │
│  ├─ 🟡 Migrate to K8s│  │  Title: Migrate Legacy Apps       │   │
│  ├─ 🔵 SOC2 Comp     │  │         to Kubernetes             │   │
│  └─ 🟢 Observability │  │                                   │   │
│                      │  │  Desc: Move monolith from VMs...  │   │
│  + New Epic          │  │                                   │   │
│                      │  │  Priority: P1    Status: Active   │   │
│  ── Actions ──       │  │  Tags: [migration] [infra]        │   │
│  🤖 Decompose All    │  │                                   │   │
│  📊 Summary          │  │  ──────────────────────────────   │   │
│                      │  │                                   │   │
│  ── LLM Status ──    │  │  FEATURES                          │   │
│  🟢 Ollama ready     │  │                                   │   │
│  Model: llama3.1:8b  │  │  ☑ Container Orchestration        │   │
│                      │  │     "Move app deployments..."      │   │
│                      │  │     [Edit] [🤖] [✕]               │   │
│  ── Stats ──         │  │                                   │   │
│  3 Epics · 7 Feat    │  │  ☐ Network & Ingress              │   │
│  12 Stories          │  │     "Configure load balancers..."  │   │
│                      │  │     [Edit] [🤖] [✕]               │   │
│                      │  │                                   │   │
│                      │  │  [+ Add Feature]                   │   │
│                      │  │                                   │   │
│                      │  │  ──────────────────────────────   │   │
│                      │  │                                   │   │
│                      │  │  USER STORIES (under selected)     │   │
│                      │  │                                   │   │
│                      │  │  ☑ As a DevOps eng, I want...     │   │
│                      │  │     AC: [✓] Pods start in <30s    │   │
│                      │  │     AC: [✓] Health check passes   │   │
│                      │  │     [S] [Edit] [🤖] [✕]          │   │
│                      │  │                                   │   │
│                      │  │  ☐ As a Platform owner, I want... │   │
│                      │  │     AC: [ ] Rollback in <5min     │   │
│                      │  │     [M] [Edit] [🤖] [✕]          │   │
│                      │  │                                   │   │
│                      │  │  [+ Add Story]                     │   │
│                      │  └───────────────────────────────────┘   │
├──────────────────────┴──────────────────────────────────────────┤
│  Status: Ready | LLM: Ollama (llama3.1:8b) | 3 Epics · 7 Feat  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Page Sections

### Sidebar

| Section | Contents |
|---------|----------|
| **Search** | Text input to filter Epics by title or tags |
| **Epics list** | Scrollable list of all Epics with status indicators (🟡 Active, 🔵 Backlog, 🟢 Done) |
| **+ New Epic** | Opens a form: title, description, priority, tags |
| **Actions** | "Decompose All" — runs LLM decomposition on the selected Epic |
| **LLM Status** | Shows which backend is connected, model name, and whether it's reachable |
| **Stats** | Running count of Epics, Features, and User Stories |

### Main Area — Three Views

The main area switches between three views depending on user interaction:

#### 1. Epic Detail View (default)
Shows the selected Epic's metadata at the top, then its child Features below.

#### 2. Feature Detail View
When a Feature is expanded or clicked, shows its child User Stories in detail with acceptance criteria.

#### 3. Summary Dashboard
Aggregate view: Epics by status, total stories per sprint, LLM-generated vs manually created ratio.

---

## Component Design

### Epic Card (Sidebar)

```python
st.markdown(f"""
<div class="epic-card {'active' if epic.status == 'Active' else ''}">
  <span class="status-dot" style="color: {color_map[epic.status]}">●</span>
  <span class="epic-title">{epic.title}</span>
  <span class="epic-meta">{len(epics.features)}F · {len(epics.stories)}S</span>
</div>
""", unsafe_allow_html=True)
```

### Feature Row (Main Area)

Each Feature is a row with inline actions:

| Element | Description |
|---------|-------------|
| ☑ / ☐ | Checkbox to mark as done / back in backlog |
| Title + description | Clickable, expands to show full details |
| [Edit] | Opens inline edit mode (title, description fields) |
| [🤖] | Re-run LLM decomposition for this Feature's Stories |
| [✕] | Delete the Feature (with confirmation) |

### User Story Row (Main Area)

Each User Story is a row with more detail:

| Element | Description |
|---------|-------------|
| ☑ / ☐ | Checkbox to mark as done |
| Title | Standard "As a... I want... so that..." format |
| AC badges | Each acceptance criterion shown as a small tag; click to toggle complete |
| [S] / [M] / etc. | Effort estimate badge |
| [Edit] | Opens inline edit (title, description, AC, effort) |
| [🤖] | Re-run LLM suggestion for this story's AC only |
| [✕] | Delete the story |

### Confidence Indicator

When an item was generated by the LLM, show a small confidence badge:

```python
if item.llm_confidence is not None:
    color = "green" if item.llm_confidence >= 0.8 else "orange" if item.llm_confidence >= 0.5 else "red"
    st.caption(f"🤖 Generated · confidence: {item.llm_confidence:.0%}")
```

---

## Interaction States

### Creating an Epic

1. Click **+ New Epic** in sidebar
2. Form appears with fields: Title (required), Description, Priority (dropdown P0–P3), Tags (free text)
3. Click **Save** → Epic appears in the list and main area switches to it

### Decomposing an Epic

1. Select an Epic from the sidebar
2. Click **🤖 Decompose** button
3. A loading spinner shows with streaming output: "LLM is generating Features..."
4. Generated Features appear below the Epic metadata, each with a green confidence badge
5. PM can accept (checkbox), edit inline, or reject (✕) any Feature

### Decomposing a Feature

1. Click the Feature row to expand it
2. Click **🤖** button on the Feature row
3. Generated User Stories appear under the Feature with acceptance criteria
4. Same accept/edit/reject cycle

### Manual Creation

- **+ Add Feature** button at the bottom of the Features section
- **+ Add Story** button at the bottom of the Stories section (visible when a Feature is expanded)
- Opens a simple inline form: title + description for Feature; title + description + acceptance criteria for Story

---

## Settings Panel

Accessed via the ⚙️ gear icon in the top-right corner.

### LLM Configuration Tab

| Field | Control | Default |
|-------|---------|---------|
| Backend | Dropdown: Ollama / LM Studio / Custom | Ollama |
| Base URL | Text input | `http://localhost:11434` (Ollama) / `http://localhost:1234/v1` (LM Studio) |
| Model | Text input | `llama3.1:8b` |
| Temperature | Slider 0.0–1.0 | 0.7 |
| Max Tokens | Number input | 4096 |
| Timeout | Number input (seconds) | 120 |
| **Test Connection** | Button | — |

### Preferences Tab

| Field | Control | Default |
|-------|---------|---------|
| PM Name | Text input | "Anonymous" |
| Default Priority | Dropdown P0–P3 | P2 |
| Default Effort | Dropdown XS–XL | M |

---

## Export Button

Accessed via the 📤 icon in the top-right. Currently a simple dropdown:

- **Export as JSON** — downloads full database dump
- **Export Epics as CSV** — exports Epic titles, priorities, and counts (future)
- **Copy to Clipboard** — copies selected Epic's content as Markdown (future)

---

## Streamlit Page Config

```python
import streamlit as st

st.set_page_config(
    page_title="CBS PM Buddy",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

---

## Styling (Minimal Custom CSS)

Streamlit's default styling is sufficient for v1. Minimal custom CSS for visual polish:

```css
/* Sidebar epic cards */
.st-emotion-cache-1v0mbdj {
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 4px;
}

/* Confidence badges */
.confidence-high { color: #2ecc71; }
.confidence-medium { color: #f39c12; }
.confidence-low { color: #e74c3c; }
```

---

## Responsive Considerations

- Sidebar collapses on narrow viewports (Streamlit handles this)
- Feature and Story rows stack vertically on small screens
- No horizontal scrolling needed — content fits within the main area width
