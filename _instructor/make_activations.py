"""
INSTRUCTOR ONLY - do not give this file to the auditor.

Generates a stand-in for "residual-stream activations of a 16-layer model on
true/false statements". We use a simulated model rather than a real one so that
the ground truth is KNOWN, which lets us score the audit objectively.

Planted structure (the things a careful researcher should discover):
  1. A genuine but modest linear "truth" direction, strongest at middle layers.
  2. A NEGATION confound: false statements are mostly negations, true ones
     mostly affirmations. A probe can score ~75% from the word "not" alone.
  3. PARAPHRASE leakage: each statement appears as 4 paraphrases that share a
     large statement-specific component. A row-level random split puts
     near-duplicates in train and test, so a probe can memorise statements.
Nothing in the project folder states these facts.
"""
import csv
import os
import numpy as np

rng = np.random.default_rng(20261023)
N_LAYERS, D = 16, 128

capitals = [("France","Paris"),("Germany","Berlin"),("Italy","Rome"),("Spain","Madrid"),
    ("Portugal","Lisbon"),("Japan","Tokyo"),("China","Beijing"),("India","New Delhi"),
    ("Egypt","Cairo"),("Kenya","Nairobi"),("Peru","Lima"),("Chile","Santiago"),
    ("Canada","Ottawa"),("Australia","Canberra"),("Norway","Oslo"),("Sweden","Stockholm"),
    ("Finland","Helsinki"),("Poland","Warsaw"),("Greece","Athens"),("Turkey","Ankara"),
    ("Iran","Tehran"),("Iraq","Baghdad"),("Russia","Moscow"),("Ukraine","Kyiv"),
    ("Austria","Vienna"),("Hungary","Budapest"),("Ireland","Dublin"),("Belgium","Brussels"),
    ("Netherlands","Amsterdam"),("Denmark","Copenhagen"),("Mexico","Mexico City"),
    ("Argentina","Buenos Aires"),("Colombia","Bogota"),("Cuba","Havana"),("Nigeria","Abuja"),
    ("Ghana","Accra"),("Ethiopia","Addis Ababa"),("Morocco","Rabat"),("Thailand","Bangkok"),
    ("Vietnam","Hanoi"),("Indonesia","Jakarta"),("Philippines","Manila"),("Nepal","Kathmandu"),
    ("Pakistan","Islamabad"),("Bangladesh","Dhaka"),("Saudi Arabia","Riyadh"),
    ("Israel","Jerusalem"),("Jordan","Amman"),("Lebanon","Beirut"),("Syria","Damascus")]
elements = [("hydrogen","H"),("helium","He"),("lithium","Li"),("carbon","C"),("nitrogen","N"),
    ("oxygen","O"),("fluorine","F"),("neon","Ne"),("sodium","Na"),("magnesium","Mg"),
    ("aluminium","Al"),("silicon","Si"),("phosphorus","P"),("sulfur","S"),("chlorine","Cl"),
    ("argon","Ar"),("potassium","K"),("calcium","Ca"),("iron","Fe"),("copper","Cu"),
    ("zinc","Zn"),("silver","Ag"),("gold","Au"),("tin","Sn"),("lead","Pb"),("mercury","Hg"),
    ("uranium","U"),("platinum","Pt"),("nickel","Ni"),("cobalt","Co"),("titanium","Ti"),
    ("chromium","Cr"),("manganese","Mn"),("iodine","I"),("bromine","Br"),("tungsten","W"),
    ("barium","Ba"),("boron","B"),("krypton","Kr"),("xenon","Xe")]

facts = []  # (domain, template_args_correct, template_args_wrong)
for i, (c, cap) in enumerate(capitals):
    wrong = capitals[(i + 7) % len(capitals)][1]
    facts.append(("capital", c, cap, wrong))
for i, (e, s) in enumerate(elements):
    wrong = elements[(i + 5) % len(elements)][1]
    facts.append(("element", e, s, wrong))
