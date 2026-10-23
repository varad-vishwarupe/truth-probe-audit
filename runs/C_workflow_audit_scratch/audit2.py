import sys, json, warnings; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
from sklearn.metrics import balanced_accuracy_score as bacc
import verify as V
df = pd.read_csv('data/statements.csv'); A = np.load('data/activations.npz')['acts']
y = df.label.values; fact = df.fact_id.values
neg = V.surface_features(df.text.tolist())['has_negation'].astype(int)
fp = lambda a,b,c: make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000)).fit(a,b).predict(c)
X8 = A[:,8]; out = {}
for name,(trm,tem) in {'aff->neg':(0,1),'aff->aff':(0,0),'neg->aff':(1,0),'neg->neg':(1,1)}.items():
    yt=[];yp=[]
    for tr,te in GroupKFold(5).split(X8,y,fact):
        a=tr[neg[tr]==trm]; b=te[neg[te]==tem]; yt+=list(y[b]); yp+=list(fp(X8[a],y[a],X8[b]))
    yt,yp=np.array(yt),np.array(yp); out[name]={'acc':float((yt==yp).mean()),'bal_acc':float(bacc(yt,yp)),'n':len(yt),'majority':float(max(yt.mean(),1-yt.mean()))}
# negation+domain baseline
D = np.c_[neg, pd.get_dummies(df.domain).values.astype(float), V.surface_features(df.text.tolist())['n_words']]
out['neg+domain+nwords_baseline'] = V.grouped_cv_score(D,y,fact,lambda a,b,c: LogisticRegression(max_iter=5000).fit(a,b).predict(c))[0]
# duplicate texts with conflicting labels
g = df.groupby('text').label.nunique(); out['dup_texts']=int((df.text.duplicated()).sum()); out['dup_texts_conflicting_label']=int((g>1).sum())
print(json.dumps(out,indent=1))
