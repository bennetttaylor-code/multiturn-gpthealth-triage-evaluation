#!/usr/bin/env python3
"""Supplementary Figure 3: under/correct/over-triage stratified by reference
triage level (A-D), by dataset.

Usage:
    python figS3_triage_direction_by_level.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from figlib import apply_style, save_fig, load_data, row_signed, C, LETTERS

parser = argparse.ArgumentParser(description='Supplementary Figure 3: triage direction by level')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: Triage direction by dataset, stratified by A-D level...")

dataset_titles = {
    1: 'Clinically-Authored\nVignettes (CAVs)',
    2: 'Emergency\nDepartment',
    3: 'Nurse Triage',
}
dataset_order = [1, 2, 3]

COL_UNDER   = '#ED7D31'   # orange
COL_CORRECT = '#595959'   # dark gray
COL_OVER    = '#4472C4'   # blue
BAND_NT     = '#E8F0F8'   # light blue  (vs. Nurse Triage groups)
BAND_CC     = '#EAF4E5'   # light green (vs. Clinician-Adjudicated groups)

# Groups in top->bottom order: (condition label, ref label, cond key, ref ord col, ref code)
group_defs = [
    ('Natural',   'vs. Nurse\nTriage',           'nat', 'gold_ord',    'NT'),
    ('Multiturn', 'vs. Nurse\nTriage',           'mt',  'gold_ord',    'NT'),
    ('Natural',   'vs. Clinician-\nAdjudicated', 'nat', 'cc_cons_ord', 'ClinAdj'),
    ('Multiturn', 'vs. Clinician-\nAdjudicated', 'mt',  'cc_cons_ord', 'ClinAdj'),
]


def level_breakdown(sub, cond_key, ref_col, level_ord):
    """Under/correct/over breakdown for one condition among cases whose reference
    acuity == level_ord."""
    sgn = row_signed(sub[f'{cond_key}_lo'], sub[f'{cond_key}_hi'], sub[ref_col])
    ref = np.array(sub[ref_col], float)
    s   = np.array(sgn, float)
    m   = (ref == level_ord) & ~np.isnan(s)
    s   = s[m]
    n   = len(s)
    if n == 0: return dict(pct=(0.0, 0.0, 0.0), cnt=(0, 0, 0), n=0)
    cu, cc, co = int((s < 0).sum()), int((s == 0).sum()), int((s > 0).sum())
    return dict(pct=(cu / n * 100, cc / n * 100, co / n * 100), cnt=(cu, cc, co), n=n)


# Row layout: y positions top->bottom, with a gap between the 4 groups
ROW_H, GROUP_GAP = 1.0, 0.9
row_layout = []     # (y, group_idx, level_idx, level_letter)
group_bands = []    # (y_lo, y_hi, cond_lbl, ref_lbl, ref_code)
yc = 0.0
for gi, (cond_lbl, ref_lbl, cond_key, ref_col, ref_code) in enumerate(group_defs):
    ys = []
    for li, lvl in enumerate(LETTERS):          # A,B,C,D  (A first = top)
        row_layout.append((yc, gi, li, lvl))
        ys.append(yc)
        yc -= ROW_H
    group_bands.append((min(ys) - 0.5, max(ys) + 0.5, cond_lbl, ref_lbl, ref_code))
    yc -= GROUP_GAP
y_bottom = yc + GROUP_GAP   # last decrement was an unused trailing gap

# Precompute breakdowns per dataset
panel_data = {}
for ds in dataset_order:
    sub = df[df['dataset'] == ds]
    cells = {}
    for (yv, gi, li, lvl) in row_layout:
        cond_lbl, ref_lbl, cond_key, ref_col, ref_code = group_defs[gi]
        cells[(gi, li)] = level_breakdown(sub, cond_key, ref_col, li)
    panel_data[ds] = dict(n=len(sub), cells=cells)

XMAX = 132
fig2b, axes2b = plt.subplots(1, 3, figsize=(21, 13), sharex=True)
for pi, ds in enumerate(dataset_order):
    ax = axes2b[pi]
    d  = panel_data[ds]
    for (y_lo, y_hi, cond_lbl, ref_lbl, ref_code) in group_bands:
        ax.axhspan(y_lo, y_hi, color=(BAND_NT if ref_code == 'NT' else BAND_CC),
                   alpha=0.6, zorder=0)
    for (yv, gi, li, lvl) in row_layout:
        cell = d['cells'][(gi, li)]
        if cell['n'] == 0:
            ax.text(2, yv, 'n = 0', ha='left', va='center',
                    fontsize=7, color='#AAAAAA', style='italic', zorder=4)
            continue
        left = 0.0
        for val, cnt, col in zip(cell['pct'], cell['cnt'],
                                 [COL_UNDER, COL_CORRECT, COL_OVER]):
            ax.barh(yv, val, left=left, color=col, alpha=0.92,
                    edgecolor='white', height=0.66, zorder=3)
            xc = left + val / 2
            if val >= 8:
                ax.text(xc, yv + 0.12, f'{val:.0f}%', ha='center', va='center',
                        fontsize=7.5, color='white', fontweight='bold', zorder=4)
                ax.text(xc, yv - 0.15, f'({cnt})', ha='center', va='center',
                        fontsize=6, color='#E8E8E8', zorder=4)
            elif val > 0:
                ax.text(xc, yv + 0.44, f'{val:.0f}%', ha='center', va='bottom',
                        fontsize=6.5, color='#555555', fontweight='bold', zorder=4)
                ax.text(xc, yv + 0.43, f'({cnt})', ha='center', va='top',
                        fontsize=5.5, color='#999999', zorder=4)
            left += val
    if pi == 2:
        for (y_lo, y_hi, cond_lbl, ref_lbl, ref_code) in group_bands:
            yc_mid = (y_lo + y_hi) / 2
            col_g  = '#2E75B6' if ref_code == 'NT' else C['clin']
            ax.text(115, yc_mid, f'{cond_lbl}\n{ref_lbl}', ha='center', va='center',
                    fontsize=8, color=col_g, fontweight='bold',
                    linespacing=1.3, zorder=4)
    ax.set_yticks([yv for (yv, gi, li, lvl) in row_layout])
    ax.set_yticklabels([lvl for (yv, gi, li, lvl) in row_layout] if pi == 0
                       else [''] * len(row_layout), fontsize=8.5, fontweight='bold')
    ax.set_xlim(0, XMAX)
    ax.set_ylim(y_bottom - 0.5, 0.9)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel('% of Cases', fontsize=9)
    ax.set_title(f"{dataset_titles[ds]}\n(n={d['n']})", fontsize=11, fontweight='bold')
    ax.grid(False)
    if pi == 0:
        ax.set_ylabel('Reference Triage Level (A = least urgent → D = most urgent)',
                      fontsize=9)

patches2b = [mpatches.Patch(color=COL_UNDER,   label='Under-triage'),
             mpatches.Patch(color=COL_CORRECT, label='Correct'),
             mpatches.Patch(color=COL_OVER,    label='Over-triage')]
fig2b.legend(handles=patches2b, loc='lower center', ncol=3,
             bbox_to_anchor=(0.5, -0.02), frameon=True, fontsize=9)
fig2b.tight_layout()
save_fig(fig2b, 'figS3_triage_direction_by_level', args.output)
