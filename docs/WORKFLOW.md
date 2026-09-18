# Workflow — CBS PM Buddy

## The Decomposition Flow

This document describes the step-by-step workflow for using CBS PM Buddy to manage a product backlog from Epic to User Story.

---

## Step 1: Create an Epic

**Who:** Product Manager

The PM starts by creating an Epic — a strategic initiative from leadership or defined by the PM themselves.

### Actions

1. Click **+ New Epic** in the sidebar
2. Fill in the form:

| Field | Instructions |
|-------|-------------|
| **Title** | Short, clear name for the initiative (e.g., "Migrate Legacy Apps to Kubernetes") |
| **Description** | Business context and desired outcomes (e.g., "Move our 12 monolithic VM-based applications to containerized deployments on Kubernetes to improve reliability and reduce infrastructure costs by 40%") |
| **Priority** | Select P0 (critical) through P3 (nice-to-have) — this typically comes from leadership |
| **Tags** | Free-form categorization (e.g., "migration", "infrastructure", "cost-reduction") |

3. Click **Save**

The Epic appears in the sidebar list and its detail view opens in the main area.

### Example Epic

```
Title:        Migrate Legacy Apps to Kubernetes
Description:  Move our 12 monolithic VM-based applications to containerized
              deployments on Kubernetes to improve reliability and reduce
              infrastructure costs by 40%.
Priority:     P1
Tags:         [migration] [infrastructure] [cost-reduction]
Status:       Active
```

---

## Step 2: Decompose Epic → Features

**Who:** LLM suggests, PM reviews

The PM triggers the LLM to suggest Features — tangible capabilities that make up the Epic.

### Actions

1. With the Epic selected in the sidebar, click **🤖 Decompose** button
2. A loading indicator appears: *"LLM is generating Features..."*
3. The LLM responds with a list of suggested Features, each showing:
   - Title and description
   - Confidence score (green ≥80%, orange 50–79%, red <50%)
   - An "LLM Generated" label

### What the PM Sees

```
FEATURES

☑ Container Orchestration          🟢 92% confidence
   Move all application deployments to Kubernetes pods
   [Edit]  [🤖]  [✕]

☐ Network & Ingress Configuration  🟡 75% confidence
   Set up load balancers, ingress controllers, and DNS routing
   [Edit]  [🤖]  [✕]

☑ Monitoring & Observability       🟢 88% confidence
   Deploy Prometheus, Grafana dashboards, and alerting rules
   [Edit]  [🤖]  [✕]

☐ Data Migration Pipeline          🔴 45% confidence
   Migrate database schemas and data from VM-hosted databases
   to managed cloud databases
   [Edit]  [🤖]  [✕]
```

### PM Decisions Per Feature

For each suggested Feature, the PM can:

| Action | What it does |
|--------|-------------|
| **☑ Accept** | Mark as done — keeps the suggestion as-is |
| **☐ Reject** | Delete the suggestion entirely |
| **✏️ Edit** | Modify the title or description inline |
| **🤖 Regenerate** | Re-run LLM decomposition for this Feature only (useful if output was weak) |

### Best Practices

- **Review all suggestions before accepting.** The LLM may include irrelevant or overly vague items.
- **Low-confidence items deserve extra scrutiny.** A 45% confidence score means the LLM wasn't sure — verify the suggestion makes sense in your context.
- **Add manual Features if needed.** Click **+ Add Feature** to create items the LLM missed.

---

## Step 3: Decompose Feature → User Stories

**Who:** LLM suggests, PM reviews

For each Feature (accepted or manually created), the PM decomposes it into User Stories — implementable increments of work.

### Actions

1. Click on a Feature row to expand it
2. Click the **🤖** button on that Feature's row
3. The LLM generates suggested User Stories with acceptance criteria
4. Each story appears with:
   - Title in "As a... I want... so that..." format
   - Description with context
   - Acceptance criteria as checkable items
   - Confidence score

### What the PM Sees

```
── Container Orchestration ──────────────────────

USER STORIES

☑ As a DevOps Engineer, I want to containerize each application
  so that it can be deployed independently on Kubernetes
  AC: [✓] Dockerfile created for each app
  AC: [✓] Images pushed to registry
  AC: [✓] Helm charts defined
  Effort: M   🟢 90% confidence   [Edit] [🤖] [✕]

☐ As a Platform Team member, I want Kubernetes deployment manifests
  so that the team can deploy using standard tooling
  AC: [ ] Deployment YAML for each service
  AC: [ ] Service/Ingress resources defined
  Effort: L   🟢 85% confidence   [Edit] [🤖] [✕]

☐ As an SRE, I want health checks configured on all pods
  so that Kubernetes can detect and restart failed instances
  AC: [ ] Liveness probes defined
  AC: [ ] Readiness probes defined
  Effort: S   🟡 65% confidence   [Edit] [🤖] [✕]
```

