#!/usr/bin/env python3
"""
GPT Triage Analysis - Run Everything
====================================
Reproduces the full analysis from the source dataset:

  1. analysis.py            -> results/triage_analysis_results.xlsx (15-sheet workbook)
  2. fig*.py / figS*.py /
     table1_descriptives.py /
     extended_data_fig1_study_design.py
                             -> results/figures/  (Fig 1-4, Supp Fig 1-6,
                                                   Extended Data Fig 1, Table 1)
     Each figure is its own standalone script (see figlib.py for shared
     data-loading/plotting helpers); write_figure_index.py summarizes them.
  3. render_tableS1.py      -> results/figures/extended_data_table1_prompt_derivation.*
  4. render_grader_table.py -> results/figures/supp_table_grader_reliability.*

Usage (from the repository root):
    python code/run_all.py

Or with explicit paths:
    python code/run_all.py --input data/triage_evaluation_dataset.xlsx \
                           --prompts data/prompt_derivation.xlsx \
                           --output results/
"""
import argparse
import os
import subprocess
import sys

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CODE_DIR)

parser = argparse.ArgumentParser(description='Run full GPT triage analysis + figures')
parser.add_argument('--input',  default=os.path.join(REPO_ROOT, 'data', 'triage_evaluation_dataset.xlsx'),
                    help='Source dataset Excel file (sheet named C)')
parser.add_argument('--prompts', default=os.path.join(REPO_ROOT, 'data', 'prompt_derivation.xlsx'),
                    help='Per-case prompt-derivation Excel file (Extended Data Table 1)')
parser.add_argument('--output', default=os.path.join(REPO_ROOT, 'results'),
                    help='Output directory (default: <repo>/results)')
args = parser.parse_args()

python = sys.executable
fig_dir = os.path.join(args.output, 'figures')
results_xlsx = os.path.join(args.output, 'triage_analysis_results.xlsx')
os.makedirs(fig_dir, exist_ok=True)

FIGURE_SCRIPTS = [
    ('Figure 1 (direction by dataset)',        'fig1_direction_by_dataset.py'),
    ('Figure 2 (distance comparisons)',        'fig2_dist_comparisons.py'),
    ('Figure 3 (ClinAdj vs. Nurse concordance)', 'fig3_cc_concordance.py'),
    ('Figure 4 (prompt count, Multiturn)',     'fig4_promptcount_multiturn.py'),
    ('Table 1 (case characteristics)',         'table1_descriptives.py'),
    ('Extended Data Figure 1 (study design)',  'extended_data_fig1_study_design.py'),
    ('Supp. Figure 1 (confusion matrices)',    'figS1_confusion_matrices.py'),
    ('Supp. Figure 2 (sensitivity forest)',    'figS2_sensitivity_forest.py'),
    ('Supp. Figure 3 (direction by level)',    'figS3_triage_direction_by_level.py'),
    ('Supp. Figure 4 (prompt count scatter)',  'figS4_promptcount.py'),
    ('Supp. Figure 5 (complaint heatmap)',     'figS5_complaint_heatmap.py'),
    ('Supp. Figure 6 (ClinAdj vs. Nurse confusion)', 'figS6_cc_vs_nurse_confusion.py'),
]

steps = [
    ('Statistical analysis (workbook)',
     [os.path.join(CODE_DIR, 'analysis.py'), '--input', args.input, '--output', args.output]),
]
for label, script in FIGURE_SCRIPTS:
    steps.append((label,
        [os.path.join(CODE_DIR, script), '--input', args.input, '--output', fig_dir]))
steps.append(('Figure index',
    [os.path.join(CODE_DIR, 'write_figure_index.py'), '--output', fig_dir]))
steps += [
    ('Extended Data Table 1 (prompt derivation)',
     [os.path.join(CODE_DIR, 'render_tableS1.py'), '--input', args.prompts, '--output', fig_dir]),
    ('Supplementary Table 1 (grader reliability)',
     [os.path.join(CODE_DIR, 'render_grader_table.py'), '--input', results_xlsx, '--output', fig_dir]),
]

for label, cmd in steps:
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
    result = subprocess.run([python] + cmd, check=False)
    if result.returncode != 0:
        print(f"\nERROR: {label} failed (exit code {result.returncode}). Stopping.")
        sys.exit(result.returncode)

print(f"\n{'='*60}\n  ALL DONE\n{'='*60}")
print(f"  Workbook: {results_xlsx}")
print(f"  Figures:  {fig_dir}/")
