"""Audit checks 1: C sweep (where does 0.75 come from), clustered CIs, seed sensitivity, lexical baselines."""
import numpy as np, pandas as pd, json
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.feature_extraction.text import CountVectorizer
import verify as V
df = pd.read_csv("data/statements.csv"); acts = np.load("data/activations.npz")["acts"]
y = df.label.values; facts = df.fact_id.values
neg = V.surface_features(df.text.tolist())["has_negation"].astype(int)
def fp(C):
    return lambda a,b,c: make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000)).fit(a,b).predict(c)
def cvpred(X, f, folds):
    p = np.empty_like(y)
    for tr, te in folds: p[te] = f(X[tr], y[tr], X[te])
    return p
gk = list(GroupKFold(5).split(acts, y, facts))
print("== C sweep, layer 8 and 2, outer folds (test-selected!)")
for L in [2, 8]:
    for C in [0.003, 0.01, 0.03, 0.1, 1.0]:
        p = cvpred(acts[:, L], fp(C), gk)
        print(L, C, "acc %.3f strat %.3f" % ((p==y).mean(), V.stratified_score(y,p,neg)["mean"]))
# fact-cluster bootstrap of a prediction vector
def boot(p, nb=2000, seed=0):
    rng = np.random.default_rng(seed); uf = np.unique(facts); idx = {f: np.where(facts==f)[0] for f in uf}
    A, S = [], []
    for _ in range(nb):
        ii = np.concatenate([idx[f] for f in rng.choice(uf, len(uf))])
        A.append((p[ii]==y[ii]).mean()); S.append(V.stratified_score(y[ii], p[ii], neg[ii])["mean"])
    return np.percentile(A,[2.5,97.5]), np.percentile(S,[2.5,97.5])
# reproduce nested predictions cheaply? reuse honest selection: per fold (layer,C) from honest_results.json
H = json.load(open("results/honest_results.json"))
pn = np.empty_like(y)
for (tr, te), r in zip(gk, H["folds"]):
    pn[te] = fp(r["C"])(acts[tr, r["layer"]], y[tr], acts[te, r["layer"]])
print("== nested preds reproduced: acc %.4f strat %.4f" % ((pn==y).mean(), V.stratified_score(y,pn,neg)["mean"]))
a, s = boot(pn); print("fact-cluster bootstrap 95% CI acc", a.round(3), "strat", s.round(3))
# negation baseline CI
pb = cvpred(neg.reshape(-1,1).astype(float), fp(1.0), gk); print("neg baseline acc %.3f" % (pb==y).mean(), "CI", boot(pb)[0].round(3))
# early vs mid within-strata, fact-paired bootstrap of the difference
p2 = cvpred(acts[:, 2], fp(0.01), gk); p8 = cvpred(acts[:, 8], fp(0.01), gk)
rng = np.random.default_rng(1); uf = np.unique(facts); idx = {f: np.where(facts==f)[0] for f in uf}; D=[]
for _ in range(2000):
    ii = np.concatenate([idx[f] for f in rng.choice(uf, len(uf))])
    D.append(V.stratified_score(y[ii],p8[ii],neg[ii])["mean"] - V.stratified_score(y[ii],p2[ii],neg[ii])["mean"])
print("strat L8 - L2 (C=.01): %.3f CI" % (V.stratified_score(y,p8,neg)["mean"]-V.stratified_score(y,p2,neg)["mean"]), np.percentile(D,[2.5,97.5]).round(3))
print("== seed sensitivity: random fact-group fold assignments, layer 8, C=0.01")
for sd in range(5):
    perm = np.random.default_rng(sd).permutation(np.unique(facts)); fmap = {f: i%5 for i,f in enumerate(perm)}
    fo = np.array([fmap[f] for f in facts]); folds = [(np.where(fo!=k)[0], np.where(fo==k)[0]) for k in range(5)]
    p = cvpred(acts[:, 8], fp(0.01), folds)
    print(sd, "acc %.3f strat %.3f" % ((p==y).mean(), V.stratified_score(y,p,neg)["mean"]))
print("== lexical baselines (BoW unigrams+bigrams, vocab fit on train fold only), fact-grouped")
for ng in [(1,1),(1,2)]:
    p = np.empty_like(y)
    for tr, te in gk:
        cv = CountVectorizer(ngram_range=ng, token_pattern=r"(?u)\b\w+\b").fit(df.text.values[tr])
        m = LogisticRegression(C=1.0, max_iter=5000).fit(cv.transform(df.text.values[tr]), y[tr])
        p[te] = m.predict(cv.transform(df.text.values[te]))
    print(ng, "acc %.3f strat %.3f" % ((p==y).mean(), V.stratified_score(y,p,neg)["mean"]), V.stratified_score(y,p,neg)["per_stratum"])
print("== within-strata by domain and by paraphrase template (layer 8 nested preds)")
for col in ["domain", "paraphrase"]:
    for v in sorted(df[col].unique()):
        m = (df[col]==v).values
        print(col, v, "acc %.3f strat %.3f" % ((pn[m]==y[m]).mean(), V.stratified_score(y[m],pn[m],neg[m])["mean"]))
