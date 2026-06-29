#!/usr/bin/env python3
"""
Publication-quality figures for triage analysis.
All figures use range-based scoring, consistent with triage_analysis_v2.py.
"""

import argparse
import os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import matplotlib.patheffects as pe
import seaborn as sns
from scipy.stats import spearmanr, norm, binomtest
from scipy.interpolate import interp1d
from statsmodels.nonparametric.smoothers_lowess import lowess
from sklearn.metrics import cohen_kappa_score
warnings.filterwarnings('ignore')

# ─── CLI ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='GPT Triage – Figure Generation')
parser.add_argument('--input',  required=True, help='Path to input Excel file')
parser.add_argument('--output', default='./output', help='Output directory (default: ./output)')
args = parser.parse_args()

RAW_XLS = args.input
FIG_DIR = os.path.join(args.output, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

# ─── GLOBAL STYLE ────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'Arial',
    'font.size':          10,
    'axes.labelsize':     11,
    'axes.titlesize':     12,
    'figure.titlesize':   14,
    'xtick.labelsize':    9,
    'ytick.labelsize':    9,
    'legend.fontsize':    9,
    'legend.framealpha':  0.8,
    'axes.grid':          True,
    'grid.alpha':         0.3,
    'grid.color':         '#cccccc',
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'figure.dpi':         150,
})
DPI_PNG = 300
C = {
    'nat':      '#2E75B6',
    'mt':       '#ED7D31',
    'clin':     '#548235',
    'under':    '#4472C4',
    'over':     '#ED7D31',
    'exact':    '#70AD47',
    'gold_ref': '#7F7F7F',
}
LETTERS   = ['A', 'B', 'C', 'D']
ORD_MAP   = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
ORD_INV   = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
STATUS    = {}   # figure_name → 'OK' or 'SKIPPED: reason'

def save_fig(fig, name):
    png = os.path.join(FIG_DIR, f'{name}.png')
    pdf = os.path.join(FIG_DIR, f'{name}.pdf')
    fig.savefig(png, dpi=DPI_PNG, bbox_inches='tight')
    fig.savefig(pdf, bbox_inches='tight')
    plt.close(fig)
    STATUS[name] = 'OK'
    print(f'  Saved {name}')

# ─── DATA LOADING (mirror of v2 logic) ───────────────────────────────────────
def to_range(val):
    if pd.isna(val): return (np.nan, np.nan)
    v = str(val).strip()
    if v in ORD_MAP: o = ORD_MAP[v]; return (o, o)
    for sep in ['/', '-']:
        if sep in v:
            parts = [p.strip() for p in v.split(sep)]
            if all(p in ORD_MAP for p in parts):
                ords = [ORD_MAP[p] for p in parts]
                return (min(ords), max(ords))
    return (np.nan, np.nan)

def parse_col_range(series):
    parsed = series.apply(to_range)
    return parsed.apply(lambda x: x[0]), parsed.apply(lambda x: x[1])

def row_dist(lo, hi, gold):
    lo, hi, g = np.array(lo,float), np.array(hi,float), np.array(gold,float)
    in_r = (lo<=g)&(g<=hi); below = hi<g
    return np.where(in_r, 0., np.where(below, g-hi, lo-g))

def row_signed(lo, hi, gold):
    lo, hi, g = np.array(lo,float), np.array(hi,float), np.array(gold,float)
    in_r = (lo<=g)&(g<=hi); below = hi<g
    return np.where(in_r, 0., np.where(below, -(g-hi), lo-g))

def oracle_assign(lo, hi, gold):
    lo, hi, g = np.array(lo,float), np.array(hi,float), np.array(gold,float)
    return np.clip(g, lo, hi)

def wilson_ci(k, n):
    if n == 0: return np.nan, np.nan, np.nan
    p = k/n; z = 1.96
    d = 1 + z**2/n
    c = (p + z**2/(2*n))/d
    m = z*np.sqrt(p*(1-p)/n + z**2/(4*n**2))/d
    return p*100, max(0,c-m)*100, min(1,c+m)*100

def wkappa_ci(y1, y2, nboot=500, seed=42):
    mask = (~np.isnan(y1))&(~np.isnan(y2))
    a, b = y1[mask].astype(int), y2[mask].astype(int)
    if len(a)<4: return np.nan, np.nan, np.nan
    try: k = cohen_kappa_score(a, b, weights='linear', labels=[0,1,2,3])
    except: return np.nan, np.nan, np.nan
    rng = np.random.RandomState(seed); boots=[]; n=len(a)
    for _ in range(nboot):
        idx = rng.randint(0,n,n)
        try: boots.append(cohen_kappa_score(a[idx],b[idx],weights='linear',labels=[0,1,2,3]))
        except: pass
    if len(boots)<30: return k, np.nan, np.nan
    return k, float(np.percentile(boots,2.5)), float(np.percentile(boots,97.5))

def compute_all(lo_s, hi_s, gold_s):
    lo,hi,g = np.array(lo_s,float), np.array(hi_s,float), np.array(gold_s,float)
    mask = ~(np.isnan(lo)|np.isnan(hi)|np.isnan(g))
    lo,hi,g = lo[mask],hi[mask],g[mask]; n=len(lo)
    if n==0: return None
    in_r=(lo<=g)&(g<=hi); below=hi<g
    dist = np.where(in_r,0.,np.where(below,g-hi,lo-g))
    sgn  = np.where(in_r,0.,np.where(below,-(g-hi),lo-g))
    oracle = np.clip(g,lo,hi)
    k, klo, khi = wkappa_ci(oracle, g)
    n_agree = int(in_r.sum())
    agree_p, alo, ahi = wilson_ci(n_agree, n)
    return dict(n=n, agree_pct=agree_p, agree_lo=alo, agree_hi=ahi,
                dist=dist, sgn=sgn, oracle=oracle, gold=g,
                dist_pcts={i: (dist==i).mean()*100 for i in range(4)},
                mean_dist=float(dist.mean()), sd_dist=float(dist.std(ddof=1)),
                under_pct=(sgn<0).mean()*100, over_pct=(sgn>0).mean()*100,
                kappa=k, kappa_lo=klo, kappa_hi=khi)

print("Loading data...")
df_raw = pd.read_excel(RAW_XLS, sheet_name=0, header=0)
df_raw.columns = [str(c).strip() for c in df_raw.columns]
COL_MAP = {'DATASET':'dataset','Prompt':'prompt','Grader':'grader',
           'Patient Chief Complaint':'complaint','Clinician Consensus':'cc_raw',
           'GPT Natural Prompt Count':'nat_count',
           'GPT Natural Triage Decision (A-D)':'nat_triage_raw',
           'GPT Natural Reviewer':'nat_reviewer_raw',
           'GPT Multiturn Prompt Count':'mt_count',
           'GPT Multiturn Triage Decision (A-D)':'mt_triage_raw',
           'GPT Multiturn Reviewer':'mt_reviewer_raw'}
df = df_raw.rename(columns=COL_MAP)[list(COL_MAP.values())].copy()
nc = [c for c in df_raw.columns if 'Nurse' in c][0]
df['gold_raw'] = df_raw[nc]
for col in ['cc_raw','nat_triage_raw','nat_reviewer_raw','mt_triage_raw','mt_reviewer_raw','gold_raw']:
    df[col] = df[col].astype(str).str.strip().replace('nan', np.nan)
df.loc[df['nat_reviewer_raw'].isna(), 'nat_reviewer_raw'] = 'C'

