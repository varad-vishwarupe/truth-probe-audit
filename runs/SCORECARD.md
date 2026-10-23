# Scorecard: three ways of checking the same result, scored against planted ground truth

All three conditions used the same model (Claude Opus 5.5 subagents), the same tools (read files, run Python) and the same data.
**n = 1 run per condition. This is an illustration, not an experiment** (see "with more time").

Planted in the data/pipeline (known only to `_instructor/`):
- **P1** paraphrase/fact leakage from a row-level split
- **P2** negation confound (80% of negated statements are false)
- **P3** layer chosen on the test set
- **P4** scaler fit on train+test

| | A. Author session<br>("write a probe, quick, is there a truth direction?") | B. Fresh ad hoc review<br>("can you look at this before I write it up?") | C. Workflow<br>(CLAIM.md + `experiment-auditor` + `/audit`) |
|---|---|---|---|
| P1 leakage | avoided (split by `fact_id` unprompted) | **found**, measured overlap (100% fact / 98% statement) | **found**, measured overlap |
| P2 negation | **found**, within-group scores | **found**, measured 76% baseline | **found**, measured, plus polarity-transfer test (neg→aff 0.52) |
| P3 test-set selection | **committed it**: headline 86.2% = best of 16 layers on one split | **found** | **found**, and showed nested CV still picks L8 (5/5 in its run; 4/5 in honest_probe.py), so it costs ~0 here |
| P4 scaler leak | avoided | found (minor) | found (minor, quantified: 1 test item) |
| Null (shuffled-label) control *run* | no | suggested, **not run** | **run**: 0.71 under the reported split vs 0.49 grouped |
| Verdict against pre-stated falsifiers | n/a | informal ("not a real result") | **F1–F5 each marked**, verdict DOES NOT SURVIVE |
| Checks persisted in repo / reproducible | partial: negation baseline in script; CV and within-strata checks were "one-off runs, not in probe.py yet" | script written **outside the repo** | scripts in `audit_scratch/`, exact commands, `LOG.md` entry required |
| States what it could NOT check | no | no | **yes** (extraction position, familiarity confound, C sweep) |
| Paper-ready corrected sentence | partial | yes | yes, with baseline and null in the sentence |

## What I take from this (and what I'd tell the fellows)
1. **In this example (n = 1 per condition), detection of textbook bugs was not the bottleneck.** A fresh Claude with tools caught all four planted
   problems, and the authoring Claude avoided two of them unprompted. A workshop pitched as "AI writes buggy code,
   so check it" would be teaching this cohort something they half-know and the model mostly handles.
2. **The gap is process, not intelligence.** What differed was whether the check *happened at all* (the author's own
   headline was still test-set-selected and had no null), whether the controls were *run rather than suggested*,
   whether the result was judged against falsifiers *the human chose before seeing it*, and whether anything was left
   behind that a supervisor or co-author could re-run.
3. **The human's job moves to CLAIM.md.** Choosing the unit of generalisation and the falsifiers is the judgment
   call. That's exactly the "parts that need their judgment" LASR wants fellows spending time on.
4. **Caveat on the auditor:** adversarial reviewers report problems even on sound work (Anthropic's Claude Code
   guidance says this explicitly). So I ran the same auditor on the *corrected* pipeline (`D_calibration_AUDIT.md`).
   It returned WEAKENED, invented nothing, listed what passed, and caught three real errors in my own write-up
   (test-fold-selected range, unclustered CI, late-layer wording), two of which I reproduced independently.
