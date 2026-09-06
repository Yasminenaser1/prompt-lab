# prompt-lab — working notes

## Baseline (Sep 4)
- Base prompt: "Extract the job info from this text as JSON: {input}"
- train 0.250, dev 0.167
- Failure mode is **schema drift, not comprehension**. Model returned
  `jobTitle` / `workType` / `onsiteDays` instead of the expected
  `title` / `remote`. Values were mostly right, keys were invented.
- c05 (confidential company): returned `company: "confidential"` rather
  than `null` — described the absence instead of representing it.
  Also put "remote" into the `location` field.
- Zero parse failures throughout. `format: json` + temperature 0 held.

## bootstrap (Sep 4)
- Hand-labeled seeds in `tasks/extract/seeds.json`, held outside the
  dataset — no leakage, demos guaranteed clean. Tradeoff: some of the
  gain is human, not optimizer. Seeds kept deliberately minimal
  (schema only, no normalization hints).
- dev 0.167 -> 0.667 (+0.500)
- k=1, k=2, k=3 all scored 0.667 — indistinguishable. Dev split is only
  3 cases, so scores quantize to 1/12; this ablation is underpowered.
  Do NOT claim "example count doesn't matter" from this.

## Dataset caveats
- c03 expects "San Francisco, CA" inferred from "Union Square" —
  Union Square also exists in NYC. Arguably unfair ground truth.
- c05/c08 expect `null` company where text says "confidential" /
  "anonymous". Defensible, but a judgment call, not fact.

## Open
- Haven't inspected which dev cases still fail after bootstrap.
- mutate written, not yet run.

## Post-bootstrap failures (candidate 2, dev 0.667)
- Schema drift fully resolved — all keys and types correct.
- Remaining errors are location normalization, not extraction:
  c06 "Chicago" (no state), c07 "Dallas, Texas" (not abbreviated),
  c08 "NYC" (not expanded). Expected format is "City, ST".
- Seeds never demonstrated the "City, ST" rule (kept minimal on purpose),
  so this is real headroom for mutate to discover.
- c08 also returned company "Anonymous fintech startup" vs expected null
  — same describe-the-absence pattern as c05. Partly a ground-truth
  judgment call on my side.

## mutate (Sep 4)
- 4 variants from base: dev 0.083 / 0.333 / 0.417 / 0.583.
  High variance — 7x spread from the same procedure at temp 0.8.
  Worst variant scored BELOW base (0.083 vs 0.167).
- Best mutate (0.583) still lost to bootstrap (0.667).
- Both mutated from base, not from the bootstrap winner — chaining
  untested (needs start_from / hillclimb).
- Winning prompt (cand 22) fixed the schema by naming the four keys —
  that's where the gain came from. Everything else was OVERFIT to the
  3 train failures it was shown: literal string rules like
  '"Block from" indicates location is nearby', '"5 days" indicates
  non-remote', plus an invented "non-permanent employment" concept
  not in the schema, and a wrong prior ("assume remote unless stated").
- It never discovered the "City, ST" normalization rule I predicted.
- Takeaway: textual-gradient mutation memorizes the failures it's shown.
  Clean demos generalized better than derived rules on this task.
- Worst variant (cand 17, dev 0.083): "Extract company and title from the
  job posting, and the rest of the info as remote, location, and duration.
  {input}" — reads fine to a human, scores below the one-line base.
  Two causes: invented a 5th field ("duration", from the c05 contract
  case) and dropped the word "JSON" entirely.
- Core lesson: a prompt cannot be evaluated by reading it. Cand 17 reads
  BETTER than base and scores half as well. This is the argument for the
  harness.

## Chaining bootstrap -> mutate (Sep 4)
- start_from=2 (bootstrap winner, dev 0.667) as mutate's starting prompt.
- Only 2 of 4 variants survived the {input} guard — mutating a long
  few-shot prompt breaks more often than mutating a one-liner.
- Results: 0.667 (tie) and 0.250 (-0.417). Net +0.000.
- Conclusion: mutate could not improve on bootstrap's output and had a
  coin-flip chance of destroying it. On this task, mutation's only real
  contribution was fixing schema drift — which bootstrap does better,
  deterministically, and without overfitting to train failures.
- Location normalization ("City, ST") remains unsolved by both methods.

## The 0.667 ceiling (Sep 4)
- append: 4 rules generated, ALL about key naming, none about location —
  despite train failures showing location wrong in 4/4 cases. The
  meta-model pattern-matched to "extraction task -> say something about
  schemas" instead of reading the actual errors. Best 0.667 (+0.000).
- Hand-written rule ("Normalize location to City, ST...") scored 0.583 —
  WORSE than no rule. Per-case diff vs cand 2: every location identical
  (rule ignored entirely), and c07's title regressed from
  "Sr. DevOps Engineer" to "SR. DEVOPS ENGINEER!!!".
