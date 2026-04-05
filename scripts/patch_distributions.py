"""
patch_distributions.py — fixes empty fields and decodes raw NEMSIS codes
"""
import json
import pandas as pd
import os
from collections import Counter
from tqdm import tqdm

DATA_DIR    = "/Users/thesilentreaper/Documents/Projects/EMS/data/nemsis_extract"
OUTPUT_PATH = "/Users/thesilentreaper/Documents/Projects/EMS/data/distributions.json"
SEP         = "~|~"
CHUNKSIZE   = 100_000

NULL_CODES = {"7701001", "7701003", "7701005", "Not Recorded", "Not Applicable", "Unknown", ""}

def clean(val):
    return str(val).strip().strip("'").strip('"').strip("~")

def is_null(val):
    if pd.isna(val): return True
    return clean(val) in NULL_CODES

def read_chunks(filename, usecols=None, nrows=None):
    path = os.path.join(DATA_DIR, filename)
    return pd.read_csv(
        path, sep=SEP, engine="python", dtype=str,
        usecols=usecols, chunksize=CHUNKSIZE, nrows=nrows,
        on_bad_lines="skip", encoding="utf-8", encoding_errors="replace"
    )

def normalize_cols(chunk):
    chunk.columns = [clean(c) for c in chunk.columns]
    return chunk

def vectorized_count(chunk, col, counter):
    if col not in chunk.columns: return
    vals = chunk[col].apply(lambda x: clean(x) if not is_null(x) else None).dropna()
    counter.update(vals.tolist())

# NEMSIS lookup tables
DISPATCH_LOOKUP = {
    "2301001": "Abdominal Pain / Problems",
    "2301003": "Allergic Reaction / Stings",
    "2301005": "Animal Bite",
    "2301007": "Assault / Sexual Assault",
    "2301009": "Automated Crash Notification",
    "2301011": "Back Pain (Non-Traumatic)",
    "2301013": "Breathing Problems",
    "2301015": "Burns / Explosion",
    "2301017": "Carbon Monoxide / Hazmat / Inhalation",
    "2301019": "Cardiac Arrest / Death",
    "2301021": "Chest Pain (Non-Traumatic)",
    "2301023": "Choking",
    "2301025": "Convulsions / Seizures",
    "2301027": "Diabetic Problems",
    "2301029": "Drowning / Diving Accident",
    "2301031": "Electrocution / Lightning",
    "2301033": "Eye Problems / Injuries",
    "2301035": "Falls",
    "2301037": "Fire",
    "2301039": "Headache",
    "2301041": "Heart Problems / AICD",
    "2301043": "Heat / Cold Exposure",
    "2301045": "Hemorrhage / Lacerations",
    "2301047": "Industrial Accident / Inaccessible Incident",
    "2301049": "Medical Alert Alarm",
    "2301051": "Mental Health / Behavioral / Psychiatric Problem",
    "2301053": "Motor Vehicle Collision (MVC)",
    "2301055": "Motorcycle Crash",
    "2301057": "Mutual Aid",
    "2301059": "Nausea / Vomiting",
    "2301061": "Sick Person",
    "2301063": "Stab / Gunshot Wound / Penetrating Trauma",
    "2301065": "Stroke / CVA",
    "2301067": "Traffic / Transportation Incident",
    "2301069": "Traumatic Injury",
    "2301071": "Unconscious / Fainting / Near-Fainting",
    "2301073": "Unknown Problem / Person Down",
    "2301075": "Uterine Contractions / Pregnancy",
    "2301077": "Weakness",
    "2301079": "Well Person Check",
    "2301081": "Pandemic / Epidemic / Outbreak",
    "2301083": "Transfer / Interfacility",
    "2301085": "Alcohol / Drug Ingestion / Overdose",
    "2301087": "Airway Obstruction",
    "2301089": "Altercation / Fight",
    "2301091": "Other",
}

AVPU_LOOKUP = {
    "3326001": "Alert",
    "3326003": "Verbal",
    "3326005": "Pain",
    "3326007": "Unresponsive",
}

ACUITY_LOOKUP = {
    "2205001": "Critical",
    "2205003": "Emergent",
    "2205005": "Lower Acuity",
    "2205007": "Non-Acute",
    "2205009": "Dead at Scene",
}

