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
