# Operator Layout Primitives

Use these shared primitives first for page structure and layout consistency:

- `PageContainer`: top-level page rhythm/container
- `SectionCard`: section framing/card treatment
- `FormContainer`: consistent form width/spacing

Prefer shared utility classes from `app/globals.css` for common layout patterns:

- `row-wrap`, `row-wrap-tight`, `row-space-between`
- `metrics-grid`, `grid-fit-180`, `grid-fit-120`
- `table-container`, `table-container-compact`
- `panel-compact`, `stack-*` spacing classes

Avoid one-off layout wrappers and inline styling (`style={{ ... }}`) in `app/` and `components/`.
The regression guardrail test in `lib/validation/layout-guardrails.test.ts` enforces this and allows only explicitly documented exceptions.
