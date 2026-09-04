import json
import re
import sys
import requests
from lab.cache import cached_call
from lab.store import save_run

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"


def load_task(task_dir, split=None):
    with open(f"{task_dir}/prompt.txt") as f:
        prompt_template = f.read().strip()
    with open(f"{task_dir}/dataset.json") as f:
        cases = json.load(f)
    if split:
        cases = [c for c in cases if c.get("split") == split]
    return prompt_template, cases


def call_model(prompt, model=DEFAULT_MODEL, force_json=True,
               temperature=0.0):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            **({"format": "json"} if force_json else {}),
            "options": {"temperature": temperature},
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["response"]


def _strip_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


def _values_match(expected, predicted):
    if isinstance(expected, str) and isinstance(predicted, str):
        return expected.strip().lower() == predicted.strip().lower()
    return expected == predicted


def score_case(raw_text, expected):
    try:
        predicted = json.loads(_strip_fences(raw_text))
    except (json.JSONDecodeError, TypeError):
        return 0.0, False, None
    if not isinstance(predicted, dict):
        return 0.0, False, None

    hits = sum(
        1 for k, v in expected.items() if _values_match(v, predicted.get(k))
    )
    return hits / len(expected), True, predicted


def run(task_dir, split="train", model=DEFAULT_MODEL, verbose=True, candidate_id=None):
    prompt_template, cases = load_task(task_dir, split)
    results = []

    for case in cases:
        prompt = prompt_template.replace("{input}", case["input"])
        try:
             raw, hit = cached_call(prompt, model=model)
        except requests.RequestException as e:
            print(f"{case['id']}  REQUEST FAILED: {e}")
            results.append({"case_id": case["id"], "score": 0.0,
                            "parse_ok": False, "raw": None, "predicted": None})
            continue

        score, parse_ok, predicted = score_case(raw, case["expected"])
        results.append({"case_id": case["id"], "score": score,
                        "parse_ok": parse_ok, "raw": raw, "predicted": predicted})
        if verbose:
            flag = "" if parse_ok else "  [PARSE FAIL]"
            print(f"{case['id']}  {score:.2f}{flag}")

    mean = sum(r["score"] for r in results) / len(results) if results else 0.0
    run_id = save_run(task_dir, model, prompt_template, split, mean,
                      results, candidate_id=candidate_id)
    if verbose:
        print(f"\n{split}: {len(results)} cases, mean {mean:.3f}  (run {run_id})")
    return results, mean


if __name__ == "__main__":
    task = sys.argv[1]
    split = sys.argv[2] if len(sys.argv) > 2 else "train"
    run(task, split=split)
