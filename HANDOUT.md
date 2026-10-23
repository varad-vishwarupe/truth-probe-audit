# One page: "Don't let the author grade the exam"

**The practice:** before you trust a *consequential* AI-assisted result (one that
changes a paper claim, your next experiment, or a substantial implementation),
write down what it must generalise to and what would weaken it. Then let a
fresh-context assistant run that check and leave the evidence in the repo.

**When NOT to use it:** exploratory plots, refactors, cosmetic edits. Start with one
consequential result per team per week; keep it only if it saves more rework than it costs.

## 1. You: `CLAIM.md` (before AI touches the result)
- The sentence as it would appear in the paper.
- **The unit of generalisation:** new facts? new prompts? new models? new seeds?
- 2-3 falsifiers ("if X, the claim is weaker") and the number you expect for each.

## 2. AI: run the two controls that catch most of it
| Control | Catches | Red flag |
|---|---|---|
| Split by the unit of generalisation (`grouped_cv_score`) | near-duplicates, memorisation | big drop vs. your headline |
| Group-aware shuffled labels on the **same split** (`shuffled_label_control`) | leakage the split hides | well above chance |

Also in `verify.py` when relevant: surface-feature baselines, stratified score on the
strongest shortcut, `cluster_bootstrap_ci` (never a row-level CI on clustered rows).

## 3. AI: `/audit` in a fresh context, then you decide
- A subagent that never saw the authoring conversation; gets repo + `CLAIM.md` only.
- Must **run** checks, cite numbers, list what passed, and report only problems that
  would change the claim. It may share your assistant's blind spots: re-run its key numbers.
- You write the verdict line and decide what to act on:
  `Claim weakened: <reason>; next action: <experiment>; needs: <who/what>`

## Install (2 min)
```bash
cp .claude/agents/experiment-auditor.md  <your-repo>/.claude/agents/
cp .claude/commands/audit.md             <your-repo>/.claude/commands/
cp verify.py CLAIM.md                    <your-repo>/
# edit CLAIM.md for YOUR result, then in Claude Code:  /audit path/to/script.py
```

## Falsifiers by project type (LASR areas)
- **Probes / interpretability:** keyword or bag-of-words baseline; within-stratum score; random-direction control.
- **Evals / benchmarks:** answer-only baseline; contamination check; 20 hand-graded items vs the grader.
- **Control / monitoring:** does the monitor fire on the unmodified model? Is the red-team policy tuned on the test set?
- **Steering:** random direction of equal norm; off-target capability drop; prompt-only baseline.
- **LLM-as-judge:** judge from a different model family; position and length bias checks.
