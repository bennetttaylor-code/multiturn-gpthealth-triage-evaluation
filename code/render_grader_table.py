#!/usr/bin/env python3
"""Render the grader-reliability / exclusion-sensitivity supplementary table
(from the 'SUPP - Grader Reliability' sheet of the analysis workbook) into a
publication booktabs-style figure (PNG + PDF), Arial, landscape, two panels.

Usage:
    python render_grader_table.py --input triage_analysis_results.xlsx --output <dir>
"""
import argparse
import openpyxl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('--input', required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--number', default='Supplementary Table 1')   # title number label
a = ap.parse_args()

plt.rcParams.update({'font.family': 'Arial', 'mathtext.fontset': 'custom',
                     'mathtext.it': 'Arial:italic', 'mathtext.rm': 'Arial'})
ws = openpyxl.load_workbook(a.input, data_only=True)['SUPP - Grader Reliability']
rows = [[('' if c is None else str(c)) for c in r] for r in ws.iter_rows(values_only=True)]

def find(pred):
    for i, r in enumerate(rows):
        if pred(r):
            return i
    return -1

# --- per-grader block ---
hgr = find(lambda r: r and r[0] == 'Grader' and len(r) > 2 and r[1] == 'N cases')
ghead = rows[hgr]
def col(name): return ghead.index(name)
grader_rows = [r for r in rows[hgr+1:] if r and r[0] in {'1', '2', '3', '4', '5'}]

# --- group-mean note ---
gm = find(lambda r: r and r[0].startswith('Group means'))
group_note = rows[gm][0] if gm >= 0 else ''

# --- 10b sensitivity block ---
hsen = find(lambda r: r and r[0] == 'Comparison')
shead = rows[hsen]
def scol(name): return shead.index(name)
sen_rows = [r for r in rows[hsen+1:] if r and r[0] and 'vs.' in r[0]]

# ════════════════════════════════════════════════════════════════════════════
PW, PH = 14.0, 8.0
fig = plt.figure(figsize=(PW, PH))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, PW); ax.set_ylim(0, PH); ax.axis('off')

L, R = 0.5, 0.5
y = PH - 0.5
TITLE = f"{a.number}.  Inter-grader reliability and grader-exclusion sensitivity analysis"
ax.text(L, y, TITLE, fontsize=13, fontweight='bold', va='top'); y -= 0.55

# ---------- Panel A ----------
ax.text(L, y, "A   Per-grader reliability vs. each reference standard",
        fontsize=11, fontweight='bold', va='top'); y -= 0.42

# column geometry: Grader, N, then 4 blocks x (Agree, Under, kappa)
xA = L
w_g, w_n, w_m = 0.85, 0.55, 0.78
xs = [xA]
xs.append(xs[-1] + w_g)            # after Grader
xs.append(xs[-1] + w_n)            # after N
for _ in range(12):
    xs.append(xs[-1] + w_m)        # 12 metric columns
right = xs[-1]

blocks = [
    ("Natural · vs Nurse Triage",            ['Nat Agree% (NT)', 'Nat Under% (NT)', 'Nat Kappa (NT)']),
    ("Multiturn · vs Nurse Triage",          ['MT Agree% (NT)',  'MT Under% (NT)',  'MT Kappa (NT)']),
    ("Natural · vs Clin-Adjudicated",        ['Nat Agree% (ClinAdj)', 'Nat Under% (ClinAdj)', 'Nat Kappa (ClinAdj)']),
    ("Multiturn · vs Clin-Adjudicated",      ['MT Agree% (ClinAdj)',  'MT Under% (ClinAdj)',  'MT Kappa (ClinAdj)']),
]

def cx(i):  # center of metric column i (0..11), offset by Grader+N (=2 leading cols)
    j = i + 2
    return (xs[j] + xs[j+1]) / 2

# group super-headers + spanning rules
ytop = y
for b, (label, _) in enumerate(blocks):
    c0 = 2 + b*3
    xl, xr = xs[c0] + 0.04, xs[c0+3] - 0.04
    ax.text((xl+xr)/2, ytop, label, ha='center', va='top', fontsize=8.3, fontweight='bold')
    ax.plot([xl, xr], [ytop-0.20, ytop-0.20], color='black', lw=0.8)
y2 = ytop - 0.30
# sub headers
ax.text(xs[0]+0.05, y2, "Grader", ha='left', va='top', fontsize=8.3, fontweight='bold')
ax.text((xs[1]+xs[2])/2, y2, "N", ha='center', va='top', fontsize=8.3, fontweight='bold')
subs = ['Agree', 'Under', 'κ']
for i in range(12):
    ax.text(cx(i), y2, subs[i % 3], ha='center', va='top', fontsize=8.3, fontweight='bold')
# top & header-bottom rules
ax.plot([L, right], [ytop+0.16, ytop+0.16], color='black', lw=1.3)
ax.plot([L, right], [y2-0.18, y2-0.18], color='black', lw=1.0)

