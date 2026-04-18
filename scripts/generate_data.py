"""
MEDIC Synthetic Data Generator
- Batch generation (5 per call)
- NEMSIS-grounded scenarios
- Acuity-based word count validation
- Inline schema validation
- Auto-retry failed samples
- Gemini generates PMH/allergies/current meds contextually
"""

import json
import re
import random
import os
import time
import threading
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

OUTPUT_DIR         = Path("./medic_synthetic")
DISTRIBUTIONS_PATH = Path("./distributions.json")
NUM_SAMPLES        = 2500
TRAIN_SPLIT        = 0.8
VAL_SPLIT          = 0.1
MODEL_NAME         = "gemini-2.5-pro"
MAX_RETRIES        = 3
MAX_WORKERS        = 3
BATCH_SIZE         = 5
CHECKPOINT_PATH    = Path("./medic_synthetic/checkpoint.jsonl")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client          = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
checkpoint_lock = threading.Lock()

print("Loading NEMSIS distributions...")
with open(DISTRIBUTIONS_PATH) as f:
    DIST = json.load(f)

AGE_DIST = DIST["age"]

WORD_COUNT_BY_ACUITY = {
    "Critical":    (120, 250),
    "Emergent":    (80, 200),
    "Lower Acuity": (50, 150),
    "Non-Acute":   (40, 120),
}
DEFAULT_WORD_COUNT = (60, 200)

def sample_vital_percentile(field, scenario_modifier=0.0):
    FALLBACKS = {"pain": (0, 10), "gcs_total": (3, 15), "dbp": (50, 120)}
    v = DIST["vitals"].get(field)
    if not v:
        if field in FALLBACKS:
            lo, hi = FALLBACKS[field]
            return float(random.randint(lo, hi))
        return None
    p50 = v["p50"]
    iqr = v["p75"] - v["p25"]
    std = max(iqr / 1.35, 1.0)
    val = random.gauss(p50 + scenario_modifier * std, std)
    return max(v["min"], min(v["max"], val))

def get_clean_drugs():
    seen, result = set(), []
    skip = {
        "oxygen", "normal saline",
        "sodium chloride 9 mg/ml injectable solution",
        "calcium chloride / lactate / potassium chloride / sodium chloride",
        "sodium chloride"
    }
    for drug, count in DIST["medications"]["top_drugs"].items():
        normalized = drug.lower().strip()
        if normalized not in seen and normalized not in skip and count > 3000:
            seen.add(normalized)
            result.append((drug, count))
    return result

CLEAN_DRUGS = get_clean_drugs()

DISPATCH_COMPLAINTS    = list(DIST["dispatch_complaints"].keys())
DISPATCH_WEIGHTS       = list(DIST["dispatch_complaints"].values())
IMPRESSIONS            = list(DIST["impressions"].keys())
IMPRESSION_WEIGHTS     = list(DIST["impressions"].values())
SECONDARY_IMPRESSIONS  = list(DIST["secondary_impressions"].keys())
SECONDARY_IMP_WEIGHTS  = list(DIST["secondary_impressions"].values())
SYMPTOMS               = list(DIST["symptoms"].keys())
SYMPTOM_WEIGHTS        = list(DIST["symptoms"].values())
PROCEDURES             = list(DIST["procedures"].keys())
PROCEDURE_WEIGHTS      = list(DIST["procedures"].values())
AVPU_OPTIONS           = list(DIST["avpu"].keys())
AVPU_WEIGHTS           = list(DIST["avpu"].values())
INCIDENT_LOCATIONS     = list(DIST["incident_locations"].keys())
LOCATION_WEIGHTS       = list(DIST["incident_locations"].values())
PROTOCOLS              = list(DIST["protocols"].keys())      if DIST.get("protocols")        else []
PROTOCOL_WEIGHTS       = list(DIST["protocols"].values())    if DIST.get("protocols")        else []
INITIAL_ACUITY         = list(DIST["initial_acuity"].keys()) if DIST.get("initial_acuity")   else []
INITIAL_ACUITY_WEIGHTS = list(DIST["initial_acuity"].values()) if DIST.get("initial_acuity") else []

