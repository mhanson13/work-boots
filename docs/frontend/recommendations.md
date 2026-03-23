# Recommendations UX

## AI Recommendations UX Layer

The site workspace surfaces recommendation data with a strict separation of concerns:

- **Deterministic recommendations** remain authoritative and are rendered in the existing deterministic recommendations table.
- **AI opportunities** are an advisory overlay rendered from existing workspace summary payload fields only.

The `AI Opportunities` section is shown only when AI-backed signals exist in the current payload, using:

- recommendation `source === "ai"` when present in payload data, or
- AI narrative/tuning fields already returned in the workspace summary (`latest_narrative`, `tuning_suggestions`).

The UI does not generate new AI text client-side and does not mutate backend workflows.

### Card Behavior

Each AI opportunity card shows:

- title
- `AI Suggested` badge
- `Why this matters` (existing narrative/suggestion text)
- `Expected outcome` derived from deterministic recommendation fields

Cards use progressive disclosure:

- collapsed: short narrative snippet + one-line expected outcome
- expanded: full narrative context + supporting signals when present

### Authority Boundary

- AI suggestions are advisory and must be reviewed.
- Deterministic recommendation artifacts remain canonical.
- No auto-apply behavior is introduced in this layer.
