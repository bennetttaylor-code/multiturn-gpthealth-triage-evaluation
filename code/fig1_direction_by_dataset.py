#!/usr/bin/env python3
"""Figure 1: under-triage / correct / over-triage breakdown by interaction
condition and dataset.

Usage:
    python fig1_direction_by_dataset.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from figlib import apply_style, save_fig, load_data, row_signed, C

parser = argparse.ArgumentParser(description='Figure 1: triage direction by dataset')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure 1: Triage direction by dataset...")

dataset_titles = {
    1: 'Clinically-Authored\nVignettes (CAVs)',
    2: 'Emergency\nDepartment',
    3: 'Nurse Triage',
}
dataset_order = [1, 2, 3]

COL_UNDER   = '#ED7D31'   # orange
COL_CORRECT = '#595959'   # dark gray
COL_OVER    = '#4472C4'   # blue


def dir_breakdown(sgn_arr):
    s = np.array(sgn_arr, float)
    s = s[~np.isnan(s)]
    n = len(s)
    if n == 0: return dict(pct=(0.0, 0.0, 0.0), cnt=(0, 0, 0))
    cu, cc, co = int((s < 0).sum()), int((s == 0).sum()), int((s > 0).sum())
    return dict(pct=(cu / n * 100, cc / n * 100, co / n * 100), cnt=(cu, cc, co))


# Each row = dict(pct=(under,correct,over), cnt=(...)) of all valid cases (NT then ClinAdj)
panel_data = {}
for ds in dataset_order:
    sub = df[df['dataset'] == ds]
    nat_sgn_cc = row_signed(sub['nat_lo'], sub['nat_hi'], sub['cc_cons_ord'])
    mt_sgn_cc  = row_signed(sub['mt_lo'],  sub['mt_hi'],  sub['cc_cons_ord'])
    rows_ds = [
        dir_breakdown(sub['nat_signed'].values),
        dir_breakdown(sub['mt_signed'].values),
        dir_breakdown(nat_sgn_cc),
        dir_breakdown(mt_sgn_cc),
    ]
    panel_data[ds] = dict(n=len(sub), rows=rows_ds)

y_pos_b   = np.array([0, 1, 2.3, 3.3])
ylabels_b = ['Natural', 'Multiturn', 'Natural', 'Multiturn']
XMAX = 126

fig2, axes2 = plt.subplots(1, 3, figsize=(20, 6), sharex=True)
for pi, ds in enumerate(dataset_order):
    ax = axes2[pi]
    d  = panel_data[ds]
    ax.axhspan(-0.55, 1.55, color='#E8F0F8', alpha=0.6, zorder=0)
    ax.axhspan(1.75,  3.85, color='#EAF4E5', alpha=0.6, zorder=0)
    ax.axhline(1.65, color='#AAAAAA', linewidth=0.8, linestyle='-', zorder=1)
    for row, yp in zip(d['rows'], y_pos_b):
        left = 0.0
        for val, cnt, col in zip(row['pct'], row['cnt'],
                                 [COL_UNDER, COL_CORRECT, COL_OVER]):
            ax.barh(yp, val, left=left, color=col, alpha=0.92,
                    edgecolor='white', height=0.62, zorder=3)
            xc = left + val / 2
            if val >= 8:
                ax.text(xc, yp + 0.11, f'{val:.0f}%', ha='center', va='center',
                        fontsize=8, color='white', fontweight='bold', zorder=4)
                ax.text(xc, yp - 0.13, f'({cnt})', ha='center', va='center',
                        fontsize=6.5, color='#E8E8E8', zorder=4)
            elif val > 0:
                ax.text(xc, yp + 0.42, f'{val:.0f}%', ha='center', va='bottom',
                        fontsize=7, color='#555555', fontweight='bold', zorder=4)
                ax.text(xc, yp + 0.41, f'({cnt})', ha='center', va='top',
                        fontsize=6, color='#999999', zorder=4)
            left += val
    ax.text(113, 0.5, 'vs. Nurse\nTriage', ha='center', va='center',
            fontsize=8.5, color='#2E75B6', fontweight='bold', linespacing=1.4, zorder=4)
    ax.text(113, 2.8, 'vs. Clinician-\nAdjudicated', ha='center', va='center',
            fontsize=8.5, color=C['clin'], fontweight='bold', linespacing=1.4, zorder=4)
    ax.set_yticks(y_pos_b)
    ax.set_yticklabels(ylabels_b if pi == 0 else [''] * 4, fontsize=9)
    ax.set_xlim(0, XMAX)
    ax.set_ylim(-0.6, 3.9)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel('% of Cases', fontsize=9)
    ax.set_title(f"{dataset_titles[ds]}\n(n={d['n']})", fontsize=11, fontweight='bold')
    ax.grid(False)

patches2 = [mpatches.Patch(color=COL_UNDER,   label='Under-triage'),
            mpatches.Patch(color=COL_CORRECT, label='Correct'),
            mpatches.Patch(color=COL_OVER,    label='Over-triage')]
fig2.legend(handles=patches2, loc='lower center', ncol=3,
            bbox_to_anchor=(0.5, -0.04), frameon=True, fontsize=9)
fig2.tight_layout()
save_fig(fig2, 'fig1_direction_by_dataset', args.output)
