"""
MEDIC NEMSIS Preprocessing Script v3
Outputs: distributions.json

Run:
    pip install pandas tqdm numpy
    python preprocess_nemsis.py
"""

import pandas as pd
import numpy as np
import json
import os
from collections import Counter
from tqdm import tqdm

DATA_DIR    = "/Users/thesilentreaper/Documents/Projects/EMS/data/nemsis_extract"
OUTPUT_PATH = "/Users/thesilentreaper/Documents/Projects/EMS/data/distributions.json"
CHUNKSIZE   = 100_000
SEP         = "~|~"
TOP_N       = 50

SAMPLE_VITALS   = 5_000_000
SAMPLE_MEDS     = 2_000_000
SAMPLE_PROCS    = 2_000_000
SAMPLE_SYMPTOMS = 2_000_000
SAMPLE_LARGE    = 2_000_000

NULL_CODES = {"7701001", "7701003", "7701005", "Not Recorded", "Not Applicable", "Unknown", ""}

def clean(val):
    return str(val).strip().strip("'").strip('"').strip("~")

def is_null(val):
    if pd.isna(val):
        return True
    return clean(val) in NULL_CODES

def read_chunks(filename, usecols=None, nrows=None, encoding="utf-8"):
    path = os.path.join(DATA_DIR, filename)
    return pd.read_csv(
        path, sep=SEP, engine="python", dtype=str,
        usecols=usecols, chunksize=CHUNKSIZE, nrows=nrows,
        on_bad_lines="skip", encoding=encoding, encoding_errors="replace"
    )

def normalize_cols(chunk):
    chunk.columns = [clean(c) for c in chunk.columns]
    return chunk

def vectorized_count(chunk, col, counter):
    if col not in chunk.columns:
        return
    vals = chunk[col].apply(lambda x: clean(x) if not is_null(x) else None).dropna()
    counter.update(vals.tolist())

def vectorized_numeric(series):
    cleaned = series.apply(lambda x: clean(x) if not is_null(x) else np.nan)
    return pd.to_numeric(cleaned, errors="coerce").dropna()

def load_ref(filename, code_col, desc_col, encoding="utf-8"):
    mapping = {}
    try:
        df = pd.read_csv(
            os.path.join(DATA_DIR, filename),
            sep=SEP, engine="python", dtype=str,
            encoding=encoding, encoding_errors="replace"
        )
        df.columns = [clean(c) for c in df.columns]
        for _, row in df.iterrows():
            code = clean(row.get(code_col, ""))
            desc = clean(row.get(desc_col, ""))
            if code and desc and code not in NULL_CODES:
                mapping[code] = desc
    except Exception as e:
        print(f"  Warning: {filename} failed: {e}")
    return mapping

def decode_top(counter, ref_map, n=TOP_N):
    result = {}
    for code, count in counter.most_common(n * 3):
        name = ref_map.get(code)
        if name and name not in NULL_CODES:
            result[name] = count
        if len(result) >= n:
            break
    return result

# 1. Pub_PCRevents — age, dispatch, chief complaint, location, acuity
print("\n[1/11] Pub_PCRevents...")

age_values            = []
dispatch_counter      = Counter()
situation_07_counter  = Counter()
situation_08_counter  = Counter()
location_counter      = Counter()
acuity_counter        = Counter()
final_acuity_counter  = Counter()

target_cols = {
    "ePatient_15", "eDispatch_01", "eSituation_07",
    "eSituation_08", "eScene_09", "eSituation_13", "eDisposition_19"
}

for chunk in tqdm(read_chunks("Pub_PCRevents.txt",
        usecols=lambda c: clean(c) in target_cols)):
    chunk = normalize_cols(chunk)
    if "ePatient_15" in chunk.columns:
        age_values.extend(vectorized_numeric(chunk["ePatient_15"]).tolist())
    vectorized_count(chunk, "eDispatch_01",    dispatch_counter)
    vectorized_count(chunk, "eSituation_07",   situation_07_counter)
    vectorized_count(chunk, "eSituation_08",   situation_08_counter)
    vectorized_count(chunk, "eScene_09",       location_counter)
    vectorized_count(chunk, "eSituation_13",   acuity_counter)
    vectorized_count(chunk, "eDisposition_19", final_acuity_counter)

age_arr = np.array([a for a in age_values if 0 < a <= 120])
age_dist = {
    "p5":  float(np.percentile(age_arr, 5)),
    "p25": float(np.percentile(age_arr, 25)),
    "p50": float(np.percentile(age_arr, 50)),
    "p75": float(np.percentile(age_arr, 75)),
    "p95": float(np.percentile(age_arr, 95)),
}
print(f"  Age: {age_dist}")
print(f"  Top 5 dispatch: {dispatch_counter.most_common(5)}")
print(f"  Top 5 locations: {location_counter.most_common(5)}")