ROUTES = [r for r in DIST["medications"]["routes"].keys()
          if r in {"IV", "IM", "IN", "PO", "SL", "NEB", "IO"}]
if not ROUTES:
    ROUTES = ["IV", "IM", "PO", "SL", "NEB"]

EMS_MEDS = []
for drug, count in CLEAN_DRUGS:
    median_dose = DIST["medications"]["median_doses"].get(drug)
    if median_dose:
        EMS_MEDS.append({"drug": drug, "dose": median_dose, "count": count})
EMS_MED_WEIGHTS = [m["count"] for m in EMS_MEDS]

SCENARIO_MODS = {
    "cardiac":     {"sbp":  0.5, "hr":  0.5, "spo2": -0.3, "rr":  0.2, "pain":  1.5},
    "respiratory": {"sbp":  0.0, "hr":  0.3, "spo2": -1.5, "rr":  1.5, "pain":  0.5},
    "trauma":      {"sbp": -0.5, "hr":  0.8, "spo2": -0.3, "rr":  0.3, "pain":  1.5},
    "neuro":       {"sbp":  0.3, "hr":  0.2, "spo2": -0.2, "rr":  0.0, "pain":  0.0},
    "diabetic":    {"sbp":  0.0, "hr":  0.2, "spo2":  0.0, "rr":  0.0, "pain":  0.3},
    "psychiatric": {"sbp":  0.2, "hr":  0.3, "spo2":  0.0, "rr":  0.2, "pain":  0.0},
    "medical":     {"sbp":  0.0, "hr":  0.0, "spo2":  0.0, "rr":  0.0, "pain":  0.5},
}
SCENARIO_TYPES = list(SCENARIO_MODS.keys())

EXPECTED_KEYS = [
    "age", "sex", "chief_complaint", "primary_impression", "secondary_impression",
    "incident_location", "initial_acuity", "protocol_used", "bp_systolic", "bp_diastolic",
    "heart_rate", "respiratory_rate", "spo2", "gcs_total", "avpu", "pain_scale",
    "allergies", "medications_current", "past_medical_history", "medications_given",
    "procedures", "signs_symptoms", "events_leading"
]
NUMERIC_FIELDS = {"age", "bp_systolic", "bp_diastolic", "heart_rate", "respiratory_rate",
                  "spo2", "gcs_total", "pain_scale"}
STRING_FIELDS  = {"sex", "chief_complaint", "primary_impression", "secondary_impression",
                  "incident_location", "initial_acuity", "protocol_used", "avpu", "events_leading"}
ARRAY_FIELDS   = {"allergies", "medications_current", "past_medical_history",
                  "medications_given", "procedures", "signs_symptoms"}

def word_count(text):
    return len(text.strip().split())

def validate_sample(transcript, pcr_json):
    errors = []
    wc     = word_count(transcript)

    acuity    = pcr_json.get("initial_acuity", "") if isinstance(pcr_json, dict) else ""
    wc_min, wc_max = WORD_COUNT_BY_ACUITY.get(acuity, DEFAULT_WORD_COUNT)
    if wc < wc_min or wc > wc_max:
        errors.append(f"Transcript word count {wc} out of range [{wc_min},{wc_max}] for acuity '{acuity}'")

    if not isinstance(pcr_json, dict):
        return {"valid": False, "errors": ["PCR JSON is not a dict"], "word_count": wc}

    for key in EXPECTED_KEYS:
        if key not in pcr_json:
            errors.append(f"Missing key: {key}")
            continue
        value = pcr_json[key]
        if key in NUMERIC_FIELDS:
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"{key} must be number or null")
        elif key in STRING_FIELDS:
            if value is not None and not isinstance(value, str):
                errors.append(f"{key} must be string or null")
        elif key in ARRAY_FIELDS:
            if value is not None and not isinstance(value, list):
                errors.append(f"{key} must be array or null")

    meds = pcr_json.get("medications_given")
    if meds is not None and isinstance(meds, list):
        for i, med in enumerate(meds):
            if not isinstance(med, dict):
                errors.append(f"medications_given[{i}] must be an object")
                continue
            expected_med_keys = ["drug", "dose", "unit", "route"]
            if list(med.keys()) != expected_med_keys:
                errors.append(f"medications_given[{i}] keys must be exactly {expected_med_keys}")
            if "dose" in med and not isinstance(med["dose"], (int, float)):
                errors.append(f"medications_given[{i}].dose must be number")

    return {"valid": len(errors) == 0, "errors": errors, "word_count": wc}