### PM Decisions Per User Story

| Action | What it does |
|--------|-------------|
| **☑ Accept** | Mark as done — ready for sprint planning |
| **☐ Reject** | Delete the story |
| **✏️ Edit** | Modify title, description, or acceptance criteria inline |
| **🤖 Regenerate AC** | Re-generate just the acceptance criteria for this story |
| **Set Effort** | Assign XS / S / M / L / XL estimate |

### Best Practices

- **Acceptance criteria should be testable.** The LLM often produces good first drafts — refine them to be concrete and verifiable.
- **Split large stories.** If a story has an XL estimate or more than 5 acceptance criteria, break it into smaller stories manually.
- **Cross-reference stories.** Note dependencies between stories in the description field (e.g., "Depends on: Network & Ingress Feature").

---

## Step 4: Finalize and Plan

**Who:** Product Manager

After decomposition is complete, the PM finalizes the backlog for sprint planning.

### Actions

1. **Set effort estimates** on all User Stories (XS through XL)
2. **Group stories into sprints** — decide which stories go into Sprint 1, Sprint 2, etc.
3. **Reorder** — drag stories within a Feature to reflect priority
4. **Archive completed Epics** — move Epics from Active → Done when all Features are complete

### Summary View

Click **📊 Summary** in the sidebar to see:

| Metric | Description |
|--------|-------------|
| Total Epics | Count by status (Backlog / Active / Done) |
| Total Features | Count per Epic |
| Total Stories | Count per Feature, with effort breakdown |
| LLM vs Manual | Percentage of items generated by LLM vs created manually |
| Low Confidence Items | Stories/Features below 50% confidence that need review |

---

## Complete Example Walkthrough

### Scenario: SOC2 Compliance Initiative

**Step 1 — Create Epic:**

```
Title:        Achieve SOC2 Type II Compliance
Description:  Implement security controls and audit logging required
              for SOC2 certification. Target completion by Q2.
Priority:     P0
Tags:         [compliance] [security] [audit]
```

**Step 2 — Decompose to Features (LLM suggests):**

| Feature | Confidence | PM Decision |
|---------|-----------|-------------|
| Access Control & RBAC | 95% | ✅ Accept |
| Audit Logging System | 88% | ✅ Accept |
| Data Encryption at Rest | 72% | ✅ Accept, edit description |
| Vulnerability Scanning | 60% | ✅ Accept |
| Incident Response Procedures | 45% | ❌ Reject (too vague) |
| Vendor Risk Assessment | — | ➕ Add manually |

**Step 3 — Decompose "Access Control & RBAC" to Stories:**

```
☑ As a System Admin, I want role-based access controls
  so that users only have permissions for their job function
  AC: [✓] Define roles: Viewer, Editor, Admin, SuperAdmin
  AC: [✓] Implement permission checks on all API endpoints
  Effort: L   🟢 92%

☐ As a Developer, I want to create custom role definitions
  so that teams can tailor permissions to their needs
  AC: [ ] Custom role creation UI
  AC: [ ] Permission matrix validation
  Effort: M   🟢 85%

☐ As an Auditor, I want to export access logs
  so that I can verify compliance during SOC2 review
  AC: [ ] Export in CSV and PDF formats
  AC: [ ] Filter by date range and user
  Effort: S   🟡 70%
```

**Step 4 — Finalize:**

- Set effort estimates on all stories
- Assign Sprint 1: "Implement permission checks" (L), "Define roles" (S)
- Assign Sprint 2: "Custom role definitions" (M), "Export access logs" (S)
- Move Epic status to Active

---

## Error Recovery

### LLM Unavailable

If the LLM is down or not configured:

1. The **🤖 Decompose** button is disabled with a tooltip
2. The PM creates Features and Stories manually using **+ Add Feature** / **+ Add Story**
3. When the LLM becomes available again, the PM can go back and use it to fill gaps

### Poor LLM Output

If suggestions are low quality:

1. Check the **LLM Status** indicator — is the right model selected?
2. Try a different model in Settings (e.g., switch from `phi3:mini` to `llama3.1:8b`)
3. Add more context to the Epic description before regenerating
4. Increase temperature slightly (0.7 → 0.8) for more creative suggestions

### Data Loss Prevention

- The SQLite database is written atomically — partial writes won't corrupt data
- There is no "undo" button in v1, so PMs should save frequently by clicking away from edits (auto-save on blur)
- Consider adding periodic backups to a user-specified location in a future version
