# CLAIM.md: write this BEFORE you look at the headline number twice

> 5 minutes, by hand, not by Claude. The point is that *you* commit to what would
> embarrass the result before an AI tells you it looks great.

## 1. The claim, as it would appear in the paper
"A linear probe on the residual stream recovers whether a statement is true,
with accuracy of about 99% at layer 8, so the model linearly represents truth."

## 2. The unit of generalisation
What must the probe generalise to for the claim to mean anything?
→ **Facts it has never seen.** Not new phrasings of a statement it trained on.
(Look at `data/statements.csv`: there is a `statement_id` and a `fact_id`. Why?)

## 3. Falsifiers: results that would mean the claim is wrong or much weaker
| # | If this happens... | ...then |
|---|---|---|
| F1 | Probe on **shuffled labels** scores well above 50% | the eval leaks; headline is not evidence |
| F2 | Accuracy drops a lot when train/test are split by **fact** | probe memorised statements, not truth |
| F3 | A **trivial surface feature** (length, a keyword, the domain) predicts the label nearly as well | probe may be reading the shortcut |
| F4 | Accuracy within strata of that feature is **near 50%** | no truth signal beyond the shortcut |
| F5 | The reported layer/hyperparameters were **chosen on the test set** | headline is optimistically biased |

## 4. Expected numbers if the claim is TRUE (commit now)
- Shuffled-label control: ~0.50 ± 0.05
- Fact-grouped held-out accuracy: within ~5 points of the headline
- Best surface-feature baseline: clearly below the probe (>10 points)

## 5. Who is the hostile reviewer?
"Didn't Levinstein & Herrmann / the CCS follow-ups show truth probes fail on negation?"
→ the audit must answer this question with a number, not an argument.
