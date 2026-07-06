#!/usr/bin/env python3
"""Supplementary Figure 5: performance heatmap by chief-complaint category.

Usage:
    python figS5_complaint_heatmap.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from figlib import apply_style, save_fig, load_data, compute_all, C

parser = argparse.ArgumentParser(description='Supplementary Figure 5: complaint heatmap')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df = data.df

print("Figure: Category heatmap...")

cat_rows7 = []
for cat in sorted(df['category'].unique()):
    sub = df[df['category'] == cat]
    n   = len(sub)
    mn    = compute_all(sub['nat_lo'], sub['nat_hi'], sub['gold_ord'])
    mm    = compute_all(sub['mt_lo'],  sub['mt_hi'],  sub['gold_ord'])
    mn_cc = compute_all(sub['nat_lo'], sub['nat_hi'], sub['cc_cons_ord'])
    mm_cc = compute_all(sub['mt_lo'],  sub['mt_hi'],  sub['cc_cons_ord'])
    if mn is None or mm is None: continue
    cat_rows7.append({
        'Category': cat, 'n': n,
        'Nat Agree':    mn['agree_pct'],
        'MT Agree':     mm['agree_pct'],
        'Nat Under':    mn['under_pct'],
        'MT Under':     mm['under_pct'],
        'Nat Dist':     mn['mean_dist'],
        'MT Dist':      mm['mean_dist'],
        'Nat Agree ClinAdj': mn_cc['agree_pct'] if mn_cc else np.nan,
        'MT Agree ClinAdj':  mm_cc['agree_pct'] if mm_cc else np.nan,
        'Nat Under ClinAdj': mn_cc['under_pct'] if mn_cc else np.nan,
        'MT Under ClinAdj':  mm_cc['under_pct'] if mm_cc else np.nan,
        'Nat Dist ClinAdj':  mn_cc['mean_dist'] if mn_cc else np.nan,
        'MT Dist ClinAdj':   mm_cc['mean_dist'] if mm_cc else np.nan,
    })

cat_df7 = pd.DataFrame(cat_rows7).sort_values('Nat Under', ascending=False)
cats_sorted = cat_df7['Category'].tolist()

short_names = {
    'Neurological/Neuropsychiatric': 'Neurological/\nNeuropsych',
    'Infectious/Systemic': 'Infectious/\nSystemic',
    'Other/Unclassified': 'Other/\nUnclassified',
}
cat_labels7 = [short_names.get(c, c) for c in cats_sorted]

col_labels7 = ['Agree %\n(Natural)', 'Agree %\n(Multiturn)',
               'Under %\n(Natural)', 'Under %\n(Multiturn)',
               'Mean Dist\n(Natural)', 'Mean Dist\n(Multiturn)']
cmaps7 = [
    LinearSegmentedColormap.from_list('g2w', ['#FFFFFF', '#70AD47'], N=256),
    LinearSegmentedColormap.from_list('g2w', ['#FFFFFF', '#70AD47'], N=256),
    LinearSegmentedColormap.from_list('w2b', ['#FFFFFF', C['under']], N=256),
    LinearSegmentedColormap.from_list('w2b', ['#FFFFFF', C['under']], N=256),
    LinearSegmentedColormap.from_list('w2r', ['#FFFFFF', '#C00000'],  N=256),
    LinearSegmentedColormap.from_list('w2r', ['#FFFFFF', '#C00000'],  N=256),
]
col_ranges7 = [(0, 100), (0, 100), (0, 100), (0, 100), (0, 3), (0, 3)]

n_row7 = len(cats_sorted)
cell_w7, cell_h7 = 1.4, 1.0
n_count7 = cat_df7['n'].tolist()


def draw_hmap(ax, data_, col_labels, cmaps, col_ranges, cat_labels, n_count, subtitle):
    n_row, n_col = data_.shape
    for ci, (cmap, (vmin, vmax)) in enumerate(zip(cmaps, col_ranges)):
        for ri in range(n_row):
            val = data_[ri, ci]
            if np.isnan(val):
                fc = (0.88, 0.88, 0.88, 1.0); lum = 1.0
            else:
                nv = np.clip((val - vmin) / (vmax - vmin), 0, 1)
                fc = cmap(nv)
                lum = 0.299 * fc[0] + 0.587 * fc[1] + 0.114 * fc[2]
            rect = plt.Rectangle((ci * cell_w7, ri * cell_h7), cell_w7, cell_h7,
                                  facecolor=fc, edgecolor='white', linewidth=0.8)
            ax.add_patch(rect)
            tc = 'white' if lum < 0.5 else 'black'
            disp = f'{val:.0f}%' if ci < 4 else f'{val:.2f}'
            ax.text(ci * cell_w7 + cell_w7 / 2, ri * cell_h7 + cell_h7 / 2, disp,
                    ha='center', va='center', fontsize=8.5, color=tc)
    for ri, (lbl, n) in enumerate(zip(cat_labels, n_count)):
        ax.text(-0.2, ri * cell_h7 + cell_h7 * 0.64, lbl, ha='right', va='center', fontsize=9)
        ax.text(-0.2, ri * cell_h7 + cell_h7 * 0.28, f'n={n}',
                ha='right', va='center', fontsize=7.5, color='#555')
    for ci, lbl in enumerate(col_labels):
        ax.text(ci * cell_w7 + cell_w7 / 2, n_row * cell_h7 + 0.25, lbl,
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_xlim(-1.5, n_col * cell_w7 + 0.1)
    ax.set_ylim(-0.3, n_row * cell_h7 + 1.2)
    ax.axis('off')
    ax.set_title(subtitle, fontsize=11, fontweight='bold', pad=8)


metrics7_nt = ['Nat Agree', 'MT Agree', 'Nat Under', 'MT Under', 'Nat Dist', 'MT Dist']
metrics7_cc = ['Nat Agree ClinAdj', 'MT Agree ClinAdj', 'Nat Under ClinAdj',
               'MT Under ClinAdj', 'Nat Dist ClinAdj', 'MT Dist ClinAdj']
data7_nt = cat_df7[metrics7_nt].values
data7_cc = cat_df7[metrics7_cc].values

panel_h = max(6, n_row7 * 0.75 + 2)
fig7, (ax7_nt, ax7_cc) = plt.subplots(2, 1, figsize=(12, panel_h * 2 + 1))
draw_hmap(ax7_nt, data7_nt, col_labels7, cmaps7, col_ranges7, cat_labels7, n_count7,
          'vs. Nurse Triage')
draw_hmap(ax7_cc, data7_cc, col_labels7, cmaps7, col_ranges7, cat_labels7, n_count7,
          'vs. Clinician-Adjudicated')
fig7.tight_layout(h_pad=3.0)
save_fig(fig7, 'figS5_complaint_heatmap', args.output)
