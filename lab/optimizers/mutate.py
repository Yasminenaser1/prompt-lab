import json

from lab.cache import cached_call
from lab.runner import DEFAULT_MODEL, load_task

META_PROMPT = """You are improving a prompt used to extract structured JSON \
from job postings.

CURRENT PROMPT:
---
{current}
---

This prompt produced these failures. "expected" is correct, "got" is what \
the model returned:

{failures}

Rewrite the prompt so it avoids these specific failures. Rules:
- Keep the literal placeholder {{input}} exactly once, where the input goes.
- Do not add commentary, explanation, or markdown fences.
- Output only the new prompt text.
"""


def _format_failures(results, cases, limit=3):
    by_id = {c["id"]: c for c in cases}
    worst = sorted([r for r in results if r["score"] < 1.0],
                   key=lambda r: r["score"])[:limit]
    blocks = []
    for r in worst:
        case = by_id[r["case_id"]]
        blocks.append(
            f"input:    {case['input']}\n"
            f"expected: {json.dumps(case['expected'])}\n"
            f"got:      {json.dumps(r.get('predicted'))}"
        )
    return "\n\n".join(blocks)


def propose(task_dir, base_prompt, results=None, n=4,
            model=DEFAULT_MODEL, temperature=0.8):
    """Textual-gradient style: show the model its own failures, ask for a
    rewrite. Needs `results` from a prior run of base_prompt."""
    if not results:
        raise ValueError("mutate needs results from a prior run")

    _, cases = load_task(task_dir, "train")
    failures = _format_failures(results, cases)
    meta = META_PROMPT.format(current=base_prompt, failures=failures)

    candidates = []
    seen = set()
    for i in range(n):
        raw, _ = cached_call(meta + f"\n\n[variant {i}]", model=model,
                             temperature=temperature)
        new_prompt = raw.strip().strip("`").strip()
        if "{input}" not in new_prompt or new_prompt in seen:
            continue
        seen.add(new_prompt)
        candidates.append({
            "prompt": new_prompt,
            "meta": {"optimizer": "mutate", "variant": i},
        })
    return candidates
