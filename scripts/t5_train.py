"""
MEDIC T5-base Fine-tuning
Trains T5-base to extract PCR fields from paramedic transcripts.

"""

import json
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from torch.cuda.amp import autocast, GradScaler

# === CONFIG ===
MODEL_NAME     = "t5-base"
TRAIN_PATH     = "./train.jsonl"
VAL_PATH       = "./val.jsonl"
OUTPUT_DIR     = "./medic_t5"
EPOCHS         = 10
BATCH_SIZE     = 8
GRAD_ACCUM     = 4          # effective batch size = 32
LR             = 3e-4
MAX_INPUT_LEN  = 512
MAX_TARGET_LEN = 768
WARMUP_RATIO   = 0.1
SAVE_EVERY     = 1          # save checkpoint every N epochs
DEVICE         = "cuda" if torch.cuda.is_available() else "cpu"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
print(f"Device: {DEVICE} | {torch.cuda.get_device_name(0)}")

# === PCR FIELDS WE EXTRACT ===
# T5 input:  "extract pcr: <transcript>"
# T5 target: flat JSON string of PCR fields

SCALAR_FIELDS = [
    "age", "sex", "chief_complaint", "primary_impression",
    "secondary_impression", "incident_location", "initial_acuity",
    "protocol_used", "bp_systolic", "bp_diastolic", "heart_rate",
    "respiratory_rate", "spo2", "gcs_total", "avpu", "pain_scale",
    "events_leading",
]
ARRAY_FIELDS = [
    "allergies", "medications_current", "past_medical_history",
    "procedures", "signs_symptoms",
]
# medications_given is complex — handle separately
MED_FIELDS = ["medications_given"]

def pcr_to_target_string(pcr):
    """Convert PCR JSON to a flat target string T5 will generate."""
    parts = []
    for field in SCALAR_FIELDS:
        val = pcr.get(field)
        if val is not None:
            parts.append(f"{field}: {val}")
        else:
            parts.append(f"{field}: null")

    for field in ARRAY_FIELDS:
        val = pcr.get(field)
        if val and isinstance(val, list):
            parts.append(f"{field}: {' | '.join(str(v) for v in val)}")
        else:
            parts.append(f"{field}: null")

    meds = pcr.get("medications_given")
    if meds and isinstance(meds, list):
        med_strs = []
        for m in meds:
            if isinstance(m, dict):
                med_strs.append(
                    f"{m.get('drug','?')} {m.get('dose','?')}{m.get('unit','?')} {m.get('route','?')}"
                )
        parts.append(f"medications_given: {' | '.join(med_strs)}")
    else:
        parts.append("medications_given: null")

    return " ; ".join(parts)

def target_string_to_pcr(text):
    """Parse T5 output back to PCR dict for evaluation."""
    pcr = {}
    for part in text.split(" ; "):
        part = part.strip()
        if ": " not in part:
            continue
        key, val = part.split(": ", 1)
        key = key.strip()
        val = val.strip()
        if val == "null":
            pcr[key] = None
        elif key in ARRAY_FIELDS:
            pcr[key] = [v.strip() for v in val.split(" | ")] if val != "null" else None
        elif key == "medications_given":
            meds = []
            for med_str in val.split(" | "):
                parts = med_str.strip().split()
                if len(parts) >= 3:
                    meds.append({"drug": parts[0], "raw": med_str})
            pcr[key] = meds if meds else None
        elif key in {"age", "bp_systolic", "bp_diastolic", "heart_rate",
                     "respiratory_rate", "spo2", "gcs_total", "pain_scale"}:
            try:
                pcr[key] = float(val) if "." in val else int(val)
            except ValueError:
                pcr[key] = val
        else:
            pcr[key] = val
    return pcr

