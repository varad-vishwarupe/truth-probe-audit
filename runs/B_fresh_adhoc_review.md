# Review: naive_probe.py (linear truth probe)

**Short version: 99.2% is not a real result. Don't put it in the paper as it stands.** Most of it comes from train/test leakage. With a leak-free split the best layer (still layer 8) gets about **82%**, and much of that can be explained by a negation-word shortcut.

## Problems (most important first)

1. **Paraphrase and pair leakage across the split (the main problem).** The dataset has 150 `fact_id`s. Each one has 8 rows: 4 paraphrases × {true, negated-false}. `train_test_split` splits at the row level, so **100% of test rows have their `fact_id` in train** and 98% have the same `statement_id` (a paraphrase of the identical statement) in train. The probe can match test rows to near-copies it has already seen. Fix: split by `fact_id` (`GroupKFold` / `GroupShuffleSplit`).

2. **Negation confound.** The false statements are mostly the true ones with "not" added. Negated rows are 80% false and affirmative rows are 73% true, so the rule "has *not* → false" gets **76.3%** with no model at all. Negation can be decoded linearly at ~99% from every layer. Within each subgroup at layer 8 (grouped CV), the probe gets 87% on negated rows against an 80% majority baseline, and 78% on affirmative rows against 73%. That is above the shortcut, but not by much. Report accuracy within each negation subgroup, or balance the dataset so negation doesn't predict the label (e.g. add true negated / false affirmative statements in equal numbers).

3. **Layer selected on the test set.** "Best layer = 8, 99.2%" picks the maximum of 16 test scores, which inflates the number. Choose the layer with CV or a validation split, then report a separate held-out score with CIs or variation across folds/seeds. The test set has only 240 rows, so ±~2pp is noise anyway.

4. **Minor: StandardScaler is fit on all rows, test included.** It's a small leak (it made almost no difference here), but fit it on train only, e.g. in a `Pipeline`.

## Corrected numbers (I ran these; scaler inside the pipeline)

| layer | naive split | grouped 5-fold by fact | cross-domain (train 2 domains, test 3rd) |
|---|---|---|---|
| 0 | 0.82 | 0.62 | 0.61 |
| 5 | 0.87 | 0.68 | 0.69 |
| 7 | 0.97 | 0.76 | 0.73 |
| **8** | **0.99** | **0.82** | **0.80** |
| 9 | 0.96 | 0.76 | 0.77 |
| 10 | 0.94 | 0.75 | 0.79 |
| 15 | 0.78 | 0.60 | 0.59 |

Mid-layer peaking (layers 7–10) holds up under grouped CV and cross-domain tests, and that is the defensible finding. The size of the effect does not hold up: it is about 80%, not 99%.

## Before writing it up
- Switch to a grouped split by `fact_id`, choose the layer on validation data, and report mean ± sd across folds.
- Report the negation-only baseline (76%) and accuracy within the negated and affirmative subgroups. Ideally, rebalance the dataset so negation is uninformative.
- Include the cross-domain transfer result. It's the strongest evidence that the probe generalises.
- Possibly also add a control-task / shuffled-label baseline, so you know how much a 128-d linear probe can fit by chance.

The check script is at /tmp/claude-0/-home-claude/80d0ee3e-87ad-5950-a81d-0ef3a9619ff6/scratchpad/work/check.py (outside the repo). naive_probe.py was not modified.
