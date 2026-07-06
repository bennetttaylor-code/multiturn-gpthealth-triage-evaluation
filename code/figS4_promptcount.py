#!/usr/bin/env python3
"""Supplementary Figure 4: prompt count vs. clinical distance scatter, all
conditions x reference standards.

Usage:
    python figS4_promptcount.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.interpolate import interp1d
from statsmodels.nonparametric.smoothers_lowess import lowess
from figlib import apply_style, save_fig, load_data, row_dist, C

parser = argparse.ArgumentParser(description='Supplementary Figure 4: prompt count scatter')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: Prompt count scatter...")

df['nat_dist_cc_sc'] = row_dist(df['nat_lo'], df['nat_hi'], df['cc_cons_ord'])
df['mt_dist_cc_sc']  = row_dist(df['mt_lo'],  df['mt_hi'],  df['cc_cons_ord'])

triage_colors = {0: '#4DAF4A', 1: '#377EB8', 2: '#FF7F00', 3: '#E41A1C'}
triage_labels = {0: 'A (non-urgent)', 1: 'B (semi-urgent)', 2: 'C (urgent)', 3: 'D (emergent)'}

np.random.seed(42)
jitter_s4 = np.random.uniform(-0.07, 0.07, len(df))

fig_s4 = plt.figure(figsize=(13, 13))
# Two separate GridSpecs give a clear visual gap between the NT and ClinAdj groups
gs_nt = gridspec.GridSpec(2, 2, height_ratios=[4, 1], hspace=0.06, wspace=0.30,
                           top=0.88, bottom=0.50, left=0.09, right=0.97)
gs_cc = gridspec.GridSpec(2, 2, height_ratios=[4, 1], hspace=0.06, wspace=0.30,
                           top=0.44, bottom=0.06, left=0.09, right=0.97)

panels_s4 = [
    ('nat_count', 'nat_dist',       df['gold_ord'],    'A  Natural — vs. Nurse Triage',        gs_nt, 0),
    ('mt_count',  'mt_dist',        df['gold_ord'],    'B  Multiturn — vs. Nurse Triage',       gs_nt, 1),
    ('nat_count', 'nat_dist_cc_sc', df['cc_cons_ord'], 'C  Natural — vs. Clinician-Adjudicated',  gs_cc, 0),
    ('mt_count',  'mt_dist_cc_sc',  df['cc_cons_ord'], 'D  Multiturn — vs. Clinician-Adjudicated',gs_cc, 1),
]

for count_col, dist_col, ref_ord, title_lbl, gs, col_i in panels_s4:
    ax_s = fig_s4.add_subplot(gs[0, col_i])
    ax_h = fig_s4.add_subplot(gs[1, col_i])

    mask = (~df[count_col].isna()) & (~df[dist_col].isna()) & (~ref_ord.isna())
    sub  = df[mask]
    x = sub[count_col].values.astype(float)
    y = sub[dist_col].values.astype(float) + jitter_s4[sub.index]
    g = ref_ord[sub.index].astype(int).values

    for gv in [0, 1, 2, 3]:
        idx_gv = g == gv
        ax_s.scatter(x[idx_gv], y[idx_gv], c=triage_colors[gv], s=22,
                     alpha=0.65, edgecolors='white', linewidths=0.3,
                     label=triage_labels[gv], zorder=3)

    x_clean = sub[count_col].values.astype(float)
    y_clean = sub[dist_col].values.astype(float)
    if len(x_clean) > 10:
        sort_i = np.argsort(x_clean)
        xs, ys = x_clean[sort_i], y_clean[sort_i]
        sm = lowess(ys, xs, frac=0.4, return_sorted=True)
        ax_s.plot(sm[:, 0], sm[:, 1], color='#555555', linewidth=2.2, zorder=5, label='LOESS smoother')
        boot_sm = []
        rng_s4 = np.random.RandomState(0)
        for _ in range(100):
            idx_b = rng_s4.randint(0, len(xs), len(xs))
            try:
                s2 = lowess(ys[idx_b], xs[idx_b], frac=0.4, return_sorted=True)
                f  = interp1d(s2[:, 0], s2[:, 1], bounds_error=False, fill_value='extrapolate')
                boot_sm.append(f(sm[:, 0]))
            except Exception: pass
        if boot_sm:
            boot_sm = np.array(boot_sm)
            ax_s.fill_between(sm[:, 0], np.percentile(boot_sm, 2.5, axis=0),
                              np.percentile(boot_sm, 97.5, axis=0),
                              color='#555555', alpha=0.15, zorder=4)

    ax_s.set_ylim(-0.3, 3.3)
    ax_s.set_yticks([0, 1, 2, 3])
    ax_s.set_yticklabels(['0', '1', '2', '3'])
    ax_s.set_ylabel('Clinical Distance Score' if col_i == 0 else '')
    ax_s.set_title(title_lbl, fontsize=11, fontweight='bold')
    ax_s.set_xticklabels([])
    ax_s.grid(True, alpha=0.25)
    if col_i == 0:
        ax_s.legend(loc='upper right', fontsize=7.5, frameon=True, markerscale=1.2)

    ax_h.hist(x_clean, bins=20, color='#888888', alpha=0.7, edgecolor='white')
    ax_h.set_xlabel('Prompt Count', fontsize=10)
    ax_h.set_ylabel('N' if col_i == 0 else '')
    ax_h.grid(True, alpha=0.2)

fig_s4.text(0.5, 0.915, 'vs. Nurse Triage', ha='center', fontsize=12,
            fontweight='bold', color='#2E75B6')
fig_s4.text(0.5, 0.468, 'vs. Clinician-Adjudicated', ha='center', fontsize=12,
            fontweight='bold', color=C['clin'])

save_fig(fig_s4, 'figS4_promptcount', args.output)
