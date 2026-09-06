# prompt-lab

An eval harness and prompt optimizer for local LLMs. Runs entirely on
Ollama — no hosted APIs, no keys, no cost.

Given a task (dataset, starting prompt, scorer), it searches for a better
prompt and records every candidate and score in SQLite, so results are
reproducible and comparable. Two tasks are included, deliberately chosen
to be structurally different: structured extraction and multi-class
classification.

![results](results.png)

## Results

Held-out test splits, scored once at the end and never optimized against.

| | extraction (llama3.1:8b) | emotion (llama3.2:3b) |
|---|---|---|
| base prompt | 0.250 | 0.000 |
| best optimized | **0.875** | **0.450** |
| winning method | bootstrap (few-shot demos) | mutate (prompt rewrite) |

**Extraction** — pull `{company, title, location, remote}` as JSON from
messy job postings. 10 hand-written cases, scored on per-field exact match.

**Emotion** — 6-class classification (sadness/joy/love/anger/fear/surprise)
on 110 cases sampled from `dair-ai/emotion`, scored on label match.

## What I found

**Different task types have different winners.** On extraction, few-shot
demos beat every LLM-driven method — bootstrap hit 0.667 on dev while
mutate topped out at 0.583 and append at 0.667 with no gain over base.
On emotion the ranking reversed: every few-shot variant scored 0.133,
identical to base, while simply *stating* the six labels in prose jumped
to 0.333. Demos convey format well but cannot convey that a vocabulary is
closed and has exactly six members. One sentence can.

