#!/usr/bin/env python3
"""Table 1: case characteristics by dataset, rendered as a publication image
(booktabs style).

Usage:
    python table1_descriptives.py --input <xlsx> --output <fig_dir>
"""
import argparse
import textwrap as _tw
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from figlib import apply_style, save_fig, load_data, ORD_INV

parser = argparse.ArgumentParser(description='Table 1: case characteristics by dataset')
parser.add_argument('--input', required=True, help='Path to input Excel file')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()
data = load_data(args.input)
df, df_raw = data.df, data.df_raw

print("Table 1: Case characteristics by dataset...")


def _t1_pctn(x, n): return f"{int(x)} ({x/n*100:.0f}%)" if n > 0 else '—'


def _t1_med_iqr(s):
    a = np.array(s, float); a = a[~np.isnan(a)]
    if len(a) == 0: return '—'
    return f"{np.median(a):.0f} [{np.percentile(a,25):.0f}–{np.percentile(a,75):.0f}]"


def build_table1(df, df_raw):
    grp = [('CAVs',           df[df['dataset'] == 1]),
           ('Emergency Dept', df[df['dataset'] == 2]),
           ('Nurse Triage',   df[df['dataset'] == 3]),
           ('Overall',        df)]
    subs    = [g[1] for g in grp]
    headers = [f"{g[0]}\n(n={len(g[1])})" for g in grp]
    rows = []  # (label, is_header, [vals])
    def row(label, fn): rows.append((label, False, [fn(s) for s in subs]))
    def hdr(label):     rows.append((label, True, ['', '', '', '']))
    row('Cases, n',            lambda s: f"{len(s)}")
    hdr('Nurse Triage acuity, n (%)')
    for k in [0, 1, 2, 3]:
        row(f'    {ORD_INV[k]}', lambda s, k=k: _t1_pctn((s['gold_ord'] == k).sum(), len(s)))
    hdr('Clinician-Adjudicated acuity, n (%)')
    for k in [0, 1, 2, 3]:
        row(f'    {ORD_INV[k]}', lambda s, k=k: _t1_pctn((s['cc_cons_ord'] == k).sum(), len(s)))
    hdr('Chief complaint category, n (%)')
    for c in df['category'].value_counts().index.tolist():
        row(f'    {c}', lambda s, c=c: _t1_pctn((s['category'] == c).sum(), len(s)))
    hdr('Prompts to triage, median [IQR]')
    row('    Natural condition',   lambda s: _t1_med_iqr(s['nat_count']))
    row('    Multiturn condition', lambda s: _t1_med_iqr(s['mt_count']))
    ed  = df_raw[df_raw['DATASET'] == 2]
    age = pd.to_numeric(ed['Age'], errors='coerce').dropna()
    sex = ed['Gender'].astype(str).str.strip()
    nF, nM = int((sex == 'F').sum()), int((sex == 'M').sum()); ns = nF + nM
    foot = ("Age and sex were recorded only for the Emergency Department subset (n=76): "
            f"age mean {age.mean():.0f} years (SD {age.std():.0f}; range {age.min():.0f}–{age.max():.0f}); "
            f"sex {nF} female ({nF/ns*100:.0f}%), {nM} male ({nM/ns*100:.0f}%). "
            "Age and sex were not collected for the Clinically-Authored Vignettes or Nurse-Triage datasets.")
    return headers, rows, foot


t1_headers, t1_rows, t1_foot = build_table1(df, df_raw)
n_t1 = len(t1_rows)

# Scientific journal (booktabs) style: horizontal rules only, no shading/vertical lines
SERIF = 'Arial'
x_lab   = 0.005                          # left edge for the Characteristic column
x_cols  = [0.515, 0.655, 0.795, 0.935]   # centres of the 4 value columns

figT1, axT1 = plt.subplots(figsize=(10.5, 0.40 * n_t1 + 2.2))
axT1.axis('off')
axT1.set_xlim(0, 1.0)

y_header = n_t1 + 0.4
y_data0  = n_t1 - 1                       # y of first data row
y_last   = 0
top_rule = y_header + 1.15
hdr_rule = y_header - 0.55
bot_rule = y_last - 0.55
axT1.set_ylim(bot_rule - 2.6, top_rule + 1.4)


def _rule(y, lw):
    axT1.plot([0, 1.0], [y, y], color='black', linewidth=lw,
              solid_capstyle='butt', clip_on=False, zorder=5)


# Title
axT1.text(0, top_rule + 0.55,
          'Table 1.  Case characteristics by dataset (N = 255)',
          ha='left', va='bottom', fontsize=13, fontweight='bold', fontfamily=SERIF)

# Rules + header
_rule(top_rule, 1.6)
axT1.text(x_lab, y_header, 'Characteristic', ha='left', va='center',
          fontsize=9.5, fontweight='bold', fontfamily=SERIF)
for ci, h in enumerate(t1_headers):
    axT1.text(x_cols[ci], y_header, h, ha='center', va='center',
              fontsize=8.8, fontweight='bold', fontfamily=SERIF, linespacing=1.05)
_rule(hdr_rule, 1.0)

# Body
for ri, (label, is_h, vals) in enumerate(t1_rows):
    y = y_data0 - ri
    if is_h:
        axT1.text(x_lab, y, label, ha='left', va='center', fontsize=9.3,
                  fontweight='bold', fontfamily=SERIF)
    else:
        disp   = label.strip()
        indent = 0.028 if label.startswith('    ') else 0.0
        axT1.text(x_lab + indent, y, disp, ha='left', va='center',
                  fontsize=9, fontfamily=SERIF)
        for ci, v in enumerate(vals):
            axT1.text(x_cols[ci], y, v, ha='center', va='center',
                      fontsize=9, fontfamily=SERIF)

_rule(bot_rule, 1.6)

# Footnote
axT1.text(0, bot_rule - 0.5, '\n'.join(_tw.wrap(t1_foot, 135)),
          ha='left', va='top', fontsize=7.8, fontfamily=SERIF, color='#333333')
save_fig(figT1, 'table1_descriptives', args.output)