PROTOCOL_LOOKUP = {
    "9914001": "Airway",
    "9914003": "Airway-Failed",
    "9914005": "Airway-Obstruction/Foreign Body",
    "9914007": "Airway-Rapid Sequence Induction",
    "9914009": "Cardiac Arrest-Asystole",
    "9914011": "Cardiac Arrest-Fibrillation",
    "9914013": "Cardiac Arrest-Pulseless Electrical Activity",
    "9914015": "Cardiac Arrest-Resuscitation",
    "9914017": "Cardiac Arrest-Return of Spontaneous Circulation",
    "9914019": "Cardiac-Acute Coronary Syndrome",
    "9914021": "Cardiac-Arrhythmia",
    "9914023": "Cardiac-Cardiogenic Shock",
    "9914025": "Cardiac-CHF/Pulmonary Edema",
    "9914027": "Cardiac-Hypertensive Emergency",
    "9914029": "Cardiac-Newborn Resuscitation",
    "9914031": "General-Abdominal Pain",
    "9914033": "General-Altered Level of Consciousness",
    "9914035": "General-Back Pain",
    "9914037": "General-Behavioral/Psychiatric Disorders",
    "9914039": "General-Biological Agent Exposure",
    "9914041": "General-Burns",
    "9914043": "General-Carbon Monoxide Poisoning",
    "9914045": "General-Diarrhea",
    "9914047": "General-Environmental/Hypothermia",
    "9914049": "General-Fever",
    "9914051": "General-Headache",
    "9914053": "General-Heat Exhaustion/Stroke",
    "9914055": "General-Hemorrhagic Shock",
    "9914057": "General-Hypoglycemia",
    "9914059": "General-Hyperglycemia",
    "9914061": "General-Nausea/Vomiting",
    "9914063": "General-Nerve Agent Exposure",
    "9914065": "General-Newborn Care",
    "9914067": "General-Pain Control",
    "9914069": "General-Poisoning/Overdose",
    "9914071": "General-Respiratory Distress",
    "9914073": "General-Seizure",
    "9914075": "General-Sepsis",
    "9914077": "General-Shock",
    "9914079": "General-Stroke/CVA",
    "9914081": "General-Syncope",
    "9914083": "General-Traumatic Arrest",
    "9914085": "General-Weakness",
    "9914087": "Obstetrics-Delivery",
    "9914089": "Obstetrics-Eclampsia",
    "9914091": "Obstetrics-Pregnancy Related",
    "9914093": "Pediatric-Allergic Reaction",
    "9914095": "Pediatric-Altered Level of Consciousness",
    "9914097": "Pediatric-Apnea",
    "9914099": "Pediatric-Bronchospasm/Asthma",
    "9914101": "Pediatric-Cardiac Arrest",
    "9914103": "Pediatric-Fever",
    "9914105": "Pediatric-Hypoglycemia",
    "9914107": "Pediatric-Respiratory Distress",
    "9914109": "Pediatric-Seizure",
    "9914111": "Pediatric-Sepsis",
    "9914113": "Pediatric-Shock",
    "9914115": "Pediatric-Toxic Ingestion",
    "9914117": "Trauma-Burns",
    "9914119": "Trauma-Crush Syndrome",
    "9914121": "Trauma-Extremity Trauma",
    "9914123": "Trauma-Head Trauma",
    "9914125": "Trauma-Multi-system Trauma",
    "9914127": "Trauma-Penetrating Trauma",
    "9914129": "Trauma-Spinal Cord Injury",
    "9914131": "Trauma-Thoracic Trauma",
    "9914133": "Trauma-Traumatic Brain Injury",
    "9914135": "General-Allergic Reaction",
    "9914137": "General-Apparent Life Threatening Event",
    "9914139": "General-Anaphylaxis",
    "9914141": "General-Diabetic Emergency",
    "9914143": "Cardiac-STEMI",
    "9914145": "General-Chest Pain",
    "9914147": "General-Drowning/Near-Drowning",
    "9914149": "General-Eye Injury",
    "9914151": "General-Obstetrical Emergency",
    "9914153": "Trauma-Eye Injury",
    "9914155": "General-Dizziness",
    "9914157": "General-Epistaxis",
    "9914159": "General-GI Bleed",
    "9914161": "General-Influenza-Like Illness",
    "9914163": "General-Kidney Stone",
    "9914165": "General-Neonatal Care",
    "9914167": "General-Urological Emergency",
    "9914169": "Trauma-Abdominal Trauma",
}

# ICD-10 ED diagnosis lookup
ED_DIAG_LOOKUP = {
    "R07.9": "Chest pain, unspecified",
    "R55":   "Syncope and collapse",
    "W19.XXXA": "Unspecified fall, initial encounter",
    "I10":   "Essential hypertension",
    "S09.90XA": "Unspecified injury of head, initial encounter",
    "N39.0": "Urinary tract infection",
    "N17.9": "Acute kidney failure, unspecified",
    "R06.02": "Shortness of breath",
    "R10.9": "Unspecified abdominal pain",
    "R42":   "Dizziness and giddiness",
    "J18.9": "Pneumonia, unspecified",
    "R53.1": "Weakness",
    "R41.82": "Altered mental status, unspecified",
    "A41.9": "Sepsis, unspecified",
    "R56.9": "Seizure, unspecified",
    "R11.2": "Nausea with vomiting",
    "E87.6": "Hypokalemia",
    "I48.91": "Atrial fibrillation",
    "R79.89": "Other abnormal blood chemistry",
    "I50.9": "Heart failure, unspecified",
    "E86.0": "Dehydration",
    "Z79.82": "Long-term use of aspirin",
    "Z87.891": "Personal history of nicotine dependence",
    "R07.89": "Other chest pain",
    "Z79.899": "Other long-term drug therapy",
    "V87.7XXA": "Traffic accident, initial encounter",
    "R09.02": "Hypoxemia",
    "R51.9": "Headache, unspecified",
    "J44.1": "COPD with acute exacerbation",
    "D64.9": "Anemia, unspecified",
    "F41.9": "Anxiety disorder, unspecified",
    "R45.851": "Suicidal ideation",
    "E11.9": "Type 2 diabetes without complications",
    "V89.2XXA": "Motor vehicle accident, initial encounter",
    "F10.920": "Alcohol use disorder with intoxication",
    "J96.01": "Acute respiratory failure with hypoxia",
    "E87.1": "Hyponatremia",
    "I95.9": "Hypotension, unspecified",
    "R19.7": "Diarrhea, unspecified",
    "R50.9": "Fever, unspecified",
    "M54.2": "Cervicalgia",
    "U07.1": "COVID-19",
    "M54.50": "Low back pain",
    "G89.29": "Other chronic pain",
    "R11.10": "Vomiting, unspecified",
    "R00.0": "Tachycardia, unspecified",
    "I63.9": "Cerebral infarction, unspecified",
    "R00.2": "Palpitations",
    "F17.200": "Nicotine dependence",
    "D72.829": "Elevated white blood cell count",
}