# 2. FACTPCRVITAL — vitals distributions
print(f"\n[2/11] FACTPCRVITAL (sampling {SAMPLE_VITALS:,} rows)...")

vital_cols_map = {
    "eVitals_06": "sbp",
    "eVitals_10": "hr",
    "eVitals_12": "spo2",
    "eVitals_14": "rr",
    "eVitals_18": "glucose",
    "eVitals_26": "avpu",
    "eVitals_27": "pain",
}

vital_clips = {
    "sbp":     (40, 300),
    "hr":      (10, 300),
    "spo2":    (50, 100),
    "rr":      (2, 80),
    "glucose": (10, 800),
    "pain":    (0, 10),
}

vital_values  = {v: [] for v in vital_cols_map.values() if v not in ("avpu", "pain")}
avpu_counter  = Counter()
pain_values   = []

for chunk in tqdm(read_chunks("FACTPCRVITAL.txt",
        usecols=lambda c: clean(c) in vital_cols_map,
        nrows=SAMPLE_VITALS)):
    chunk = normalize_cols(chunk)
    for nemsis_col, field in vital_cols_map.items():
        if nemsis_col not in chunk.columns:
            continue
        if field == "avpu":
            vectorized_count(chunk, nemsis_col, avpu_counter)
        elif field == "pain":
            pain_values.extend(vectorized_numeric(chunk[nemsis_col]).tolist())
        else:
            vital_values[field].extend(vectorized_numeric(chunk[nemsis_col]).tolist())

vital_distributions = {}
for field, vals in vital_values.items():
    if not vals:
        continue
    arr = np.array(vals)
    lo, hi = vital_clips.get(field, (arr.min(), arr.max()))
    arr = arr[(arr >= lo) & (arr <= hi)]
    if len(arr) == 0:
        continue
    vital_distributions[field] = {
        "p5":  float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }

if pain_values:
    arr = np.array(pain_values)
    arr = arr[(arr >= 0) & (arr <= 10)]
    vital_distributions["pain"] = {
        "p5":  float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "min": 0.0,
        "max": 10.0,
    }

print(f"  Vitals extracted: {list(vital_distributions.keys())}")
print(f"  AVPU top 5: {avpu_counter.most_common(5)}")

# 3. FACTPCRMEDICATION — drug names, routes, doses
print(f"\n[3/11] FACTPCRMEDICATION (sampling {SAMPLE_MEDS:,} rows)...")

med_name_counter  = Counter()
med_route_counter = Counter()
med_unit_counter  = Counter()
med_doses_by_drug = {}

target_med_cols = {"eMedications_03Descr", "eMedications_05", "eMedications_06", "eMedications_07"}

for chunk in tqdm(read_chunks("FACTPCRMEDICATION.txt",
        usecols=lambda c: clean(c) in target_med_cols,
        nrows=SAMPLE_MEDS)):
    chunk = normalize_cols(chunk)
    vectorized_count(chunk, "eMedications_03Descr", med_name_counter)
    vectorized_count(chunk, "eMedications_07",      med_route_counter)
    vectorized_count(chunk, "eMedications_06",      med_unit_counter)

    if "eMedications_03Descr" in chunk.columns and "eMedications_05" in chunk.columns:
        sub = chunk[["eMedications_03Descr", "eMedications_05"]].copy()
        sub.columns = ["drug", "dose"]
        sub = sub[~sub["drug"].apply(is_null) & ~sub["dose"].apply(is_null)]
        sub["drug"] = sub["drug"].apply(clean)
        sub["dose"] = pd.to_numeric(sub["dose"].apply(clean), errors="coerce")
        sub = sub.dropna()
        for drug, grp in sub.groupby("drug"):
            if drug not in med_doses_by_drug:
                med_doses_by_drug[drug] = []
            if len(med_doses_by_drug[drug]) < 5000:
                med_doses_by_drug[drug].extend(grp["dose"].tolist())

top_meds = [d for d, _ in med_name_counter.most_common(TOP_N)]
med_median_doses = {
    drug: float(np.median(med_doses_by_drug[drug]))
    for drug in top_meds
    if drug in med_doses_by_drug and med_doses_by_drug[drug]
}

print(f"  Top 5 meds: {med_name_counter.most_common(5)}")

# 4. FACTPCRPRIMARYIMPRESSION
print("\n[4/11] FACTPCRPRIMARYIMPRESSION...")

