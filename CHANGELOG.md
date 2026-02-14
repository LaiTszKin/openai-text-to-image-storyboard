# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-02-14

### Added
- Added `--image-size`/`--size` CLI options and `OPENAI_IMAGE_SIZE` env support for providers that require explicit pixel size.
- Added generated image dimension metadata (`width`, `height`) and optional `image_size` to `storyboard.json`.

### Changed
- Updated README, SKILL docs, and `.env.example` with size-based guidance when aspect-ratio controls are ignored by a provider.

### Fixed
- Added post-generation aspect-ratio mismatch detection and warning to highlight when providers ignore `aspect_ratio`.

## [0.1.0] - 2026-02-14

### Added
- Initial release of the OpenAI text-to-image storyboard skill and generation script.
- Support for generating ordered storyboard images and `storyboard.json` from direct prompts or a JSON prompts file.
- OpenAI-compatible image generation support via `/images/generations` with configurable model, ratio, quality, and style.

### Changed
- Clarified skill workflow so the agent starts image generation immediately after receiving article or chapter content.
- Updated usage docs and agent default prompt to reflect the expected execution flow.

### Fixed
- Default `.env` loading now points to this skill folder instead of the target project directory.
