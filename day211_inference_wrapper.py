"""
day211_inference_wrapper.py (Day215 local/merged-model version)

Production inference wrapper for the TeleServe India ticket priority classifier.
Same public contract as the original Day211 module (predict_ticket_priority(text) ->
{priority, confidence, all_probs, routing_decision, truncated_input, error}), but
loads the Day215 merged model (plain full precision, no bitsandbytes/PEFT/GPU
needed) instead of the original 4-bit base + LoRA adapter combo. This is what
lets it run on a laptop with no CUDA.
"""

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ---- Constants (same values as Day210/211; loading mechanism changed for Day215) ----
MODEL_PATH = "teleserve_merged_215"  # merged model+tokenizer folder, same dir as this file
ID2LABEL = {0: "P1", 1: "P2", 2: "P3"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}
CONFIDENCE_THRESHOLD = 0.60  # from Day210: avg conf correct 0.8766, incorrect 0.6401
MAX_INPUT_LENGTH = 2000

# ---- Lazy loading (load on first call) ----
_model = None
_tokenizer = None


def _load_model():
    """Load the merged model and tokenizer once. Plain full precision, CPU-friendly."""
    global _model, _tokenizer
    if _model is not None:
        return
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    _model.eval()


def predict_ticket_priority(text: str) -> dict:
    """
    Predict priority and confidence for a ticket text.

    Args:
        text (str): Raw customer ticket text.

    Returns:
        dict: {
            "priority": str,           # "P1", "P2", or "P3"
            "confidence": float,       # softmax probability of predicted class
            "all_probs": dict,         # {"P1": prob, "P2": prob, "P3": prob}
            "routing_decision": str,   # "auto_route" or "human_review"
            "truncated_input": bool,   # True if input was longer than 2000 chars
            "error": str or None       # None if successful, else error message
        }
    """
    _load_model()

    # ---- Input validation (same as Day211 Task 3) ----
    if not isinstance(text, str):
        return {
            "error": "input must be a string",
            "priority": None,
            "confidence": None,
            "all_probs": None,
            "routing_decision": None,
            "truncated_input": False,
        }
    stripped = text.strip()
    if len(stripped) == 0:
        return {
            "error": "input too short (empty or whitespace)",
            "priority": None,
            "confidence": None,
            "all_probs": None,
            "routing_decision": None,
            "truncated_input": False,
        }
    truncated = False
    if len(stripped) > MAX_INPUT_LENGTH:
        stripped = stripped[:MAX_INPUT_LENGTH]
        truncated = True

    # ---- Inference (CPU, no .cuda() call needed) ----
    inputs = _tokenizer(stripped, truncation=True, padding=True, max_length=64, return_tensors="pt")

    with torch.no_grad():
        logits = _model(**inputs).logits
        probs = F.softmax(logits, dim=-1).numpy()[0]

    probs_dict = {ID2LABEL[i]: float(probs[i]) for i in range(3)}
    pred_label = max(probs_dict, key=probs_dict.get)
    confidence = probs_dict[pred_label]
    routing = "human_review" if confidence < CONFIDENCE_THRESHOLD else "auto_route"

    return {
        "priority": pred_label,
        "confidence": round(confidence, 4),
        "all_probs": probs_dict,
        "routing_decision": routing,
        "truncated_input": truncated,
        "error": None,
    }
