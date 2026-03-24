# Recommendations

## Optional Competitor Signal Integration

Recommendation narrative generation can consume an optional, bounded competitor context signal. This is additive and does not change deterministic recommendation artifacts or provider/model architecture.

### Competitor Fields Used
Only normalized competitor output is consumed:
- `top_opportunities` (deduped, bounded list)
- `summary` (bounded string)
- competitor `name` values (deduped, bounded list)

### Integration Rules
- Competitor signal is optional.
- If competitor data is missing or empty, recommendation generation continues with existing behavior.
- If competitor payload is malformed, no exception is raised and no competitor signal is injected.
- Normalizer fallback payloads are treated as no-signal for recommendations.

### Prompt/Context Behavior
- Competitor context is injected as a small, structured context block.
- The model is instructed to use provided competitor gaps to improve specificity.
- The model is also instructed not to invent competitor facts beyond provided context.

### Reliability Boundaries
- No new persistence is introduced.
- No new endpoint is introduced.
- No competitor parsing failure can block recommendation generation.
- Recommendations consume normalized competitor output only, never raw malformed AI text.
