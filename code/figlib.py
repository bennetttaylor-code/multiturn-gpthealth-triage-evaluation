#!/usr/bin/env python3
"""
Shared data loading, statistical helpers, and plotting style for the
per-figure scripts (fig*.py, figS*.py, table1_descriptives.py,
extended_data_fig1_study_design.py). All figures use range-based scoring,
consistent with analysis.py.

Not a standalone script: imported by the individual figure scripts, each of
which is independently runnable (python code/fig1_direction_by_dataset.py
--input ... --output ...).
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import cohen_kappa_score

# ─── GLOBAL STYLE ────────────────────────────────────────────────────────────
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
LETTERS = ['A', 'B', 'C', 'D']
ORD_MAP = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
ORD_INV = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}


def apply_style():
    """Apply the shared matplotlib rcParams. Call once at the top of each script."""
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


def save_fig(fig, name, fig_dir):
    """Save a figure as both PNG (300 DPI) and PDF into fig_dir."""
    os.makedirs(fig_dir, exist_ok=True)
    png = os.path.join(fig_dir, f'{name}.png')
    pdf = os.path.join(fig_dir, f'{name}.pdf')
    fig.savefig(png, dpi=DPI_PNG, bbox_inches='tight')
    fig.savefig(pdf, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved {name}')


# ─── SCORING HELPERS ──────────────────────────────────────────────────────────
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
    lo, hi, g = np.array(lo, float), np.array(hi, float), np.array(gold, float)
    in_r = (lo <= g) & (g <= hi); below = hi < g
    return np.where(in_r, 0., np.where(below, g - hi, lo - g))


def row_signed(lo, hi, gold):
    lo, hi, g = np.array(lo, float), np.array(hi, float), np.array(gold, float)
    in_r = (lo <= g) & (g <= hi); below = hi < g
    return np.where(in_r, 0., np.where(below, -(g - hi), lo - g))


def oracle_assign(lo, hi, gold):
    lo, hi, g = np.array(lo, float), np.array(hi, float), np.array(gold, float)
    return np.clip(g, lo, hi)


def wilson_ci(k, n):
    if n == 0: return np.nan, np.nan, np.nan
    p = k / n; z = 1.96
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    m = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return p * 100, max(0, c - m) * 100, min(1, c + m) * 100


def wkappa_ci(y1, y2, nboot=500, seed=42):
    mask = (~np.isnan(y1)) & (~np.isnan(y2))
    a, b = y1[mask].astype(int), y2[mask].astype(int)
    if len(a) < 4: return np.nan, np.nan, np.nan
    try: k = cohen_kappa_score(a, b, weights='linear', labels=[0, 1, 2, 3])
    except Exception: return np.nan, np.nan, np.nan
    rng = np.random.RandomState(seed); boots = []; n = len(a)
    for _ in range(nboot):
        idx = rng.randint(0, n, n)
        try: boots.append(cohen_kappa_score(a[idx], b[idx], weights='linear', labels=[0, 1, 2, 3]))
        except Exception: pass
    if len(boots) < 30: return k, np.nan, np.nan
    return k, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def compute_all(lo_s, hi_s, gold_s):
    lo, hi, g = np.array(lo_s, float), np.array(hi_s, float), np.array(gold_s, float)
    mask = ~(np.isnan(lo) | np.isnan(hi) | np.isnan(g))
    lo, hi, g = lo[mask], hi[mask], g[mask]; n = len(lo)
    if n == 0: return None
    in_r = (lo <= g) & (g <= hi); below = hi < g
    dist = np.where(in_r, 0., np.where(below, g - hi, lo - g))
    sgn  = np.where(in_r, 0., np.where(below, -(g - hi), lo - g))
    oracle = np.clip(g, lo, hi)
    k, klo, khi = wkappa_ci(oracle, g)
    n_agree = int(in_r.sum())
    agree_p, alo, ahi = wilson_ci(n_agree, n)
    return dict(n=n, agree_pct=agree_p, agree_lo=alo, agree_hi=ahi,
                dist=dist, sgn=sgn, oracle=oracle, gold=g,
                dist_pcts={i: (dist == i).mean() * 100 for i in range(4)},
                mean_dist=float(dist.mean()), sd_dist=float(dist.std(ddof=1)),
                under_pct=(sgn < 0).mean() * 100, over_pct=(sgn > 0).mean() * 100,
                kappa=k, kappa_lo=klo, kappa_hi=khi)


def resolve_pair(ph, rl, method='cons'):
    out = []
    for p, r in zip(ph, rl):
        if np.isnan(p) or np.isnan(r): out.append(p if not np.isnan(p) else r)
        elif p == r: out.append(p)
        else: out.append(max(p, r) if method == 'cons' else min(p, r))
    return np.array(out, float)


# ─── CHIEF-COMPLAINT CATEGORY MAP ─────────────────────────────────────────────
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


# ─── DATA LOADING ─────────────────────────────────────────────────────────────
class Data:
    """Namespace holding the parsed dataframe and precomputed primary metrics."""
    def __init__(self, df, df_raw, m_nat, m_mt, m_cc):
        self.df, self.df_raw = df, df_raw
        self.m_nat, self.m_mt, self.m_cc = m_nat, m_mt, m_cc


def load_data(input_path):
    """Load and parse the source workbook, mirroring analysis.py's logic.
    Returns a Data namespace with df, df_raw, and primary metrics dicts."""
    print("Loading data...")
    df_raw = pd.read_excel(input_path, sheet_name=0, header=0)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    COL_MAP = {'DATASET':'dataset','Prompt':'prompt','Grader':'grader',
               'Patient Chief Complaint':'complaint','Clinician Adjudication':'cc_raw',
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
    df['nat_dist']    = row_dist(df['nat_lo'], df['nat_hi'], df['gold_ord'])
    df['mt_dist']     = row_dist(df['mt_lo'],  df['mt_hi'],  df['gold_ord'])
    df['nat_signed']  = row_signed(df['nat_lo'], df['nat_hi'], df['gold_ord'])
    df['mt_signed']   = row_signed(df['mt_lo'],  df['mt_hi'],  df['gold_ord'])

    df['nat_res_cons'] = resolve_pair(df['nat_hi'].values, df['nat_rev_hi'].values, 'cons')
    df['nat_res_agg']  = resolve_pair(df['nat_lo'].values, df['nat_rev_lo'].values, 'agg')
    df['mt_res_cons']  = resolve_pair(df['mt_hi'].values,  df['mt_rev_hi'].values,  'cons')
    df['mt_res_agg']   = resolve_pair(df['mt_lo'].values,  df['mt_rev_lo'].values,  'agg')

    m_nat = compute_all(df['nat_lo'], df['nat_hi'], df['gold_ord'])
    m_mt  = compute_all(df['mt_lo'],  df['mt_hi'],  df['gold_ord'])
    m_cc  = compute_all(df['cc_lo'],  df['cc_hi'],  df['gold_ord'])

    print(f"  Loaded {len(df)} rows. Nat={m_nat['agree_pct']:.1f}%, "
          f"MT={m_mt['agree_pct']:.1f}%, ClinAdj={m_cc['agree_pct']:.1f}%")

    df['category'] = df['complaint'].map(COMPLAINT_CAT).fillna('Other/Unclassified')

    return Data(df, df_raw, m_nat, m_mt, m_cc)