print("Loading distributions.json...")
with open(OUTPUT_PATH) as f:
    dist = json.load(f)

# Fix dispatch complaints
print("Decoding dispatch complaints...")
dist["dispatch_complaints"] = {
    DISPATCH_LOOKUP.get(clean(k), k): v
    for k, v in dist["dispatch_complaints"].items()
    if DISPATCH_LOOKUP.get(clean(k))
}

# Fix AVPU
print("Decoding AVPU...")
dist["avpu"] = {
    AVPU_LOOKUP.get(clean(k), k): v
    for k, v in dist["avpu"].items()
    if AVPU_LOOKUP.get(clean(k))
}

# Fix ED diagnoses
print("Decoding ED diagnoses...")
dist["ed_diagnoses"] = {
    ED_DIAG_LOOKUP.get(clean(k), k): v
    for k, v in dist["ed_diagnoses"].items()
}

# Fix protocols — re-extract with correct column name
print("Re-extracting protocols...")
protocol_counter = Counter()
for chunk in tqdm(pd.read_csv(
        os.path.join(DATA_DIR, "FACTPCRPROTOCOL.txt"),
        sep=SEP, engine="python", dtype=str,
        chunksize=CHUNKSIZE, nrows=2_000_000,
        on_bad_lines="skip", encoding="utf-8", encoding_errors="replace")):
    chunk.columns = [clean(c) for c in chunk.columns]
    if "eProtocols_01" in chunk.columns:
        vals = chunk["eProtocols_01"].apply(
            lambda x: clean(x) if not is_null(x) else None).dropna()
        protocol_counter.update(vals.tolist())

dist["protocols"] = {
    PROTOCOL_LOOKUP.get(clean(k), k): v
    for k, v in protocol_counter.most_common(50)
    if PROTOCOL_LOOKUP.get(clean(k))
}

# Fix acuity — re-extract with correct column names
print("Re-extracting acuity...")
initial_acuity_counter = Counter()
final_acuity_counter   = Counter()

for chunk in tqdm(pd.read_csv(
        os.path.join(DATA_DIR, "Pub_PCRevents.txt"),
        sep=SEP, engine="python", dtype=str,
        usecols=lambda c: clean(c) in {"eSituation_13", "eDisposition_19"},
        chunksize=CHUNKSIZE,
        on_bad_lines="skip", encoding="utf-8", encoding_errors="replace")):
    chunk.columns = [clean(c) for c in chunk.columns]
    if "eSituation_13" in chunk.columns:
        vals = chunk["eSituation_13"].apply(
            lambda x: clean(x) if not is_null(x) else None).dropna()
        initial_acuity_counter.update(vals.tolist())
    if "eDisposition_19" in chunk.columns:
        vals = chunk["eDisposition_19"].apply(
            lambda x: clean(x) if not is_null(x) else None).dropna()
        final_acuity_counter.update(vals.tolist())

dist["initial_acuity"] = {
    ACUITY_LOOKUP.get(clean(k), k): v
    for k, v in initial_acuity_counter.most_common()
    if ACUITY_LOOKUP.get(clean(k))
}
dist["final_acuity"] = {
    ACUITY_LOOKUP.get(clean(k), k): v
    for k, v in final_acuity_counter.most_common()
    if ACUITY_LOOKUP.get(clean(k))
}

print(f"  Initial acuity: {dist['initial_acuity']}")
print(f"  Final acuity:   {dist['final_acuity']}")
print(f"  Protocols:      {list(dist['protocols'].items())[:5]}")
print(f"  Dispatch top3:  {list(dist['dispatch_complaints'].items())[:3]}")

with open(OUTPUT_PATH, "w") as f:
    json.dump(dist, f, indent=2)

print(f"\nDone. Patched distributions.json saved.")