def generate_scenario():
    scenario_type = random.choice(SCENARIO_TYPES)
    mods = SCENARIO_MODS[scenario_type]

    age  = int(random.gauss(AGE_DIST["p50"], (AGE_DIST["p75"] - AGE_DIST["p25"]) / 1.35))
    age  = max(1, min(100, age))
    sex  = random.choices(["male", "female"], weights=[0.51, 0.49])[0]

    sbp  = int(sample_vital_percentile("sbp",  mods.get("sbp",  0)))
    hr   = int(sample_vital_percentile("hr",   mods.get("hr",   0)))
    rr   = int(sample_vital_percentile("rr",   mods.get("rr",   0)))
    spo2 = int(sample_vital_percentile("spo2", mods.get("spo2", 0)))
    pain_raw = sample_vital_percentile("pain", mods.get("pain", 0))
    pain = int(round(pain_raw)) if pain_raw is not None else random.randint(0, 10)
    pain = max(0, min(10, pain))
    dbp  = max(20, min(150, int(sbp * random.uniform(0.55, 0.70))))

    gcs = random.choices(
        list(range(3, 16)),
        weights=[1, 1, 1, 2, 2, 2, 3, 3, 4, 5, 8, 15, 30], k=1
    )[0]

    avpu                 = random.choices(AVPU_OPTIONS, weights=AVPU_WEIGHTS)[0]
    chief_complaint      = random.choices(DISPATCH_COMPLAINTS, weights=DISPATCH_WEIGHTS)[0]
    primary_impression   = random.choices(IMPRESSIONS, weights=IMPRESSION_WEIGHTS)[0]
    secondary_impression = random.choices(SECONDARY_IMPRESSIONS, weights=SECONDARY_IMP_WEIGHTS)[0]
    incident_location    = random.choices(INCIDENT_LOCATIONS, weights=LOCATION_WEIGHTS)[0]
    initial_acuity       = random.choices(INITIAL_ACUITY, weights=INITIAL_ACUITY_WEIGHTS)[0] if INITIAL_ACUITY else "Emergent"
    protocol             = random.choices(PROTOCOLS, weights=PROTOCOL_WEIGHTS)[0] if PROTOCOLS else ""

    signs_symptoms = list(dict.fromkeys(
        random.choices(SYMPTOMS, weights=SYMPTOM_WEIGHTS, k=random.randint(2, 5))
    ))
    procedures = list(dict.fromkeys(
        random.choices(PROCEDURES, weights=PROCEDURE_WEIGHTS,
                       k=random.choices([1, 2, 3, 4], weights=[0.2, 0.4, 0.3, 0.1])[0])
    ))

    num_meds   = random.choices([0, 1, 2, 3], weights=[0.25, 0.40, 0.25, 0.10])[0]
    meds_given = []
    if EMS_MEDS and num_meds > 0:
        chosen = random.choices(EMS_MEDS, weights=EMS_MED_WEIGHTS, k=num_meds)
        seen   = set()
        for med in chosen:
            key = med["drug"].lower()
            if key not in seen:
                seen.add(key)
                dose = round(med["dose"] * random.uniform(0.8, 1.2), 2)
                meds_given.append({
                    "drug": med["drug"], "dose": dose,
                    "unit": "mg", "route": random.choice(ROUTES)
                })

    wc_min, wc_max = WORD_COUNT_BY_ACUITY.get(initial_acuity, DEFAULT_WORD_COUNT)

    return scenario_type, {
        "age": age, "sex": sex,
        "chief_complaint": chief_complaint,
        "primary_impression": primary_impression,
        "secondary_impression": secondary_impression,
        "incident_location": incident_location,
        "initial_acuity": initial_acuity,
        "protocol_used": protocol,
        "bp_systolic": sbp, "bp_diastolic": dbp,
        "heart_rate": hr, "respiratory_rate": rr,
        "spo2": spo2, "gcs_total": gcs,
        "avpu": avpu, "pain_scale": pain,
        "medications_given": meds_given,
        "procedures": procedures,
        "signs_symptoms": signs_symptoms,
        "_transcript_word_count_guidance": f"{wc_min} to {wc_max} words appropriate for {initial_acuity} acuity",
    }

