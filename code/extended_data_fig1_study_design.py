#!/usr/bin/env python3
"""Extended Data Figure 1: study design and analysis workflow (illustrative
diagram; does not depend on the source dataset's contents).

Usage:
    python extended_data_fig1_study_design.py --input <xlsx> --output <fig_dir>
"""
import argparse
import textwrap as _twed
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from figlib import apply_style, save_fig

parser = argparse.ArgumentParser(description='Extended Data Figure 1: study design')
parser.add_argument('--input', required=True, help='Path to input Excel file (unused; accepted for CLI uniformity)')
parser.add_argument('--output', required=True, help='Output directory for the figure')
args = parser.parse_args()

apply_style()

print("Extended Data Figure 1: study design & analysis workflow...")

FILL, EDGE, ARROW = '#E8EAF6', '#5C6BC0', '#9FA8DA'
TFS, BFS, DFS = 12.5, 11.0, 10.0
LH, TB, PT, PB, RGAP = 0.50, 0.70, 0.36, 0.36, 1.15
XL0, XL1 = 0.4, 11.6           # full-width box
HL0, HL1 = 0.4, 5.6            # left half
HR0, HR1 = 6.4, 11.6           # right half
CPI = 11                       # ~chars per x-unit

# box = (title, [(text, kind)]);  kind '' = normal, 'dim' = small grey note
A = ("Evaluation dataset (n = 255)", [
    ("39 standardized patient-language vignettes — 21 clinical domains (Ramaswamy et al., 2026)", ''),
    ("76 community emergency department encounters", ''),
    ("140 nurse-line encounters — Schmitt–Thompson protocols", '')])
B = ("Triage-disposition scale (A–D)", [
    ("A: home care", ''), ("B: seek provider > 24 h", ''),
    ("C: seek care within 24 h", ''), ("D: emergency department now", ''),
    ("Under-triage = safety-critical error direction", 'dim')])
Cb = ("ChatGPT Health (CGPTH) evaluation — two conditions", [
    ("Natural conversational: single-sentence complaint; converse until first explicit triage recommendation", ''),
    ("Multi-turn: same cases; model asks one question at a time before deciding", ''),
    ("Standard consumer app · no custom prompts · history cleared between cases · 5 Mar – 21 May 2026", 'dim')])
Db = ("Independent grading on the A–D scale", [
    ("5 graders, non-overlapping sets", ''),
    ("G1 n = 78 (postdoctoral fellow)", ''),
    ("G2 n = 62 · G3 n = 43 · G5 n = 14 (medical students) · G4 n = 58 (undergraduate)", ''),
    ("Grader 5: blind independent reviewer of CGPTH triage decisions", '')])
Eb = ("Reference standards (applied to all 255 cases)", [
    ("Clinician-adjudicated: Dataset 1 NYC physician panel · Dataset 2 attending EM · Dataset 3 medical director", ''),
    ("Nurse triage (Schmitt–Thompson): graders for Datasets 1–2; contemporaneous protocol for Dataset 3", '')])
Fb = ("Primary outcomes", [
    ("Exact agreement rate · Cohen's weighted κ", ''),
    ("Under- / over-triage asymmetry", ''),
    ("Mean clinical distance · safety-critical under-triage (≥ 2)", '')])
Gb = ("Secondary outcomes", [
    ("Grader–reviewer discordance sensitivity (conservative / aggressive)", ''),
    ("Subgroup by dataset & chief complaint", ''),
    ("Prompt count vs. clinical distance", '')])
Hb = ("Statistical analysis", [
    ("Exact (Clopper–Pearson) 95% CIs · bootstrapped weighted κ", ''),
    ("Wilcoxon signed-rank (ordinal distance) · McNemar's test (exact agreement)", ''),
    ("Two-sided exact binomial safety test · Spearman (prompt count) · χ² / Mann–Whitney (generalization)", ''),
    ("Two-sided α = 0.05 · Bonferroni α = 0.025 across the two reference standards", 'dim')])


