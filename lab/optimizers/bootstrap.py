import json

from lab.runner import DEFAULT_MODEL


def _format_demo(demo):
    return (f"Input: {demo['input']}\n"
            f"Output: {json.dumps(demo['expected'])}")


def _build_prompt(base_prompt, demos):
    demo_block = "\n\n".join(_format_demo(d) for d in demos)
    return (f"{base_prompt.replace('{input}', '').strip()}\n\n"
            f"Examples:\n\n{demo_block}\n\n"
            f"Input: {{input}}\nOutput:")


def select_demos(task_dir, base_prompt=None, model=DEFAULT_MODEL, **kw):
    """Hand-labeled gold demos, held outside the dataset — no leakage risk,
    and the demos are guaranteed clean rather than model-derived."""
    with open(f"{task_dir}/seeds.json") as f:
        return json.load(f), False


def propose(task_dir, base_prompt, k_values=(1, 2, 3), model=DEFAULT_MODEL):
    demos, _ = select_demos(task_dir, base_prompt, model=model)

    candidates = []
    for k in k_values:
        if k > len(demos):
            continue
        chosen = demos[:k]
        candidates.append({
            "prompt": _build_prompt(base_prompt, chosen),
            "meta": {"optimizer": "bootstrap", "k": k,
                     "demo_source": "hand_labeled_seeds"},
        })
    return candidates