SYSTEM_PROMPT = """You are generating synthetic EMS training data for MEDIC, a voice-to-PCR documentation assistant for paramedics.

You must generate exactly one paired sample:
1. a realistic paramedic verbal handoff transcript
2. a structured PCR JSON extracted only from that transcript

This dataset will train clinical information extraction models. Clinical realism, strict faithfulness, and JSON correctness are mandatory.

PRIMARY TASK
Given a grounded scenario from the user, write:
- a spoken EMS handoff transcript with length appropriate to the acuity level
- a PCR JSON object containing only facts explicitly stated in the transcript

The user-provided scenario values are ground truth for generation. However, the JSON must be based only on what is actually spoken in the transcript.

NON-NEGOTIABLE RULES
- Do not invent facts.
- Do not change numeric values.
- Do not substitute different medications, procedures, symptoms, or impressions.
- Do not add details not supported by the user scenario.
- Do not output any explanatory text.
- Output exactly one transcript and one JSON object.

TRANSCRIPT LENGTH
Match transcript length to acuity:
- Critical: 120 to 250 words — complex, urgent, detailed
- Emergent: 80 to 200 words — moderately detailed
- Lower Acuity: 50 to 150 words — concise
- Non-Acute: 40 to 120 words — brief
The scenario will include a _transcript_word_count_guidance field — follow it.

TRANSCRIPT RULES
The transcript must:
- sound like authentic US paramedic handoff speech
- use realistic EMS jargon and abbreviations naturally: BP, HR, RR, SpO2, GCS, AVPU, LOC, ALOC, AMS, Pt, Hx, Rx, c/o, denies, s/p, VSS, IV, NC, NRB
- include mild natural disfluencies such as "uh," "um," or "..." occasionally, not excessively
- match urgency and tone to the stated initial_acuity
- preserve all mentioned ground-truth values exactly
- read like one continuous spoken handoff, not a list

GROUNDING RULES
- Treat all user-supplied scenario values as authoritative.
- You may choose not to mention every available field in the transcript.
- If a field is not explicitly spoken in the transcript, it must be null in the JSON.
- Never let the JSON leak information that was present in the scenario but absent from the transcript.
- Do not include _transcript_word_count_guidance in the JSON output.

ALLERGIES, CURRENT MEDICATIONS, AND PAST MEDICAL HISTORY
These three fields are NOT provided in the scenario. You must generate them yourself.
- Generate clinically plausible values consistent with the patient age, sex, primary impression, secondary impression, and scenario type.
- A 70-year-old with cardiac impression should have realistic cardiac comorbidities and medications.
- A young trauma patient should have minimal or no PMH.
- Vary these across samples.
- If you mention them in the transcript, include them in the JSON.
- If you do not mention them in the transcript, they must be null in the JSON.

EVENTS_LEADING RULES
events_leading must:
- be 1 to 2 sentences
- be specific to this scenario
- reflect the incident location and likely context of the call
- fit the patient age, sex, chief complaint, signs/symptoms, and impression
- avoid generic phrases such as "patient called 911", "symptoms began suddenly", "EMS was dispatched", "patient was found like this"
- be varied across samples

JSON EXTRACTION RULES
Create strict valid JSON using only information explicitly present in the transcript.
- If not explicitly spoken, use null.
- Use null for missing scalar fields.
- Use null for list fields unless the transcript explicitly states none or explicitly states the list contents.
- Use empty arrays only if the transcript clearly states none, for example NKDA, no home meds, no PMH, no meds given.
- medications_given must include only medications explicitly mentioned in the transcript.
- medications_given must be an array of objects with exactly these keys: drug, dose, unit, route.
- Preserve exact wording where feasible for complaints, impressions, procedures, symptoms, and locations.
- Preserve exact numbers for vitals and pain scale.

REQUIRED TOP-LEVEL JSON KEYS
Use exactly these keys in exactly this order:
age, sex, chief_complaint, primary_impression, secondary_impression, incident_location,
initial_acuity, protocol_used, bp_systolic, bp_diastolic, heart_rate, respiratory_rate,
spo2, gcs_total, avpu, pain_scale, allergies, medications_current, past_medical_history,
medications_given, procedures, signs_symptoms, events_leading

FIELD TYPING
- age: number or null
- sex: string or null
- chief_complaint: string or null
- primary_impression: string or null
- secondary_impression: string or null
- incident_location: string or null
- initial_acuity: string or null
- protocol_used: string or null
- bp_systolic: number or null
- bp_diastolic: number or null
- heart_rate: number or null
- respiratory_rate: number or null
- spo2: number or null
- gcs_total: number or null
- avpu: string or null
- pain_scale: number or null
- allergies: array or null
- medications_current: array or null
- past_medical_history: array or null
- medications_given: array or null
- procedures: array or null
- signs_symptoms: array or null
- events_leading: string or null

SELF-CHECK BEFORE OUTPUT
Internally verify all of the following before answering:
1. Transcript length matches the acuity-based word count guidance.
2. Every non-null JSON field is explicitly supported by the transcript.
3. No JSON field contains information absent from the transcript.
4. All mentioned numeric values exactly match the grounded scenario.
5. medications_given includes only drugs explicitly spoken in the transcript.
6. events_leading is specific, non-generic, and scenario-grounded.
7. JSON is valid and uses exactly the required keys in the required order.
8. allergies, medications_current, and past_medical_history are clinically coherent with the patient profile.
9. _transcript_word_count_guidance is not present in the JSON output.

OUTPUT FORMAT
Output exactly in this format and nothing else:

TRANSCRIPT:
[transcript here]

PCR_JSON:
[json here]"""

