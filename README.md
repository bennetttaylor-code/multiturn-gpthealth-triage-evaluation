# ChatGPT Health Triage Evaluation — Analysis Code & Data

[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](LICENSE-data)
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->

Reproducible analysis code, source dataset, results workbook, and publication
figures for:

> **Conversational interaction does not ensure triage-disposition alignment in
> ChatGPT Health in real and synthetic patient encounters.**
> Tyagi A, Taylor B, … Nadkarni GN\*, Naved BA\*. (2026).

ChatGPT Health was evaluated on **255 clinical triage cases** across three
datasets (39 clinically-authored vignettes, 76 emergency-department encounters,
140 nurse-line encounters) under two interaction conditions (single-message
"natural" and structured "multi-turn"), scored against two reference standards
(**nurse triage** and **clinician-adjudicated**) on an A–D ordinal urgency scale.

---

## Repository structure

```
.
├── code/                     # analysis software (MIT)
│   ├── analysis.py           #   → results workbook (15 sheets)
│   ├── figures.py            #   → Fig 1–4, Supp Fig 1–6, Extended Data Fig 1, Table 1
│   ├── render_tableS1.py     #   → Extended Data Table 1 (prompt derivation)
│   ├── render_grader_table.py#   → Supplementary Table 1 (grader reliability)
│   ├── run_all.py            #   orchestrates all four steps
│   └── run                   #   entrypoint for Code Ocean (and local use)
├── data/                     # source data (CC BY 4.0, de-identified)
│   ├── triage_evaluation_dataset.xlsx   # 255-case input (sheet "C")
│   └── prompt_derivation.xlsx           # per-case natural & multi-turn prompts
├── results/                  # shipped outputs (CC BY 4.0)
│   ├── triage_analysis_results.xlsx     # 15-sheet workbook
│   └── figures/                         # all figures/tables (.png + .pdf)
├── environment/
│   └── Dockerfile            # Code Ocean / reproducible environment (incl. Arial)
├── requirements.txt
├── CITATION.cff
├── .zenodo.json
├── LICENSE                   # MIT (code)
└── LICENSE-data              # CC BY 4.0 (data & figures)
```

---

## Reproducing the analysis

