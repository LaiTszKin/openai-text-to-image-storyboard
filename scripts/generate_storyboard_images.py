#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib import error, request

INVALID_PATH_CHARS = re.compile(r"[\\/:*?\"<>|]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate storyboard images from agent-decided prompts via an OpenAI-compatible image API.",
    )
    parser.add_argument("--content-name", required=True, help="Output subfolder name under pictures/")
    parser.add_argument("--project-dir", default=".", help="Project root path (default: current directory)")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Environment file path (default: .env under project dir)",
    )

    prompt_source = parser.add_mutually_exclusive_group(required=True)
    prompt_source.add_argument(
        "--prompts-file",
        help="Path to a JSON file containing prompt entries",
    )
    prompt_source.add_argument(
        "--prompt",
        action="append",
        help="Image prompt text; pass multiple times to generate multiple images",
    )

    parser.add_argument(
        "--image-model",
        help="Image model for /images/generations (or OPENAI_IMAGE_MODEL, default: gpt-image-1)",
    )
    parser.add_argument(
        "--aspect-ratio",
        help=(
            "Image aspect ratio, e.g. 16:9 or 4:3 "
            "(or OPENAI_IMAGE_RATIO / OPENAI_IMAGE_ASPECT_RATIO). "
            "If omitted, use model/API default size."
        ),
    )
    parser.add_argument(
        "--quality",
        help="Optional image quality parameter (or OPENAI_IMAGE_QUALITY)",
    )
    parser.add_argument(
        "--style",
        help="Optional image style parameter (or OPENAI_IMAGE_STYLE)",
    )
    return parser.parse_args()


def required_env(name: str, env_file: Path | None = None) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        location_hint = f" and {env_file}" if env_file else ""
        raise SystemExit(f"Missing required configuration: {name}. Set it in environment{location_hint}.")
    return value


