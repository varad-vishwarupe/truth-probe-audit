# Project rules for Claude (research repo)

## Results discipline
- A number is not a *result* until it has an entry in `results/LOG.md` with: the
  command that produced it, the git hash / file version, the split strategy, and
  the controls that were run alongside it.
- Never describe a result as "strong", "clear" or "significant" in a summary.
  Report the number, the control numbers next to it, and the CI. Let the human judge.
- Any metric used to pick a layer, checkpoint, prompt or hyperparameter must come
  from a validation split. The test split is touched once, at the end.

## Splits
- Data has structure: `fact_id` ⊃ `statement_id` ⊃ paraphrases. Default to
  splitting by the **coarsest** id that the claim is meant to generalise across.
  If you split at a finer level, say so explicitly and why.

## Standard controls (use `verify.py`, don't re-implement)
Every probe/classifier result ships with:
1. `shuffled_label_control` (group-aware shuffle)
2. `surface_baselines` (length, keyword, domain)
3. `stratified_score` on the strongest surface baseline

## Review
- Before a result goes into a draft, slides, or a supervisor message, run `/audit`.
  It launches `experiment-auditor` in a fresh context that has NOT seen this
  conversation. Do not paste your reasoning into it; it gets the repo and CLAIM.md only.
- Do not "fix" audit findings silently. Record each finding and the response in
  `results/LOG.md`.
