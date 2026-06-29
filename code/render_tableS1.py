#!/usr/bin/env python3
"""Render Extended Data Table 1 (prompt derivation) from its xlsx into a
paginated, Arial, booktabs-style multi-page PDF (+ page-1 PNG preview).

Usage:
    python render_tableS1.py --input tableS1_prompt_derivation.xlsx --output <dir>
"""
import argparse, textwrap
import openpyxl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ap = argparse.ArgumentParser()
ap.add_argument('--input', required=True)
ap.add_argument('--output', required=True)
a = ap.parse_args()

plt.rcParams.update({'font.family': 'Arial'})
ws = openpyxl.load_workbook(a.input, data_only=True).active
rows = list(ws.iter_rows(values_only=True))
subtitle = str(rows[1][0])                       # descriptive subtitle
header = [('' if c is None else str(c)) for c in rows[2]]
body = rows[3:]

TITLE = "Extended Data Table 1.  " + subtitle

# layout (landscape)
PW, PH = 14.0, 9.0
L, R, TOP, BOT = 0.45, 0.45, 0.55, 0.45
usable_w = PW - L - R
col_frac = [0.045, 0.05, 0.205, 0.34, 0.36]
colw = [f * usable_w for f in col_frac]
colx = [L]
for w in colw:
    colx.append(colx[-1] + w)
wrap_chars = [7, 6, 46, 82, 86]
FS = 6.5
LINE_H = 0.135

def wrap_cell(text, n):
    out = []
    for para in str(text).split('\n'):
        out += textwrap.wrap(para, n) or ['']
    return out

def measure(r):
    filled = [i for i, c in enumerate(r) if c not in (None, '')]
    if filled == [0]:                            # full-width dataset note
        lines = wrap_cell(r[0], 150)
        return ('note', [lines], len(lines) * LINE_H + 0.12)
    cells = [wrap_cell('' if i >= len(r) or r[i] is None else r[i], wrap_chars[i]) for i in range(5)]
    nl = max(len(c) for c in cells)
    return ('data', cells, nl * LINE_H + 0.10)

pdf = PdfPages(f"{a.output}/extended_data_table1_prompt_derivation.pdf")
first_fig = [None]

def start_page(first=False):
    fig = plt.figure(figsize=(PW, PH))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, PW); ax.set_ylim(0, PH); ax.axis('off')
    y = PH - TOP
    if first:
        ax.text(L, y, TITLE, fontsize=11, fontweight='bold', va='top')
        y -= 0.42
        first_fig[0] = fig
    for i in range(5):
        ax.text(colx[i] + 0.05, y, header[i].replace('\n', ' '), fontsize=7.2,
                fontweight='bold', va='top')
    ax.plot([L, PW - R], [y - 0.30, y - 0.30], color='black', lw=1.1)
    return fig, ax, y - 0.42

fig, ax, y = start_page(first=True)
for r in body:
    kind, cells, h = measure(r)
    if y - h < BOT:
        pdf.savefig(fig);
        if fig is not first_fig[0]: plt.close(fig)
        fig, ax, y = start_page(first=False)
    if kind == 'note':
        ax.text(L + 0.05, y, '\n'.join(cells[0]), fontsize=6.8, style='italic',
                color='#333333', va='top', linespacing=1.05)
    else:
        for i in range(5):
            ha = 'center' if i in (0, 1) else 'left'
            xref = (colx[i] + colx[i+1]) / 2 if ha == 'center' else colx[i] + 0.05
            ax.text(xref, y, '\n'.join(cells[i]), fontsize=FS, va='top', ha=ha, linespacing=1.0)
    y -= h
    ax.plot([L, PW - R], [y + 0.02, y + 0.02], color='#cfcfcf', lw=0.3)
pdf.savefig(fig)
# page-1 PNG preview
first_fig[0].savefig(f"{a.output}/extended_data_table1_prompt_derivation.png", dpi=200, bbox_inches='tight')
plt.close('all'); pdf.close()
print(f"Extended Data Table 1 rendered ({len(body)} rows) -> {a.output}/extended_data_table1_prompt_derivation.pdf (+ page-1 PNG)")