ry = y2 - 0.40
for r in grader_rows:
    flag = r[col('Outlier Flag')] if col('Outlier Flag') < len(r) else ''
    # outlier markers for the four weighted-κ cells (block order: Nat-NT, MT-NT, Nat-CC, MT-CC)
    natNT = '*' if 'Nat κ outlier (NT)' in flag else ''
    mtNT  = '*' if 'MT κ outlier (NT)'  in flag else ''
    natCC = '†' if 'Nat κ outlier (ClinAdj)' in flag else ''
    mtCC  = '†' if 'MT κ outlier (ClinAdj)'  in flag else ''
    kmark = [natNT, mtNT, natCC, mtCC]
    ax.text(xs[0]+0.05, ry, r[0], ha='left', va='top', fontsize=8.2)
    ax.text((xs[1]+xs[2])/2, ry, r[1], ha='center', va='top', fontsize=8.2)
    vals = []
    for _, cols in blocks:
        for cn in cols:
            vals.append(r[col(cn)] if col(cn) < len(r) else '')
    for i, v in enumerate(vals):
        txt = v
        if i % 3 == 2:  # kappa column -> attach marker
            txt = v + kmark[i // 3]
        ax.text(cx(i), ry, txt, ha='center', va='top', fontsize=8.2)
    ax.plot([L, right], [ry-0.10, ry-0.10], color='#d9d9d9', lw=0.3)
    ry -= 0.33
ax.plot([L, right], [ry+0.05, ry+0.05], color='black', lw=1.1)  # bottom rule

# panel-A footnotes
ry -= 0.16
fn = [
    "* Weighted κ >1 SD below the group mean vs nurse triage.   † Weighted κ >1 SD below the group mean vs clinician-adjudicated.",
    "Group-mean weighted κ — vs nurse triage: Natural 0.363 (SD 0.131), Multiturn 0.347 (SD 0.120); vs clinician-adjudicated: Natural 0.370 (SD 0.210), Multiturn 0.311 (SD 0.114).",
    "Grader 5 is a blind self-reviewer (same person as reviewer; Dataset 1, n=14). Agree = exact agreement; Under = under-triage rate; κ = Cohen’s weighted κ. Per-grader mean clinical distance is reported in the analysis workbook.",
]
for line in fn:
    ax.text(L, ry, line, ha='left', va='top', fontsize=7.0, color='#333333')
    ry -= 0.22

# ---------- Panel B ----------
ry -= 0.30
ax.text(L, ry, "B   Primary-endpoint sensitivity excluding the flagged grader (Grader 3)",
        fontsize=11, fontweight='bold', va='top'); ry -= 0.42

# columns
bcols = [
    ("Comparison", 'Comparison', 'left', 3.6),
    ("Agreement\nfull (N=255)", 'Agree% (full N=255)', 'center', 1.5),
    ("Agreement\nexcl. G3 (N=212)", 'Agree% (excl G3 N=212)', 'center', 1.7),
    ("Under-triage\nfull", 'Under-triage% (full)', 'center', 1.9),
    ("P\nfull", 'Under p (full)', 'center', 1.2),
    ("Under-triage\nexcl. G3", 'Under-triage% (excl G3)', 'center', 1.9),
    ("P\nexcl. G3", 'Under p (excl G3)', 'center', 1.2),
]
bx = [L]
for _, _, _, w in bcols:
    bx.append(bx[-1] + w)
bright = bx[-1]

ax.plot([L, bright], [ry+0.16, ry+0.16], color='black', lw=1.3)
for i, (hdr, _, ha, _) in enumerate(bcols):
    xref = bx[i] + 0.05 if ha == 'left' else (bx[i]+bx[i+1])/2
    for li, line in enumerate(hdr.split('\n')):     # italicize the statistical 'P'
        ax.text(xref, ry - li*0.20, line, ha=ha, va='top', fontsize=8.2,
                fontweight='bold', style=('italic' if line == 'P' else 'normal'))
ry -= 0.50
ax.plot([L, bright], [ry+0.06, ry+0.06], color='black', lw=1.0)
ry -= 0.06
for r in sen_rows:
    for i, (_, key, ha, _) in enumerate(bcols):
        v = r[scol(key)] if scol(key) < len(r) else ''
        xref = bx[i] + 0.05 if ha == 'left' else (bx[i]+bx[i+1])/2
        ax.text(xref, ry, v, ha=ha, va='top', fontsize=8.2)
    ry -= 0.30
    ax.plot([L, bright], [ry+0.08, ry+0.08], color='#d9d9d9', lw=0.3)
ax.plot([L, bright], [ry+0.06, ry+0.06], color='black', lw=1.1)
ry -= 0.18
ax.text(L, ry, "Under-triage % and its two-sided exact-binomial $P$ are computed among disagreement cases. "
               "Excluding Grader 3 (N=212) is compared with the full cohort (N=255).",
        ha='left', va='top', fontsize=7.0, color='#333333')

fig.savefig(f"{a.output}/supp_table_grader_reliability.pdf", bbox_inches='tight')
fig.savefig(f"{a.output}/supp_table_grader_reliability.png", dpi=200, bbox_inches='tight')
plt.close(fig)
print(f"Grader reliability table rendered ({len(grader_rows)} graders, {len(sen_rows)} sensitivity rows) "
      f"-> {a.output}/supp_table_grader_reliability.(pdf|png)  [title: {a.number}]")