- Conclusion: ceiling is llama3.1:8b's instruction-following, not the
  search method. Prose rules are ignored AND still perturb unrelated
  fields (rule interference).
- Next test: change the DEMOS, not the instructions — a seed showing
  "Denver" -> "Denver, CO" demonstrates the transform instead of
  describing it. Hypothesis: demonstration beats instruction on 8b.

## Final results (Sep 4)
- k=4 test: adding a "Portland" -> "Portland, OR" demo changed nothing
  (0.667 both). Demonstration didn't beat instruction either — the
  ceiling is the model, not the method.
- HELD-OUT TEST (scored once, never tuned against):
    base           test 0.250
    bootstrap k=3  test 0.875
- Caveat: test is only 2 cases; scores quantize to 1/8. Test > dev is
  small-sample noise, not evidence the prompt is better than dev showed.
- Story: prompt optimization captured the schema-compliance gain
  immediately, then hit a hard capability ceiling that three optimizers,
  a hand-written rule, and a targeted demo all failed to move.

## Task 2: emotion classification (dair-ai/emotion, 200 cases)
- 100 train / 60 dev / 40 test, shuffled with seed 0. Imbalanced:
  joy 36% of train, surprise 5%. Majority-class floor is 0.36.
- Base prompt ("What emotion is in this text? {input}") scored train
  0.140 -- BELOW the majority-class floor. 6:53 uncached.
- Failure mode: open-vocabulary answers in prose. Model returned
  "EXUBERANCE", "amusement", "delight", "relief", "gratitude" -- all
  defensible readings, none in the six-label set. Comprehension is fine;
  it was never told the options exist.
- Scorer caveat: first-known-label-wins means e005 ("sadness or grief")
  scored 1.0 partly by word order. Documented in scorers.py.

## Emotion + bootstrap (3B) — unexpected result
- Switched to llama3.2:3b after 8b caused thermal timeouts at 60-case
  dev. Splits reduced to 60/30/20.
- 3B base scored train 0.133 vs 8B's 0.140 on the same task — the
  open-vocabulary failure is NOT a model-size problem.
- bootstrap on emotion: base 0.133, k=1 0.067, k=2 0.133, k=3 0.100.
  Best +0.000. Demos did nothing here, opposite of the extraction task.
- Every dev case was a parse fail (predicted=None) — the model still
  produced no label word despite two worked examples in the prompt.
- Prompt itself verified well-formed, so this is not a template bug.
- OPEN: check whether raw responses are empty (3B + trailing "Output:")
  vs genuinely off-vocabulary. That distinction decides whether this is
  a real finding or a mechanical artifact.

## Emotion: demos vs. instructions (3B, 30-case dev) — REVERSED from task 1
- Investigated the all-parse-fail result. Two failure modes in raw output:
  off-vocabulary answers ("gratitude", "guilt") AND prompt echoing
  (model continued the few-shot pattern, emitting "Input: ..." instead
  of answering). Echo is a 3B + trailing "Output:" artifact.
- Removed the trailing "Output:": dev 0.133, unchanged. Echo was not
  the cause.
- Hand-written prompt STATING the six labels explicitly: dev 0.333.
  2.5x over base (0.133), while every few-shot variant scored 0.133.
- FINDING: on classification, telling the model the label set works and
  showing examples does not. This is the reverse of the extraction task,
  where demos beat every instruction (human and optimizer written).
  Interpretation: demos convey FORMAT well but cannot convey that a
  vocabulary is CLOSED and has exactly six members. One sentence can.
- Caveat: 0.333 is still below the 0.36 majority-class floor. The
  vocabulary problem is fixed; the classification itself is still poor.

## Instruction PLACEMENT beats instruction content (emotion, 3B)
- append's _insert_rule split on "\n\nExamples:" and fell through to
  end-append for prompts without a demo block. On the emotion prompt
  that put the rule AFTER the answer cue ("Emotion:"), breaking the
  prompt structurally. All 4 variants scored below base (0.100-0.267).
- Fixed: tasks now declare config["insert_before"] so the rule lands at
  the end of the instruction block. Same optimizer, same generation
  process, re-run: 0.167-0.367. Best (0.367) beat base (0.333) and
  cleared the 0.36 majority-class floor for the first time.
- FINDING: placement mattered more than content. Identical rule-writing
  produced a 0.267 ceiling in the wrong position and 0.367 in the right
  one.
- CAVEAT: the winning rule is semantically empty -- "for emotional words
  like 'joy', 'love'... return the corresponding sentiment value if a
  related text is detected". It restates the task. +0.033 on 30 cases is
  one case flipping, so this is inside noise. Cannot distinguish between
  (a) noise, (b) rule presence mattering more than content, (c) real gain.
- Across both tasks, append's generated rules never tracked the actual
  errors: key-naming rules for location failures on extraction, a
  circular restatement here.
