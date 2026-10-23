"""
honest_probe.py: the same experiment after the audit loop.

Changes vs naive_probe.py (each maps to an audit finding):
  * split by fact_id (GroupKFold), so no fact, and hence no paraphrase, crosses train/test
  * scaler lives inside the pipeline (fit on train folds only)
  * layer and C chosen by an INNER grouped CV; the outer folds are only scored
  * ships with the standard controls from verify.py: group-aware shuffled labels,
    surface-feature baselines, and accuracy *within* negation strata
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import verify as V

SEED = 0
df = pd.read_csv("data/statements.csv")
acts = np.load("data/activations.npz")["acts"]
y = df["label"].values
facts = df["fact_id"].values
stmts = df["statement_id"].values
feats = V.surface_features(df["text"].tolist(),
                           extra={"domain": pd.factorize(df["domain"])[0].astype(float)})
neg = feats["has_negation"].astype(int)
L = acts.shape[1]
C_GRID = [0.003, 0.01, 0.03, 0.1, 1.0]


def make_fp(C):
    def fp(Xtr, ytr, Xte):
        m = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000))
        return m.fit(Xtr, ytr).predict(Xte)
    return fp


# ---- nested grouped CV: select (layer, C) on inner folds, score on outer fold
outer = GroupKFold(n_splits=5)
fold_rows, all_pred, all_idx = [], [], []
for k, (tr, te) in enumerate(outer.split(acts, y, facts)):
    best = (-1, None, None)
    for layer in range(L):
        for C in C_GRID:
            s, _ = V.grouped_cv_score(acts[tr, layer], y[tr], facts[tr], make_fp(C), n_splits=4)
            if s > best[0]:
                best = (s, layer, C)
    _, layer, C = best
    pred = make_fp(C)(acts[tr, layer], y[tr], acts[te, layer])
    fold_rows.append({"fold": k, "layer": layer, "C": C, "inner_acc": best[0],
                      "outer_acc": float((pred == y[te]).mean()),
                      "outer_within_negation_strata": V.stratified_score(y[te], pred, neg[te])["mean"]})
    all_pred.append(pred); all_idx.append(te)
    print(fold_rows[-1])

pred = np.empty_like(y); pred[np.concatenate(all_idx)] = np.concatenate(all_pred)
acc = float((pred == y).mean())
k = int((pred == y).sum())
strat = V.stratified_score(y, pred, neg)

# ---- controls
fp_naive = make_fp(1.0)
naive_split = lambda X, yy: train_test_split(np.arange(len(yy)), test_size=0.2,
                                              random_state=SEED, stratify=yy)
def grouped_split(X, yy):
    return next(GroupKFold(5).split(X, yy, facts))

shuf_naive, _ = V.shuffled_label_control(acts[:, 8], y, stmts, naive_split, fp_naive, n_perm=5)
shuf_group, _ = V.shuffled_label_control(acts[:, 8], y, stmts, grouped_split, make_fp(0.01), n_perm=5)
tr0, te0 = naive_split(None, y)
overlap_stmt = V.group_overlap(tr0, te0, stmts)
overlap_fact = V.group_overlap(tr0, te0, facts)
baselines = V.surface_baselines(feats, y, facts, make_fp(1.0))

# ---- per-layer curves for the figure (fixed C=0.01 for readability)
curve_group, curve_strat = [], []
for layer in range(L):
    ps = np.empty_like(y)
    for tr, te in GroupKFold(5).split(acts, y, facts):
        ps[te] = make_fp(0.01)(acts[tr, layer], y[tr], acts[te, layer])
    curve_group.append(float((ps == y).mean()))
    curve_strat.append(V.stratified_score(y, ps, neg)["mean"])
naive_curve = [r["test_acc"] for r in json.load(open("results/naive_results.json"))["per_layer"]]

out = {
    "headline_naive": max(naive_curve),
    "nested_grouped_acc": acc, "wilson_95ci": V.wilson_ci(k, len(y)),
    "within_negation_strata_bal_acc": strat,
    "folds": fold_rows,
    "controls": {
        "shuffled_labels_under_naive_split_layer8": shuf_naive,
        "shuffled_labels_under_grouped_split_layer8": shuf_group,
        "naive_split_overlap_statement": overlap_stmt,
        "naive_split_overlap_fact": overlap_fact,
        "surface_baselines_grouped_cv": baselines,
    },
    "curves": {"naive_random_split": naive_curve, "grouped": curve_group,
               "grouped_within_negation_strata": curve_strat},
}
json.dump(out, open("results/honest_results.json", "w"), indent=2)

fig, ax = plt.subplots(figsize=(7.5, 5.2))
x = np.arange(L)
ax.plot(x, naive_curve, "o-", c="#c0392b", label="naive: random row split, best layer picked on test")
ax.plot(x, curve_group, "s-", c="#2c3e50", label="grouped by fact (no paraphrase leakage)")
ax.plot(x, curve_strat, "^-", c="#16a085", label="grouped, within negation strata (confound removed)")
ax.axhline(baselines["has_negation"], ls="--", c="#8e44ad", label=f"'contains not' baseline ({baselines['has_negation']:.2f})")
ax.axhline(shuf_naive, ls=":", c="#c0392b", label=f"shuffled labels, naive split ({shuf_naive:.2f})")
ax.axhline(0.5, ls=":", c="grey")
ax.set_xlabel("layer"); ax.set_ylabel("accuracy"); ax.set_ylim(0.4, 1.02)
ax.set_title("Same activations, same probe: what the number means depends on the checks")
ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=False)
fig.tight_layout(); fig.savefig("results/before_after.png", dpi=160)
print(json.dumps({k: v for k, v in out.items() if k not in ("curves", "folds")}, indent=2))
