import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, train_test_split
P='/tmp/claude-0/-home-claude/80d0ee3e-87ad-5950-a81d-0ef3a9619ff6/scratchpad/sandbox_adhoc/project/'
df=pd.read_csv(P+'data/statements.csv'); A=np.load(P+'data/activations.npz')['acts']; y=df.label.values
neg=df.text.str.contains(r"\bnot\b",regex=True).values.astype(int)
print('neg-word baseline acc (predict false if not):', ((1-neg)==y).mean())
mk=lambda: make_pipeline(StandardScaler(),LogisticRegression(max_iter=5000))
tr,te=train_test_split(np.arange(len(df)),test_size=0.2,random_state=0,stratify=y)
print('test rows whose statement_id in train:', np.isin(df.statement_id.values[te],df.statement_id.values[tr]).mean(),
      'fact_id in train:', np.isin(df.fact_id.values[te],df.fact_id.values[tr]).mean())
gkf=GroupKFold(5)
rows=[]
for L in range(A.shape[1]):
    X=A[:,L]
    # grouped CV by fact
    acc=[];accN=[];accP=[];negacc=[]
    for a,b in gkf.split(X,y,df.fact_id):
        m=mk().fit(X[a],y[a]); p=m.predict(X[b])
        acc.append((p==y[b]).mean())
        nb=neg[b]==1; accN.append((p[nb]==y[b][nb]).mean()); accP.append((p[~nb]==y[b][~nb]).mean())
        negacc.append((mk().fit(X[a],neg[a]).predict(X[b])==neg[b]).mean())
    # cross-domain: train two domains, test held-out, average
    xd=[]
    for d in df.domain.unique():
        a=df.domain.values!=d; m=mk().fit(X[a],y[a]); xd.append(m.score(X[~a],y[~a]))
    # orig naive split for comparison
    naive=mk().fit(X[tr],y[tr]).score(X[te],y[te])
    rows.append(dict(layer=L,naive=naive,grouped=np.mean(acc),grp_negated=np.mean(accN),grp_affirm=np.mean(accP),xdomain=np.mean(xd),neg_decode=np.mean(negacc)))
r=pd.DataFrame(rows).round(3); print(r.to_string(index=False))
