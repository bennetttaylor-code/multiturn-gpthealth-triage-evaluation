#!/usr/bin/env python3
"""Figure 3: concordance between clinician-adjudicated and nurse-triage
standards (distribution of category differences).

Usage:
    python fig3_cc_concordance.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from figlib import apply_style, save_fig, load_data

parser = argparse.ArgumentParser(description='Figure 3: ClinAdj vs. Nurse Triage concordance')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: ClinAdj vs. Nurse Triage concordance distribution...")

_cc = np.array(df['cc_cons_ord'], float); _nu = np.array(df['gold_ord'], float)
_m  = ~np.isnan(_cc) & ~np.isnan(_nu)
_diff = np.abs(_cc[_m] - _nu[_m]).astype(int)
N_cc = int(_m.sum())
cnts = [int((_diff == d).sum()) for d in range(4)]
pcts = [c / N_cc * 100 for c in cnts]

figCC, axCC = plt.subplots(figsize=(8.5, 5.6))
bar_cols = ['#70AD47', '#FFC000', '#ED7D31', '#C00000']
axCC.bar(range(4), pcts, color=bar_cols, edgecolor='white', width=0.7, zorder=3)
for i, (c, p) in enumerate(zip(cnts, pcts)):
    axCC.text(i, p + 1.2, f'{p:.1f}%\n(n={c})', ha='center', va='bottom',
              fontsize=10, fontweight='bold', color='#333333')
axCC.set_xticks(range(4))
axCC.set_xticklabels(['0\nExact agreement', '1', '2', '3'], fontsize=10)
axCC.set_xlabel('Triage categories apart  (Clinician-Adjudicated − Nurse Triage)', fontsize=11)
axCC.set_ylabel('Percentage of cases (%)', fontsize=11)
axCC.set_ylim(0, max(pcts) * 1.25)
axCC.grid(True, axis='y', alpha=0.3, zorder=0)
save_fig(figCC, 'fig3_cc_concordance', args.output)
