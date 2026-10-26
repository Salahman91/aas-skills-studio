# Changelog

All notable changes to this project are documented here.
الصيغة تتبع [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) و[Semantic Versioning](https://semver.org/).

## [2.4.0] — 2026-10-26

### Added
- Natural-language **Arabic smart search** with a 130-entry concept map and IDF weighting.
- Optional **Gemini reranking** (`gemini-2.5-flash`, `2.5-pro`, `2.5-flash-lite`, `2.0-flash`) with a per-skill Arabic reason and graceful fallback to local results.
- **Slash-form invocation** (`/skill-id`) matching tool command palettes, with one-click copy.
- Arabic description for every skill: 39 hand-written + 2,711 translated, plus a separate English-terms line.
- **9-group / 23-subsection** taxonomy replacing 115 loose categories; leaf groups have no expand caret.
- Bilingual UI (`عربي / EN`) with full RTL↔LTR layout mirroring.
- Multi-select, “download selected/results/all”, 12 install targets, download log, cancel button.
- CLI: `--selftest`, `--download-test`, `--bulk-test`.
- Professional repository scaffolding: CI workflow, issue/PR templates, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT.

### Changed
- Detail pane prioritises the Arabic explanation and isolates English terms on their own line.
- Vague upstream descriptions (`Curated upstream guidance for X…`) were rewritten into explicit Arabic guidance.

### Fixed
- Search ranking no longer lets generic words (e.g. «إدارة») outrank specific ones (e.g. «فيسبوك»).
- Arabic label text no longer disappears when mixed with symbol glyphs in one widget.
- Bundled data path resolution inside the PyInstaller one-file build.

## [2.0.0] — 2026-10-26

### Added
- Full 2,750-skill catalog, grouping, multi-select, download-all, per-tool install targets.
- Arabic and English interface.

## [1.0.0] — 2026-10-26

### Added
- First version: 39 curated skills with Arabic descriptions, download and copy actions.