**Added instructions rarely help and often hurt.** This held across both
tasks and both models. A hand-written rule stating the location format
explicitly *lowered* the extraction score (0.667 → 0.583) — locations were
unchanged and an unrelated field regressed. On emotion, append's
best-scoring generated rule was semantically circular ("for emotional
words like 'joy', 'love', return the corresponding sentiment value").
And mutate's winning prompt beat the human-written one by *deleting* an
instruction. What moves the score is structural — the label set, rule
placement, demo format — not prose.

**Placement mattered more than content.** `append` inserted its rule at
the end of the prompt, which on the emotion task landed it *after* the
answer cue (`Emotion:`). All four variants scored below base. Fixing the
insertion point — tasks now declare `insert_before` in their config — and
re-running the identical generation process moved the range from
0.100–0.267 to 0.167–0.367. Same rules, different position, opposite
result.

**A prompt can't be evaluated by reading it.** The worst mutate variant on
extraction reads perfectly well and scores half as well as the lazy
one-line base: it dropped the word "JSON" and invented a fifth field.

**Failure-driven optimizers don't reliably read their failures.** On
extraction, append generated four rules about key naming while every
failure it was shown had the location wrong. Part of this traces to a bug
(below), but the pattern survived the fix.

## A bug worth reporting

With `start_from` set — chaining one optimizer onto another's output —
the train run that collects failures still read `prompt.txt` from disk
rather than the prompt being optimized. So the optimizer was shown the
*wrong prompt's* failures. Before the fix, mutate on emotion produced zero
valid candidates and crashed. After, three of four were valid and the best
scored 0.433, a +0.100 gain. Any conclusion drawn from a chained run
before this fix is suspect, which is why the extraction append result is
reported with that caveat rather than as a clean finding.

## Caveats

The extraction task has 10 hand-written cases (5/3/2). Dev scores quantize
to 1/12 and test to 1/8, so its ablations are underpowered — the k=1/2/3
sweep scored identically, which is not evidence that example count doesn't
matter. Two cases encode judgment calls rather than ground truth:
"Union Square" → "San Francisco, CA" is ambiguous, and "confidential" →
`null` company is defensible either way.

The emotion task is larger (60/30/20) but imbalanced — joy is 36% of
train, so a prompt that always answered "joy" would score 0.36. Only the
final mutate winner clearly clears that floor.

The two tasks use different models (8b and 3b), because the 8b caused
thermal timeouts on a laptop at 60-case dev splits. Cross-task comparisons
are therefore confounded by model size. One check against this: the 3b and
8b base prompts scored 0.133 and 0.140 on the same emotion train split, so
the vocabulary failure at least is not a size effect.

## Running it
git add -A && git commit -m "Emotion held-out test 0.000 -> 0.450" && git push
cat > README.md << 'PYEOF'
# prompt-lab

An eval harness and prompt optimizer for local LLMs. Runs entirely on
Ollama — no hosted APIs, no keys, no cost.

Given a task (dataset, starting prompt, scorer), it searches for a better
prompt and records every candidate and score in SQLite, so results are
reproducible and comparable. Two tasks are included, deliberately chosen
to be structurally different: structured extraction and multi-class
classification.

![results](results.png)

## Results

Held-out test splits, scored once at the end and never optimized against.

| | extraction (llama3.1:8b) | emotion (llama3.2:3b) |
|---|---|---|
| base prompt | 0.250 | 0.000 |
| best optimized | **0.875** | **0.450** |
| winning method | bootstrap (few-shot demos) | mutate (prompt rewrite) |

**Extraction** — pull `{company, title, location, remote}` as JSON from
messy job postings. 10 hand-written cases, scored on per-field exact match.

**Emotion** — 6-class classification (sadness/joy/love/anger/fear/surprise)
on 110 cases sampled from `dair-ai/emotion`, scored on label match.

## What I found

**Different task types have different winners.** On extraction, few-shot
demos beat every LLM-driven method — bootstrap hit 0.667 on dev while
mutate topped out at 0.583 and append at 0.667 with no gain over base.
On emotion the ranking reversed: every few-shot variant scored 0.133,
identical to base, while simply *stating* the six labels in prose jumped
to 0.333. Demos convey format well but cannot convey that a vocabulary is
closed and has exactly six members. One sentence can.

**Added instructions rarely help and often hurt.** This held across both
tasks and both models. A hand-written rule stating the location format
explicitly *lowered* the extraction score (0.667 → 0.583) — locations were
unchanged and an unrelated field regressed. On emotion, append's
best-scoring generated rule was semantically circular ("for emotional
words like 'joy', 'love', return the corresponding sentiment value").
And mutate's winning prompt beat the human-written one by *deleting* an
instruction. What moves the score is structural — the label set, rule
placement, demo format — not prose.

**Placement mattered more than content.** `append` inserted its rule at
the end of the prompt, which on the emotion task landed it *after* the
answer cue (`Emotion:`). All four variants scored below base. Fixing the
insertion point — tasks now declare `insert_before` in their config — and
re-running the identical generation process moved the range from
0.100–0.267 to 0.167–0.367. Same rules, different position, opposite
result.

**A prompt can't be evaluated by reading it.** The worst mutate variant on
extraction reads perfectly well and scores half as well as the lazy
one-line base: it dropped the word "JSON" and invented a fifth field.

**Failure-driven optimizers don't reliably read their failures.** On
extraction, append generated four rules about key naming while every
failure it was shown had the location wrong. Part of this traces to a bug
(below), but the pattern survived the fix.

## A bug worth reporting

With `start_from` set — chaining one optimizer onto another's output —
the train run that collects failures still read `prompt.txt` from disk
rather than the prompt being optimized. So the optimizer was shown the
*wrong prompt's* failures. Before the fix, mutate on emotion produced zero
valid candidates and crashed. After, three of four were valid and the best
scored 0.433, a +0.100 gain. Any conclusion drawn from a chained run
before this fix is suspect, which is why the extraction append result is
reported with that caveat rather than as a clean finding.

## Caveats

The extraction task has 10 hand-written cases (5/3/2). Dev scores quantize
to 1/12 and test to 1/8, so its ablations are underpowered — the k=1/2/3
sweep scored identically, which is not evidence that example count doesn't
matter. Two cases encode judgment calls rather than ground truth:
"Union Square" → "San Francisco, CA" is ambiguous, and "confidential" →
`null` company is defensible either way.

The emotion task is larger (60/30/20) but imbalanced — joy is 36% of
train, so a prompt that always answered "joy" would score 0.36. Only the
final mutate winner clearly clears that floor.

The two tasks use different models (8b and 3b), because the 8b caused
thermal timeouts on a laptop at 60-case dev splits. Cross-task comparisons
are therefore confounded by model size. One check against this: the 3b and
8b base prompts scored 0.133 and 0.140 on the same emotion train split, so
the vocabulary failure at least is not a size effect.

## Running it
git add -A && git commit -m "Emotion held-out test 0.000 -> 0.450" && git push
cat > README.md << 'PYEOF'
# prompt-lab

An eval harness and prompt optimizer for local LLMs. Runs entirely on
Ollama — no hosted APIs, no keys, no cost.

Given a task (dataset, starting prompt, scorer), it searches for a better
prompt and records every candidate and score in SQLite, so results are
reproducible and comparable. Two tasks are included, deliberately chosen
to be structurally different: structured extraction and multi-class
classification.

![results](results.png)

## Results

Held-out test splits, scored once at the end and never optimized against.

| | extraction (llama3.1:8b) | emotion (llama3.2:3b) |
|---|---|---|
| base prompt | 0.250 | 0.000 |
| best optimized | **0.875** | **0.450** |
| winning method | bootstrap (few-shot demos) | mutate (prompt rewrite) |

**Extraction** — pull `{company, title, location, remote}` as JSON from
messy job postings. 10 hand-written cases, scored on per-field exact match.

**Emotion** — 6-class classification (sadness/joy/love/anger/fear/surprise)
on 110 cases sampled from `dair-ai/emotion`, scored on label match.

## What I found

**Different task types have different winners.** On extraction, few-shot
demos beat every LLM-driven method — bootstrap hit 0.667 on dev while
mutate topped out at 0.583 and append at 0.667 with no gain over base.
On emotion the ranking reversed: every few-shot variant scored 0.133,
identical to base, while simply *stating* the six labels in prose jumped
to 0.333. Demos convey format well but cannot convey that a vocabulary is
closed and has exactly six members. One sentence can.

**Added instructions rarely help and often hurt.** This held across both
tasks and both models. A hand-written rule stating the location format
explicitly *lowered* the extraction score (0.667 → 0.583) — locations were
unchanged and an unrelated field regressed. On emotion, append's
best-scoring generated rule was semantically circular ("for emotional
words like 'joy', 'love', return the corresponding sentiment value").
And mutate's winning prompt beat the human-written one by *deleting* an
instruction. What moves the score is structural — the label set, rule
placement, demo format — not prose.

**Placement mattered more than content.** `append` inserted its rule at
the end of the prompt, which on the emotion task landed it *after* the
answer cue (`Emotion:`). All four variants scored below base. Fixing the
insertion point — tasks now declare `insert_before` in their config — and
re-running the identical generation process moved the range from
0.100–0.267 to 0.167–0.367. Same rules, different position, opposite
result.

**A prompt can't be evaluated by reading it.** The worst mutate variant on
extraction reads perfectly well and scores half as well as the lazy
one-line base: it dropped the word "JSON" and invented a fifth field.

**Failure-driven optimizers don't reliably read their failures.** On
extraction, append generated four rules about key naming while every
failure it was shown had the location wrong. Part of this traces to a bug
(below), but the pattern survived the fix.

## A bug worth reporting

With `start_from` set — chaining one optimizer onto another's output —
the train run that collects failures still read `prompt.txt` from disk
rather than the prompt being optimized. So the optimizer was shown the
*wrong prompt's* failures. Before the fix, mutate on emotion produced zero
valid candidates and crashed. After, three of four were valid and the best
scored 0.433, a +0.100 gain. Any conclusion drawn from a chained run
before this fix is suspect, which is why the extraction append result is
reported with that caveat rather than as a clean finding.

## Caveats

The extraction task has 10 hand-written cases (5/3/2). Dev scores quantize
to 1/12 and test to 1/8, so its ablations are underpowered — the k=1/2/3
sweep scored identically, which is not evidence that example count doesn't
matter. Two cases encode judgment calls rather than ground truth:
"Union Square" → "San Francisco, CA" is ambiguous, and "confidential" →
`null` company is defensible either way.

The emotion task is larger (60/30/20) but imbalanced — joy is 36% of
train, so a prompt that always answered "joy" would score 0.36. Only the
final mutate winner clearly clears that floor.

The two tasks use different models (8b and 3b), because the 8b caused
thermal timeouts on a laptop at 60-case dev splits. Cross-task comparisons
are therefore confounded by model size. One check against this: the 3b and
8b base prompts scored 0.133 and 0.140 on the same emotion train split, so
the vocabulary failure at least is not a size effect.

## Running it

Every model call is cached in SQLite keyed on model, prompt and
temperature, so re-runs are instant and scores are deterministic. The
model name in the key is what lets 8b and 3b results coexist.

## Structure

A task declares its scorer and prompt structure in `config.json`, so the
harness is not hardcoded to one output shape.

## Future work

Bigger extraction dataset — 10 cases is too few for its ablations to be
conclusive. Parallelizing the eval loop, which is currently serial and
dominates wall time. And re-running the final prompts on a single model to
remove the 8b/3b confound.
