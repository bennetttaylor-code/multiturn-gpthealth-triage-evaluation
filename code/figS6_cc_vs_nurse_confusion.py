#!/usr/bin/env python3
"""Supplementary Figure 6: clinician-adjudicated vs. nurse-triage agreement
matrix.

Usage:
    python figS6_cc_vs_nurse_confusion.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from figlib import apply_style, save_fig, load_data, LETTERS

parser = argparse.ArgumentParser(description='Supplementary Figure 6: ClinAdj vs. Nurse Triage confusion')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: ClinAdj vs. Nurse Triage confusion matrix...")

valid_10 = (~df['cc_cons_ord'].isna()) & (~df['gold_ord'].isna())
cc_v10   = df.loc[valid_10, 'cc_cons_ord'].astype(int).values
nu_v10   = df.loc[valid_10, 'gold_ord'].astype(int).values
N10      = int(valid_10.sum())

conf10 = np.zeros((4, 4), dtype=int)
for ci, ni in zip(cc_v10, nu_v10):
    conf10[ci, ni] += 1
row_tots10 = conf10.sum(axis=1)
col_tots10 = conf10.sum(axis=0)

C10_AGREE = '#70AD47'
C10_CCOVR = '#4472C4'
C10_NUHGH = '#ED7D31'
C10_TOT   = '#D9D9D9'
C10_GRAND = '#ABABAB'
C10_HDNU  = '#2E75B6'
C10_HDCC  = '#548235'
C10_HDOTH = '#808080'
TW = '#FFFFFF'
TB = '#1A1A1A'
AF10 = dict(fontfamily='Arial', fontweight='bold')

fig10 = plt.figure(figsize=(9, 10))
ax10  = fig10.add_subplot(111)
ax10.axis('off')
ax10.set_xlim(-2.1, 5.6)
ax10.set_ylim(-1.6, 6.1)
ax10.set_aspect('equal')


def _dc(x, y, w=1.0, h=1.0, fc='white', lw=2.0):
    ax10.add_patch(mpatches.Rectangle(
        (x, y), w, h, facecolor=fc, edgecolor='white', linewidth=lw, zorder=2))


def _dt(x, y, w, h, lines):
    for txt, fs, col, dy in lines:
        ax10.text(x + w / 2, y + h / 2 + dy, txt, ha='center', va='center',
                  fontsize=fs, color=col, zorder=5, **AF10)


for i in range(4):
    for j in range(4):
        count = conf10[i, j]
        pct   = count / N10 * 100
        yp    = 3 - i
        fc    = C10_AGREE if i == j else (C10_CCOVR if i > j else C10_NUHGH)
        _dc(j, yp, fc=fc)
        _dt(j, yp, 1, 1, [(str(count),      16, TW,  0.16),
                            (f'({pct:.0f}%)',  9, TW, -0.17)])

for i in range(4):
    yp = 3 - i
    _dc(4, yp, fc=C10_TOT)
    _dt(4, yp, 1, 1, [(str(row_tots10[i]), 14, TB, 0)])

for j in range(4):
    _dc(j, -1, fc=C10_TOT)
    _dt(j, -1, 1, 1, [(str(col_tots10[j]), 14, TB, 0)])

_dc(4, -1, fc=C10_GRAND)
_dt(4, -1, 1, 1, [(f'N={N10}', 12, TB, 0)])

for j, ltr in enumerate(LETTERS):
    _dc(j, 4, h=0.85, fc=C10_HDNU)
    _dt(j, 4, 1, 0.85, [(ltr, 15, TW, 0)])

for i, ltr in enumerate(LETTERS):
    yp = 3 - i
    _dc(-1, yp, w=0.9, fc=C10_HDCC)
    _dt(-1, yp, 0.9, 1, [(ltr, 15, TW, 0)])

_dc(4, 4, w=1.0, h=0.85, fc=C10_HDOTH)
_dt(4, 4, 1.0, 0.85, [('Total', 11, TW, 0)])
_dc(-1, -1, w=0.9, h=1.0, fc=C10_HDOTH)
_dt(-1, -1, 0.9, 1.0, [('Total', 11, TW, 0)])

ax10.text(2.0, 5.15, 'Nurse Triage Decision',
          ha='center', va='center', fontsize=15, color=TB, **AF10)
ax10.text(-1.65, 1.5, 'Clinician-Adjudicated',
          ha='center', va='center', fontsize=15, color=TB, rotation=90, **AF10)
leg10_patches = [
    mpatches.Patch(facecolor=C10_AGREE, label='Exact agreement  (ClinAdj = Nurse)'),
    mpatches.Patch(facecolor=C10_CCOVR, label='Clinician over-triage  (ClinAdj > Nurse)'),
    mpatches.Patch(facecolor=C10_NUHGH, label='Nurse higher acuity  (Nurse > ClinAdj)'),
]
ax10.legend(handles=leg10_patches,
            loc='lower center',
            bbox_to_anchor=(0.5, -0.18),
            bbox_transform=ax10.transAxes,
            ncol=1, frameon=True, framealpha=0.95,
            prop={'family': 'Arial', 'weight': 'bold', 'size': 11},
            handlelength=1.8, handleheight=1.3,
            borderpad=0.9, labelspacing=0.45)
save_fig(fig10, 'figS6_cc_vs_nurse_confusion', args.output)
