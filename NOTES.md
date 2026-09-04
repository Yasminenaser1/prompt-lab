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
