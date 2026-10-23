# AUDIT: naive_probe.py vs CLAIM.md

**Verdict: DOES NOT SURVIVE, as stated.** The 99% comes from a row-level split that puts every test fact in training. With facts held out the probe scores 0.82 [0.80, 0.84], and a single "has negation" feature gets 0.76. Falsifiers F1, F2 and F3 all trigger. F4 partly triggers. F5 triggers on the method, though the layer choice itself holds up.

## Findings (ranked by impact on headline)

| # | Severity | Finding | Evidence (command → number) | Suggested fix |
|---|---|---|---|---|
| 1 | Critical | **Wrong unit of generalisation (F2).** The 80/20 split is by row. Every fact has 8 rows (4 paraphrases × true/false statement), so 100% of test rows share a `fact_id` with training and 98.3% share a `statement_id`. | `audit.py` → `group_overlap`: fact 240/240, statement 236/240. Fact-grouped 5-fold CV at layer 8: **0.818 ± 0.005 SE** (vs 0.992). Statement-grouped: 0.840. | Split with GroupKFold on `fact_id` (CLAUDE.md requires the coarsest id). |
| 2 | Critical | **Null control fails under the reported split (F1).** Shuffle the labels at statement level, keeping paraphrases tied, and the naive pipeline still scores 0.71. Under a fact split the same shuffle scores 0.49. So about 20 points of the headline is paraphrase matching. | `shuffled_label_control`, 10 perms, L8: row split **0.707**, fact split **0.493** | Report the null next to every number, using the split actually used. |
| 3 | Critical | **Shortcut on negation (F3).** 80% of negated statements are false and 73% of affirmative ones are true. A depth-3 tree on `has_negation` alone gets 0.763 (fact-grouped), which is 5.5 points below the probe. CLAIM.md asked for a gap above 10 points. Layer 8 decodes negation at 0.994. | `surface_baselines` (fact CV): has_negation **0.763**, n_words 0.619, n_chars 0.586, domain/digit/paraphrase 0.50. neg+domain+n_words LR: 0.763. `decode_negation_l8` = 0.994. | Rebalance the data so label is independent of negation, or report only within-stratum numbers. |
| 4 | Major | **Truth signal beyond negation is weak and does not transfer (F4, the hostile reviewer's question).** Within negation strata the probe's balanced accuracy is 0.75 (affirmative 0.69, negated 0.81), so it is not at chance. Results from fact-disjoint training on one polarity and testing on the other: aff→aff acc 0.743 vs majority 0.734 (bal 0.64); aff→neg 0.660 vs majority 0.80 (bal 0.70); neg→aff **0.521** (bal 0.62). A direction for "fact is correct, ignoring negation" decodes at only 0.627. | `stratified_score` on nested-CV preds; `audit2.py` transfer block; `decode_factcorrect_l8` | State the negation-transfer numbers in the paper. Test on a polarity-balanced held-out set. |
| 5 | Major | **Layer chosen on the test set (F5).** `naive_probe.py:36` takes the argmax over 16 layers of test accuracy and reports it. Here it costs nothing: nested fact-grouped CV picks L8 in 5/5 outer folds, and the outer score is 0.818. | `audit.py` → `nested_fact_cv.chosen_layers` = [8,8,8,8,8] | Keep nested selection. Report the outer-fold number. |
| 6 | Minor | **Scaler fit on all rows** (`naive_probe.py:27`), including test. | Fitting the scaler on train only gives 0.9875 vs 0.9917 (1 test item) | Put the scaler in a Pipeline. |
| 7 | Minor | **Small test set / seed sensitivity.** n=240. Across 10 seeds the naive split ranges 0.958–0.992. The headline is the best seed-0 layer. | Wilson CI on naive L8 [0.964, 0.996]. `naive_seed_l8` | Report CV mean ± SE, not a single split. |
| 8 | Minor | **Wording (G).** "Linearly represents truth" is stronger than "decodable at 82% on 150 templated facts in 3 domains, largely through negation". Leaving one domain out gives 0.77–0.82. That is consistent with this weaker claim, and no stronger claim was tested. | `leave_domain_out_l8`: arith 0.798, element 0.819, capital 0.770 | Rephrase. See below. |

## Corrected estimate
Fact-grouped nested CV (layer picked on inner folds, scaler inside the pipeline), layer 8: **0.818** (fold SE 0.005; pooled Wilson 95% CI [0.796, 0.839], n=1200). Controls: shuffled-label null 0.493, best surface baseline (negation) 0.763, within-negation-stratum balanced accuracy 0.752. A defensible sentence would be: *"At layer 8 a linear probe classifies held-out facts at 82% (negation-only baseline 76%, null 49%). It transfers poorly from negated to affirmative statements (52%)."*

## What I could not check
- How the activations were extracted: token position, model, and whether the label or a template leaks into the prompt. UNTESTED. Only the `.npz` was available.
- Whether "true" facts are more frequent or more typical in pretraining (a familiarity confound). UNTESTED.
- Probe regularisation sweep. The default C=1 was used throughout. A tuned C could move the result by a few points but would not close the gap to 0.99.
- My verdict would move to WEAKENED if a polarity-balanced dataset showed the probe clearly above the negation baseline and transferring across polarity.

## Reproduce
All commands are run from the project root:
```
python3 audit_scratch/audit.py    # findings 1,2,3,5,6,7,8 and corrected estimate → audit_scratch/audit_out.json
python3 audit_scratch/audit2.py   # finding 4 transfer numbers, neg+domain baseline → audit_scratch/audit2_out.json
```
Per CLAUDE.md, `results/LOG.md` still needs an entry recording these findings and the response to each. The auditor did not edit it.