def sanitize_component(name: str, fallback: str) -> str:
    cleaned = INVALID_PATH_CHARS.sub("_", name.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or fallback


def normalize_aspect_ratio(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if not re.fullmatch(r"\d{1,3}:\d{1,3}", candidate):
        raise SystemExit("Invalid aspect ratio. Use format like 16:9 or 4:3.")
    return candidate


def first_nonempty_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value
    return None


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def parse_dotenv_line(content: str, line_no: int, file_path: Path) -> tuple[str, str] | None:
    stripped = content.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[7:].strip()

    if "=" not in stripped:
        raise SystemExit(f"Invalid .env format at {file_path}:{line_no}: missing =")

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        raise SystemExit(f"Invalid .env key at {file_path}:{line_no}: {key}")

    if value and value[0] in {"'", '"'}:
        quote = value[0]
        if len(value) >= 2 and value[-1] == quote:
            value = value[1:-1]
    else:
        value = value.split(" #", 1)[0].strip()

    return key, value


def load_dotenv_file(env_file: Path, override: bool = False) -> bool:
    if not env_file.exists():
        return False

    for line_no, line in enumerate(env_file.read_text(encoding="utf-8").splitlines(), start=1):
        parsed = parse_dotenv_line(line, line_no, env_file)
        if not parsed:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value
    return True


def normalize_base_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise SystemExit("OPENAI_API_URL cannot be empty.")
    return base


def post_json(base_url: str, endpoint: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{normalize_base_url(base_url)}{endpoint}"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} when calling {url}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error when calling {url}: {exc.reason}") from exc


def fetch_binary(url: str) -> bytes:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=180) as response:
        return response.read()


def parse_prompts_file(prompts_file: Path) -> list[dict[str, str]]:
    raw = prompts_file.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {prompts_file}: {exc}") from exc

    if not isinstance(parsed, list):
        raise SystemExit(f"Invalid prompt file {prompts_file}: top-level JSON must be an array")

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(parsed, start=1):
        if isinstance(item, str):
            prompt = item.strip()
            title = f"scene-{index}"
        elif isinstance(item, dict):
            prompt = str(item.get("prompt", "")).strip()
            title = str(item.get("title") or f"scene-{index}").strip() or f"scene-{index}"
        else:
            raise SystemExit(
                f"Invalid item type in {prompts_file} at index {index}: expected string or object"
            )

        if not prompt:
            raise SystemExit(f"Empty prompt in {prompts_file} at index {index}")

        normalized.append({"title": title, "prompt": prompt})

    if not normalized:
        raise SystemExit(f"No prompts found in {prompts_file}")

    return normalized


def build_prompt_items(prompts_file: str | None, prompt_values: list[str] | None) -> list[dict[str, str]]:
    if prompts_file:
        return parse_prompts_file(Path(prompts_file).expanduser())

    if not prompt_values:
        raise SystemExit("At least one --prompt is required when --prompts-file is not set")

    items: list[dict[str, str]] = []
    for index, prompt in enumerate(prompt_values, start=1):
        text = prompt.strip()
        if not text:
            raise SystemExit(f"Empty --prompt at position {index}")
        items.append({"title": f"scene-{index}", "prompt": text})
    return items


def generate_image(
    base_url: str,
    api_key: str,
    image_model: str,
    prompt: str,
    aspect_ratio: str | None,
    quality: str | None,
    style: str | None,
) -> tuple[bytes, str | None]:
    payload: dict[str, Any] = {
        "model": image_model,
        "prompt": prompt,
    }
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if quality:
        payload["quality"] = quality
    if style:
        payload["style"] = style

    response = post_json(base_url, "/images/generations", api_key, payload)
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise RuntimeError("Image generation response has no data.")

    first = data[0]
    if not isinstance(first, dict):
        raise RuntimeError("Unexpected image data format.")

    revised_prompt = first.get("revised_prompt")
    if isinstance(first.get("b64_json"), str):
        raw = base64.b64decode(first["b64_json"])
        return raw, revised_prompt if isinstance(revised_prompt, str) else None

    if isinstance(first.get("url"), str):
        raw = fetch_binary(first["url"])
        return raw, revised_prompt if isinstance(revised_prompt, str) else None

    raise RuntimeError("Image payload missing b64_json/url.")


def main() -> int:
    args = parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    env_file = Path(args.env_file).expanduser()
    if not env_file.is_absolute():
        env_file = project_dir / env_file
    load_dotenv_file(env_file, override=False)

    api_url = required_env("OPENAI_API_URL", env_file)
    api_key = required_env("OPENAI_API_KEY", env_file)

    image_model = args.image_model or os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    aspect_ratio = normalize_aspect_ratio(
        args.aspect_ratio
        if args.aspect_ratio is not None
        else first_nonempty_env("OPENAI_IMAGE_RATIO", "OPENAI_IMAGE_ASPECT_RATIO")
    )
    quality = args.quality if args.quality is not None else os.getenv("OPENAI_IMAGE_QUALITY")
    style = args.style if args.style is not None else os.getenv("OPENAI_IMAGE_STYLE")

    prompts = build_prompt_items(args.prompts_file, args.prompt)

    content_dir_name = sanitize_component(args.content_name, "untitled-content")
    output_dir = project_dir / "pictures" / content_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for index, item in enumerate(prompts, start=1):
        title_slug = sanitize_component(item["title"], f"scene-{index}")
        filename = f"{index:02d}_{title_slug}.png"
        image_path = unique_path(output_dir / filename)

        image_bytes, revised_prompt = generate_image(
            base_url=api_url,
            api_key=api_key,
            image_model=image_model,
            prompt=item["prompt"],
            aspect_ratio=aspect_ratio,
            quality=quality,
            style=style,
        )
        image_path.write_bytes(image_bytes)

        record: dict[str, Any] = {
            "index": index,
            "title": item["title"],
            "prompt": item["prompt"],
            "file": str(image_path),
        }
        if revised_prompt:
            record["revised_prompt"] = revised_prompt
        records.append(record)
        print(f"[OK] Generated {image_path}")

    summary = {
        "content_name": args.content_name,
        "project_dir": str(project_dir),
        "output_dir": str(output_dir),
        "image_model": image_model,
        "images": records,
    }
    if aspect_ratio:
        summary["aspect_ratio"] = aspect_ratio
    summary_path = output_dir / "storyboard.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote plan to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