df['cc_lo'],      df['cc_hi']      = parse_col_range(df['cc_raw'])
df['nat_lo'],     df['nat_hi']     = parse_col_range(df['nat_triage_raw'])
df['nat_rev_lo'], df['nat_rev_hi'] = parse_col_range(df['nat_reviewer_raw'])
df['mt_lo'],      df['mt_hi']      = parse_col_range(df['mt_triage_raw'])
df['mt_rev_lo'],  df['mt_rev_hi']  = parse_col_range(df['mt_reviewer_raw'])
df['gold_lo'],    df['gold_hi']    = parse_col_range(df['gold_raw'])
df['gold_ord']    = df['gold_hi']
df['nat_ord']     = df['nat_hi']
df['mt_ord']      = df['mt_hi']
df['nat_rev_ord'] = df['nat_rev_hi']
df['mt_rev_ord']  = df['mt_rev_hi']
df['cc_cons_ord'] = df['cc_hi']
df['nat_dist']    = row_dist(df['nat_lo'],df['nat_hi'],df['gold_ord'])
df['mt_dist']     = row_dist(df['mt_lo'], df['mt_hi'], df['gold_ord'])
df['nat_signed']  = row_signed(df['nat_lo'],df['nat_hi'],df['gold_ord'])
df['mt_signed']   = row_signed(df['mt_lo'], df['mt_hi'], df['gold_ord'])

def resolve_pair(ph, rl, method='cons'):
    out=[]
    for p,r in zip(ph,rl):
        if np.isnan(p) or np.isnan(r): out.append(p if not np.isnan(p) else r)
        elif p==r: out.append(p)
        else: out.append(max(p,r) if method=='cons' else min(p,r))
    return np.array(out,float)

df['nat_res_cons'] = resolve_pair(df['nat_hi'].values,df['nat_rev_hi'].values,'cons')
df['nat_res_agg']  = resolve_pair(df['nat_lo'].values,df['nat_rev_lo'].values,'agg')
df['mt_res_cons']  = resolve_pair(df['mt_hi'].values, df['mt_rev_hi'].values,'cons')
df['mt_res_agg']   = resolve_pair(df['mt_lo'].values, df['mt_rev_lo'].values,'agg')

m_nat  = compute_all(df['nat_lo'],df['nat_hi'],df['gold_ord'])
m_mt   = compute_all(df['mt_lo'], df['mt_hi'], df['gold_ord'])
m_cc   = compute_all(df['cc_lo'], df['cc_hi'], df['gold_ord'])

print(f"  Loaded {len(df)} rows. Nat={m_nat['agree_pct']:.1f}%, MT={m_mt['agree_pct']:.1f}%, ClinAdj={m_cc['agree_pct']:.1f}%")

COMPLAINT_CAT = {
    'Abdomen Pain':'Gastrointestinal','Abdominal Pain - Male':'Gastrointestinal',
    'Abdominal Pain - female':'Gastrointestinal','abdominal pain ':'Gastrointestinal',
    'Nausea':'Gastrointestinal','nausea':'Gastrointestinal',
    'Vomiting':'Gastrointestinal','vomiting':'Gastrointestinal',
    'Diarrhea and trouble urinating':'Gastrointestinal','diarrhea':'Gastrointestinal',
    'Rectal bleeding':'Gastrointestinal','rectal symptoms':'Gastrointestinal',
    'Constipation':'Gastrointestinal','constipation ':'Gastrointestinal',
    'Stools - Unusual Color':'Gastrointestinal','Jaundice':'Gastrointestinal',
    'Mild-Moderate abdominal pain (per triage but notes actually say severe pain), constant for > 2 hours ':'Gastrointestinal',
    'Chest Pain':'Cardiovascular','Chest or Rib Pain':'Cardiovascular',
    'Palpitations':'Cardiovascular','Heart Rate and Heartbeat Questions':'Cardiovascular',
    'Blood Pressure - High':'Cardiovascular','High blood pressure':'Cardiovascular',
    'HIGH BLOOD PRESSURE':'Cardiovascular','high blood pressure':'Cardiovascular',
    'Leg Swelling and Edema':'Cardiovascular','leg swelling':'Cardiovascular',
    'leg swellling':'Cardiovascular','Thigh, calf or ankle swelling and only one side':'Cardiovascular',
    'Ankle Swelling':'Cardiovascular','Calf or leg pain, one sided, present 1 hour':'Cardiovascular',
    'Cough':'Respiratory','cough':'Respiratory','Shortness of Breath':'Respiratory',
    'Asthma Attack':'Respiratory','difficulty breathing':'Respiratory',
    'Mild difficulty breathing, new onset, worse than normal ':'Respiratory',
    'Nose Stuffiness or Congestion':'Respiratory',
    'Headache':'Neurological/Neuropsychiatric','headache':'Neurological/Neuropsychiatric',
    'Dizziness':'Neurological/Neuropsychiatric','dizziness':'Neurological/Neuropsychiatric',
    'Loss of Consciousness':'Neurological/Neuropsychiatric',
    'Neurologic Deficit':'Neurological/Neuropsychiatric',
    'Neurologic deficit':'Neurological/Neuropsychiatric',
    'Neurological Deficit':'Neurological/Neuropsychiatric',
    'Muscle Jerks or Twitches':'Neurological/Neuropsychiatric',
    'Depression':'Neurological/Neuropsychiatric','Suicide Concerns':'Neurological/Neuropsychiatric',
    'head injury':'Neurological/Neuropsychiatric',
    'Arm Pain':'Musculoskeletal','Back Pain':'Musculoskeletal','Back pain':'Musculoskeletal',
    'back pain':'Musculoskeletal','back pain ':'Musculoskeletal','Hip Pain':'Musculoskeletal',
    'Knee Pain':'Musculoskeletal','Knee Swelling':'Musculoskeletal','Leg Pain':'Musculoskeletal',
    'Foot Pain':'Musculoskeletal','Foot pain':'Musculoskeletal','Hand Pain':'Musculoskeletal',
    'hand pain':'Musculoskeletal','left hand pain and swelling':'Musculoskeletal',
    'Rib Pain':'Musculoskeletal','rib pain ':'Musculoskeletal','shoulder pain ':'Musculoskeletal',
    'Toe Injury':'Musculoskeletal','toe pain ':'Musculoskeletal','right toe pain ':'Musculoskeletal',
    'groin pain':'Musculoskeletal','neck pain ':'Musculoskeletal','muscle spasms':'Musculoskeletal',
    'Fall':'Musculoskeletal','fall ':'Musculoskeletal',
    'Severe ankle pain not improved 2 hours after medication ':'Musculoskeletal',
    'Severe arm pain and not better after medications and ice ':'Musculoskeletal',
    'Severe back pain, unable to do normal activities, not improved 2 hours after pain meds':'Musculoskeletal',
    'Redness or Rash':'Dermatological','Rash-widespread':'Dermatological','rash':'Dermatological',
    'Skin Blisters':'Dermatological','Skin Lesion - Moles or Growths':'Dermatological',
    'Localized purple or blood colored spots, not from injury or friction and no fever':'Dermatological',
    'Purple or blood colored rash, no fever, user sounds good to triager, drug rash suspected, started new medication ':'Dermatological',
    'Rash - Purple Spots or Dots':'Dermatological','Cold sore':'Dermatological',
    'Face Swelling':'Dermatological','Neck Swelling':'Dermatological',
    'skin growth ':'Dermatological','skin lump':'Dermatological','itching':'Dermatological',
    'Cut or Laceration':'Dermatological','Cuts and Lacerations':'Dermatological',
    'sting':'Dermatological','Eyelid Swelling':'Dermatological',
    'Hematuria':'Genitourinary','Urine - Blood In':'Genitourinary','Urine-blood in':'Genitourinary',
    'blood in urine':'Genitourinary','Urinary symptoms':'Genitourinary',
    'Urination Pain, Female':'Genitourinary','urination pain ':'Genitourinary',
    'Fever':'Infectious/Systemic','Fever >100 AND bedridden':'Infectious/Systemic',
    'Fever >101 AND >60 years old':'Infectious/Systemic','Fever >103':'Infectious/Systemic',
    'Fever of 101F and age 60 ':'Infectious/Systemic','fever':'Infectious/Systemic',
    'High risk patient (>64 years old, diabetes, heart disease, weak immune system) AND flu exposure within 7 days AND cold symptoms':'Infectious/Systemic',
    'High risk patient (>64 years old, diabetes, heart disease, weak immune system) AND symptoms are worsening':'Infectious/Systemic',
    'Fatigue':'Infectious/Systemic','Generalized Weakness':'Infectious/Systemic',
    'Weakness (Generalized) and Fatigue':'Infectious/Systemic','weakness':'Infectious/Systemic',
    'Anaphylaxis':'Infectious/Systemic','Blood sugar problem or diabetes':'Infectious/Systemic',
    'Diabetes - High Blood Sugar':'Infectious/Systemic',
    'blood sugar problem or diabetes':'Infectious/Systemic',
    'diabetes':'Infectious/Systemic','high blood sugar':'Infectious/Systemic',
    'Vaginal Discharge':'OB/GYN','Vaginal Pain or Irritation':'OB/GYN',
    'Vaginal bleeding':'OB/GYN','vaginal bleeding':'OB/GYN',
    'Ear Pain':'Other/Unclassified','Eye - Redness':'Other/Unclassified',
    'Eye Pain':'Other/Unclassified','eye pain':'Other/Unclassified',
    'Sore Throat':'Other/Unclassified','Throat Pain':'Other/Unclassified',
    'sore throat':'Other/Unclassified','Tooth or Gum Pain':'Other/Unclassified',
    'Nosebleed':'Other/Unclassified','earwax problems':'Other/Unclassified',
    'Mouth Pain':'Other/Unclassified','Mouth Symptoms':'Other/Unclassified',
    'mouth sores':'Other/Unclassified','Medication question':'Other/Unclassified',
    'medication refill ':'Other/Unclassified','inhaler refill':'Other/Unclassified',
    'psych referral ':'Other/Unclassified','severe pain after surgery':'Other/Unclassified',
    'post op wound':'Other/Unclassified','wound care':'Other/Unclassified',
    'wound check':'Other/Unclassified',
}
df['category'] = df['complaint'].map(COMPLAINT_CAT).fillna('Other/Unclassified')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: CONFUSION MATRICES
# ═══════════════════════════════════════════════════════════════════════════════
print("\nFigure 1: Confusion matrices...")