impression_counter = Counter()
for chunk in tqdm(read_chunks("FACTPCRPRIMARYIMPRESSION.txt",
        usecols=lambda c: clean(c) == "eSituation_11")):
    chunk = normalize_cols(chunk)
    vectorized_count(chunk, "eSituation_11", impression_counter)

print(f"  Top 5 impressions (raw): {impression_counter.most_common(5)}")

# 5. FACTPCRSECONDARYIMPRESSION
print("\n[5/11] FACTPCRSECONDARYIMPRESSION...")

secondary_impression_counter = Counter()
for chunk in tqdm(read_chunks("FACTPCRSECONDARYIMPRESSION.txt",
        usecols=lambda c: clean(c) == "eSituation_12")):
    chunk = normalize_cols(chunk)
    vectorized_count(chunk, "eSituation_12", secondary_impression_counter)

print(f"  Top 5 secondary impressions (raw): {secondary_impression_counter.most_common(5)}")

# 6. Symptoms
print(f"\n[6/11] Symptoms (sampling {SAMPLE_SYMPTOMS:,} rows each)...")

symptom_counter = Counter()
for fname, col in [
    ("FACTPCRPRIMARYSYMPTOM.txt",    "eSituation_09"),
    ("FACTPCRADDITIONALSYMPTOM.txt", "eSituation_10"),
]:
    for chunk in tqdm(read_chunks(fname,
            usecols=lambda c: clean(c) == col,
            nrows=SAMPLE_SYMPTOMS), desc=fname):
        chunk = normalize_cols(chunk)
        vectorized_count(chunk, col, symptom_counter)

print(f"  Top 5 symptoms (raw): {symptom_counter.most_common(5)}")

# 7. FACTPCRPROCEDURE
print(f"\n[7/11] FACTPCRPROCEDURE (sampling {SAMPLE_PROCS:,} rows)...")

procedure_counter = Counter()
for chunk in tqdm(read_chunks("FACTPCRPROCEDURE.txt",
        usecols=lambda c: clean(c) == "eProcedures_03",
        nrows=SAMPLE_PROCS)):
    chunk = normalize_cols(chunk)
    vectorized_count(chunk, "eProcedures_03", procedure_counter)

print(f"  Top 5 procedures (raw): {procedure_counter.most_common(5)}")

# 8. FACTPCRPROTOCOL
print(f"\n[8/11] FACTPCRPROTOCOL (sampling {SAMPLE_LARGE:,} rows)...")

protocol_counter = Counter()
for chunk in tqdm(read_chunks("FACTPCRPROTOCOL.txt",
        usecols=lambda c: clean(c) == "eProtocol_01",
        nrows=SAMPLE_LARGE)):
    chunk = normalize_cols(chunk)
    vectorized_count(chunk, "eProtocol_01", protocol_counter)

print(f"  Top 5 protocols: {protocol_counter.most_common(5)}")

# 9. FactPcreOutcomeEDDiag — actual ED diagnoses
print(f"\n[9/11] FactPcreOutcomeEDDiag (sampling {SAMPLE_LARGE:,} rows)...")

ed_diag_counter = Counter()
ed_cols_found   = None

for chunk in tqdm(read_chunks("FactPcreOutcomeEDDiag.txt", nrows=SAMPLE_LARGE)):
    chunk = normalize_cols(chunk)
    if ed_cols_found is None:
        # auto-detect the diagnosis column on first chunk
        for col in chunk.columns:
            if any(k in col.lower() for k in ["diag", "icd", "outcome", "eoutcome"]):
                ed_cols_found = col
                print(f"  Using column: {col}")
                break
    if ed_cols_found and ed_cols_found in chunk.columns:
        vectorized_count(chunk, ed_cols_found, ed_diag_counter)

print(f"  Top 5 ED diagnoses (raw): {ed_diag_counter.most_common(5)}")

# 10. REF tables — code to human-readable
print("\n[10/11] Loading REF tables...")

symptom_ref    = load_ref("ESITUATION_09REF.txt",  "eSituation_09", "DiagnosisCodeDescr")
impression_ref = load_ref("ESITUATION_11REF.txt",  "eSituation_11", "DiagnosisCodeDescr",
                          encoding="latin-1")
secondary_ref  = load_ref("ESITUATION_12REF.txt",  "eSituation_12", "DiagnosisCodeDescr",
                          encoding="latin-1")
assoc_ref      = load_ref("ESITUATION_10REF.txt",  "eSituation_10", "DiagnosisCodeDescr")
injury_ref     = load_ref("EINJURY_01REF.txt",     "eInjury_01",    "DiagnosisCodeDescr")
procedure_ref  = load_ref("EPROCEDURES_03REF.txt", "eProcedures_03","ProcedureCodeDescr")