def _wrap_box(box, width_units):
    title, lines = box
    cw = int(width_units * CPI)
    out = []
    for txt, kind in lines:
        for sub in (_twed.wrap(txt, cw) or ['']):
            out.append((sub, kind))
    return title, out, PT + TB + len(out) * LH + PB


rows = [('pair', A, B), ('single', Cb), ('single', Db), ('single', Eb),
        ('pair', Fb, Gb), ('single', Hb)]
laid = []
for r in rows:
    if r[0] == 'single':
        laid.append(('single', _wrap_box(r[1], XL1 - XL0)))
    else:
        wl, wr = _wrap_box(r[1], HL1 - HL0), _wrap_box(r[2], HR1 - HR0)
        laid.append(('pair', wl, wr, max(wl[2], wr[2])))
total_h = sum((row[3] if row[0] == 'pair' else row[1][2]) for row in laid) + RGAP * (len(laid) - 1)

fig_ed = plt.figure(figsize=(12, 0.56 * total_h + 1.0))
ax_ed = fig_ed.add_axes([0, 0, 1, 1]); ax_ed.set_xlim(0, 12)
ax_ed.set_ylim(-0.3, total_h + 0.3); ax_ed.axis('off')


def _draw_box(x0, x1, ytop, title, sublines, h):
    ax_ed.add_patch(FancyBboxPatch((x0, ytop - h), x1 - x0, h,
        boxstyle="round,pad=0,rounding_size=0.16", linewidth=1.6,
        edgecolor=EDGE, facecolor=FILL, zorder=2))
    cx = (x0 + x1) / 2
    ax_ed.text(cx, ytop - PT, title, ha='center', va='top', fontsize=TFS, fontweight='bold', zorder=3)
    yy = ytop - PT - TB
    for sub, kind in sublines:
        ax_ed.text(cx, yy, sub, ha='center', va='top',
                   fontsize=(DFS if kind == 'dim' else BFS),
                   color=('#555555' if kind == 'dim' else '#1a1a1a'), zorder=3)
        yy -= LH


def _arrow(x0, y0, x1, y1):
    ax_ed.annotate('', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='-|>', color=ARROW, lw=3.0,
                        shrinkA=2, shrinkB=0, mutation_scale=26), zorder=1)


y = total_h; centers = []
for row in laid:
    if row[0] == 'single':
        title, subs, h = row[1]
        _draw_box(XL0, XL1, y, title, subs, h)
        centers.append({'t': 'single', 'cx': (XL0 + XL1) / 2, 'top': y, 'bot': y - h})
        y -= h + RGAP
    else:
        _, (tl, sl, _hl), (tr, sr, _hr), h = row
        _draw_box(HL0, HL1, y, tl, sl, h)
        _draw_box(HR0, HR1, y, tr, sr, h)
        centers.append({'t': 'pair', 'lcx': (HL0 + HL1) / 2, 'rcx': (HR0 + HR1) / 2, 'top': y, 'bot': y - h})
        y -= h + RGAP

for cu, nx in zip(centers, centers[1:]):
    if cu['t'] == 'single' and nx['t'] == 'single':
        _arrow(cu['cx'], cu['bot'], nx['cx'], nx['top'])
    elif cu['t'] == 'pair' and nx['t'] == 'single':                 # converge
        _arrow(cu['lcx'], cu['bot'], nx['cx'], nx['top'])
        _arrow(cu['rcx'], cu['bot'], nx['cx'], nx['top'])
    elif cu['t'] == 'single' and nx['t'] == 'pair':                 # diverge
        _arrow(cu['cx'], cu['bot'], nx['lcx'], nx['top'])
        _arrow(cu['cx'], cu['bot'], nx['rcx'], nx['top'])

save_fig(fig_ed, 'extended_data_fig1_study_design', args.output)