def build_conf_pct(lo_s, hi_s, gold_s):
    """4x4 matrix of counts; oracle assignment for range values."""
    conf = np.zeros((4,4), int)
    lo, hi, g = np.array(lo_s,float), np.array(hi_s,float), np.array(gold_s,float)
    for l,h,gg in zip(lo,hi,g):
        if np.isnan(l) or np.isnan(h) or np.isnan(gg): continue
        oracle = int(np.clip(gg,l,h))
        conf[oracle, int(gg)] += 1
    row_pct = np.where(conf.sum(axis=1, keepdims=True)==0, 0,
                       conf / conf.sum(axis=1, keepdims=True) * 100)
    return conf, row_pct

def draw_conf(ax, conf, pct, title, agree_pct, kappa, ref_label='Nurse Triage'):
    n_total = conf.sum()
    cmap = LinearSegmentedColormap.from_list('blue_white', ['#FFFFFF','#2E75B6'], N=256)
    im = ax.imshow(conf, cmap=cmap, aspect='equal', vmin=0, vmax=conf.max() or 1)
    for i in range(4):
        for j in range(4):
            c_val = conf[i, j]
            p_val = pct[i, j]
            txt_color = 'white' if c_val > conf.max()*0.55 else 'black'
            ax.text(j, i-0.15, str(c_val),
                    ha='center', va='center', fontsize=11, fontweight='bold', color=txt_color)
            ax.text(j, i+0.2, f'({p_val:.0f}%)',
                    ha='center', va='center', fontsize=8, color=txt_color)
    for i in range(4):
        rect = plt.Rectangle((i-0.5, i-0.5), 1, 1,
                              linewidth=2.5, edgecolor='#FFD700', facecolor='none', zorder=5)
        ax.add_patch(rect)
    for i in range(4):
        for j in range(i+1, 4):
            rect = plt.Rectangle((j-0.5, i-0.5), 1, 1,
                                  linewidth=0, facecolor=C['under'], alpha=0.12, zorder=2)
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

from matplotlib.patches import Patch
figS1, axes_s1 = plt.subplots(2, 2, figsize=(14, 12))
draw_conf(axes_s1[0,0], conf_nat, pct_nat, 'A  Natural — vs. Nurse Triage',
          m_nat['agree_pct'], m_nat['kappa'], 'Nurse Triage')
draw_conf(axes_s1[0,1], conf_mt,  pct_mt,  'B  Multiturn — vs. Nurse Triage',
          m_mt['agree_pct'],  m_mt['kappa'],  'Nurse Triage')
draw_conf(axes_s1[1,0], conf_nat_cc, pct_nat_cc, 'C  Natural — vs. Clinician-Adjudicated',
          m_nat_cc_conf['agree_pct'], m_nat_cc_conf['kappa'], 'Clinician-Adjudicated')
draw_conf(axes_s1[1,1], conf_mt_cc,  pct_mt_cc,  'D  Multiturn — vs. Clinician-Adjudicated',
          m_mt_cc_conf['agree_pct'],  m_mt_cc_conf['kappa'],  'Clinician-Adjudicated')
leg_patches = [
    Patch(facecolor='#FFD700',              label='Diagonal: exact agreement'),
    Patch(facecolor=C['under'], alpha=0.35, label='Below diagonal: under-triage'),
]
figS1.legend(handles=leg_patches, loc='lower center', ncol=2,
             bbox_to_anchor=(0.5, -0.02), frameon=True, fontsize=9)
figS1.tight_layout()
save_fig(figS1, 'figS1_confusion_matrices')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: CLINICAL DISTANCE DISTRIBUTIONS (combined: vs ClinAdj and vs Nurse Triage)
# ═══════════════════════════════════════════════════════════════════════════════
print("Figure 1: Distance distributions (combined)...")

m_nat_cc_gold = compute_all(df['nat_lo'], df['nat_hi'], df['cc_cons_ord'])
m_mt_cc_gold  = compute_all(df['mt_lo'],  df['mt_hi'],  df['cc_cons_ord'])

_dist_labels = ['Exact (0)', 'Minor (1)', 'Moderate (2)', 'Severe (3)']

