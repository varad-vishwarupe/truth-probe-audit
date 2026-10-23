# Results log

| date | script | number | split | controls run | audited? |
|---|---|---|---|---|---|
| 2026-10-23 | naive_probe.py | 0.992 @ layer 8 | random 80/20 (row) | none | no |
| 2026-10-23 | /audit naive_probe.py | verdict DOES NOT SURVIVE | – | auditor: findings 1–8 (see results/AUDIT.md) | yes |
| 2026-10-23 | honest_probe.py | 0.819 nested fact-grouped (fact-clustered CI 0.78–0.86, now printed by honest_probe.py itself); within-negation-strata 0.685 nested (CI 0.63–0.74); C sweep 0.69–0.75 = sensitivity only | GroupKFold(fact_id), nested selection | shuffled-label 0.49 (grouped) / 0.70 (naive split); has_negation baseline 0.763; overlap report | calibration audit: runs/D_calibration_AUDIT.md |

## Responses to audit findings
- F1/F2 (leakage, null): switched to fact-grouped nested CV; null reported with every number.
- F3/F4 (negation): within-strata balanced accuracy is now the primary metric; polarity-balanced dataset = next step.
- F5 (selection): nested selection; costs ~0 here but kept.
- Minor: scaler moved into pipeline; claim reworded.

## Calibration audit (D) on honest_probe.py → WEAKENED
- Accepted after independent bootstrap: report nested within-strata 0.685 (not the 0.69–0.75 range); fact-clustered CIs; late layers 12–14 ≈0.55, not 'absent'.
- To do: ≥20-permutation full nested null; within-stratum non-linear surface baseline.

## Verdict lines (what a team brings to stand-up; prompts for discussion, not grades)
- naive_probe.py: `Claim does not survive: row split leaks paraphrases (null 0.70); next action: fact-grouped nested CV; needs: nothing`
- honest_probe.py: `Claim weakened: accuracy 0.82 [0.78, 0.86] vs 'not' baseline 0.76; within-strata balanced 0.68; next action: polarity-balanced evaluation; needs: supervisor input on intended generalisation (new facts vs new domains)`
