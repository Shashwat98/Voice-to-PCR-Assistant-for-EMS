# MEDIC — Voice-to-PCR EMS Documentation Assistant

Fully local voice-driven assistant that converts paramedic speech into structured Pre-hospital Care Reports (PCR) in real time. Wake word activation → speech recognition → structured extraction → gap detection → LLM completion — **zero cloud dependency, no PHI leaves the device**.

**Course:** CS 6170 Human-AI Interaction, Northeastern University  
**Team:** Akshatt Kain · Anubhab Das · Ksheeraj Prakash · Shashwat Singh

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [ML Models](#ml-models)
- [PCR Schema](#pcr-schema)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Evaluation Results](#evaluation-results)
- [Key Technical Details](#key-technical-details)
- [Known Gaps](#known-gaps)
- [Common Commands](#common-commands)

---

## Architecture

```
Wake Word ("Hey MEDIC")
        │
        ↓
Voice Activity Detection (VAD)
        │
        ↓
Whisper medium (local STT on MPS)
        │
        ↓
Fine-tuned T5-base (structured PCR extraction)
        │
        ↓
Gap Detection (missing field identification)
        │
        ↓
Llama 3.1 8B via Ollama (contextual field completion)
        │
        ↓
PCR JSON (23 fields)
        │
        ↓
React / Streamlit UI
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Speech-to-Text** | Whisper medium (local, MPS-accelerated) |
| **Structured Extraction** | Fine-tuned T5-base (770M planned upgrade to T5-large) |
| **Gap Completion** | Llama 3.1 8B via Ollama (fully local) |
| **Training Data** | NEMSIS v3.5 2024 public release — 60M EMS activations, all 53 US states/territories |
| **Synthetic Generation** | Gemini 2.5 Pro (batch generation, NEMSIS-grounded scenarios) |
| **Training Infra** | Google Colab L4 GPU |
| **Inference** | MacBook (MPS for Whisper + T5, Ollama for Llama) |
| **Frontend** | React / Streamlit |
| **Evaluation** | Exact Match, Field-level F1, ROUGE-L |

---

## ML Models

| Model | Task | Training Data | Output |
|---|---|---|---|
| Whisper medium | Speech → transcript | Pre-trained (OpenAI) | Raw paramedic transcript |
| T5-base (fine-tuned) | Transcript → structured PCR | 1,920 synthetic samples, 10 epochs, LR 3e-4 | 23-field PCR key-value pairs |
| Llama 3.1 8B | Gap detection + completion | Zero-shot via Ollama | Filled missing PCR fields |

**Training split**: 1,920 train / 239 val / 239 test

---

## PCR Schema

23 fields extracted from paramedic speech:

| Category | Fields |
|---|---|
| **Demographics** | age, sex |
| **Assessment** | chief_complaint, primary_impression, secondary_impression, initial_acuity |
| **Vitals** | bp_systolic, bp_diastolic, heart_rate, respiratory_rate, spo2, gcs_total, avpu, pain_scale |
| **History** | allergies, medications_current, past_medical_history, events_leading |
| **Treatment** | medications_given (drug/dose/unit/route), procedures, protocol_used |
| **Scene** | incident_location, signs_symptoms |

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) with `llama3.1:8b` pulled locally
- CUDA GPU or Apple MPS for T5 inference

### Installation

```bash
git clone https://github.com/Akshattkain/MEDIC.git
cd MEDIC
pip install -r requirements.txt

# Pull Llama for gap completion
ollama pull llama3.1:8b
```

### Training

```bash
python scripts/t5_train.py
```

### Evaluation

```bash
python scripts/evaluate_t5.py
```

---

## Project Structure

| Module | Purpose |
|---|---|
| `data/distributions.json` | NEMSIS field distributions extracted from 60M activations |
| `data/medic-synthetic/` | Raw generated data (train/val/test.json) |
| `data/medic_synthetic_fixed/` | Cleaned data after preprocessing |
| `data/eval_results.json` | T5 evaluation output |
| `data/sample_output.json` | Example PCR output |
| `models/` | T5-base fine-tuned checkpoint (5 files) |
| `scripts/preprocess_nemsis.py` | NEMSIS raw data → distributions.json |
| `scripts/patch_distributions.py` | Distribution post-processing |
| `scripts/generate_data.py` | Synthetic data generation (Gemini 2.5 Pro) |
| `scripts/fix_medic_data.py` | Data cleaning & validation |
| `scripts/t5_train.py` | T5-base fine-tuning |
| `scripts/evaluate_t5.py` | Evaluation with EM / F1 / ROUGE |

---

## Data Pipeline

```
1. Extract      preprocess_nemsis.py → distributions.json (60M NEMSIS activations)
2. Generate     generate_data.py (Gemini 2.5 Pro) → data/medic-synthetic/ (2,398 samples)
3. Clean        fix_medic_data.py → data/medic_synthetic_fixed/
4. Train        t5_train.py → models/ (best checkpoint at epoch 9)
5. Evaluate     evaluate_t5.py → data/eval_results.json
```

**Data volumes**: 60M NEMSIS activations (148 GB uncompressed), 2,398 validated synthetic samples

---

## Evaluation Results

T5-base | Trained on 1,920 samples | Evaluated on 239 test samples

| Field | Metric | Score |
|---|---|---|
| age, sex, initial_acuity, gcs_total, bp_diastolic | Exact Match | 100.0% |
| bp_systolic, heart_rate, rr, spo2, pain_scale | Exact Match | 97–99% |
| chief_complaint | Exact Match | 91.6% |
| medications_current | F1 | 96.5% |
| past_medical_history | F1 | 94.2% |
| procedures | F1 | 86.0% |
| signs_symptoms | F1 | 85.4% |
| protocol_used | Exact Match | 79.4% |
| incident_location | Exact Match | 65.7% |
| primary_impression | Exact Match | 63.6% |
| secondary_impression | Exact Match | 35.4% |
| events_leading | ROUGE-L | — |
| **Overall Combined** | | **84.96%** |

---

## Key Technical Details

| Detail | Value |
|---|---|
| T5 input format | `"extract pcr: <transcript>"` |
| T5 target format | `"field1: value1 ; field2: value2 ; ..."` with `" \| "` array separator |
| NEMSIS delimiter | `~\|~` |
| NEMSIS encoding | `ESITUATION_11REF.txt` requires `latin-1` |
| Gemini SDK | `from google import genai` (new SDK, not `google.generativeai`) |
| Gemini model | `gemini-2.5-pro` (paid GCP key) |
| Training hardware | Colab L4 GPU, batch size 32 effective |
| Inference hardware | MacBook MPS (Whisper + T5), Ollama (Llama 3.1 8B) |

---

## Known Gaps

1. NaN train loss at epochs 3 and 9 — needs `if torch.isnan(loss): continue` guard
2. `AGE_VITAL_RANGES` fix written but not yet applied to generator
3. `events_leading` evaluation uses exact match — needs ROUGE-L scoring
4. `medications_given` parsing in eval returns raw string, not structured dict
5. `primary_impression` at 63.6% EM — planned improvement via T5-large on 5,000 samples
6. `secondary_impression` at 35.4% EM — rarely stated explicitly in transcripts

---

## Common Commands

```bash
# Generate synthetic data (requires Gemini API key)
python scripts/generate_data.py

# Clean generated data
python scripts/fix_medic_data.py

# Train T5-base (Colab L4 recommended)
python scripts/t5_train.py

# Evaluate on test set
python scripts/evaluate_t5.py

# Run Ollama for gap completion
ollama serve
ollama pull llama3.1:8b

# Extract NEMSIS distributions (requires raw NEMSIS data)
python scripts/preprocess_nemsis.py
```

---

## Novelty

- **First prehospital documentation assistant** trained on nationally representative EMS distributions spanning 60M activations across rural, urban, and suburban settings in all 53 US states/territories.
- **Fully local inference** — no PHI leaves the device. Whisper + T5 + Llama all run on-device.
- **Noise robustness evaluation** — ASR error injection to measure T5 degradation under realistic speech conditions.

---

**Status**: Active Development | **Last Updated**: 2026-04-05