BATCH_SYSTEM_PROMPT = """You are generating synthetic EMS training data for MEDIC, a voice-to-PCR documentation assistant for paramedics.

You must generate multiple independent paired samples. Each sample contains:
1. a realistic paramedic verbal handoff transcript
2. a structured PCR JSON extracted only from that transcript

This dataset will train clinical information extraction models. Clinical realism, strict faithfulness, and JSON correctness are mandatory.

For each scenario provided:
- Write a transcript with length appropriate to the acuity level
- Produce a PCR JSON extracted only from facts explicitly stated in that transcript
- Do not mix details across scenarios
- Each sample must be fully independent

TRANSCRIPT LENGTH BY ACUITY
- Critical: 120 to 250 words
- Emergent: 80 to 200 words
- Lower Acuity: 50 to 150 words
- Non-Acute: 40 to 120 words
Each scenario includes a _transcript_word_count_guidance field — follow it.

All rules from single-sample generation apply to every sample:
- Treat all scenario values as ground truth
- Do not invent or change numeric values
- JSON must only contain facts explicitly spoken in the transcript
- If not spoken, use null
- medications_given must only include drugs explicitly spoken in the transcript
- events_leading must be specific, varied, and scenario-grounded
- Use authentic US paramedic jargon and natural disfluencies
- Do not include _transcript_word_count_guidance in any JSON output

ALLERGIES, CURRENT MEDICATIONS, AND PAST MEDICAL HISTORY
These are NOT provided in the scenario. Generate them contextually:
- Match the patient age, sex, primary impression, and scenario type
- Vary them across samples
- Only include in JSON if mentioned in the transcript

REQUIRED JSON KEY ORDER FOR EVERY SAMPLE:
age, sex, chief_complaint, primary_impression, secondary_impression, incident_location,
initial_acuity, protocol_used, bp_systolic, bp_diastolic, heart_rate, respiratory_rate,
spo2, gcs_total, avpu, pain_scale, allergies, medications_current, past_medical_history,
medications_given, procedures, signs_symptoms, events_leading

OUTPUT FORMAT — use exactly this structure:
SAMPLE_1
TRANSCRIPT:
[transcript]
PCR_JSON:
[json]
SAMPLE_2
TRANSCRIPT:
[transcript]
PCR_JSON:
[json]
... and so on for all samples."""

