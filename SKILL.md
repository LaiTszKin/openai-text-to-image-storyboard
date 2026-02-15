---
name: openai-text-to-image-storyboard
description: Generate storyboard images by using agent-decided prompts and calling an OpenAI-compatible image generation API. Use when users want chapters, novels, articles, or scripts converted into image sets under pictures/{content_name}, with API URL and API key loaded from this skill folder's .env by default.
---

# OpenAI Text to Image Storyboard

## Overview

Let the agent decide which images are needed from the text, then call only `/images/generations` to render them.
Always save outputs in `pictures/<content_name>/` (example: `pictures/1_小說章節名稱/`).

## Workflow

1. Read user text and decide the target scenes in the agent.
2. If characters repeat across scenes (typical in novels), define recurring characters once with JSON skeletons before generation.
3. As soon as article/chapter content is available, directly prepare prompts and run the script (do not stop at suggestion-only mode).
4. Use this skill folder's `.env` first, then call `/images/generations` to render images.
5. Save files in narrative order and write `storyboard.json`.

## Agent Execution Requirement

- After receiving article/chapter/script content, immediately enter generation flow.
- Convert content into scene prompts and execute the Python script in the same turn whenever possible.
- Only ask follow-up questions when mandatory inputs are missing (for example: no output project path or no content name).
- For recurring characters, always send the same character JSON skeleton (`id/name/appearance/outfit/description`) in every relevant scene prompt and only update `description`.
- For multi-character scenes, include all involved character skeletons in the same `characters` array and update each character's `description` independently.

## Environment Configuration

Create `.env` in this skill folder (default path used by script):

- `/Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env`

You can still override via `--env-file` when needed.
All CLI parameters take priority over environment variables.

- `OPENAI_API_URL` (required)
- `OPENAI_API_KEY` (required)
- `OPENAI_IMAGE_MODEL` (optional, default `gpt-image-1`)
- `OPENAI_IMAGE_RATIO` (optional, e.g. `16:9` / `4:3`; recommended)
- `OPENAI_IMAGE_ASPECT_RATIO` (optional fallback alias)
- `OPENAI_IMAGE_SIZE` (optional, e.g. `1024x768`, for providers that expect `size`)
- `OPENAI_IMAGE_QUALITY` (optional)
- `OPENAI_IMAGE_STYLE` (optional)

A template is provided at:
- `/Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env.example`

## Command

Use direct prompts:

```bash
python /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/scripts/generate_storyboard_images.py \
  --project-dir /path/to/project \
  --env-file /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env \
  --content-name "1_小說章節名稱" \
  --prompt "Cinematic night market alley, rain reflections, protagonist with umbrella, neon bokeh" \
  --prompt "Old library at dawn, warm dust particles, heroine opening a hidden book compartment"
```

If the provider ignores `aspect_ratio`, pass `--image-size 1024x768` or set `OPENAI_IMAGE_SIZE=1024x768`.
You can also pass `--api-url` and `--api-key` to override `OPENAI_API_URL` and `OPENAI_API_KEY`.
When an aspect ratio is set, the script also applies center-crop post-processing so output files still match the target ratio.

Use JSON prompt file:

```bash
python /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/scripts/generate_storyboard_images.py \
  --project-dir /path/to/project \
  --env-file /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env \
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

Structured `prompts.json` format for recurring characters (recommended for novels):

```json
{
  "characters": [
    {
      "id": "lin_xia",
      "name": "Lin Xia",
      "appearance": "short black hair, amber eyes, slim build",
      "outfit": "dark trench coat, silver pendant, leather boots",
      "description": "standing calmly, observant expression"
    },
    {
      "id": "chen_yu",
      "name": "Chen Yu",
      "appearance": "wavy brown hair, tall, sharp jawline",
      "outfit": "navy suit with loosened tie, long overcoat",
      "description": "alert posture, slightly tense"
    }
  ],
  "scenes": [
    {
      "title": "Rain Alley Encounter",
      "description": "night alley with neon reflections and light rain",
      "character_ids": ["lin_xia", "chen_yu"],
      "character_descriptions": {
        "lin_xia": "holding a black umbrella, wary gaze",
        "chen_yu": "half-turned to check behind him, breathing fast"
      },
      "camera": "medium shot, slight low angle",
      "lighting": "blue-magenta neon rim light"
    },
    {
      "title": "Library Clue",
      "description": "dusty old library at dawn, warm shafts of light",
      "character_ids": ["lin_xia"],
      "character_descriptions": {
        "lin_xia": "opening a hidden compartment in a bookcase"
      }
    }
  ]
}
```

Notes for structured mode:

- Top-level `characters` defines reusable character skeletons.
- Each scene lists `character_ids`; the script injects the same skeleton every time and only overrides `description` via `character_descriptions`.
- `camera`, `lighting`, and `style` are optional scene keys.
- This format supports multiple recurring characters and keeps cross-scene visual consistency.

## Output Convention

Generated files:

- `pictures/1_小說章節名稱/01_雨夜追逐.png`
- `pictures/1_小說章節名稱/02_地下書庫.png`
- `pictures/1_小說章節名稱/storyboard.json`

If a filename already exists, the script appends `_2`, `_3`, etc. to avoid overwriting.