print(f"  impression_ref:  {len(impression_ref)} entries")
print(f"  symptom_ref:     {len(symptom_ref)} entries")
print(f"  procedure_ref:   {len(procedure_ref)} entries")

# 11. NEMSIS code lookups for acuity + location
print("\n[11/11] Building acuity + location lookup tables...")

# NEMSIS acuity codes
acuity_lookup = {
    "2205001": "Critical",
    "2205003": "Emergent",
    "2205005": "Lower Acuity",
    "2205007": "Non-Acute",
    "2205009": "Dead at Scene",
}

# ICD-10 location codes (eScene_09) — top ones
location_lookup = {
    "Y92.00": "Unspecified non-institutional residence",
    "Y92.01": "Single-family non-institutional residence",
    "Y92.02": "Mobile home",
    "Y92.09": "Other non-institutional residence",
    "Y92.1":  "Institutional residence",
    "Y92.11": "Nursing home",
    "Y92.12": "School",
    "Y92.14": "Reform school",
    "Y92.15": "Prison",
    "Y92.16": "Military base",
    "Y92.19": "Other institutional residence",
    "Y92.2":  "School/institution",
    "Y92.21": "Elementary/secondary school",
    "Y92.22": "College",
    "Y92.3":  "Sports area",
    "Y92.4":  "Street/highway",
    "Y92.41": "Street and highway",
    "Y92.48": "Other paved roadway",
    "Y92.5":  "Trade/service area",
    "Y92.51": "Private commercial establishment",
    "Y92.52": "Service area",
    "Y92.53": "Ambulatory health services",
    "Y92.59": "Other trade area",
    "Y92.6":  "Industrial area",
    "Y92.7":  "Farm",
    "Y92.8":  "Other place",
    "Y92.81": "Transport vehicle",
    "Y92.89": "Other specified place",
    "Y92.9":  "Unspecified place",
}

def decode_location(counter, lookup, n=TOP_N):
    result = {}
    for code, count in counter.most_common(n * 2):
        name = lookup.get(code, None)
        if not name:
            # try prefix match
            for prefix in ["Y92.0", "Y92.1", "Y92.2", "Y92.3", "Y92.4",
                           "Y92.5", "Y92.6", "Y92.7", "Y92.8", "Y92.9"]:
                if code.startswith(prefix):
                    name = lookup.get(prefix)
                    break
        if name:
            result[name] = result.get(name, 0) + count
        if len(result) >= n:
            break
    return dict(sorted(result.items(), key=lambda x: -x[1]))

def decode_acuity(counter, lookup):
    result = {}
    for code, count in counter.most_common():
        name = lookup.get(clean(code))
        if name:
            result[name] = count
    return result

# Build final distributions
print("\nBuilding distributions.json...")

distributions = {
    "meta": {
        "source":   "NEMSIS v3.5 2024 Public Release",
        "records":  "~60M EMS activations",
        "sampling": {
            "vitals":     SAMPLE_VITALS,
            "meds":       SAMPLE_MEDS,
            "procedures": SAMPLE_PROCS,
            "symptoms":   SAMPLE_SYMPTOMS,
        }
    },
    "age":               age_dist,
    "dispatch_complaints": dict(dispatch_counter.most_common(TOP_N)),
    "chief_complaints":  {
        "anatomic_location": dict(situation_07_counter.most_common(TOP_N)),
        "organ_system":      dict(situation_08_counter.most_common(TOP_N)),
    },
    "incident_locations": decode_location(location_counter, location_lookup),
    "initial_acuity":    decode_acuity(acuity_counter, acuity_lookup),
    "final_acuity":      decode_acuity(final_acuity_counter, acuity_lookup),
    "vitals":            vital_distributions,
    "avpu":              dict(avpu_counter.most_common(10)),
    "medications": {
        "top_drugs":    dict(med_name_counter.most_common(TOP_N)),
        "routes":       dict(med_route_counter.most_common(20)),
        "units":        dict(med_unit_counter.most_common(20)),
        "median_doses": med_median_doses,
    },
    "impressions":           decode_top(impression_counter,           impression_ref),
    "secondary_impressions": decode_top(secondary_impression_counter, secondary_ref),
    "symptoms":              decode_top(symptom_counter,              symptom_ref),
    "procedures":            decode_top(procedure_counter,            procedure_ref),
    "protocols":             dict(protocol_counter.most_common(TOP_N)),
    "ed_diagnoses":          dict(ed_diag_counter.most_common(TOP_N)),
}

with open(OUTPUT_PATH, "w") as f:
    json.dump(distributions, f, indent=2)

size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
print(f"\nDone. Saved to {OUTPUT_PATH} ({size_mb:.1f} MB)")