# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions track Zenodo releases.

## [1.0.1] — 2026-10-12
### Fixed
- Dataset 3 prompt numbering in `data/prompt_derivation.xlsx`. Dataset 3 Prompt 86 was removed before evaluation as a repeat, as noted in `data/triage_evaluation_dataset.xlsx` (row 217, column R). The evaluation file kept the original identifiers (1–85, 87–141), but the derivation file numbered the remaining 140 cases 1–140, so its Prompt Nos. 86–140 did not match evaluation Prompts 87–141. Derivation Prompt Nos. 86–140 (Excel rows 207–261) are now 87–141. Dataset plus prompt number now joins the two files one-to-one for all 255 cases, and chief complaints agree for every Dataset 2 and Dataset 3 case (ignoring capitalization and whitespace).
- No chief complaints, prompts, labels or model outputs changed; `data/triage_evaluation_dataset.xlsx` is unchanged. The analysis reads only the evaluation file, so the results workbook and all figures other than Extended Data Table 1 are unaffected.

### Changed
- Extended Data Table 1 regenerated with the corrected Dataset 3 numbering.
- `CITATION.cff` now cites the Zenodo concept DOI (10.5281/zenodo.21223678), which resolves to the latest version.
- Zenodo DOI and repository URL filled in after the first release.
- `environment/Dockerfile` builds when the environment is built before code is mounted.
- `code/run` tolerates nested Code Ocean data-asset mount paths.

### Documentation
- README explains how the two data files join and what the released prompts represent: they are the opening message of each conversation, not the complete model input; clinician adjudication considered the whole conversation.

Thanks to Cole Peterson for reporting the identifier mismatch.

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
