# Changelog

All notable changes to this project will be documented in this file.

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
