#!/usr/bin/env python3
"""Supplementary Figure 1: 4x4 confusion matrices, Natural & Multiturn vs.
both reference standards (oracle assignment for range-valued decisions).

Usage:
    python figS1_confusion_matrices.py --input <xlsx> --output <fig_dir>
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from figlib import apply_style, save_fig, load_data, compute_all, LETTERS

parser = argparse.ArgumentParser(description='Supplementary Figure 1: confusion matrices')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df, m_nat, m_mt = data.df, data.m_nat, data.m_mt

print("Figure: Confusion matrices...")


def build_conf_pct(lo_s, hi_s, gold_s):
    """4x4 matrix of counts; oracle assignment for range values."""
    conf = np.zeros((4, 4), int)
    lo, hi, g = np.array(lo_s, float), np.array(hi_s, float), np.array(gold_s, float)
    for l, h, gg in zip(lo, hi, g):
        if np.isnan(l) or np.isnan(h) or np.isnan(gg): continue
        oracle = int(np.clip(gg, l, h))
        conf[oracle, int(gg)] += 1
    row_pct = np.where(conf.sum(axis=1, keepdims=True) == 0, 0,
                       conf / conf.sum(axis=1, keepdims=True) * 100)
    return conf, row_pct


def draw_conf(ax, conf, pct, title, agree_pct, kappa, ref_label='Nurse Triage'):
    cmap = LinearSegmentedColormap.from_list('blue_white', ['#FFFFFF', '#2E75B6'], N=256)
    ax.imshow(conf, cmap=cmap, aspect='equal', vmin=0, vmax=conf.max() or 1)
    for i in range(4):
        for j in range(4):
            c_val = conf[i, j]
            p_val = pct[i, j]
            txt_color = 'white' if c_val > conf.max() * 0.55 else 'black'
            ax.text(j, i - 0.15, str(c_val),
                    ha='center', va='center', fontsize=11, fontweight='bold', color=txt_color)
            ax.text(j, i + 0.2, f'({p_val:.0f}%)',
                    ha='center', va='center', fontsize=8, color=txt_color)
    for i in range(4):
        rect = plt.Rectangle((i - 0.5, i - 0.5), 1, 1,
                              linewidth=2.5, edgecolor='#FFD700', facecolor='none', zorder=5)
        ax.add_patch(rect)
    for i in range(4):
        for j in range(i + 1, 4):
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                  linewidth=0, facecolor='#4472C4', alpha=0.12, zorder=2)
            ax.add_patch(rect)
    ax.set_xticks(range(4)); ax.set_yticks(range(4))
    ax.set_xticklabels(LETTERS, fontsize=10)
    ax.set_yticklabels(LETTERS, fontsize=10)
    ax.set_xlabel(ref_label, fontsize=10, labelpad=6)
    ax.set_ylabel('Grader Decision', fontsize=10, labelpad=6)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    ax.grid(False)
    kap_str = f"{kappa:.3f}" if not np.isnan(kappa) else 'N/A'
    ax.text(0.5, -0.22,
            f"Exact agreement: {agree_pct:.1f}%    Weighted κ = {kap_str}",
            transform=ax.transAxes, ha='center', fontsize=9,
            style='italic', color='#444444')


conf_nat, pct_nat = build_conf_pct(df['nat_lo'], df['nat_hi'], df['gold_ord'])
conf_mt,  pct_mt  = build_conf_pct(df['mt_lo'],  df['mt_hi'],  df['gold_ord'])
conf_nat_cc, pct_nat_cc = build_conf_pct(df['nat_lo'], df['nat_hi'], df['cc_cons_ord'])
conf_mt_cc,  pct_mt_cc  = build_conf_pct(df['mt_lo'],  df['mt_hi'],  df['cc_cons_ord'])
m_nat_cc_conf = compute_all(df['nat_lo'], df['nat_hi'], df['cc_cons_ord'])
m_mt_cc_conf  = compute_all(df['mt_lo'],  df['mt_hi'],  df['cc_cons_ord'])

figS1, axes_s1 = plt.subplots(2, 2, figsize=(14, 12))
draw_conf(axes_s1[0, 0], conf_nat, pct_nat, 'A  Natural — vs. Nurse Triage',
          m_nat['agree_pct'], m_nat['kappa'], 'Nurse Triage')
draw_conf(axes_s1[0, 1], conf_mt,  pct_mt,  'B  Multiturn — vs. Nurse Triage',
          m_mt['agree_pct'],  m_mt['kappa'],  'Nurse Triage')
draw_conf(axes_s1[1, 0], conf_nat_cc, pct_nat_cc, 'C  Natural — vs. Clinician-Adjudicated',
          m_nat_cc_conf['agree_pct'], m_nat_cc_conf['kappa'], 'Clinician-Adjudicated')
draw_conf(axes_s1[1, 1], conf_mt_cc,  pct_mt_cc,  'D  Multiturn — vs. Clinician-Adjudicated',
          m_mt_cc_conf['agree_pct'],  m_mt_cc_conf['kappa'],  'Clinician-Adjudicated')
leg_patches = [
    Patch(facecolor='#FFD700',              label='Diagonal: exact agreement'),
    Patch(facecolor='#4472C4', alpha=0.35, label='Below diagonal: under-triage'),
]
figS1.legend(handles=leg_patches, loc='lower center', ncol=2,
             bbox_to_anchor=(0.5, -0.02), frameon=True, fontsize=9)
figS1.tight_layout()
save_fig(figS1, 'figS1_confusion_matrices', args.output)
