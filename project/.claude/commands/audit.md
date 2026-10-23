---
description: Run a fresh-context adversarial audit of the current result against CLAIM.md
argument-hint: [optional path to the script that produced the result]
---

Launch the `experiment-auditor` subagent to audit the result produced by
${ARGUMENTS:-the main experiment script in this repo} against `CLAIM.md`.

Pass it ONLY: the repo path, the script path, and the instruction to follow its
own checklist. Do NOT pass it any of this conversation's reasoning, conclusions,
or summaries of the result. It must form its own view.

When it finishes:
1. Show me the verdict line and the findings table from `results/AUDIT.md`, verbatim.
2. Do not start fixing anything. Ask me which findings to act on.
3. Append a dated entry to `results/LOG.md`: script, verdict, finding ids.
