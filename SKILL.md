---
name: openai-text-to-image-storyboard
description: Generate storyboard images by using agent-decided prompts and calling an OpenAI-compatible image generation API. Use when users want chapters, novels, articles, or scripts converted into image sets under pictures/{content_name}, with API URL and API key loaded from .env or environment variables.
---

# OpenAI Text to Image Storyboard

## Overview

Let the agent decide which images are needed from the text, then call only `/images/generations` to render them.
Always save outputs in `pictures/<content_name>/` (example: `pictures/1_小說章節名稱/`).

## Workflow

1. Read user text and decide the target scenes in the agent.
2. Prepare image prompts (`--prompt` multiple times, or `--prompts-file` JSON).
3. Run the script to generate images through `/images/generations`.
4. Save files in narrative order and write `storyboard.json`.

## Environment Configuration

Create `.env` in the target project root (or pass `--env-file`):

- `OPENAI_API_URL` (required)
- `OPENAI_API_KEY` (required)
- `OPENAI_IMAGE_MODEL` (optional, default `gpt-image-1`)
- `OPENAI_IMAGE_RATIO` (optional, e.g. `16:9` / `4:3`; recommended)
- `OPENAI_IMAGE_ASPECT_RATIO` (optional fallback alias)
- `OPENAI_IMAGE_QUALITY` (optional)
- `OPENAI_IMAGE_STYLE` (optional)

A template is provided at:
- `/Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env.example`

## Command

Use direct prompts:

```bash
python /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/scripts/generate_storyboard_images.py \
  --project-dir /path/to/project \
  --content-name "1_小說章節名稱" \
  --aspect-ratio 16:9 \
  --prompt "Cinematic night market alley, rain reflections, protagonist with umbrella, neon bokeh" \
  --prompt "Old library at dawn, warm dust particles, heroine opening a hidden book compartment"
```

Use JSON prompt file:

```bash
python /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/scripts/generate_storyboard_images.py \
  --project-dir /path/to/project \
  --content-name "1_小說章節名稱" \
  --prompts-file /path/to/prompts.json
```

`prompts.json` format:

```json
[
  {
    "title": "雨夜追逐",
    "prompt": "cinematic rain-soaked alley, tense running pose, blue neon reflections, dramatic rim light"
  },
  {
    "title": "地下書庫",
    "prompt": "ancient underground library, floating dust in warm volumetric light, mysterious atmosphere"
  }
]
```

## Output Convention

Generated files:

- `pictures/1_小說章節名稱/01_雨夜追逐.png`
- `pictures/1_小說章節名稱/02_地下書庫.png`
- `pictures/1_小說章節名稱/storyboard.json`

If a filename already exists, the script appends `_2`, `_3`, etc. to avoid overwriting.
