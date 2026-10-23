---
title: "LASR Labs Research Manager / Coordinator: Work Test"
---

**Varad Vishwarupe**, Department of Computer Science and Institute for Ethics in AI, University of Oxford · 23 October 2026

**Repo (worked example, runnable):** <https://github.com/varad-vishwarupe/truth-probe-audit>

# TL;DR

**The one practice I would teach:** *don't let the author grade the exam.* Before trusting a consequential AI-assisted result, the researcher writes down what it must generalise to and what would weaken it; a fresh-context assistant then runs that check and leaves the evidence in the repo. The researcher keeps the judgment; the assistant does the mechanical verification.

**Why it fits this cohort:** these fellows are already fast with AI. What they lack, per the brief, is a repeatable practice and a calibrated sense of where AI quietly leads them astray. In a 13-week proposal-to-publication programme, the costliest way that happens is a headline number that is wrong for a reason nobody checked.

**What makes this submission different:** I did not just assert the pitch; I tested it. On a LASR-style probing experiment with planted ground truth, a fresh Claude found the textbook bugs when asked (in this example), so the uplift is not "AI writes buggy code". The uplift is making the check *happen*, *run* and *leave evidence*. Then the same auditor, run on our own corrected write-up, caught three errors in it, and a second model (GPT) critiqued the whole submission. Every number below was re-run after those corrections.

# Part 1: The workshop

## The one thing

> **A result is not a result until something other than its author has tried to break it, against a claim you wrote down before you looked.**

Fellows leave with: a `CLAIM.md` for one real result of their own, a discriminating check, a verdict line, and a drop-in kit (`/audit` command, auditor subagent, `verify.py` controls). The kit is for *consequential* results only, one per team per week to start, and it is kept only if it saves more rework than it costs. Arcadia's own scaffold post found that added machinery killed adoption, so proportionality is part of the lesson, not an afterthought.

## Session plan (30 min, about 20 fellows in research-team pairs, laptops open)

