"""
verify.py: small, boring, reusable controls for probe/classifier results.

Each function answers one question a reviewer will ask. They are deliberately
model-agnostic: pass in a `fit_predict(X_tr, y_tr, X_te) -> y_pred` function and
your arrays. Copy this file into any project.
"""
from __future__ import annotations

import re
from typing import Callable, Sequence

import numpy as np
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold

FitPredict = Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]


# ---------------------------------------------------------------- splits
def group_overlap(train_idx, test_idx, groups) -> dict:
    """How many test rows share a group with some training row? Should be 0."""
    tr = set(np.asarray(groups)[train_idx])
    shared = np.isin(np.asarray(groups)[test_idx], list(tr))
    return {"test_rows_sharing_group": int(shared.sum()),
            "frac_test_rows_sharing_group": float(shared.mean())}


def grouped_cv_score(X, y, groups, fit_predict: FitPredict, n_splits=5, metric=None):
    """Mean/SE of accuracy under GroupKFold (no group appears in train and test)."""
    metric = metric or (lambda yt, yp: float(np.mean(yt == yp)))
    scores = []
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        scores.append(metric(y[te], fit_predict(X[tr], y[tr], X[te])))
    scores = np.array(scores)
    return float(scores.mean()), float(scores.std(ddof=1) / np.sqrt(len(scores)))


# ---------------------------------------------------------------- null control
def shuffle_within_structure(y, shuffle_groups, rng):
    """Permute labels at the level of `shuffle_groups` (e.g. statement_id) so that
    rows that share a group keep a shared (now meaningless) label. A row-level
    shuffle would destroy the very structure that causes leakage, and hide it."""
    y = np.asarray(y); shuffle_groups = np.asarray(shuffle_groups)
    uniq = np.unique(shuffle_groups)
    first = {g: y[np.argmax(shuffle_groups == g)] for g in uniq}
    perm_vals = rng.permutation([first[g] for g in uniq])
    mapping = dict(zip(uniq, perm_vals))
    return np.array([mapping[g] for g in shuffle_groups])


def shuffled_label_control(X, y, shuffle_groups, split_fn, fit_predict: FitPredict,
                           n_perm=5, seed=0):
    """Score of the *same pipeline* when labels carry no information.
    `split_fn(X, y) -> (train_idx, test_idx)` must be the split you actually used."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_perm):
        ys = shuffle_within_structure(y, shuffle_groups, rng)
        tr, te = split_fn(X, ys)
        out.append(float(np.mean(fit_predict(X[tr], ys[tr], X[te]) == ys[te])))
    return float(np.mean(out)), out


# ---------------------------------------------------------------- shortcuts
def surface_features(texts: Sequence[str], extra: dict | None = None) -> dict:
    """Cheap features that often predict labels for the wrong reason."""
    feats = {
        "n_chars": np.array([len(t) for t in texts], float),
        "n_words": np.array([len(t.split()) for t in texts], float),
        "has_negation": np.array([bool(re.search(r"\b(not|no|never|n't)\b", t.lower()))
                                  for t in texts], float),
        "has_digit": np.array([bool(re.search(r"\d", t)) for t in texts], float),
    }
    feats.update(extra or {})
    return feats


def surface_baselines(feats: dict, y, groups, fit_predict: FitPredict) -> dict:
    """Grouped-CV accuracy of a classifier that sees ONE surface feature only."""
    return {name: grouped_cv_score(np.asarray(v, float).reshape(-1, 1), np.asarray(y),
                                   groups, fit_predict)[0]
            for name, v in feats.items()}


def stratified_score(y_true, y_pred, strata) -> dict:
    """Balanced accuracy *within* each stratum of a confound, then averaged.
    A probe that only reads the confound scores 0.5 here."""
    y_true, y_pred, strata = map(np.asarray, (y_true, y_pred, strata))
    per = {}
    for s in np.unique(strata):
        m = strata == s
        if len(np.unique(y_true[m])) == 2:
            per[str(s)] = float(balanced_accuracy_score(y_true[m], y_pred[m]))
    return {"mean": float(np.mean(list(per.values()))), "per_stratum": per}


# ---------------------------------------------------------------- stats
def cluster_bootstrap_ci(y_true, y_pred, clusters, metric=None, n_boot=2000, seed=0,
                         alpha=0.05):
    """CI that respects clustering (e.g. 8 paraphrase rows per fact). Resamples whole
    clusters with replacement. Use this, not wilson_ci, whenever rows are not
    independent; otherwise the interval is too narrow.
    `metric(idx) -> float` lets you bootstrap any score, e.g. a stratified one."""
    y_true, y_pred, clusters = map(np.asarray, (y_true, y_pred, clusters))
    metric = metric or (lambda idx: float(np.mean(y_true[idx] == y_pred[idx])))
    rng = np.random.default_rng(seed)
    uniq = np.unique(clusters)
    members = {c: np.flatnonzero(clusters == c) for c in uniq}
    stats = [metric(np.concatenate([members[c] for c in rng.choice(uniq, len(uniq))]))
             for _ in range(n_boot)]
    lo, hi = np.percentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def wilson_ci(k: int, n: int, z: float = 1.96):
    """Only valid for independent rows. For clustered data use cluster_bootstrap_ci."""
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(centre - half), float(centre + half)
