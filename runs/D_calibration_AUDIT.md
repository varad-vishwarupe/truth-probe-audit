# AUDIT: honest_probe.py vs CLAIM.md (2026-10-23)

**Verdict: WEAKENED, as stated.** The core result holds up: held-out facts, nested CV, null near 0.50, a mid-layer within-negation signal well above early layers, and no lexical shortcut found. But the upper end of the within-strata range was chosen on test folds, the CI on the headline is too narrow, and "absent in late layers" is not supported.

## Findings (ranked by impact on headline)

| # | Severity | Finding | Evidence (command → number) | Suggested fix |
|---|---|---|---|---|
| 1 | Major | The "~0.69–0.75 depending on regularisation" range was picked on test folds. 0.75 is layer 8, C=1.0, scored on the outer folds (F2). The nested, untouched within-strata number is 0.685. | `a1_checks.py` C sweep L8: strat 0.692/0.736/0.737/0.730/**0.752** for C=.003…1.0; nested preds reproduced → strat **0.6845** | Report 0.68 (nested) as the number. Give the C sweep only as a sensitivity analysis and label it that way. |
| 2 | Major | The Wilson CI treats all 1200 rows as independent, but each fact contributes 8 correlated rows (2 statements × 4 paraphrases), so the effective n is 150 facts. | `a1_checks.py` fact-cluster bootstrap: acc **[0.779, 0.859]** (vs Wilson [0.796, 0.840]); within-strata **[0.631, 0.743]** | Report the fact-clustered bootstrap CI. |
| 3 | Major | "Absent in … late layers" is overstated. Layers 12–14 keep a small within-strata signal whose CIs exclude 0.5. Only layer 15 is at chance. | `a2_checks.py` C=0.01: L12 0.572 [0.512,0.630], L13 0.575 [0.525,0.628], L14 0.553 [0.503,0.603], L15 0.497 [0.455,0.545] | Rephrase as "peaks at layers 7–11 and is weak (≈0.55–0.57) in layers 12–14". |
| 4 | Minor | The per-layer curves and the "peak at 8" description use fixed C=0.01 scored on outer folds, so they are descriptive and not selection-free. The nested inner selection still chose layer 8 in 4/5 folds (layer 9 in 1). | `results/honest_run.txt` folds; `honest_probe.py:74-80` | Say that the curve is descriptive. The peak claim is fine. |
| 5 | Minor | The nested shuffled-label null used only 3 permutations, and the script's own control does not run the full nested selection (it fixes layer 8, C=0.01). | `a2_checks.py 3`: full nested pipeline on statement-shuffled labels → acc 0.502 / 0.551 / 0.477; strat 0.498 / 0.552 / 0.476. Script control: 0.487 | Run ≥20 permutations of the full nested pipeline and report the null distribution. F1 is not triggered. |
| 6 | Minor | The project rule is not met: the honest result has no `results/LOG.md` entry (only the naive 0.992 is logged). | `cat results/LOG.md` | Add an entry with the command, split, controls and the audit findings. |

## Checks that passed (I tried to break these)
- **A. Unit:** GroupKFold on `fact_id`. Each fact holds both its statements and all 4 paraphrases, so no fact appears in both train and test. (`honest_probe.py:37-39`; data: 150 facts × 2 statements × 4 paraphrases)
- **B. Preprocessing:** StandardScaler sits inside the per-fold pipeline (`honest_probe.py:31`). Nothing is fit on test.
- **C. Selection:** the headline 0.819 comes from inner-fold (layer, C) selection. I reproduced it: 0.8192.
- **E. Shortcuts:** the negation baseline scores 0.763 [0.713, 0.810]. The probe beats it by **0.056 [0.019, 0.094]** (fact-paired bootstrap). A fold-fit bag-of-words model (uni/bigrams) scores 0.69–0.73 overall but **0.47–0.49 within negation strata**, so no token or entity shortcut explains the residual. Within each stratum, length, digit and domain baselines are at 0.50 (a weak test, see below). The regex misses no negation forms (0 texts with n't/never/no/false). The within-strata score is stable across domains (0.65–0.72) and paraphrase templates (0.67–0.70) (F3 not triggered).
- **F4:** within-strata layer 8 minus layer 2 = **0.248 [0.178, 0.315]**, which clears the >10-point expectation.
- **Seeds:** 5 random fact-fold assignments give layer-8 acc 0.829–0.844 and strat 0.725–0.745.

## Corrected estimate
- Held-out-fact accuracy: **0.82 (fact-clustered 95% CI 0.78–0.86)**, against a negation baseline of 0.76. The gain over negation is 0.06 [0.02, 0.09].
- Within negation strata (nested, untouched): **0.68 [0.63, 0.74]**.
- Early layers (0–4) sit at ≈0.49–0.53. Late layers 12–14 sit at ≈0.55–0.57, and layer 15 at 0.50.
- **G. Wording:** what this supports is "truth is linearly decodable beyond negation polarity on these templated arithmetic/capital/element statements." It does not support anything about truth in general.

## What I could not check
- How the activations were made (model, token position, how they were extracted). If they were made with the labels in view, everything changes.
- Whether the result generalises across domains. A leave-one-domain-out split was not run, and the claim does not ask for it.
- A non-linear surface baseline inside each stratum. My single-feature logistic-regression baselines can only predict the majority class, which gives exactly 0.50 by construction. A within-stratum gradient-boosted model on all surface features would be the stronger test.
- A larger nested null (n=3 here).

What would flip the verdict: a full nested null with mean well above 0.5, or a within-stratum surface or lexical model approaching 0.68.

## Reproduce
```
cd <project>
PYTHONPATH=. python3 audit_scratch/a1_checks.py     # C sweep, nested repro, cluster CIs, L8-L2, seeds, BoW, domain/template strata
PYTHONPATH=. python3 audit_scratch/a2_checks.py 3   # within-stratum baselines, probe-minus-negation CI, late-layer CIs, nested null (~45s)
cat results/honest_run.txt results/LOG.md
```