| Min | Activity | Purpose |
|-----|----------|---------|
| 0-3 | Show the 99.2% truth-probe result. Each fellow **privately** records ship / don't ship / insufficient evidence, plus the one missing fact they most want. | Commit to a judgment before the reveal. |
| 3-7 | **Before any AI:** fellows write the unit of generalisation ("new facts, not new phrasings") and predict one falsifying check and its expected number. | The human contribution: the part models are weakest at (Arcadia's scaffold finding). |
| 7-17 | **Live `/audit`** in a fresh context. Focus on two controls only: the grouped split and the group-aware shuffled-label null (0.70 under the naive split vs 0.49 grouped). All other controls stay in the repo for later. | Watch the assistant do the mechanical work against *their* falsifiers. |
| 17-25 | Pairs apply the same practice to **one real claim from their own project**: one writes `CLAIM.md`, the other uses AI to run or specify the cheapest discriminating check. Swap who explains. | Transfer on their own research, not my toy. |
| 25-28 | The corrected result and what remains unsupported. The twist: the auditor, run on my corrected write-up, caught three errors in it. Calibration applies to the checker too. | Lands the "fresh-context checker, not authority" point. |
| 28-30 | Individual **transfer answer** on a new case ("an AI summary says a monitor generalises to a new model family; what is the cheapest observation that would change your view?"). | Measure transfer, not satisfaction. |

**Load-bearing assumptions:**

- Run in week 2 or 3, when teams have first results but haven't written them up.
- Fellows use Claude Code (as the brief says).
- The kit is shared a day ahead, so install is 2 minutes.
- Supervisors agree to treat verdict lines as discussion prompts.
- If live generation fails, I replay the captured run in `runs/`.

## The worked example

**Repo:** <https://github.com/varad-vishwarupe/truth-probe-audit>

**Orientation.** A linear probe across 16 layers to detect whether a statement is true: the kind of experiment LASR fellows run. A fluent Claude Code session produced **99.2% accuracy at layer 8**. The activations come from a *simulated* model with planted ground truth, so every review method can be scored objectively:

- a modest mid-layer truth direction;
- a negation shortcut, where 80% of "not" statements are false;
- paraphrase leakage across the split;
- the best layer chosen on the test set.

The negation confound is the failure documented for real truth probes (Levinstein & Herrmann; Marks & Tegmark). Keyword shortcuts are also what LASR's own NeurIPS 2025 paper on high-stakes probes controlled for with a bag-of-words baseline.

![Same activations, same probe: what the headline means depends on the checks](project/results/before_after.png)

| Metric (all produced by `honest_probe.py`; CIs resample whole facts) | Value |
|---|---|
| **Accuracy**, naive random row split, best of 16 layers chosen on test | **0.992** |
| Accuracy, shuffled labels under the *same* naive split (should be ~0.50) | **0.70** |
| Test rows that are paraphrases of a training statement | 98% |
| **Accuracy**, nested fact-grouped CV (layer + C chosen on inner folds; layer 8 in 4/5 folds, 9 in 1) | **0.82** [0.78, 0.86] |
| Accuracy, "does the sentence contain *not*?" baseline | 0.76 |
| Accuracy, shuffled-label null under the grouped split | 0.49 |
| **Balanced accuracy *within* negation strata** (nested) | **0.68** [0.63, 0.74] |

**What a paper could say if these were real activations:** "On held-out facts a mid-layer linear probe reaches 82% accuracy [78, 86] against a negation-only baseline of 76% and a shuffled-label null of 49%. Within negation strata its balanced accuracy is 0.68 [0.63, 0.74]: a modest signal beyond the negation shortcut, peaking at layers 7-11." Because the data is synthetic, this demonstrates the workflow; it is not an empirical finding about a real model.

### The kit (drop-in, for consequential results only)

- **`CLAIM.md`** (written by the human): claim sentence · unit of generalisation · 2-3 falsifiers with expected numbers · the hostile reviewer's one-liner.
- **`.claude/agents/experiment-auditor.md`**: a fresh-context subagent.
  - It trusts no prose, and every finding must cite a number it generated.
  - It may not edit source.
  - It reports only problems that would change the claim, and lists the checks that passed. This follows Anthropic's own warning that adversarial reviewers find gaps even in sound work.
  - It states that it is a checker, not an authority, and can be run on a different model family.
- **`.claude/commands/audit.md`**: `/audit` passes only the repo and `CLAIM.md`, never the authoring conversation. It doesn't auto-fix. It writes a verdict line to `results/LOG.md`.
- **`verify.py`**:
  - group-aware shuffled-label control (a row-level shuffle hides the very leakage it should expose);
  - grouped CV and an overlap report;
  - surface baselines and a stratified score;
  - `cluster_bootstrap_ci`.

![Screenshot: the auditor subagent definition](screens/experiment-auditor-1.png)

### Real audit output (excerpt of `results/AUDIT.md`, verbatim apart from dash punctuation)

> **Verdict: DOES NOT SURVIVE, as stated.** The 99% comes from a row-level split that puts every test fact in training. With facts held out the probe scores 0.82, and a single "has negation" feature gets 0.76. Falsifiers F1, F2 and F3 all trigger.

| # | Sev. | Finding | Evidence the auditor generated |
|--|--------|--------------------|--------------------|
| 1 | Critical | Wrong unit of generalisation: row split | fact overlap 240/240, statement 236/240; fact-grouped CV 0.818 |
| 2 | Critical | Null control fails under the reported split | shuffled labels: row split 0.707, fact split 0.493 |
| 3 | Critical | Negation shortcut | has_negation baseline 0.763; negation decodable at 0.994 at layer 8 |
| 4 | Major | Signal beyond negation is weak and transfers poorly | negated→affirmative transfer 0.52 |
| 5 | Major | Layer chosen on test | nested CV still picks layer 8, so it costs ~0 here |
| 6-8 | Minor | Scaler leak (1 item); seed range 0.958-0.992; claim wording | leave-one-domain-out 0.77-0.82 |

![Screenshot: the real results/AUDIT.md produced by /audit in a fresh context](screens/C_workflow_AUDIT-1.png)

### Testing the pitch: three ways of checking the same result

These runs used the same model, the same tools and the same data. **n = 1 per condition, so this is an illustration, not a study.** Each review style is scored against the planted ground truth; the full table is in `runs/SCORECARD.md`.

| | A. Author session ("quick, is there a truth direction?") | B. Fresh ad hoc review ("look at this before I write it up?") | C. `CLAIM.md` + `/audit` |
|----------|----------|----------|----------|
| Leakage | avoided unprompted | found | found + measured |
| Negation shortcut | found | found | found + polarity transfer |
| Layer chosen on test | **committed it** (86.2% = best of 16 on one split) | found | found + cost measured |
| Null control actually *run* | no | suggested, not run | **run** (0.70 vs 0.49) |
| Judged against pre-stated falsifiers | no | no | **yes** |
| Evidence left in the repo | partial ("one-off runs") | script saved *outside* the repo | scripts + commands + log |
| Says what it could not check | no | no | **yes** |

**In this example, ad hoc review identified the planted problems; the structured workflow additionally ran the controls, tested the pre-stated falsifiers and preserved the evidence.** That is the gap the workshop targets.

**The auditor, audited (run D).** I ran the same auditor on the *corrected* pipeline with an honest claim. It returned **WEAKENED** and invented nothing: it listed the checks that passed, including a full nested shuffled-label null averaging about 0.51 over 3 permutations and a bag-of-words model at 0.47-0.49 within strata. It caught three real errors in the first-draft write-up:

1. a within-strata range whose upper end had been chosen on test folds;
2. a row-level confidence interval on clustered data;
3. "absent in late layers", when layers 12-14 retain about 0.55.

The two quantitative findings were reproduced before being accepted (0.819 [0.779, 0.859]; 0.685 [0.631, 0.743]). Then the pipeline itself was fixed: `honest_probe.py` now prints the clustered intervals. Calibration applies to the checker as well.

# Part 2: Why this, for this cohort

**1. It targets the gap this cohort actually has.** The brief describes fellows who are fluent but improvised. The repeatable step they lack is deciding what a result must generalise to *before* an AI-written pipeline produces a persuasive number. A fresh model can often find textbook bugs when asked. The failure is that nobody asks, the control is suggested but never run, or the evidence evaporates with the chat.

**2. It puts human judgment exactly where Arcadia's own evidence says it is needed.** Arcadia's automated-research-scaffold post found that models were strong at building and running defined experiments but weak at interpreting results and choosing the next question. Told to "do good science", they also over-emphasised controls on uninteresting questions. This design follows that finding:

- The fellow owns the claim, the unit of generalisation and the interpretation.
- The assistant runs the controls the fellow chose, scoped by `CLAIM.md` rather than "verify everything".
- Arcadia's oversight post warns that checking individual steps does not establish the overall argument. That is why the final step is a human verdict on the *claim*, not a pass/fail on each check.

**3. The cost asymmetry in a 13-week programme is extreme.** About half of a recent LASR cohort's papers reached NeurIPS, and the alumni retrospective advises a draft by weeks 2-3. A leaked or confounded headline found in week 3 costs one check; found in week 11, or by a reviewer, it costs the paper.

The evidence that this risk is real:

- Leakage affected 294 papers across 17 fields before coding agents existed (Kapoor & Narayanan).
- In an independent evaluation of Sakana's AI Scientist, 42% of experiments failed on coding errors.
- AI-assisted participants were more likely to believe insecure code was secure (Perry et al.).
- Automation-bias research finds accountability among the few reliable mitigations (Goddard et al.).

**4. It transfers across LASR's research areas.** Probes, CoT monitoring, control, evals, SAEs and steganography all make claims about held-out generalisation that shortcuts can undermine. Only the falsifiers change. For evals: an answer-only baseline. For monitors: does it fire on the unmodified model? For steering: a random direction of equal norm. For LLM judges: a judge from a different model family, since models favour their own outputs (Panickssery et al.).

**5. Considered and rejected.**

| Option | Why not, for this cohort, in 30 minutes |
|------------|------------------------------|
| Paper-reading / literature workflows | Their strongest existing habit; errors there are cheaper and supervisors catch them. |
| Claude Code feature tour / prompt library | Hygiene, not a research practice; the useful part (a `CLAUDE.md` block) is folded into the kit. |
| Parallel agents and multi-agent critics for throughput | More machinery and more unverified output; Arcadia's own scaffold found friction outweighed uplift. Teach after verification is a habit. |
| A broad "verify everything" lesson | No stopping rule. Proportionality is the point. |
| A second, simpler worked example (e.g. a monitor-abstention metric) | GPT drafted one; it was clear but too elementary for this cohort, and two demos would halve the time on transfer. |

# Part 3: How this does the job LASR describes

The Research Manager role combines research management with technical enablement. It covers running workshops on using AI tools to research and code more efficiently, hands-on debugging to unblock teams, tracking progress and reporting to the Programme Manager, and evaluating project proposals. The test is whether an artifact helps capable researchers **make better decisions** while **reducing the mechanical work** needed to support them.

**Better decisions, named.** The demo changes four concrete decisions:

1. **Don't ship the 99%.**
2. **Which sentence goes in the paper:** accuracy 0.82 against a 0.76 baseline, with balanced accuracy of 0.68 within strata.
3. **The next experiment:** a polarity-balanced evaluation.
4. **What to escalate:** "supervisor input needed on the intended generalisation (new facts vs new domains)".

The fourth arrives as a verdict line:

`Claim weakened: accuracy 0.82 [0.78, 0.86] vs 'not' baseline 0.76; next action: polarity-balanced evaluation; needs: supervisor input on intended generalisation`

A verdict line is a prompt for a stand-up conversation, not a grade. It tells a manager where to look, not which team is "good".

**Mechanical work moved to the assistant.** The assistant did all of the following:

- the grouped nested CV;
- both null controls;
- surface baselines and stratified scores;
- clustered bootstraps;
- reproduction commands and the log entry.

Measured from this session's logs:

| Run | Agent wall-clock |
|---|---|
| Fresh-context audit (C) | 2.3 min |
| Calibration audit (D) | 4.1 min |
| Ad hoc review (B) | 1.5 min |
| Corrected pipeline end to end | ~0.6 min |

I am **not** claiming measured time savings. The researcher-side allowances in the workshop (about 4 minutes on `CLAIM.md`, a few minutes reading the verdict) are allowances, not observations. A pilot would measure total researcher time including setup, review and rework, and whether the verdict changed the next step.

**How the artifact maps onto the role's duties.**

| Role duty (from the Research Manager page) | Deliverable in this submission |
|---|---|
| Run technical workshops on AI tools for research and coding | The 30-minute session, the live demo and the one-page handout |
| Hands-on debugging to unblock experiments | `verify.py` + `/audit` catch the leakage and confound bugs a manager would otherwise find by reading code; `AUDIT.md` is reviewable in minutes |
| Help teams set goals, track progress, report to the Programme Manager | Verdict lines in `results/LOG.md`, read at stand-up, rolled into weekly reports |
| Evaluate project proposals | The `CLAIM.md` template doubles as a falsifiability check on proposals |
| Advise on tooling | Proportionality rules: when the loop is worth its cost and when it isn't |

**Follow-up I would run as Research Manager:**

- At the next team check-in, review one real `CLAIM.md` per team and record setup, review and rework time, and whether it changed the next step.
- By week 6, collect a "things our audits caught" page. This becomes the next cohort's workshop material, built from real failures in LASR's own projects.

**Why I'd be good at running this.**

- **Mentoring.** This autumn I mentor two SPAR projects on AI-welfare evaluation. The mentees range from industry engineers at Google and Meta to postgraduate students without heavy ML backgrounds, and the main design is pre-registered. The most valuable mentor intervention is rarely writing code. It is asking, before anything runs, what the result must generalise to and what would embarrass it. This workshop hands that question to every fellow.
- **Industry.** As a Research Scientist at Amazon Alexa AI and an engineer at Microsoft Azure ML, I learned the same lesson at production scale: an evaluation number is only as good as the split behind it.
- **Programmes like LASR.** As a Senior Research Fellow in Pivotal's programme at UK AISI, I have been inside the kind of fellowship this role supports, alongside teaching and research assistance in Oxford's Department of Computer Science.

# Part 4: My process

**Tools.**

- **Claude (Opus 5.5, claude.ai agentic workspace):** built and ran everything: the simulated data, both pipelines, the kit, four review runs, the web research and the repo.
- **ChatGPT/Codex:** used as a **second-model critic**. It independently reproduced the main numbers and critiqued the submission, and drafted an alternative workshop design.
- I directed both.

**My calls.**

- I chose to seek a second-model critique.
- I assessed which criticisms to accept or reject.
- I required a stronger connection to LASR's role and cohort.

Claude and GPT proposed the combined design; I directed the comparison and approved the final scope. The assistants generated the code and performed the recorded computational checks.

On GPT's two overclaiming points: I initially set them aside. The final version applies a one-line correction to the "publishable finding" sentence, because it was factually wrong for synthetic data, and adds a scope qualifier ("in this example") to the detection claim.

**What changed because of criticism (the audit trail).**

1. My first pitch, that AI writes buggy code so you should check it, was falsified by run B. Claude added run A and reframed the thesis around process.
2. The calibration audit (D) caught three errors in the corrected write-up; two were reproduced and fixed in the pipeline.
3. GPT's review led to:
   - integrating the clustered CI into the main script;
   - labelling the accuracy vs balanced-accuracy metrics;
   - reconciling the fold counts;
   - describing the auditor as a checker, not an authority;
   - cutting the live demo to two controls;
   - adding proportionality rules;
   - removing any claim of measured time savings;
   - rewriting this attribution.
4. Arcadia's scaffold and oversight posts, surfaced by GPT's research, shaped the proportionality and "human owns the claim" framing.

**Timeline (BST, 23 Oct; approximate).**

| Time | Step |
|---|---|
| 10:06 | Clock started |
| 10:08 | Task received; topic chosen; build started |
| 10:16-10:24 | Runs A-D and research |
| 10:26 | Repo pushed to GitHub, doc drafted |
| 10:41 | GPT critique received |
| 10:52 | Final scope agreed |
| ~11:15 | Revisions, re-runs, final checks |

Full annotated outputs: `runs/` (A/B/C/D + `SCORECARD.md`) and `results/LOG.md`.

## With more time

1. **Real activations.** Use a small open model on Marks & Tegmark-style datasets with negations. The kit is unchanged; only the planted ground truth goes away.
2. **More runs.** Repeat each review condition about 10 times to measure *variance*. My hypothesis is that the real cost of ad hoc review is inconsistency across sessions.
3. **Subtler traps** that ad hoc review plausibly misses: label misalignment after a sort, token-position leakage, a familiarity confound.
4. **A pilot with one cohort.** Measure researcher time including rework, verdict lines that changed a decision, and the transfer-answer quality from the exit question.
5. **Falsifier packs per LASR area,** co-written with 2-3 supervisors.

## Sources

- **LASR Labs and Arcadia**
  - LASR Labs: <https://www.lasrlabs.org/>
  - Research Manager role: <https://www.arcadiaimpact.org/careers/research-manager>
  - Arcadia, "Lessons from building an automated research scaffold": <https://www.arcadiaimpact.org/blog/lessons-from-building-an-automated-research-scaffold>
  - Arcadia, "Obstacles to the scalable oversight of auto-alignment research": <https://www.arcadiaimpact.org/blog/obstacles-to-the-scalable-oversight-of-auto-alignment-research>
  - LASR alumni retrospective: <https://www.lesswrong.com/posts/CCxB3e2oL8yeLKESH/lasr-retrospective-and-advice>
  - LASR Summer 2026 call: <https://www.lesswrong.com/posts/dzSAsL4fPuBvCCarT/lasr-labs-summer-2026-applications-are-open>
- **Probing**
  - McKenzie et al., *Detecting High-Stakes Interactions with Activation Probes* (NeurIPS 2025): <https://www.lesswrong.com/posts/utcZSRv2JfahD8yfz/detecting-high-stakes-interactions-with-activation-probes>
  - Levinstein & Herrmann, *Still No Lie Detector for Language Models*: <https://arxiv.org/abs/2307.00175>
  - Marks & Tegmark, *The Geometry of Truth*: <https://arxiv.org/abs/2310.06824>
  - Hewitt & Liang, *Designing and Interpreting Probes with Control Tasks*: <https://arxiv.org/abs/1909.03368>
- **Leakage and automated research**
  - Kapoor & Narayanan, leakage and the reproducibility crisis: <https://reproducible.cs.princeton.edu/>
  - Beel et al., evaluation of the AI Scientist: <https://arxiv.org/abs/2502.14297>
- **AI assistance and human oversight**
  - Perry et al., *Do Users Write More Insecure Code with AI Assistants?*: <https://arxiv.org/abs/2211.03622>
  - Goddard et al., automation bias: <https://academic.oup.com/jamia/article/19/1/121/732254>
  - Panickssery et al., self-preference in LLM evaluators: <https://arxiv.org/abs/2404.13076>
  - METR developer study: <https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/>
  - Claude Code best practices: <https://code.claude.com/docs/en/best-practices>

**Time to completion: 1 hour 11 minutes, as at the time of submission.**