USER_PROMPT_SINGLE = """Generate exactly 1 synthetic EMS training pair from the grounded scenario below.

- Treat all scenario values as ground truth for transcript generation.
- Write a transcript matching the word count guidance for this acuity level.
- Then produce PCR_JSON extracted only from facts explicitly spoken in the transcript.
- Any field not explicitly stated in the transcript must be null in the JSON.
- medications_given must include only medications actually spoken in the transcript.
- events_leading must be specific, varied, and grounded in the scenario context.
- Generate clinically coherent allergies, medications_current, and past_medical_history based on the patient profile. Only include in JSON if mentioned in transcript.
- Do not include _transcript_word_count_guidance in the JSON output.
- Output only in the required TRANSCRIPT / PCR_JSON format.

SCENARIO_GROUND_TRUTH:
{scenario_json}"""

USER_PROMPT_BATCH = """Generate exactly {n} synthetic EMS training pairs from the grounded scenarios below.

- Produce one independent sample per scenario.
- For each scenario, write a transcript matching the word count guidance for that acuity level.
- Produce a PCR JSON extracted only from facts explicitly stated in that transcript.
- Do not mix details across scenarios.
- Any field not explicitly stated in a transcript must be null in that transcript's JSON.
- medications_given must include only medications actually spoken in that transcript.
- events_leading must be specific, varied, and grounded in each scenario's context.
- Generate clinically coherent allergies, medications_current, and past_medical_history for each patient. Only include in JSON if mentioned in transcript.
- Do not include _transcript_word_count_guidance in any JSON output.
- Output samples in order using the required SAMPLE_N / TRANSCRIPT / PCR_JSON format.

SCENARIOS:
{scenarios_json}"""

def repair_json(s):
    last = s.rfind('}')
    if last != -1:
        s = s[:last + 1]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    s = re.sub(r'//[^\n]*', '', s)
    s = re.sub(r'#[^\n]*',  '', s)
    return s.strip()

def parse_single(text):
    if "TRANSCRIPT:" not in text or "PCR_JSON:" not in text:
        return None
    try:
        transcript = text.split("PCR_JSON:")[0].replace("TRANSCRIPT:", "").strip()
        json_str   = text.split("PCR_JSON:")[1].strip()
        json_str   = re.sub(r'```json|```', '', json_str).strip()
        try:
            pcr = json.loads(json_str)
        except json.JSONDecodeError:
            pcr = json.loads(repair_json(json_str))
        # remove guidance key if Gemini leaked it
        pcr.pop("_transcript_word_count_guidance", None)
        return {"transcript": transcript, "pcr_json": pcr}
    except Exception as e:
        print(f"  Parse error (single): {e}")
    return None

def parse_batch(text, n):
    results = []
    parts   = re.split(r'SAMPLE_\d+', text)
    parts   = [p.strip() for p in parts if p.strip()]
    for part in parts:
        parsed = parse_single(part)
        if parsed:
            results.append(parsed)
    return results[:n]

def save_checkpoint(item):
    with checkpoint_lock:
        with open(CHECKPOINT_PATH, 'a') as f:
            f.write(json.dumps(item) + "\n")

def load_checkpoint():
    if not CHECKPOINT_PATH.exists():
        return []
    data = []
    with open(CHECKPOINT_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    if data:
        print(f"Resumed from checkpoint: {len(data)} samples already saved")
    return data

def call_gemini(prompt, system_prompt, max_tokens=8000):
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
            max_output_tokens=max_tokens,
        )
    )
    return response.text

