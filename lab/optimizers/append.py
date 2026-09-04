import json

from lab.cache import cached_call
from lab.runner import DEFAULT_MODEL, load_task

META_PROMPT = """A prompt is producing these errors. "expected" is correct, \
"got" is what the model returned:

{failures}

Write ONE short instruction line that would prevent these specific errors. \
State a general rule, not a list of the examples above. Output only the \
instruction line, nothing else.
"""


def _format_failures(results, cases, limit=4):
    by_id = {c["id"]: c for c in cases}
    worst = sorted([r for r in results if r["score"] < 1.0],
                   key=lambda r: r["score"])[:limit]
    return "\n\n".join(
        f"input:    {by_id[r['case_id']]['input']}\n"
        f"expected: {json.dumps(by_id[r['case_id']]['expected'])}\n"
        f"got:      {json.dumps(r.get('predicted'))}"
        for r in worst
    )


def _insert_rule(base_prompt, rule):
    """Append the rule to the instruction block, before any examples."""
    marker = "\n\nExamples:"
    if marker in base_prompt:
        head, tail = base_prompt.split(marker, 1)
        return f"{head}\n{rule}{marker}{tail}"
    return f"{base_prompt.rstrip()}\n{rule}"


def propose(task_dir, base_prompt, results=None, n=4,
            model=DEFAULT_MODEL, temperature=0.9):
    if not results:
        raise ValueError("append needs results from a prior run")

    _, cases = load_task(task_dir, "train")
    meta = META_PROMPT.format(failures=_format_failures(results, cases))

    candidates = []
    seen = set()
    for i in range(n):
        raw, _ = cached_call(meta + f"\n\n[variant {i}]", model=model,
                             temperature=temperature, force_json=False)
        rule = raw.strip().strip("`").strip().split("\n")[0].strip()
        if not rule or len(rule) > 300 or rule in seen:
            continue
        seen.add(rule)
        candidates.append({
            "prompt": _insert_rule(base_prompt, rule),
            "meta": {"optimizer": "append", "variant": i, "rule": rule},
        })
    return candidates