for i in range(60):
    a, b = int(rng.integers(2, 20)), int(rng.integers(2, 20))
    facts.append(("arith", f"{a} plus {b}", str(a + b), str(a + b + int(rng.choice([-3,-2,-1,1,2,3])))))

TEMPLATES = {
    "capital": ["The capital of {s} is {neg}{o}.", "{o} is {neg}the capital city of {s}.",
                "In {s}, the capital is {neg}{o}.", "The capital city of {s} is {neg}{o}."],
    "element": ["The chemical symbol for {s} is {neg}{o}.", "{o} is {neg}the symbol for {s}.",
                "On the periodic table, {s} is {neg}written as {o}.", "The symbol of {s} is {neg}{o}."],
    "arith":   ["{s} is {neg}{o}.", "{s} {eq} {o}.",
                "The sum of {s} is {neg}{o}.", "If you add {s}, you do {neg}get {o}."],
}

def render(domain, s, o, negated, k):
    neg = "not " if negated else ""
    if domain == "arith" and k == 3:
        return TEMPLATES[domain][k].replace("do {neg}", "do not " if negated else "").format(s=s, o=o)
    eq = "does not equal" if negated else "equals"
    return TEMPLATES[domain][k].format(s=s, o=o, neg=neg, eq=eq)

# directions
u_truth = rng.standard_normal(D); u_truth /= np.linalg.norm(u_truth)
u_neg = rng.standard_normal(D); u_neg -= u_neg @ u_truth * u_truth; u_neg /= np.linalg.norm(u_neg)
layer_truth = float(os.environ.get('T', 0.7)) * np.exp(-0.5 * ((np.arange(N_LAYERS) - 9) / 3.0) ** 2)   # peaks mid-network
layer_neg = float(os.environ.get('NG', 4.0)) * np.ones(N_LAYERS)                                          # lexical, everywhere
layer_stmt = float(os.environ.get('S', 8.0)) * np.linspace(0.8, 1.07, N_LAYERS)                                 # memorisable identity
NOISE = float(os.environ.get('NZ', 0.15))                                             # per-paraphrase noise

rows, acts = [], []
stmt_id = 0
for fact_id, (domain, s, correct, wrong) in enumerate(facts):
    fact_vec = rng.standard_normal((N_LAYERS, D)) / np.sqrt(D) * 2.0
    for label in (1, 0):
        if label == 1:
            negated = rng.random() < 0.20   # true-by-negating-a-wrong-object
            obj = wrong if negated else correct
        else:
            negated = rng.random() < 0.70   # false-by-negating-the-right-object
            obj = correct if negated else wrong
        stmt_vec = rng.standard_normal((N_LAYERS, D)) / np.sqrt(D)
        for k in range(4):
            x = (fact_vec
                 + layer_stmt[:, None] * stmt_vec
                 + (layer_truth[:, None] * (1 if label else -1)) * u_truth[None, :]
                 + (layer_neg[:, None] * (1 if negated else -1) * 0.5) * u_neg[None, :]
                 + rng.standard_normal((N_LAYERS, D)) * NOISE)
            acts.append(x.astype(np.float32))
            rows.append(dict(row_id=len(rows), statement_id=stmt_id, fact_id=fact_id, domain=domain,
                             paraphrase=k, text=render(domain, s, obj, negated, k), label=label))
        stmt_id += 1

acts = np.stack(acts)
# shuffle row order so the file doesn't look grouped (as real extraction output often isn't)
perm = rng.permutation(len(rows))
acts = acts[perm]
rows = [dict(rows[i], row_id=j) for j, i in enumerate(perm)]

np.savez_compressed("../project/data/activations.npz", acts=acts)
with open("../project/data/statements.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["row_id", "statement_id", "fact_id", "domain", "paraphrase", "text", "label"])
    w.writeheader(); w.writerows(rows)
print("wrote", acts.shape, "rows:", len(rows))
