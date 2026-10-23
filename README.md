# truth-probe-audit: worked example for the LASR workshop
### "Don't let the author grade the exam: a claim → controls → fresh-context audit loop for AI-written experiments"

**What this is.** The live demo for a 30-minute workshop (full write-up: `SUBMISSION.md`). A plausible AI-safety
experiment (a linear "truth probe" across layers) written in one fluent Claude
Code session reports **99.2% at layer 8**. The repo contains the reusable kit that
turns "looks great, ship it" into a 15-minute routine, plus the real outputs of
running that routine (and two weaker review styles) on the result.

The activations come from a **simulated model with planted ground truth**
(`_instructor/make_activations.py`). That's deliberate: because we know exactly
what's wrong, we can *score* each review style instead of arguing about it.
Swap in real activations (e.g. from a small open model on a true/false dataset)
for a live cohort run; the kit doesn't change.

```
project/                         ← what fellows see / what the auditor sees
  naive_probe.py                 the tempting 99.2% result
  CLAIM.md                       5-min human pre-registration (claim, unit of generalisation, falsifiers)
  CLAUDE.md                      project rules: results discipline, splits, controls, review
  .claude/agents/experiment-auditor.md   fresh-context adversarial auditor subagent
  .claude/commands/audit.md      /audit slash command
  verify.py                      reusable controls: group-aware shuffled labels, overlap,
                                 surface baselines, stratified score, Wilson CI
  honest_probe.py                the result after acting on the audit (nested grouped CV + controls)
  results/                       naive + honest outputs, before_after.png, LOG.md, AUDIT.md
runs/                            real transcripts/outputs of the three review conditions
  A_author_probe.*               Claude writing the probe from scratch ("quick, is there a truth direction?")
  B_fresh_adhoc_review.md        fresh Claude, ad hoc "can you look at this before I write it up?"
  C_workflow_AUDIT.md (+ scratch) /audit: CLAIM.md + checklist + fresh context
  D_calibration_AUDIT.md         same auditor on the CORRECTED pipeline: does it invent problems?
  SCORECARD.md                   each condition scored against the planted ground truth
_instructor/                     ground-truth generator: do NOT give to the auditor
HANDOUT.md                       one-page take-away + install instructions
```

## When to use it
Only for **consequential** results (ones that change a paper claim, the next experiment or a
substantial implementation). Start with one per team per week; keep it only if it saves more
rework than it costs. The auditor is a fresh-context checker, not an authority: re-run its key numbers.

## Reproduce
```bash
cd _instructor && python3 make_activations.py      # regenerates project/data/*
cd ../project && python3 naive_probe.py            # → 0.992 @ layer 8
python3 honest_probe.py                            # → 0.819 nested grouped; controls; figure
# in Claude Code, inside project/:   /audit naive_probe.py
```

## Headline numbers (printed by `honest_probe.py`; CIs resample whole facts)
| | value |
|---|---|
| Naive: random row split, best of 16 layers picked on test | **0.992** |
| Shuffled labels (statement-level), *same naive split* | 0.70 ← should be 0.50 |
| Test rows that are paraphrases of a training statement | 98% |
| Accuracy, nested grouped CV (split by fact, layer/C chosen on inner folds; layer 8 in 4/5 folds) | **0.819** (fact-clustered 95% CI 0.78–0.86) |
| Baseline: "does the sentence contain *not*?" | 0.763 |
| **Balanced** accuracy *within* negation strata (nested) | **0.685** (CI 0.63–0.74) |

Read: the planted mid-layer signal is real but modest: accuracy 0.82 on held-out facts (vs a
0.76 "contains not" baseline) and balanced accuracy 0.68 within negation strata, not 0.99.
Because the data is synthetic, this demonstrates the workflow, not a finding about a real model.
(CIs and wording were corrected after the calibration audit in `runs/D_calibration_AUDIT.md`,
which caught errors in the first write-up.)
