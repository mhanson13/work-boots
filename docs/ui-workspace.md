# UI Workspace

## Prompt Preview vs Last Run

Prompt preview and run history are different concepts:

- Prompt preview: current assembled prompt payload returned by workspace summary preview fields.
- Last run: historical execution metadata from previously completed/failed runs.

Rules:

- Workspace prompt panel must render only preview payload prompt text.
- Last-run metadata must never be concatenated into preview prompt text.
- If preview is unavailable, hide the preview panel rather than falling back to run prompt content.

## No Merging Rule

- Do not combine `latest_run` data with `*_prompt_preview.user_prompt` or `*_prompt_preview.system_prompt`.
- Do not preserve prior prompt body text across site changes or refreshes when new preview payload is received.