### Option A — local (Python ≥ 3.9)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python code/run_all.py
```

Outputs are written to `results/` (workbook) and `results/figures/`.
Figures use the **Arial** font; on systems without Arial, matplotlib will
substitute a default sans-serif (results are unchanged, only the font differs).

### Option B — Docker / Code Ocean (bit-for-bit fonts)

The `environment/Dockerfile` installs Arial (via msttcorefonts) so figures
render with the publication font. On **Code Ocean**, import this repository as a
capsule: attach the two files in `data/` as the capsule's data asset, set the
Dockerfile under *Environment*, and the reproducible run command is `code/run`,
which writes to `/results`. Locally:

```bash
docker build -t triage-eval environment/
docker run --rm -v "$PWD":/capsule -w /capsule/code triage-eval python run_all.py
```

---

## Data

Two de-identified Excel inputs in `data/`:

**`triage_evaluation_dataset.xlsx`** (sheet `C`) — one row per graded case:

| Column | Description |
|--------|-------------|
| `DATASET` | Dataset number (1 = vignettes, 2 = ED, 3 = nurse-line) |
| `Prompt` | Prompt/case identifier |
| `Grader` | Grader ID (1–5) |
| `Patient Chief Complaint` | Free-text complaint category |
| `Age`, `Gender` | Demographics (ED dataset only) |
| `Clinician Consensus` | Clinician-adjudicated level (A–D, or range A/B, B/C, C/D) |
| `GPT Natural Prompt Count` | Turns in the natural condition |
| `GPT Natural Triage Decision (A-D)` | Natural primary decision |
| `GPT Natural Reviewer` | Natural reviewer decision |
| `GPT Multiturn Prompt Count` | Turns in the multi-turn condition |
| `GPT Multiturn Triage Decision (A-D)` | Multi-turn primary decision |
| `GPT Multiturn Reviewer` | Multi-turn reviewer decision |
| `Nurse Triage Decision (A-D)` | Nurse-triage reference level |

**`prompt_derivation.xlsx`** — per-case chief complaint and the exact natural and
multi-turn prompts presented to ChatGPT Health (source of Extended Data Table 1).

**Scale:** A = 0 (home care) → B → C → D = 3 (emergency department); under-triage
(decision < reference) is the pre-specified safety-critical error direction.
Range values (`A/B`, `B/C`, `C/D`) use minimum-distance scoring; the 17
range-valued clinician-adjudicated dispositions use the higher-acuity bound as
the reference. The data are de-identified and retrospectively derived; see the
article Methods for provenance and the ethics/IRB-exemption statement.

---

## Outputs

### `results/triage_analysis_results.xlsx` — 15 sheets (Arial, booktabs style)

| Sheet | Contents |
|-------|----------|
| `Table 1` | Case characteristics by dataset |
| `PRIMARY - Performance` | Both conditions vs. each reference: agreement (exact CI), weighted κ, distance, under/over rates, confusion matrices |
| `PRIMARY - Safety-Critical` | Cases with distance ≥ 2; safety-critical under-triage by condition × reference |
| `PRIMARY - Error Direction` | Two-sided binomial direction-of-error tests |
| `SECONDARY - Sensitivity` | Conservative / aggressive resolution sensitivity |
| `SECONDARY - By Dataset` | Results stratified by dataset |
| `SECONDARY - Dataset x Level` | Under/correct/over by reference level × dataset |
| `SECONDARY - By Complaint` | Performance by chief-complaint category |
| `SECONDARY - Prompt Count` | Prompt count vs. distance (Spearman; pooled + per-dataset) |
| `SECONDARY - Nat vs Multiturn` | Paired tests (McNemar, Wilcoxon) vs. both references |
| `SUPP - Descriptives` | Data summary, value counts, cleaning log |
| `SUPP - ClinAdj vs Nurse` | Reference-standard agreement, κ, concordance & disagreement direction |
| `SUPP - Grader Reliability` | Per-grader κ + grader-3 exclusion sensitivity |
| `SUPP - Summary Table` | Consolidated key metrics |
| `SUPP - Comparison Summary` | Compact agreement / under / over comparison |

### `results/figures/` — publication figures (PNG 300 DPI + PDF vector)

| Manuscript label | File |
|------------------|------|
| Table 1 | `table1_descriptives` |
| Figure 1 | `fig1_direction_by_dataset` |
| Figure 2 | `fig2_dist_comparisons` |
| Figure 3 | `fig3_cc_concordance` |
| Figure 4 | `fig4_promptcount_multiturn` |
| Extended Data Fig. 1 | `extended_data_fig1_study_design` |
| Extended Data Table 1 | `extended_data_table1_prompt_derivation` |
| Supplementary Fig. 1 | `figS1_confusion_matrices` |
| Supplementary Fig. 2 | `figS2_sensitivity_forest` |
| Supplementary Fig. 3 | `figS3_triage_direction_by_level` |
| Supplementary Fig. 4 | `figS4_promptcount` |
| Supplementary Fig. 5 | `figS5_complaint_heatmap` |
| Supplementary Fig. 6 | `figS6_cc_vs_nurse_confusion` |
| Supplementary Table 1 | `supp_table_grader_reliability` |

---

## Statistical methods

All tests are two-sided (α = 0.05), except the two primary
LLM-versus-reference-standard comparisons, which use a Bonferroni-corrected
α = 0.025. 95% CIs are reported for all primary estimates.

- **Exact (Clopper–Pearson) binomial 95% CIs** for agreement and all proportions
- **Cohen's weighted κ** (linear weights), bootstrapped 95% CI (1,000 resamples)
- **McNemar's test** for paired exact-agreement / under-triage comparisons
- **Wilcoxon signed-rank** for paired ordinal-distance comparisons (effect-size *r*)
- **Two-sided exact binomial test** for direction-of-error asymmetry
- **Spearman correlation** (Fisher-*z* 95% CI) for prompt count vs. distance
- **χ²** and **Mann–Whitney U** for cross-dataset generalization
- **LOESS smoother** for the prompt-count figures

### Cohen's κ interpretation
| Range | Interpretation |
|-------|---------------|
| < 0.20 | Slight |
| 0.21–0.40 | Fair |
| 0.41–0.60 | Moderate |
| 0.61–0.80 | Substantial |
| 0.81–1.00 | Almost perfect |

---

## Citation

Please cite both the article and this repository (see `CITATION.cff`; add the
Zenodo DOI once minted).

## License

- **Code** (`code/`): MIT — see [`LICENSE`](LICENSE)
- **Data & figures** (`data/`, `results/`): CC BY 4.0 — see [`LICENSE-data`](LICENSE-data)

## Notes

- Grader 5 is a blind reviewer present in Dataset 1 only (n = 14 self-review rows).
- No prompt overlap between graders → Fleiss' / pairwise inter-grader κ not computable.
- Analysis assisted by Claude Code (Anthropic); figures in Matplotlib.