def draw_dist_panel(ax, groups, title, x_label):
    n_g = len(groups)
    x = np.arange(4)
    width = 0.72 / n_g
    offsets = np.linspace(-(n_g-1)*width/2, (n_g-1)*width/2, n_g)
    for i, (lbl, dpcts, col) in enumerate(groups):
        vals = [dpcts[k] for k in range(4)]
        bars = ax.bar(x + offsets[i], vals, width=width, color=col,
                      label=lbl, alpha=0.88, edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            if v > 1:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{v:.0f}%', ha='center', va='bottom', fontsize=7.5,
                        color=col, fontweight='bold')
        if i == 0:
            for k, v in enumerate(vals):
                ax.hlines(v, x[k]+offsets[0]-width*0.5, x[k]+offsets[-1]+width*0.5,
                          colors=col, linestyles='--', linewidths=1.2, alpha=0.5)
    bracket_y = max(max(g[1][2], g[1][3]) for g in groups) + 6
    ax.annotate('', xy=(x[3]+offsets[-1]+width/2, bracket_y),
                xytext=(x[2]+offsets[0]-width/2, bracket_y),
                arrowprops=dict(arrowstyle='-', color='#C00000', lw=1.5))
    ax.text((x[2]+x[3])/2, bracket_y+0.8, '⚠ Safety-concerning',
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
save_fig(fig1_dist, 'fig2_dist_comparisons')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3: SENSITIVITY ANALYSIS FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════════════
print("Figure 3: Sensitivity forest plot...")

def sens_metrics(lo_arr, hi_arr, gold_arr):
    lo,hi,g = np.array(lo_arr,float),np.array(hi_arr,float),np.array(gold_arr,float)
    mask = ~(np.isnan(lo)|np.isnan(hi)|np.isnan(g))
    lo,hi,g = lo[mask],hi[mask],g[mask]; n=len(lo)
    in_r=(lo<=g)&(g<=hi)
    na = int(in_r.sum())
    ag_p, ag_lo, ag_hi = wilson_ci(na, n)
    oracle = np.clip(g,lo,hi)
    k,klo,khi = wkappa_ci(oracle, g)
    return ag_p, ag_lo, ag_hi, k, klo, khi

# Primary
p_nat_ag, p_nat_alo, p_nat_ahi, p_nat_k, p_nat_klo, p_nat_khi = \
    sens_metrics(df['nat_lo'],df['nat_hi'],df['gold_ord'])
p_mt_ag,  p_mt_alo,  p_mt_ahi,  p_mt_k,  p_mt_klo,  p_mt_khi  = \
    sens_metrics(df['mt_lo'], df['mt_hi'], df['gold_ord'])
# Conservative
c_nat_ag, c_nat_alo, c_nat_ahi, c_nat_k, c_nat_klo, c_nat_khi = \
    sens_metrics(df['nat_res_cons'],df['nat_res_cons'],df['gold_ord'])
c_mt_ag,  c_mt_alo,  c_mt_ahi,  c_mt_k,  c_mt_klo,  c_mt_khi  = \
    sens_metrics(df['mt_res_cons'], df['mt_res_cons'], df['gold_ord'])
# Aggressive
a_nat_ag, a_nat_alo, a_nat_ahi, a_nat_k, a_nat_klo, a_nat_khi = \
    sens_metrics(df['nat_res_agg'],df['nat_res_agg'],df['gold_ord'])
a_mt_ag,  a_mt_alo,  a_mt_ahi,  a_mt_k,  a_mt_klo,  a_mt_khi  = \
    sens_metrics(df['mt_res_agg'], df['mt_res_agg'], df['gold_ord'])
# Clinician benchmark
cc_ag, cc_alo, cc_ahi, cc_k, cc_klo, cc_khi = \
    sens_metrics(df['cc_lo'],df['cc_hi'],df['gold_ord'])

rows = [
    ('Natural',   'Primary',       'o', C['nat'],  p_nat_ag, p_nat_alo, p_nat_ahi, p_nat_k, p_nat_klo, p_nat_khi),
    ('Natural',   'Conservative',  '^', C['nat'],  c_nat_ag, c_nat_alo, c_nat_ahi, c_nat_k, c_nat_klo, c_nat_khi),
    ('Natural',   'Aggressive',    's', C['nat'],  a_nat_ag, a_nat_alo, a_nat_ahi, a_nat_k, a_nat_klo, a_nat_khi),
    ('Multiturn', 'Primary',       'o', C['mt'],   p_mt_ag,  p_mt_alo,  p_mt_ahi,  p_mt_k,  p_mt_klo,  p_mt_khi),
    ('Multiturn', 'Conservative',  '^', C['mt'],   c_mt_ag,  c_mt_alo,  c_mt_ahi,  c_mt_k,  c_mt_klo,  c_mt_khi),
    ('Multiturn', 'Aggressive',    's', C['mt'],   a_mt_ag,  a_mt_alo,  a_mt_ahi,  a_mt_k,  a_mt_klo,  a_mt_khi),
]
ylabels = ['Natural / Primary','Natural / Conservative','Natural / Aggressive',
           'Multiturn / Primary','Multiturn / Conservative','Multiturn / Aggressive']
y_pos = np.arange(len(rows))[::-1]

fig4, axes4 = plt.subplots(1, 2, figsize=(12, 5))
panels = [
    (0, 'Exact Agreement Rate (%)', [(r[4]*100,r[5],r[6]) for r in rows], cc_ag*100, cc_alo, cc_ahi),
    (1, "Cohen's Weighted Kappa",   [(r[7],r[8],r[9])     for r in rows], cc_k,    cc_klo,  cc_khi),
]
for pi, (col_i, xlabel, vals, ref_val, ref_lo, ref_hi) in enumerate(panels):
    ax = axes4[pi]
    for i, (cond, res, marker, col, *_) in enumerate(rows):
        yi = y_pos[i]
        est, lo_ci, hi_ci = vals[i]
        if np.isnan(est): continue
        ax.plot([lo_ci, hi_ci], [yi,yi], color=col, linewidth=2, alpha=0.6)
        ax.plot(est, yi, marker=marker, color=col, markersize=9,
                markeredgecolor='white', markeredgewidth=0.8, zorder=5)
    # Clinician benchmark line
    if not np.isnan(ref_val):
        ax.axvline(ref_val, color=C['clin'], linestyle='--', linewidth=1.5,
                   label='Physician benchmark', alpha=0.85)
        ax.axvspan(ref_lo, ref_hi, color=C['clin'], alpha=0.08)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(ylabels if pi==0 else ['']*6, fontsize=9)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(('A  ' if pi==0 else 'B  ') + xlabel, fontsize=11, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    ax.grid(False, axis='y')

# Legend
from matplotlib.lines import Line2D
leg_elements = [
    Line2D([0],[0], color=C['nat'],  linewidth=2, label='Natural'),
    Line2D([0],[0], color=C['mt'],   linewidth=2, label='Multiturn'),
    Line2D([0],[0], marker='o', color='gray', linestyle='', markersize=8, label='Primary'),
    Line2D([0],[0], marker='^', color='gray', linestyle='', markersize=8, label='Conservative'),
    Line2D([0],[0], marker='s', color='gray', linestyle='', markersize=8, label='Aggressive'),
    Line2D([0],[0], color=C['clin'],linestyle='--',linewidth=1.5,label='Physician benchmark'),
]
fig4.legend(handles=leg_elements, loc='lower center', ncol=3,
            bbox_to_anchor=(0.5,-0.1), frameon=True, fontsize=9)
fig4.tight_layout()
save_fig(fig4, 'figS2_sensitivity_forest')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2: TRIAGE DECISION DIRECTION BY DATASET
# Three side-by-side panels; 100% stacked bars: Under-triage / Correct / Over-triage
# ═══════════════════════════════════════════════════════════════════════════════
print("Figure 2: Triage direction by dataset...")

dataset_titles = {
    1: 'Clinically-Authored\nVignettes (CAVs)',
    2: 'Emergency\nDepartment',
    3: 'Nurse Triage',
}
dataset_order = [1, 2, 3]

COL_UNDER   = '#ED7D31'   # orange
COL_CORRECT = '#595959'   # dark gray
COL_OVER    = '#4472C4'   # blue

def dir_breakdown(sgn_arr):
    s = np.array(sgn_arr, float)
    s = s[~np.isnan(s)]
    n = len(s)
    if n == 0: return dict(pct=(0.0, 0.0, 0.0), cnt=(0, 0, 0))
    cu, cc, co = int((s < 0).sum()), int((s == 0).sum()), int((s > 0).sum())
    return dict(pct=(cu/n*100, cc/n*100, co/n*100), cnt=(cu, cc, co))

# Each row = dict(pct=(under,correct,over), cnt=(...)) of all valid cases (NT then ClinAdj)
panel_data = {}
for ds in dataset_order:
    sub = df[df['dataset'] == ds]
    nat_sgn_cc = row_signed(sub['nat_lo'], sub['nat_hi'], sub['cc_cons_ord'])
    mt_sgn_cc  = row_signed(sub['mt_lo'],  sub['mt_hi'],  sub['cc_cons_ord'])
    rows_ds = [
        dir_breakdown(sub['nat_signed'].values),
        dir_breakdown(sub['mt_signed'].values),
        dir_breakdown(nat_sgn_cc),
        dir_breakdown(mt_sgn_cc),
    ]
    panel_data[ds] = dict(n=len(sub), rows=rows_ds)

y_pos_b   = np.array([0, 1, 2.3, 3.3])
ylabels_b = ['Natural', 'Multiturn', 'Natural', 'Multiturn']
XMAX = 126

fig2, axes2 = plt.subplots(1, 3, figsize=(20, 6), sharex=True)
for pi, ds in enumerate(dataset_order):
    ax = axes2[pi]
    d  = panel_data[ds]
    ax.axhspan(-0.55, 1.55, color='#E8F0F8', alpha=0.6, zorder=0)
    ax.axhspan(1.75,  3.85, color='#EAF4E5', alpha=0.6, zorder=0)
    ax.axhline(1.65, color='#AAAAAA', linewidth=0.8, linestyle='-', zorder=1)
    for row, yp in zip(d['rows'], y_pos_b):
        left = 0.0
        for val, cnt, col in zip(row['pct'], row['cnt'],
                                 [COL_UNDER, COL_CORRECT, COL_OVER]):
            ax.barh(yp, val, left=left, color=col, alpha=0.92,
                    edgecolor='white', height=0.62, zorder=3)
            xc = left + val/2
            if val >= 8:
                # Label inside the segment: % (white) with n underneath (light gray)
                ax.text(xc, yp + 0.11, f'{val:.0f}%', ha='center', va='center',
                        fontsize=8, color='white', fontweight='bold', zorder=4)
                ax.text(xc, yp - 0.13, f'({cnt})', ha='center', va='center',
                        fontsize=6.5, color='#E8E8E8', zorder=4)
            elif val > 0:
                # Thin segment: label above the bar so it remains visible
                ax.text(xc, yp + 0.42, f'{val:.0f}%', ha='center', va='bottom',
                        fontsize=7, color='#555555', fontweight='bold', zorder=4)
                ax.text(xc, yp + 0.41, f'({cnt})', ha='center', va='top',
                        fontsize=6, color='#999999', zorder=4)
            left += val
    # Group labels inside the shaded bands (right of the 100% bars)
    ax.text(113, 0.5, 'vs. Nurse\nTriage', ha='center', va='center',
            fontsize=8.5, color='#2E75B6', fontweight='bold', linespacing=1.4, zorder=4)
    ax.text(113, 2.8, 'vs. Clinician-\nAdjudicated', ha='center', va='center',
            fontsize=8.5, color=C['clin'], fontweight='bold', linespacing=1.4, zorder=4)
    ax.set_yticks(y_pos_b)
    ax.set_yticklabels(ylabels_b if pi == 0 else [''] * 4, fontsize=9)
    ax.set_xlim(0, XMAX)
    ax.set_ylim(-0.6, 3.9)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel('% of Cases', fontsize=9)
    ax.set_title(f"{dataset_titles[ds]}\n(n={d['n']})", fontsize=11, fontweight='bold')
    ax.grid(False)

patches2 = [mpatches.Patch(color=COL_UNDER,   label='Under-triage'),
            mpatches.Patch(color=COL_CORRECT, label='Correct'),
            mpatches.Patch(color=COL_OVER,    label='Over-triage')]
fig2.legend(handles=patches2, loc='lower center', ncol=3,
            bbox_to_anchor=(0.5, -0.04), frameon=True, fontsize=9)
fig2.tight_layout()
save_fig(fig2, 'fig1_direction_by_dataset')

# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLEMENTARY FIGURE 5: TRIAGE DECISION DIRECTION BY DATASET, STRATIFIED BY A–D LEVEL
# 3 dataset panels; 4 groups (condition × reference); each group split A→D (A top)
# 100% stacked bars: Under-triage / Correct / Over-triage; strata by each case's
# own reference level (Nurse Triage for NT rows, Clinician-Adjudicated for ClinAdj rows)
# ═══════════════════════════════════════════════════════════════════════════════
print("Supplementary Figure 5: Triage direction by dataset, stratified by A–D level...")

dataset_titles = {
    1: 'Clinically-Authored\nVignettes (CAVs)',
    2: 'Emergency\nDepartment',
    3: 'Nurse Triage',
}
dataset_order = [1, 2, 3]

COL_UNDER   = '#ED7D31'   # orange
COL_CORRECT = '#595959'   # dark gray
COL_OVER    = '#4472C4'   # blue
BAND_NT     = '#E8F0F8'   # light blue  (vs. Nurse Triage groups)
BAND_CC     = '#EAF4E5'   # light green (vs. Clinician-Adjudicated groups)

# Groups in top→bottom order: (condition label, ref label, cond key, ref ord col, ref code)
group_defs = [
    ('Natural',   'vs. Nurse\nTriage',        'nat', 'gold_ord',    'NT'),
    ('Multiturn', 'vs. Nurse\nTriage',        'mt',  'gold_ord',    'NT'),
    ('Natural',   'vs. Clinician-\nAdjudicated', 'nat', 'cc_cons_ord', 'ClinAdj'),
    ('Multiturn', 'vs. Clinician-\nAdjudicated', 'mt',  'cc_cons_ord', 'ClinAdj'),
]

def level_breakdown(sub, cond_key, ref_col, level_ord):
    """Under/correct/over breakdown for one condition among cases whose reference
    acuity == level_ord."""
    sgn = row_signed(sub[f'{cond_key}_lo'], sub[f'{cond_key}_hi'], sub[ref_col])
    ref = np.array(sub[ref_col], float)
    s   = np.array(sgn, float)
    m   = (ref == level_ord) & ~np.isnan(s)
    s   = s[m]
    n   = len(s)
    if n == 0: return dict(pct=(0.0, 0.0, 0.0), cnt=(0, 0, 0), n=0)
    cu, cc, co = int((s < 0).sum()), int((s == 0).sum()), int((s > 0).sum())
    return dict(pct=(cu/n*100, cc/n*100, co/n*100), cnt=(cu, cc, co), n=n)

# Row layout: y positions top→bottom, with a gap between the 4 groups
ROW_H, GROUP_GAP = 1.0, 0.9
row_layout = []     # (y, group_idx, level_idx, level_letter)
group_bands = []    # (y_lo, y_hi, cond_lbl, ref_lbl, ref_code)
yc = 0.0
for gi, (cond_lbl, ref_lbl, cond_key, ref_col, ref_code) in enumerate(group_defs):
    ys = []
    for li, lvl in enumerate(LETTERS):          # A,B,C,D  (A first = top)
        row_layout.append((yc, gi, li, lvl))
        ys.append(yc)
        yc -= ROW_H
    group_bands.append((min(ys) - 0.5, max(ys) + 0.5, cond_lbl, ref_lbl, ref_code))
    yc -= GROUP_GAP
y_bottom = yc + GROUP_GAP   # last decrement was an unused trailing gap

# Precompute breakdowns per dataset
panel_data = {}
for ds in dataset_order:
    sub = df[df['dataset'] == ds]
    cells = {}
    for (yv, gi, li, lvl) in row_layout:
        cond_lbl, ref_lbl, cond_key, ref_col, ref_code = group_defs[gi]
        cells[(gi, li)] = level_breakdown(sub, cond_key, ref_col, li)
    panel_data[ds] = dict(n=len(sub), cells=cells)

XMAX = 132
fig2b, axes2b = plt.subplots(1, 3, figsize=(21, 13), sharex=True)
for pi, ds in enumerate(dataset_order):
    ax = axes2b[pi]
    d  = panel_data[ds]
    # Group background bands
    for (y_lo, y_hi, cond_lbl, ref_lbl, ref_code) in group_bands:
        ax.axhspan(y_lo, y_hi, color=(BAND_NT if ref_code == 'NT' else BAND_CC),
                   alpha=0.6, zorder=0)
    # Bars
    for (yv, gi, li, lvl) in row_layout:
        cell = d['cells'][(gi, li)]
        if cell['n'] == 0:
            ax.text(2, yv, 'n = 0', ha='left', va='center',
                    fontsize=7, color='#AAAAAA', style='italic', zorder=4)
            continue
        left = 0.0
        for val, cnt, col in zip(cell['pct'], cell['cnt'],
                                 [COL_UNDER, COL_CORRECT, COL_OVER]):
            ax.barh(yv, val, left=left, color=col, alpha=0.92,
                    edgecolor='white', height=0.66, zorder=3)
            xc = left + val/2
            if val >= 8:
                ax.text(xc, yv + 0.12, f'{val:.0f}%', ha='center', va='center',
                        fontsize=7.5, color='white', fontweight='bold', zorder=4)
                ax.text(xc, yv - 0.15, f'({cnt})', ha='center', va='center',
                        fontsize=6, color='#E8E8E8', zorder=4)
            elif val > 0:
                ax.text(xc, yv + 0.44, f'{val:.0f}%', ha='center', va='bottom',
                        fontsize=6.5, color='#555555', fontweight='bold', zorder=4)
                ax.text(xc, yv + 0.43, f'({cnt})', ha='center', va='top',
                        fontsize=5.5, color='#999999', zorder=4)
            left += val
    # Group labels inside the shaded bands (right of the 100% bars), rightmost panel
    if pi == 2:
        for (y_lo, y_hi, cond_lbl, ref_lbl, ref_code) in group_bands:
            yc_mid = (y_lo + y_hi) / 2
            col_g  = '#2E75B6' if ref_code == 'NT' else C['clin']
            ax.text(115, yc_mid, f'{cond_lbl}\n{ref_lbl}', ha='center', va='center',
                    fontsize=8, color=col_g, fontweight='bold',
                    linespacing=1.3, zorder=4)
    ax.set_yticks([yv for (yv, gi, li, lvl) in row_layout])
    ax.set_yticklabels([lvl for (yv, gi, li, lvl) in row_layout] if pi == 0
                       else [''] * len(row_layout), fontsize=8.5, fontweight='bold')
    ax.set_xlim(0, XMAX)
    ax.set_ylim(y_bottom - 0.5, 0.9)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel('% of Cases', fontsize=9)
    ax.set_title(f"{dataset_titles[ds]}\n(n={d['n']})", fontsize=11, fontweight='bold')
    ax.grid(False)
    if pi == 0:
        ax.set_ylabel('Reference Triage Level (A = least urgent → D = most urgent)',
                      fontsize=9)

patches2b = [mpatches.Patch(color=COL_UNDER,   label='Under-triage'),
             mpatches.Patch(color=COL_CORRECT, label='Correct'),
             mpatches.Patch(color=COL_OVER,    label='Over-triage')]
fig2b.legend(handles=patches2b, loc='lower center', ncol=3,
             bbox_to_anchor=(0.5, -0.02), frameon=True, fontsize=9)
fig2b.tight_layout()
save_fig(fig2b, 'figS3_triage_direction_by_level')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 5: CHIEF COMPLAINT CATEGORY HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════
print("Figure 5: Category heatmap...")

cat_rows7 = []
for cat in sorted(df['category'].unique()):
    sub = df[df['category']==cat]
    n   = len(sub)
    mn    = compute_all(sub['nat_lo'],sub['nat_hi'],sub['gold_ord'])
    mm    = compute_all(sub['mt_lo'], sub['mt_hi'], sub['gold_ord'])
    mn_cc = compute_all(sub['nat_lo'],sub['nat_hi'],sub['cc_cons_ord'])
    mm_cc = compute_all(sub['mt_lo'], sub['mt_hi'], sub['cc_cons_ord'])
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

col_labels7 = ['Agree %\n(Natural)','Agree %\n(Multiturn)',
               'Under %\n(Natural)','Under %\n(Multiturn)',
               'Mean Dist\n(Natural)','Mean Dist\n(Multiturn)']
cmaps7 = [
    LinearSegmentedColormap.from_list('g2w', ['#FFFFFF','#70AD47'], N=256),
    LinearSegmentedColormap.from_list('g2w', ['#FFFFFF','#70AD47'], N=256),
    LinearSegmentedColormap.from_list('w2b', ['#FFFFFF', C['under']], N=256),
    LinearSegmentedColormap.from_list('w2b', ['#FFFFFF', C['under']], N=256),
    LinearSegmentedColormap.from_list('w2r', ['#FFFFFF','#C00000'],  N=256),
    LinearSegmentedColormap.from_list('w2r', ['#FFFFFF','#C00000'],  N=256),
]
col_ranges7 = [(0,100),(0,100),(0,100),(0,100),(0,3),(0,3)]

n_row7 = len(cats_sorted)
n_col7 = 6
cell_w7, cell_h7 = 1.4, 1.0
n_count7 = cat_df7['n'].tolist()

def draw_hmap(ax, data, col_labels, cmaps, col_ranges, cat_labels, n_count, subtitle):
    n_row, n_col = data.shape
    for ci, (cmap, (vmin, vmax)) in enumerate(zip(cmaps, col_ranges)):
        for ri in range(n_row):
            val = data[ri, ci]
            if np.isnan(val):
                fc = (0.88, 0.88, 0.88, 1.0); lum = 1.0
            else:
                nv = np.clip((val - vmin) / (vmax - vmin), 0, 1)
                fc = cmap(nv)
                lum = 0.299*fc[0]+0.587*fc[1]+0.114*fc[2]
            rect = plt.Rectangle((ci*cell_w7, ri*cell_h7), cell_w7, cell_h7,
                                  facecolor=fc, edgecolor='white', linewidth=0.8)
            ax.add_patch(rect)
            tc = 'white' if lum < 0.5 else 'black'
            disp = f'{val:.0f}%' if ci < 4 else f'{val:.2f}'
            ax.text(ci*cell_w7 + cell_w7/2, ri*cell_h7 + cell_h7/2, disp,
                    ha='center', va='center', fontsize=8.5, color=tc)
    for ri, (lbl, n) in enumerate(zip(cat_labels, n_count)):
        ax.text(-0.2, ri*cell_h7 + cell_h7*0.64, lbl, ha='right', va='center', fontsize=9)
        ax.text(-0.2, ri*cell_h7 + cell_h7*0.28, f'n={n}',
                ha='right', va='center', fontsize=7.5, color='#555')
    for ci, lbl in enumerate(col_labels):
        ax.text(ci*cell_w7 + cell_w7/2, n_row*cell_h7 + 0.25, lbl,
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_xlim(-1.5, n_col*cell_w7 + 0.1)
    ax.set_ylim(-0.3, n_row*cell_h7 + 1.2)
    ax.axis('off')
    ax.set_title(subtitle, fontsize=11, fontweight='bold', pad=8)

metrics7_nt = ['Nat Agree','MT Agree','Nat Under','MT Under','Nat Dist','MT Dist']
metrics7_cc = ['Nat Agree ClinAdj','MT Agree ClinAdj','Nat Under ClinAdj','MT Under ClinAdj','Nat Dist ClinAdj','MT Dist ClinAdj']
data7_nt = cat_df7[metrics7_nt].values
data7_cc = cat_df7[metrics7_cc].values

panel_h = max(6, n_row7*0.75+2)
fig7, (ax7_nt, ax7_cc) = plt.subplots(2, 1, figsize=(12, panel_h*2 + 1))
draw_hmap(ax7_nt, data7_nt, col_labels7, cmaps7, col_ranges7, cat_labels7, n_count7,
          'vs. Nurse Triage')
draw_hmap(ax7_cc, data7_cc, col_labels7, cmaps7, col_ranges7, cat_labels7, n_count7,
          'vs. Clinician-Adjudicated')
fig7.tight_layout(h_pad=3.0)
save_fig(fig7, 'figS5_complaint_heatmap')

# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLEMENTARY FIGURE 4: PROMPT COUNT VS. DISTANCE (NT and ClinAdj)
# ═══════════════════════════════════════════════════════════════════════════════
print("Supplementary Figure 4: Prompt count scatter...")

df['nat_dist_cc_sc'] = row_dist(df['nat_lo'], df['nat_hi'], df['cc_cons_ord'])
df['mt_dist_cc_sc']  = row_dist(df['mt_lo'],  df['mt_hi'],  df['cc_cons_ord'])

triage_colors = {0:'#4DAF4A', 1:'#377EB8', 2:'#FF7F00', 3:'#E41A1C'}
triage_labels  = {0:'A (non-urgent)', 1:'B (semi-urgent)', 2:'C (urgent)', 3:'D (emergent)'}

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
        ax_s.plot(sm[:,0], sm[:,1], color='#555555', linewidth=2.2, zorder=5, label='LOESS smoother')
        boot_sm = []
        rng_s4 = np.random.RandomState(0)
        for _ in range(100):
            idx_b = rng_s4.randint(0, len(xs), len(xs))
            try:
                s2 = lowess(ys[idx_b], xs[idx_b], frac=0.4, return_sorted=True)
                f  = interp1d(s2[:,0], s2[:,1], bounds_error=False, fill_value='extrapolate')
                boot_sm.append(f(sm[:,0]))
            except: pass
        if boot_sm:
            boot_sm = np.array(boot_sm)
            ax_s.fill_between(sm[:,0], np.percentile(boot_sm,2.5,axis=0),
                              np.percentile(boot_sm,97.5,axis=0),
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

# Group labels in the gap between the two GridSpec blocks
fig_s4.text(0.5, 0.915, 'vs. Nurse Triage', ha='center', fontsize=12,
            fontweight='bold', color='#2E75B6')
fig_s4.text(0.5, 0.468, 'vs. Clinician-Adjudicated', ha='center', fontsize=12,
            fontweight='bold', color=C['clin'])

save_fig(fig_s4, 'figS4_promptcount')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 7: CLINICIAN CONSENSUS vs. NURSE TRIAGE AGREEMENT MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
print("Figure 7: ClinAdj vs. Nurse Triage confusion matrix...")

valid_10 = (~df['cc_cons_ord'].isna()) & (~df['gold_ord'].isna())
cc_v10   = df.loc[valid_10, 'cc_cons_ord'].astype(int).values
nu_v10   = df.loc[valid_10, 'gold_ord'].astype(int).values
N10      = int(valid_10.sum())

conf10 = np.zeros((4, 4), dtype=int)
for ci, ni in zip(cc_v10, nu_v10):
    conf10[ci, ni] += 1
row_tots10 = conf10.sum(axis=1)
col_tots10 = conf10.sum(axis=0)

C10_AGREE = '#70AD47'
C10_CCOVR = '#4472C4'
C10_NUHGH = '#ED7D31'
C10_TOT   = '#D9D9D9'
C10_GRAND = '#ABABAB'
C10_HDNU  = '#2E75B6'
C10_HDCC  = '#548235'
C10_HDOTH = '#808080'
TW = '#FFFFFF'
TB = '#1A1A1A'
AF10 = dict(fontfamily='Arial', fontweight='bold')

fig10 = plt.figure(figsize=(9, 10))
ax10  = fig10.add_subplot(111)
ax10.axis('off')
ax10.set_xlim(-2.1, 5.6)
ax10.set_ylim(-1.6, 6.1)
ax10.set_aspect('equal')

def _dc(x, y, w=1.0, h=1.0, fc='white', lw=2.0):
    ax10.add_patch(mpatches.Rectangle(
        (x, y), w, h, facecolor=fc, edgecolor='white', linewidth=lw, zorder=2))

def _dt(x, y, w, h, lines):
    for txt, fs, col, dy in lines:
        ax10.text(x+w/2, y+h/2+dy, txt, ha='center', va='center',
                  fontsize=fs, color=col, zorder=5, **AF10)

for i in range(4):
    for j in range(4):
        count = conf10[i, j]
        pct   = count / N10 * 100
        yp    = 3 - i
        fc    = C10_AGREE if i == j else (C10_CCOVR if i > j else C10_NUHGH)
        _dc(j, yp, fc=fc)
        _dt(j, yp, 1, 1, [(str(count),      16, TW,  0.16),
                            (f'({pct:.0f}%)',  9, TW, -0.17)])

for i in range(4):
    yp = 3 - i
    _dc(4, yp, fc=C10_TOT)
    _dt(4, yp, 1, 1, [(str(row_tots10[i]), 14, TB, 0)])

for j in range(4):
    _dc(j, -1, fc=C10_TOT)
    _dt(j, -1, 1, 1, [(str(col_tots10[j]), 14, TB, 0)])

_dc(4, -1, fc=C10_GRAND)
_dt(4, -1, 1, 1, [(f'N={N10}', 12, TB, 0)])

for j, ltr in enumerate(LETTERS):
    _dc(j, 4, h=0.85, fc=C10_HDNU)
    _dt(j, 4, 1, 0.85, [(ltr, 15, TW, 0)])

for i, ltr in enumerate(LETTERS):
    yp = 3 - i
    _dc(-1, yp, w=0.9, fc=C10_HDCC)
    _dt(-1, yp, 0.9, 1, [(ltr, 15, TW, 0)])

_dc(4, 4, w=1.0, h=0.85, fc=C10_HDOTH)
_dt(4, 4, 1.0, 0.85, [('Total', 11, TW, 0)])
_dc(-1, -1, w=0.9, h=1.0, fc=C10_HDOTH)
_dt(-1, -1, 0.9, 1.0, [('Total', 11, TW, 0)])

ax10.text(2.0, 5.15, 'Nurse Triage Decision',
          ha='center', va='center', fontsize=15, color=TB, **AF10)
ax10.text(-1.65, 1.5, 'Clinician-Adjudicated',
          ha='center', va='center', fontsize=15, color=TB, rotation=90, **AF10)
leg10_patches = [
    mpatches.Patch(facecolor=C10_AGREE, label='Exact agreement  (ClinAdj = Nurse)'),
    mpatches.Patch(facecolor=C10_CCOVR, label='Clinician over-triage  (ClinAdj > Nurse)'),
    mpatches.Patch(facecolor=C10_NUHGH, label='Nurse higher acuity  (Nurse > ClinAdj)'),
]
leg10 = ax10.legend(handles=leg10_patches,
                    loc='lower center',
                    bbox_to_anchor=(0.5, -0.18),
                    bbox_transform=ax10.transAxes,
                    ncol=1, frameon=True, framealpha=0.95,
                    prop={'family': 'Arial', 'weight': 'bold', 'size': 11},
                    handlelength=1.8, handleheight=1.3,
                    borderpad=0.9, labelspacing=0.45)
save_fig(fig10, 'figS6_cc_vs_nurse_confusion')

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 1: CASE CHARACTERISTICS BY DATASET (rendered as a publication image)
# ═══════════════════════════════════════════════════════════════════════════════
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
ROW_H   = 1.0

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
import textwrap as _tw
axT1.text(0, bot_rule - 0.5, '\n'.join(_tw.wrap(t1_foot, 135)),
          ha='left', va='top', fontsize=7.8, fontfamily=SERIF, color='#333333')
save_fig(figT1, 'table1_descriptives')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE: CLINICIAN CONSENSUS vs. NURSE TRIAGE CONCORDANCE (category-difference dist.)
# ═══════════════════════════════════════════════════════════════════════════════
print("Figure: ClinAdj vs. Nurse Triage concordance distribution...")

_cc = np.array(df['cc_cons_ord'], float); _nu = np.array(df['gold_ord'], float)
_m  = ~np.isnan(_cc) & ~np.isnan(_nu)
_diff = np.abs(_cc[_m] - _nu[_m]).astype(int)
N_cc = int(_m.sum())
cnts = [int((_diff == d).sum()) for d in range(4)]
pcts = [c / N_cc * 100 for c in cnts]

figCC, axCC = plt.subplots(figsize=(8.5, 5.6))
bar_cols = ['#70AD47', '#FFC000', '#ED7D31', '#C00000']
barsCC = axCC.bar(range(4), pcts, color=bar_cols, edgecolor='white', width=0.7, zorder=3)
for i, (c, p) in enumerate(zip(cnts, pcts)):
    axCC.text(i, p + 1.2, f'{p:.1f}%\n(n={c})', ha='center', va='bottom',
              fontsize=10, fontweight='bold', color='#333333')
axCC.set_xticks(range(4))
axCC.set_xticklabels(['0\nExact agreement', '1', '2', '3'], fontsize=10)
axCC.set_xlabel('Triage categories apart  (Clinician-Adjudicated − Nurse Triage)', fontsize=11)
axCC.set_ylabel('Percentage of cases (%)', fontsize=11)
axCC.set_ylim(0, max(pcts) * 1.25)
axCC.grid(True, axis='y', alpha=0.3, zorder=0)
save_fig(figCC, 'fig3_cc_concordance')

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE: PROMPT COUNT vs. CLINICAL DISTANCE (Multiturn condition)
# ═══════════════════════════════════════════════════════════════════════════════
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
save_fig(figPC, 'fig4_promptcount_multiturn')

# ═══════════════════════════════════════════════════════════════════════════════
# EXTENDED DATA FIGURE 1: STUDY DESIGN & ANALYSIS WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════
print("Extended Data Figure 1: study design & analysis workflow...")
import textwrap as _twed
from matplotlib.patches import FancyBboxPatch

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
save_fig(fig_ed, 'extended_data_fig1_study_design')

# ─── FIGURE INDEX ─────────────────────────────────────────────────────────────
index_lines = [
    "FIGURE INDEX — Triage Analysis Publication Figures",
    "="*60,
    "",
    "MAIN FIGURES",
    "-"*40,
    "fig1_direction_by_dataset.png/pdf",
    "  Figure 1: Under-triage / correct / over-triage by interaction condition and dataset.",
    "fig2_dist_comparisons.png/pdf",
    "  Figure 2: Clinical distance-score distributions vs. clinician-adjudicated and nurse triage.",
    "fig3_cc_concordance.png/pdf",
    "  Figure 3: Concordance between clinician-adjudicated and nurse-triage standards",
    "  (distribution of category differences).",
    "fig4_promptcount_multiturn.png/pdf",
    "  Figure 4: Multiturn prompt count vs. clinical distance from nurse triage (Spearman).",
    "",
    "TABLE",
    "-"*40,
    "table1_descriptives.png/pdf",
    "  Table 1: Case characteristics by dataset (booktabs style).",
    "",
    "EXTENDED DATA",
    "-"*40,
    "extended_data_fig1_study_design.png/pdf",
    "  Extended Data Figure 1: Study design and analysis workflow.",
    "",
    "SUPPLEMENTARY FIGURES",
    "-"*40,
    "figS1_confusion_matrices.png/pdf",
    "  Supplementary Figure 1: 4×4 confusion matrices, Natural & Multiturn vs. both references.",
    "figS2_sensitivity_forest.png/pdf",
    "  Supplementary Figure 2: Sensitivity forest (primary/conservative/aggressive resolution).",
    "figS3_triage_direction_by_level.png/pdf",
    "  Supplementary Figure 3: Under/correct/over stratified by reference triage level (A–D).",
    "figS4_promptcount.png/pdf",
    "  Supplementary Figure 4: Prompt count vs. distance scatter (all conditions × references).",
    "figS5_complaint_heatmap.png/pdf",
    "  Supplementary Figure 5: Performance heatmap by chief-complaint category.",
    "figS6_cc_vs_nurse_confusion.png/pdf",
    "  Supplementary Figure 6: Clinician-adjudicated vs. nurse-triage agreement matrix.",
    "",
    "="*60,
    "RENDER STATUS:",
]
for name, status in STATUS.items():
    index_lines.append(f"  {name}: {status}")

idx_path = os.path.join(FIG_DIR, 'figure_index.txt')
with open(idx_path, 'w') as f:
    f.write('\n'.join(index_lines))
print(f"\nFigure index saved: {idx_path}")

# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("FIGURE GENERATION COMPLETE")
print("="*55)
for name, status in STATUS.items():
    icon = '✓' if status == 'OK' else '✗'
    print(f"  {icon} {name}: {status}")
print(f"\nAll files saved to: {FIG_DIR}")
