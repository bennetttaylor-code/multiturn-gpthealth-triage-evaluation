#!/usr/bin/env python3
"""Supplementary Figure 2: sensitivity forest plot (primary / conservative /
aggressive grader-reviewer discordance resolution).

Usage:
    python figS2_sensitivity_forest.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from figlib import apply_style, save_fig, load_data, wilson_ci, wkappa_ci, C

parser = argparse.ArgumentParser(description='Supplementary Figure 2: sensitivity forest plot')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: Sensitivity forest plot...")


def sens_metrics(lo_arr, hi_arr, gold_arr):
    lo, hi, g = np.array(lo_arr, float), np.array(hi_arr, float), np.array(gold_arr, float)
    mask = ~(np.isnan(lo) | np.isnan(hi) | np.isnan(g))
    lo, hi, g = lo[mask], hi[mask], g[mask]; n = len(lo)
    in_r = (lo <= g) & (g <= hi)
    na = int(in_r.sum())
    ag_p, ag_lo, ag_hi = wilson_ci(na, n)
    oracle = np.clip(g, lo, hi)
    k, klo, khi = wkappa_ci(oracle, g)
    return ag_p, ag_lo, ag_hi, k, klo, khi


# Primary
p_nat_ag, p_nat_alo, p_nat_ahi, p_nat_k, p_nat_klo, p_nat_khi = \
    sens_metrics(df['nat_lo'], df['nat_hi'], df['gold_ord'])
p_mt_ag,  p_mt_alo,  p_mt_ahi,  p_mt_k,  p_mt_klo,  p_mt_khi  = \
    sens_metrics(df['mt_lo'], df['mt_hi'], df['gold_ord'])
# Conservative
c_nat_ag, c_nat_alo, c_nat_ahi, c_nat_k, c_nat_klo, c_nat_khi = \
    sens_metrics(df['nat_res_cons'], df['nat_res_cons'], df['gold_ord'])
c_mt_ag,  c_mt_alo,  c_mt_ahi,  c_mt_k,  c_mt_klo,  c_mt_khi  = \
    sens_metrics(df['mt_res_cons'], df['mt_res_cons'], df['gold_ord'])
# Aggressive
a_nat_ag, a_nat_alo, a_nat_ahi, a_nat_k, a_nat_klo, a_nat_khi = \
    sens_metrics(df['nat_res_agg'], df['nat_res_agg'], df['gold_ord'])
a_mt_ag,  a_mt_alo,  a_mt_ahi,  a_mt_k,  a_mt_klo,  a_mt_khi  = \
    sens_metrics(df['mt_res_agg'], df['mt_res_agg'], df['gold_ord'])
# Clinician benchmark
cc_ag, cc_alo, cc_ahi, cc_k, cc_klo, cc_khi = \
    sens_metrics(df['cc_lo'], df['cc_hi'], df['gold_ord'])

rows = [
    ('Natural',   'Primary',       'o', C['nat'],  p_nat_ag, p_nat_alo, p_nat_ahi, p_nat_k, p_nat_klo, p_nat_khi),
    ('Natural',   'Conservative',  '^', C['nat'],  c_nat_ag, c_nat_alo, c_nat_ahi, c_nat_k, c_nat_klo, c_nat_khi),
    ('Natural',   'Aggressive',    's', C['nat'],  a_nat_ag, a_nat_alo, a_nat_ahi, a_nat_k, a_nat_klo, a_nat_khi),
    ('Multiturn', 'Primary',       'o', C['mt'],   p_mt_ag,  p_mt_alo,  p_mt_ahi,  p_mt_k,  p_mt_klo,  p_mt_khi),
    ('Multiturn', 'Conservative',  '^', C['mt'],   c_mt_ag,  c_mt_alo,  c_mt_ahi,  c_mt_k,  c_mt_klo,  c_mt_khi),
    ('Multiturn', 'Aggressive',    's', C['mt'],   a_mt_ag,  a_mt_alo,  a_mt_ahi,  a_mt_k,  a_mt_klo,  a_mt_khi),
]
ylabels = ['Natural / Primary', 'Natural / Conservative', 'Natural / Aggressive',
           'Multiturn / Primary', 'Multiturn / Conservative', 'Multiturn / Aggressive']
y_pos = np.arange(len(rows))[::-1]

fig4, axes4 = plt.subplots(1, 2, figsize=(12, 5))
panels = [
    (0, 'Exact Agreement Rate (%)', [(r[4] * 100, r[5], r[6]) for r in rows], cc_ag * 100, cc_alo, cc_ahi),
    (1, "Cohen's Weighted Kappa",   [(r[7], r[8], r[9])       for r in rows], cc_k,    cc_klo,  cc_khi),
]
for pi, (col_i, xlabel, vals, ref_val, ref_lo, ref_hi) in enumerate(panels):
    ax = axes4[pi]
    for i, (cond, res, marker, col, *_) in enumerate(rows):
        yi = y_pos[i]
        est, lo_ci, hi_ci = vals[i]
        if np.isnan(est): continue
        ax.plot([lo_ci, hi_ci], [yi, yi], color=col, linewidth=2, alpha=0.6)
        ax.plot(est, yi, marker=marker, color=col, markersize=9,
                markeredgecolor='white', markeredgewidth=0.8, zorder=5)
    if not np.isnan(ref_val):
        ax.axvline(ref_val, color=C['clin'], linestyle='--', linewidth=1.5,
                   label='Physician benchmark', alpha=0.85)
        ax.axvspan(ref_lo, ref_hi, color=C['clin'], alpha=0.08)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(ylabels if pi == 0 else [''] * 6, fontsize=9)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(('A  ' if pi == 0 else 'B  ') + xlabel, fontsize=11, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    ax.grid(False, axis='y')

leg_elements = [
    Line2D([0], [0], color=C['nat'],  linewidth=2, label='Natural'),
    Line2D([0], [0], color=C['mt'],   linewidth=2, label='Multiturn'),
    Line2D([0], [0], marker='o', color='gray', linestyle='', markersize=8, label='Primary'),
    Line2D([0], [0], marker='^', color='gray', linestyle='', markersize=8, label='Conservative'),
    Line2D([0], [0], marker='s', color='gray', linestyle='', markersize=8, label='Aggressive'),
    Line2D([0], [0], color=C['clin'], linestyle='--', linewidth=1.5, label='Physician benchmark'),
]
fig4.legend(handles=leg_elements, loc='lower center', ncol=3,
            bbox_to_anchor=(0.5, -0.1), frameon=True, fontsize=9)
fig4.tight_layout()
save_fig(fig4, 'figS2_sensitivity_forest', args.output)
