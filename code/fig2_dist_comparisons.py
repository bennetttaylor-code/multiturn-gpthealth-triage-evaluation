#!/usr/bin/env python3
"""Figure 2: clinical distance-score distributions vs. clinician-adjudicated
and nurse triage reference standards.

Usage:
    python fig2_dist_comparisons.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from figlib import apply_style, save_fig, load_data, compute_all, C

parser = argparse.ArgumentParser(description='Figure 2: distance distributions')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df, m_nat, m_mt = data.df, data.m_nat, data.m_mt

print("Figure 2: Distance distributions (combined)...")

m_nat_cc_gold = compute_all(df['nat_lo'], df['nat_hi'], df['cc_cons_ord'])
m_mt_cc_gold  = compute_all(df['mt_lo'],  df['mt_hi'],  df['cc_cons_ord'])

_dist_labels = ['Exact (0)', 'Minor (1)', 'Moderate (2)', 'Severe (3)']


def draw_dist_panel(ax, groups, title, x_label):
    n_g = len(groups)
    x = np.arange(4)
    width = 0.72 / n_g
    offsets = np.linspace(-(n_g - 1) * width / 2, (n_g - 1) * width / 2, n_g)
    for i, (lbl, dpcts, col) in enumerate(groups):
        vals = [dpcts[k] for k in range(4)]
        bars = ax.bar(x + offsets[i], vals, width=width, color=col,
                      label=lbl, alpha=0.88, edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            if v > 1:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        f'{v:.0f}%', ha='center', va='bottom', fontsize=7.5,
                        color=col, fontweight='bold')
        if i == 0:
            for k, v in enumerate(vals):
                ax.hlines(v, x[k] + offsets[0] - width * 0.5, x[k] + offsets[-1] + width * 0.5,
                          colors=col, linestyles='--', linewidths=1.2, alpha=0.5)
    bracket_y = max(max(g[1][2], g[1][3]) for g in groups) + 6
    ax.annotate('', xy=(x[3] + offsets[-1] + width / 2, bracket_y),
                xytext=(x[2] + offsets[0] - width / 2, bracket_y),
                arrowprops=dict(arrowstyle='-', color='#C00000', lw=1.5))
    ax.text((x[2] + x[3]) / 2, bracket_y + 0.8, '⚠ Safety-concerning',
            ha='center', va='bottom', fontsize=9, color='#C00000', fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(_dist_labels, fontsize=10)
    ax.set_ylabel('Percentage of Cases (%)', fontsize=11)
    ax.set_xlabel(x_label, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', frameon=True)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.2)


fig1_dist, axes_f1 = plt.subplots(1, 2, figsize=(18, 5.5))
draw_dist_panel(
    axes_f1[0],
    groups=[
        ('GPT Natural  (vs. Clinician-Adjudicated)', m_nat_cc_gold['dist_pcts'], C['nat']),
        ('GPT Multiturn  (vs. Clinician-Adjudicated)', m_mt_cc_gold['dist_pcts'], C['mt']),
    ],
    title='A  LLM Distance from Clinician-Adjudicated',
    x_label='Clinical Distance Score (steps from Clinician-Adjudicated)',
)
draw_dist_panel(
    axes_f1[1],
    groups=[
        ('GPT Natural  (vs. Nurse Triage)', m_nat['dist_pcts'], C['nat']),
        ('GPT Multiturn  (vs. Nurse Triage)', m_mt['dist_pcts'], C['mt']),
    ],
    title='B  LLM Distance from Nurse Triage',
    x_label='Clinical Distance Score (steps from Nurse Triage)',
)
fig1_dist.tight_layout()
save_fig(fig1_dist, 'fig2_dist_comparisons', args.output)
