"""Audit checks 2: nested shuffled-label null, missed negation forms, within-stratum surface baselines,
late-layer CIs, probe-minus-negation paired CI."""
import numpy as np, pandas as pd, json, re, sys
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
import verify as V
df = pd.read_csv("data/statements.csv"); acts = np.load("data/activations.npz")["acts"]
y = df.label.values; facts = df.fact_id.values; stmts = df.statement_id.values
F = V.surface_features(df.text.tolist(), extra={"domain": pd.factorize(df.domain)[0].astype(float)})
neg = F["has_negation"].astype(int)
print("texts with n't/isn't/false/incorrect/never:", df.text.str.contains(r"n't|\bfalse\b|incorrect|\bnever\b|\bno\b", case=False).sum())
print("texts with 'not' but neg==0:", (df.text.str.contains(r"\bnot\b", case=False) & (neg==0)).sum())
def fp(C): return lambda a,b,c: make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000)).fit(a,b).predict(c)
gk = list(GroupKFold(5).split(acts, y, facts))
def cvpred(X, f, yy=y):
    p = np.empty_like(yy)
    for tr, te in gk: p[te] = f(X[tr], yy[tr], X[te])
    return p
print("== within-negation-stratum surface baselines (fit separately in each stratum, fact-grouped CV)")
for name in ["n_chars","n_words","has_digit","domain"]:
    res = []
    for s in [0,1]:
        m = neg==s; Xs = F[name][m].reshape(-1,1); ys=y[m]; p=np.empty_like(ys)
        for tr,te in GroupKFold(5).split(Xs, ys, facts[m]): p[te]=fp(1.0)(Xs[tr],ys[tr],Xs[te])
        res.append(V.stratified_score(ys,p,np.zeros_like(ys))["mean"])
    print(name, np.round(res,3))
H = json.load(open("results/honest_results.json"))
pn = np.empty_like(y)
for (tr,te), r in zip(gk, H["folds"]): pn[te] = fp(r["C"])(acts[tr, r["layer"]], y[tr], acts[te, r["layer"]])
pb = cvpred(neg.reshape(-1,1).astype(float), fp(1.0))
uf = np.unique(facts); idx = {f: np.where(facts==f)[0] for f in uf}; rng = np.random.default_rng(2)
D = []
for _ in range(2000):
    ii = np.concatenate([idx[f] for f in rng.choice(uf, len(uf))]); D.append((pn[ii]==y[ii]).mean()-(pb[ii]==y[ii]).mean())
print("probe - negation baseline: %.3f CI" % ((pn==y).mean()-(pb==y).mean()), np.percentile(D,[2.5,97.5]).round(3))
print("== per-layer within-strata at C=0.01 with fact-bootstrap CI")
for L in [0,1,12,13,14,15]:
    p = cvpred(acts[:,L], fp(0.01)); S=[]
    for _ in range(1000):
        ii = np.concatenate([idx[f] for f in rng.choice(uf, len(uf))]); S.append(V.stratified_score(y[ii],p[ii],neg[ii])["mean"])
    print(L, "%.3f" % V.stratified_score(y,p,neg)["mean"], np.percentile(S,[2.5,97.5]).round(3))
print("== full nested pipeline under statement-level label shuffle (n_perm=%s)" % sys.argv[1])
CG=[0.003,0.01,0.03,0.1,1.0]
for perm in range(int(sys.argv[1])):
    ys = V.shuffle_within_structure(y, stmts, np.random.default_rng(100+perm)); p=np.empty_like(ys)
    for tr,te in gk:
        best=(-1,None,None)
        for L in range(acts.shape[1]):
            for C in CG:
                s,_=V.grouped_cv_score(acts[tr,L], ys[tr], facts[tr], fp(C), n_splits=4)
                if s>best[0]: best=(s,L,C)
        p[te]=fp(best[2])(acts[tr,best[1]], ys[tr], acts[te,best[1]])
    print(perm, "acc %.3f strat %.3f inner_best %.3f" % ((p==ys).mean(), V.stratified_score(ys,p,neg)["mean"], best[0]))
