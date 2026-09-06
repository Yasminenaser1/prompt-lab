"""Scorers. Each takes (raw_text, expected, config) and returns
(score, parse_ok, predicted)."""
import json
import re


def _strip_fences(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text)
    return re.sub(r"```$", "", text).strip()


def _values_match(expected, predicted):
    if isinstance(expected, str) and isinstance(predicted, str):
        return expected.strip().lower() == predicted.strip().lower()
    return expected == predicted


def score_fields(raw_text, expected, config=None):
    """Per-field exact match over a dict of expected keys."""
    try:
        predicted = json.loads(_strip_fences(raw_text))
    except (json.JSONDecodeError, TypeError):
        return 0.0, False, None
    if not isinstance(predicted, dict):
        return 0.0, False, None
    hits = sum(1 for k, v in expected.items()
               if _values_match(v, predicted.get(k)))
    return hits / len(expected), True, predicted


def score_label(raw_text, expected, config=None):
    """Single-label classification.

    Design choice: we look for whichever known label appears FIRST in the
    response, rather than requiring exact match. This tolerates
    "The emotion is joy" (a formatting miss, not a wrong answer) without
    the false positives of a bare substring check on the expected label
    alone -- "sadness, not joy" resolves to sadness, which is correct.
    """
    text = _strip_fences(raw_text).lower()
    labels = (config or {}).get("labels", [])
    hits = [(text.find(l), l) for l in labels if l in text]
    if not hits:
        return 0.0, False, None
    predicted = min(hits)[1]
    return (1.0 if predicted == expected.strip().lower() else 0.0), True, predicted


SCORERS = {"fields": score_fields, "label": score_label}