class MEDICDataset(Dataset):
    def __init__(self, path, tokenizer):
        self.samples = []
        self.tokenizer = tokenizer
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    s = json.loads(line)
                    transcript = s.get("transcript", "").strip()
                    pcr        = s.get("pcr_json", {})
                    if not transcript or not pcr:
                        continue
                    target = pcr_to_target_string(pcr)
                    self.samples.append((transcript, target))
                except Exception:
                    continue
        print(f"  Loaded {len(self.samples)} samples from {path}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        transcript, target = self.samples[idx]
        input_text  = f"extract pcr: {transcript}"
        return input_text, target

def collate_fn(batch, tokenizer):
    inputs, targets = zip(*batch)
    enc = tokenizer(
        list(inputs),
        max_length=MAX_INPUT_LEN,
        truncation=True,
        padding="longest",
        return_tensors="pt",
    )
    with tokenizer.as_target_tokenizer():
        dec = tokenizer(
            list(targets),
            max_length=MAX_TARGET_LEN,
            truncation=True,
            padding="longest",
            return_tensors="pt",
        )
    labels = dec["input_ids"]
    labels[labels == tokenizer.pad_token_id] = -100
    return {
        "input_ids":      enc["input_ids"],
        "attention_mask": enc["attention_mask"],
        "labels":         labels,
    }

def compute_field_f1(pred_pcr, gold_pcr):
    """Simple field-level F1 — fraction of non-null fields correctly extracted."""
    correct = 0
    total   = 0
    for field in SCALAR_FIELDS + ARRAY_FIELDS:
        gold = gold_pcr.get(field)
        pred = pred_pcr.get(field)
        if gold is None:
            continue
        total += 1
        if isinstance(gold, list):
            gold_set = set(str(g).lower() for g in gold)
            pred_set = set(str(p).lower() for p in pred) if isinstance(pred, list) else set()
            if gold_set and pred_set:
                correct += len(gold_set & pred_set) / len(gold_set | pred_set)
        else:
            if str(pred).lower().strip() == str(gold).lower().strip():
                correct += 1
    return correct / total if total > 0 else 0.0

def evaluate(model, loader, tokenizer, num_batches=20):
    model.eval()
    total_loss = 0.0
    field_f1s  = []
    with torch.no_grad():
        for i, batch in enumerate(loader):
            if i >= num_batches:
                break
            input_ids      = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels         = batch["labels"].to(DEVICE)

            loss = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            ).loss
            total_loss += loss.item()

            # generate and compute field F1 on first batch only
            if i == 0:
                preds = model.generate(
                    input_ids=input_ids[:4],
                    attention_mask=attention_mask[:4],
                    max_new_tokens=MAX_TARGET_LEN,
                    num_beams=4,
                )
                pred_texts = tokenizer.batch_decode(preds, skip_special_tokens=True)
                gold_texts = tokenizer.batch_decode(
                    labels[:4].masked_fill(labels[:4] == -100, tokenizer.pad_token_id),
                    skip_special_tokens=True,
                )
                for pred_t, gold_t in zip(pred_texts, gold_texts):
                    pred_pcr = target_string_to_pcr(pred_t)
                    gold_pcr = target_string_to_pcr(gold_t)
                    field_f1s.append(compute_field_f1(pred_pcr, gold_pcr))

    avg_loss = total_loss / min(num_batches, len(loader))
    avg_f1   = np.mean(field_f1s) if field_f1s else 0.0
    model.train()
    return avg_loss, avg_f1

# === LOAD MODEL + TOKENIZER ===
print(f"\nLoading {MODEL_NAME}...")
tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
model     = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(DEVICE)
print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")

# === DATASETS ===
print("\nLoading datasets...")
train_ds = MEDICDataset(TRAIN_PATH, tokenizer)
val_ds   = MEDICDataset(VAL_PATH,   tokenizer)

from functools import partial
collate  = partial(collate_fn, tokenizer=tokenizer)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                          collate_fn=collate, num_workers=2, pin_memory=True)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                          collate_fn=collate, num_workers=2, pin_memory=True)

# === OPTIMIZER + SCHEDULER ===
total_steps   = (len(train_loader) // GRAD_ACCUM) * EPOCHS
warmup_steps  = int(total_steps * WARMUP_RATIO)

optimizer = AdamW(model.parameters(), lr=LR, weight_decay=0.01)
scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
scaler    = GradScaler()

print(f"\nTotal steps: {total_steps} | Warmup: {warmup_steps}")
print(f"Effective batch size: {BATCH_SIZE * GRAD_ACCUM}")
print(f"\nStarting training...\n")

# === TRAINING LOOP ===
best_val_loss = float("inf")

for epoch in range(1, EPOCHS + 1):
    model.train()
    epoch_loss = 0.0
    optimizer.zero_grad()

    for step, batch in enumerate(train_loader):
        input_ids      = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels         = batch["labels"].to(DEVICE)

        with autocast():
            loss = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            ).loss / GRAD_ACCUM

        scaler.scale(loss).backward()
        epoch_loss += loss.item() * GRAD_ACCUM

        if (step + 1) % GRAD_ACCUM == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            optimizer.zero_grad()

    avg_train_loss = epoch_loss / len(train_loader)
    val_loss, val_f1 = evaluate(model, val_loader, tokenizer)

    print(f"Epoch {epoch:02d}/{EPOCHS} | "
          f"train_loss: {avg_train_loss:.4f} | "
          f"val_loss: {val_loss:.4f} | "
          f"val_field_f1: {val_f1:.4f}")

    # save best
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        model.save_pretrained(f"{OUTPUT_DIR}/best")
        tokenizer.save_pretrained(f"{OUTPUT_DIR}/best")
        print(f"  → Saved best model (val_loss={val_loss:.4f})")

    # save checkpoint every epoch
    if epoch % SAVE_EVERY == 0:
        model.save_pretrained(f"{OUTPUT_DIR}/epoch_{epoch}")
        tokenizer.save_pretrained(f"{OUTPUT_DIR}/epoch_{epoch}")

print("\nTraining complete.")
print(f"Best model saved to: {OUTPUT_DIR}/best")