"""
Linear truth probe across layers.

Written in one fluent Claude Code session ("train a logistic regression probe
on each layer's activations to predict whether the statement is true, report
the best layer, make a plot"). It runs first time, the plot looks great, and
the summary Claude wrote at the end said the result was strong. This is the
version a fellow would be tempted to put in a draft.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

SEED = 0

df = pd.read_csv("data/statements.csv")
acts = np.load("data/activations.npz")["acts"]          # (n_statements, n_layers, d_model)
y = df["label"].values
n_layers = acts.shape[1]

train_idx, test_idx = train_test_split(
    np.arange(len(df)), test_size=0.2, random_state=SEED, stratify=y
)

results = []
for layer in range(n_layers):
    X = acts[:, layer, :]
    scaler = StandardScaler().fit(X)                      # normalise features
    X = scaler.transform(X)
    probe = LogisticRegression(max_iter=5000)
    probe.fit(X[train_idx], y[train_idx])
    acc = probe.score(X[test_idx], y[test_idx])
    results.append({"layer": layer, "test_acc": acc})
    print(f"layer {layer:2d}  test acc {acc:.3f}")

res = pd.DataFrame(results)
best = res.loc[res["test_acc"].idxmax()]
print(f"\nBest layer: {int(best.layer)}  accuracy {best.test_acc:.3f}")

plt.figure(figsize=(6, 3.5))
plt.plot(res["layer"], res["test_acc"], marker="o")
plt.axhline(0.5, ls="--", c="grey", label="chance")
plt.xlabel("layer"); plt.ylabel("test accuracy"); plt.ylim(0.4, 1.0)
plt.title("Linear truth probe accuracy by layer")
plt.legend(); plt.tight_layout()
plt.savefig("results/naive_probe_by_layer.png", dpi=150)

with open("results/naive_results.json", "w") as f:
    json.dump({"best_layer": int(best.layer), "best_test_acc": float(best.test_acc),
               "per_layer": results}, f, indent=2)
