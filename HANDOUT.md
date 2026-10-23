# One page: "Don't let the author grade the exam"

**The habit:** before any AI-assisted result leaves your laptop (draft, figure,
Slack to your supervisor), run the 3-step loop. Budget: ~15 minutes of your time,
the rest is Claude's.

## 1. Pre-register: `CLAIM.md` (5 min, you, by hand)
- The sentence as it would appear in the paper.
- **The unit of generalisation.** New facts? New prompts? New models? New seeds?
- 3–5 falsifiers: "if X, the claim is wrong/weaker".
- The numbers you expect if the claim is true: shuffled-label score, gap
  between headline and grouped split, best trivial baseline.
- The one-line objection your harshest reviewer will raise.

## 2. Controls ship with the number (Claude writes, `verify.py` standardises)
| Control | Catches | Red flag |
|---|---|---|
| Group-aware shuffled labels, **same split** | leakage, memorisation | ≫ chance |
| Group overlap report | near-duplicates across split | > 0 |
| Trivial-feature baselines | shortcuts (length, keyword, template) | close to headline |
| Stratified score on strongest shortcut | probe reading the shortcut | ≈ 0.5 |
| Validation-only selection | optimistic headline | layer/HP picked on test |

## 3. Fresh-context audit: `/audit` (Claude, ~5–10 min wall-clock)
- A **subagent that never saw the conversation** that wrote the code.
- Gets: repo + `CLAIM.md`. Does *not* get: your reasoning, Claude's summary.
- Must **run** checks and cite numbers; may not edit source.
- You read the verdict + table and decide what to act on. Log it.

## Why not just ask Claude "does this look right?"
Same model, same chat → it shares the author's framing and assumptions, it's
prompted to be helpful about *your* result, and it reviews by reading rather than
measuring. In our demo the ad-hoc review and the audit had the same model, same
tools, same code. The difference was entirely the workflow. (See the doc for what each found.)

## Install in your repo (2 min)
```bash
cp -r .claude/agents/experiment-auditor.md  <your-repo>/.claude/agents/
cp -r .claude/commands/audit.md             <your-repo>/.claude/commands/
cp verify.py CLAIM.md                        <your-repo>/
# then: edit CLAIM.md for YOUR result, and in Claude Code run:  /audit path/to/script.py
```

## Adapting the checklist to your project type
- **Evals / benchmarks:** unit = held-out task family; controls = answer-only
  baselines, contamination check, grader agreement with humans on 20 items.
- **Steering / interventions:** controls = random direction of same norm,
  off-target capability drop, effect vs. prompt-only baseline.
- **Model organisms / sandbagging / control:** controls = does the "detector"
  fire on the un-modified model? Is the red-team policy tuned on the test set?
- **LLM-as-judge results:** judge ≠ policy model family; position/length bias
  checks; 30 hand labels to calibrate.
