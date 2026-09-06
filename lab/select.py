import sys

from lab.runner import DEFAULT_MODEL, load_task, run
from lab.store import save_candidate, set_candidate_score, get_candidate
from lab.optimizers.bootstrap import propose as bootstrap_propose
from lab.optimizers.mutate import propose as mutate_propose
from lab.optimizers.append import propose as append_propose
from lab.store import save_candidate, set_candidate_score, get_candidate

OPTIMIZERS = {"bootstrap": bootstrap_propose, "mutate": mutate_propose,
              "append": append_propose}
NEEDS_RESULTS = {"mutate", "append"}


def _score_prompt(task_dir, prompt_text, split, model, candidate_id):
    """Run a candidate prompt without touching the task's prompt.txt."""
    import lab.runner as runner
    original = runner.load_task

    def patched(td, sp=None):
        _, cases = original(td, sp)
        return prompt_text, cases

    runner.load_task = patched
    try:
        _, mean = run(task_dir, split=split, model=model,
                      verbose=False, candidate_id=candidate_id)
    finally:
        runner.load_task = original
    return mean


def optimize(task_dir, optimizer="bootstrap", split="dev",
             model=DEFAULT_MODEL, start_from=None):
    if start_from:
        base_prompt = get_candidate(start_from)[1]
    else:
        base_prompt, _ = load_task(task_dir)
    base_id = save_candidate(task_dir, base_prompt, "base")
    base_score = _score_prompt(task_dir, base_prompt, split, model, base_id)
    set_candidate_score(base_id, base_score)
    print(f"base            {split} {base_score:.3f}")

    if optimizer in NEEDS_RESULTS:
        import lab.runner as _r
        _orig = _r.load_task
        _r.load_task = lambda td, sp=None: (base_prompt, _orig(td, sp)[1])
        try:
            train_results, _ = run(task_dir, split='train', model=model,
                                   verbose=False, candidate_id=base_id)
        finally:
            _r.load_task = _orig
        candidates = OPTIMIZERS[optimizer](task_dir, base_prompt,
                                           results=train_results)
    else:
        candidates = OPTIMIZERS[optimizer](task_dir, base_prompt)
    scored = []

    for cand in candidates:
        cid = save_candidate(task_dir, cand["prompt"], optimizer,
                             parent_id=base_id)
        score = _score_prompt(task_dir, cand["prompt"], split, model, cid)
        set_candidate_score(cid, score)
        scored.append((score, cid, cand))
        tag = cand['meta'].get('k', cand['meta'].get('variant'))
        label = f"{optimizer} {tag}"
        print(f"{label:<15} {split} {score:.3f}")

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_id, best = scored[0]
    delta = best_score - base_score
    print(f"\nbest: candidate {best_id}  {best_score:.3f}  "
          f"({delta:+.3f} vs base)")
    return best, best_score, base_score


if __name__ == "__main__":
    task = sys.argv[1]
    split = sys.argv[2] if len(sys.argv) > 2 else "dev"
    optimizer = sys.argv[3] if len(sys.argv) > 3 else "bootstrap"
    optimize(task, optimizer=optimizer, split=split)
