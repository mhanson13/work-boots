# Prompt System

## Single Source of Truth

Workspace prompt preview rendering must use only the resolved prompt payload returned by the API preview object:

- `competitor_prompt_preview.system_prompt`
- `competitor_prompt_preview.user_prompt`
- `recommendation_prompt_preview.system_prompt`
- `recommendation_prompt_preview.user_prompt`

Rules:

- Do not merge preview prompt text with historical run prompt fields.
- Do not append stored/raw/admin prompt fields in the UI render path.
- Treat preview metadata (`prompt_version`, `prompt_label`, `source`, `truncated`) as metadata only.
- Prompt body content shown in UI must be exactly the API preview prompt body.

## Version Consistency

- `prompt_version` shown in preview metadata must match the effective rendered prompt marker when available.
- Historical run metadata is not the source of truth for preview prompt version display.
