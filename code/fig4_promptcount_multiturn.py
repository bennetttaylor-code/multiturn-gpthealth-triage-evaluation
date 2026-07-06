#!/usr/bin/env python3
"""Figure 4: multiturn prompt count vs. clinical distance from nurse triage
(Spearman correlation with LOESS smoother).

Usage:
    python fig4_promptcount_multiturn.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from scipy.interpolate import interp1d
from statsmodels.nonparametric.smoothers_lowess import lowess
from figlib import apply_style, save_fig, load_data, C

parser = argparse.ArgumentParser(description='Figure 4: prompt count vs. distance (Multiturn)')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: Prompt count vs. distance (Multiturn)...")

sub_pc = df[(~df['mt_count'].isna()) & (~df['mt_dist'].isna())].copy()
x_pc = sub_pc['mt_count'].values.astype(float)
y_pc = sub_pc['mt_dist'].values.astype(float)
rho_pc, p_pc = spearmanr(x_pc, y_pc)
np.random.seed(7)
jit_pc = np.random.uniform(-0.08, 0.08, len(x_pc))

figPC, axPC = plt.subplots(figsize=(9, 5.8))
axPC.scatter(x_pc, y_pc + jit_pc, s=30, c=C['mt'], alpha=0.55,
             edgecolors='white', linewidths=0.4, zorder=3)
if len(x_pc) > 10:
    si = np.argsort(x_pc); xs, ys = x_pc[si], y_pc[si]
    sm = lowess(ys, xs, frac=0.5, return_sorted=True)
    axPC.plot(sm[:, 0], sm[:, 1], color='#C00000', linewidth=2.4, zorder=5,
              label='LOESS smoother')
    boot = []; rngp = np.random.RandomState(3)
    for _ in range(200):
        ib = rngp.randint(0, len(xs), len(xs))
        try:
            s2 = lowess(ys[ib], xs[ib], frac=0.5, return_sorted=True)
            f2 = interp1d(s2[:, 0], s2[:, 1], bounds_error=False, fill_value='extrapolate')
            boot.append(f2(sm[:, 0]))
        except Exception: pass
    if boot:
        boot = np.array(boot)
        axPC.fill_between(sm[:, 0], np.percentile(boot, 2.5, axis=0),
                          np.percentile(boot, 97.5, axis=0),
                          color='#C00000', alpha=0.12, zorder=4)
axPC.set_ylim(-0.3, 3.3); axPC.set_yticks([0, 1, 2, 3])
axPC.set_xlabel('Number of prompts to triage (Multiturn condition)', fontsize=11)
axPC.set_ylabel('Clinical distance from Nurse Triage (steps)', fontsize=11)
axPC.legend(loc='upper right', frameon=True, fontsize=9)
axPC.grid(True, alpha=0.25)
save_fig(figPC, 'fig4_promptcount_multiturn', args.output)
