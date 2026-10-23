"""Per-layer logistic-regression truth probe.

Split is grouped by fact_id so paraphrases of the same fact never appear in
both train and test. Because negation ("not") is correlated with the label in
this dataset, we also report accuracy separately on negated / non-negated test
statements and a negation-only baseline, to tell a truth direction apart from
a "contains not" direction.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 0
os.makedirs("results", exist_ok=True)

acts = np.load("data/activations.npz")["acts"]          # (n, L, d)
df = pd.read_csv("data/statements.csv")
assert len(df) == acts.shape[0]
y = df["label"].to_numpy()
neg = df["text"].str.contains(r"\bnot\b", case=False).to_numpy()
groups = df["fact_id"].to_numpy()

tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED)
              .split(acts, y, groups))
assert not set(groups[tr]) & set(groups[te])

# Baseline: predict label from presence of "not" alone (fit direction on train)
neg_rule = (y[tr][neg[tr]].mean() < 0.5)  # True -> negated means false
base_pred = np.where(neg[te], 0, 1) if neg_rule else np.where(neg[te], 1, 0)
base_acc = (base_pred == y[te]).mean()

def probe():
    return make_pipeline(StandardScaler(),
                         LogisticRegression(C=0.1, max_iter=2000))

rows = []
for layer in range(acts.shape[1]):
    X = acts[:, layer, :]
    clf = probe().fit(X[tr], y[tr])
    pred = clf.predict(X[te])
    ok = pred == y[te]
    nclf = probe().fit(X[tr], neg[tr])            # is negation decodable?
    rows.append(dict(layer=layer,
                     train_acc=clf.score(X[tr], y[tr]),
                     test_acc=ok.mean(),
                     test_acc_negated=ok[neg[te]].mean(),
                     test_acc_affirmative=ok[~neg[te]].mean(),
                     negation_probe_acc=nclf.score(X[te], neg[te])))
res = pd.DataFrame(rows)
res.to_csv("results/probe_accuracy.csv", index=False)

pd.set_option("display.float_format", "{:.3f}".format)
print(f"n_train={len(tr)} n_test={len(te)} (grouped by fact_id)")
print(f"Negation-only baseline test acc: {base_acc:.3f}\n")
print(res.to_string(index=False))
best = res.loc[res.test_acc.idxmax()]
print(f"\nBest layer: {int(best.layer)}  test acc {best.test_acc:.3f} "
      f"(negated {best.test_acc_negated:.3f}, "
      f"affirmative {best.test_acc_affirmative:.3f})")

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(res.layer, res.test_acc, "o-", lw=2, label="Truth probe (all test)")
ax.plot(res.layer, res.test_acc_affirmative, "--", label="Truth probe: affirmative")
ax.plot(res.layer, res.test_acc_negated, "--", label="Truth probe: negated")
ax.axhline(base_acc, color="gray", ls=":", label=f"'not'-only baseline ({base_acc:.2f})")
ax.axhline(0.5, color="lightgray", lw=1)
ax.set(xlabel="Layer", ylabel="Test accuracy", ylim=(0.3, 1.02),
       title="Per-layer truth probe (split grouped by fact)")
ax.legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig("results/probe_accuracy.png", dpi=150)
print("Saved results/probe_accuracy.png and results/probe_accuracy.csv")
