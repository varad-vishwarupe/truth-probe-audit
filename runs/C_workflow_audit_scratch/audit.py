import sys, json, warnings; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split, GroupKFold
from sklearn.tree import DecisionTreeClassifier
import verify as V

df = pd.read_csv('data/statements.csv'); A = np.load('data/activations.npz')['acts']
y = df.label.values; fact = df.fact_id.values; stmt = df.statement_id.values
def fp(Xtr, ytr, Xte):
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000)).fit(Xtr, ytr).predict(Xte)
def fp_tree(Xtr, ytr, Xte): return DecisionTreeClassifier(max_depth=3, random_state=0).fit(Xtr, ytr).predict(Xte)
out = {}
tr, te = train_test_split(np.arange(len(df)), test_size=0.2, random_state=0, stratify=y)
out['A_overlap_statement'] = V.group_overlap(tr, te, stmt)
out['A_overlap_fact'] = V.group_overlap(tr, te, fact)
# Reproduce naive (scaler on all) vs scaler on train only, layer 8
X8 = A[:, 8]
out['naive_l8_scaler_all'] = float(np.mean(LogisticRegression(max_iter=5000).fit(StandardScaler().fit_transform(X8)[tr], y[tr]).predict(StandardScaler().fit_transform(X8)[te]) == y[te]))
out['naive_l8_scaler_train'] = float(np.mean(fp(X8[tr], y[tr], X8[te]) == y[te]))
k = int(round(out['naive_l8_scaler_train'] * len(te))); out['naive_l8_wilson'] = V.wilson_ci(k, len(te)); out['n_test'] = len(te)
# Per-layer fact-grouped CV
out['fact_cv_by_layer'] = {L: V.grouped_cv_score(A[:, L], y, fact, fp) for L in range(A.shape[1])}
out['stmt_cv_by_layer_l8'] = V.grouped_cv_score(X8, y, stmt, fp)
# Nested: choose layer on inner fact-grouped CV, evaluate on outer fact fold
outer = []; chosen = []; preds = np.zeros(len(y), int)
for otr, ote in GroupKFold(5).split(X8, y, fact):
    inner = [V.grouped_cv_score(A[otr, L], y[otr], fact[otr], fp, n_splits=4)[0] for L in range(A.shape[1])]
    L = int(np.argmax(inner)); chosen.append(L)
    p = fp(A[otr, L], y[otr], A[ote, L]); preds[ote] = p; outer.append(float(np.mean(p == y[ote])))
out['nested_fact_cv'] = {'mean': float(np.mean(outer)), 'se': float(np.std(outer, ddof=1)/np.sqrt(5)), 'folds': outer, 'chosen_layers': chosen}
k = int((preds == y).sum()); out['nested_pooled_wilson'] = V.wilson_ci(k, len(y))
# Shuffled-label controls (group-aware: shuffle at fact level? labels vary within fact, so shuffle at statement level)
split_rand = lambda X, yy: train_test_split(np.arange(len(yy)), test_size=0.2, random_state=0, stratify=yy)
out['shuffle_stmt_rowsplit_l8'] = V.shuffled_label_control(X8, y, stmt, split_rand, fp, n_perm=10)[0]
def split_fact(X, yy):
    t, e = next(GroupKFold(5).split(X, yy, fact)); return t, e
out['shuffle_stmt_factsplit_l8'] = V.shuffled_label_control(X8, y, stmt, split_fact, fp, n_perm=10)[0]
# Surface baselines (fact-grouped)
feats = V.surface_features(df.text.tolist(), extra={'domain': pd.factorize(df.domain)[0].astype(float), 'paraphrase': df.paraphrase.values.astype(float)})
out['surface_baselines_fact_cv'] = V.surface_baselines(feats, y, fact, fp_tree)
neg = feats['has_negation'].astype(int)
# Stratified score of nested probe predictions on negation
out['stratified_by_negation_nested'] = V.stratified_score(y, preds, neg)
out['stratified_by_neg_x_domain_nested'] = V.stratified_score(y, preds, df.domain + '_' + neg.astype(str))
# Hostile reviewer: train on affirmative only, test on negated (fact-disjoint), and vice versa
for Ltest in [8, out['nested_fact_cv']['chosen_layers'][0]]:
    r = []
    for otr, ote in GroupKFold(5).split(X8, y, fact):
        a = otr[neg[otr] == 0]; b = ote[neg[ote] == 1]
        r.append(float(np.mean(fp(A[a, Ltest], y[a], A[b, Ltest]) == y[b])))
    out[f'aff_to_neg_factdisjoint_L{Ltest}'] = float(np.mean(r))
    r = []
    for otr, ote in GroupKFold(5).split(X8, y, fact):
        a = otr[neg[otr] == 0]; b = ote[neg[ote] == 0]
        r.append(float(np.mean(fp(A[a, Ltest], y[a], A[b, Ltest]) == y[b])))
    out[f'aff_to_aff_factdisjoint_L{Ltest}'] = float(np.mean(r))
# Cross-domain: leave one domain out, layer 8
out['leave_domain_out_l8'] = {d: float(np.mean(fp(X8[df.domain.values != d], y[df.domain.values != d], X8[df.domain.values == d]) == y[df.domain.values == d])) for d in df.domain.unique()}
# Does layer 8 linearly decode negation & fact-correctness (affirmative-truth)?
factcorrect = np.where(neg == 1, 1 - y, y)
out['decode_negation_l8'] = V.grouped_cv_score(X8, neg, fact, fp)[0]
out['decode_factcorrect_l8'] = V.grouped_cv_score(X8, factcorrect, fact, fp)[0]
out['label_given_negation_balance'] = pd.crosstab(neg, y).to_dict()
# Seed sensitivity of naive row split
out['naive_seed_l8'] = [float(np.mean(fp(X8[a], y[a], X8[b]) == y[b])) for a, b in (train_test_split(np.arange(len(y)), test_size=0.2, random_state=s, stratify=y) for s in range(10))]
print(json.dumps(out, indent=1, default=str))
