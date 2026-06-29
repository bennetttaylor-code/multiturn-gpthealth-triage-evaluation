# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions track Zenodo releases.

## [1.0.0] — 2026-06-29
### Added
- Initial release: analysis code, source dataset, 15-sheet results workbook, and
  all manuscript figures/tables for the ChatGPT Health triage evaluation (255 cases).
- One-command reproduction via `code/run_all.py` (analysis → figures → Extended
  Data Table 1 → Supplementary Table 1).
- Code Ocean entrypoint (`code/run`) and Docker environment with Arial
  (`environment/Dockerfile`) for faithful figure reproduction on Linux.
- Licensing: MIT for code, CC BY 4.0 for data and figures.
- Archive/citation metadata: `CITATION.cff`, `.zenodo.json`.
- Continuous reproducibility check (`.github/workflows/reproduce.yml`).
