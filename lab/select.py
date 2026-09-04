import sys

from lab.runner import DEFAULT_MODEL, load_task, run
from lab.store import save_candidate, set_candidate_score
from lab.optimizers.bootstrap import propose as bootstrap_propose

OPTIMIZERS = {"bootstrap": bootstrap_propose}


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
             model=DEFAULT_MODEL):
    base_prompt, _ = load_task(task_dir)
    base_id = save_candidate(task_dir, base_prompt, "base")
    base_score = _score_prompt(task_dir, base_prompt, split, model, base_id)
    set_candidate_score(base_id, base_score)
    print(f"base            {split} {base_score:.3f}")

    candidates = OPTIMIZERS[optimizer](task_dir, base_prompt)
    scored = []

    for cand in candidates:
        cid = save_candidate(task_dir, cand["prompt"], optimizer,
                             parent_id=base_id)
        score = _score_prompt(task_dir, cand["prompt"], split, model, cid)
        set_candidate_score(cid, score)
        scored.append((score, cid, cand))
        label = f"{optimizer} k={cand['meta'].get('k')}"
        print(f"{label:<15} {split} {score:.3f}")

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_id, best = scored[0]
    delta = best_score - base_score
    print(f"\nbest: candidate {best_id}  {best_score:.3f}  "
          f"({delta:+.3f} vs base)")
    return best, best_score, base_score


if __name__ == "__main__":
    task = sys.argv[1]
    optimize(task, split=sys.argv[2] if len(sys.argv) > 2 else "dev")