def generate_batch(_):
    scenarios      = [generate_scenario() for _ in range(BATCH_SIZE)]
    scenario_list  = [s for _, s in scenarios]
    scenario_types = [t for t, _ in scenarios]

    prompt = USER_PROMPT_BATCH.format(
        n=BATCH_SIZE,
        scenarios_json=json.dumps(scenario_list, indent=2)
    )

    for attempt in range(MAX_RETRIES):
        try:
            text    = call_gemini(prompt, BATCH_SYSTEM_PROMPT, max_tokens=10000)
            parsed  = parse_batch(text, BATCH_SIZE)
            results = []

            for i, item in enumerate(parsed):
                transcript = item.get("transcript", "")
                pcr_json   = item.get("pcr_json", {})
                validation = validate_sample(transcript, pcr_json)

                if validation["valid"]:
                    item["scenario_type"] = scenario_types[i] if i < len(scenario_types) else "unknown"
                    save_checkpoint(item)
                    results.append(item)
                else:
                    print(f"  Sample {i+1} failed validation: {validation['errors']}")
                    single_prompt = USER_PROMPT_SINGLE.format(
                        scenario_json=json.dumps(scenario_list[i], indent=2)
                    )
                    for retry in range(MAX_RETRIES):
                        try:
                            single_text   = call_gemini(single_prompt, SYSTEM_PROMPT, max_tokens=2500)
                            single_parsed = parse_single(single_text)
                            if single_parsed:
                                v = validate_sample(
                                    single_parsed["transcript"],
                                    single_parsed["pcr_json"]
                                )
                                if v["valid"]:
                                    single_parsed["scenario_type"] = scenario_types[i] if i < len(scenario_types) else "unknown"
                                    save_checkpoint(single_parsed)
                                    results.append(single_parsed)
                                    break
                                else:
                                    print(f"  Single retry {retry+1} still invalid: {v['errors']}")
                        except Exception as e:
                            print(f"  Single retry {retry+1} error: {e}")
                            time.sleep(2 ** retry)

            return results

        except Exception as e:
            wait = 2 ** attempt
            print(f"  Batch error (attempt {attempt+1}/{MAX_RETRIES}): {e}, retrying in {wait}s...")
            time.sleep(wait)

    return []

def main():
    existing  = load_checkpoint()
    already   = len(existing)
    remaining = NUM_SAMPLES - already

    if remaining <= 0:
        print("Checkpoint already complete.")
        data = existing
    else:
        num_batches = (remaining + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\nGenerating {remaining} samples ({already} already done)")
        print(f"Batches: {num_batches} x {BATCH_SIZE} | Workers: {MAX_WORKERS} | Model: {MODEL_NAME}")
        print(f"Estimated time: ~{num_batches / (MAX_WORKERS * 0.3):.0f} min\n")

        data      = list(existing)
        completed = 0
        failures  = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(generate_batch, i): i for i in range(num_batches)}
            for future in as_completed(futures):
                results = future.result()
                completed += 1
                if results:
                    data.extend(results)
                else:
                    failures += 1
                if completed % 10 == 0 or completed == num_batches:
                    print(f"  [{completed}/{num_batches} batches] "
                          f"samples: {len(data)} | failed batches: {failures}")

        print(f"\nDone. {len(data)} total samples | {failures} failed batches")

    random.shuffle(data)
    n         = len(data)
    train_end = int(n * TRAIN_SPLIT)
    val_end   = int(n * (TRAIN_SPLIT + VAL_SPLIT))

    for split_name, split_data in [
        ("train", data[:train_end]),
        ("val",   data[train_end:val_end]),
        ("test",  data[val_end:]),
    ]:
        path = OUTPUT_DIR / f"{split_name}.jsonl"
        with open(path, 'w') as f:
            for item in split_data:
                f.write(json.dumps(item) + "\n")
        print(f"  {split_name:5s}: {len(split_data):4d} samples → {path}")

if __name__ == "__main__":
    main()