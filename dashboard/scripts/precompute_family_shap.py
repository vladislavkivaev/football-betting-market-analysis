"""
Precompute per-league, per-family mean signed SHAP contributions for the
universal Isolation Forest (H2) — the same computation as 03_modeling.ipynb
Cell 15 ("which families push GREECE toward anomaly"), generalized to all
four leagues so the dashboard can show any league, not just Greece.

Run this ONCE from the repo root, after 03_modeling.ipynb has been run (so
features.parquet and feature_dictionary.csv already exist). It reuses the
exact same imputation, hyperparameters, and family-grouping as that notebook
— this script does not introduce a new methodology, it just persists Cell
15's output as a small artifact so the Streamlit dashboard never has to
refit the model or re-run SHAP itself (refitting on every page load would be
slow, and SHAP/sklearn version differences between machines could make the
numbers drift slightly from what's already in the presentation — better to
freeze the numbers once, the same way scored_matches.parquet freezes if_u_score).

Output: data/processed/family_shap_by_league.csv
Columns: league, family, mean_signed_shap
(more negative mean_signed_shap = that family pushes that league's matches
further toward the anomalous end, on average, across ALL matches — not just
flagged ones. This matches the "0.49 / 0.34 / 0.10 / 0.05 / 0.02" style chart
from the mid-project presentation, generalized beyond just Greece.)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import json
from sklearn.ensemble import IsolationForest


def find_repo_root(marker="data/processed"):
    p = Path.cwd()
    for cand in [p, *p.parents]:
        if (cand / marker).is_dir():
            return cand
    raise FileNotFoundError(f"couldn't locate '{marker}' from {Path.cwd()} upward")


REPO = find_repo_root()
PROC = REPO / "data" / "processed"

df = pd.read_parquet(PROC / "features.parquet")
fd = pd.read_csv(PROC / "feature_dictionary.csv")
assert len(df) == 8915, f"expected 8915 rows, got {len(df)}"

roles_path = PROC / "feature_roles.json"
if roles_path.exists():
    # exact match to 03_modeling.ipynb Cell 2: universal = cols_for("model_natural", "model_both")
    roles = json.load(open(roles_path))["roles"]
    universal = [c for c, r in roles.items() if r in ("model_natural", "model_both")]
    print(f"using feature_roles.json (exact match to notebook's universal set)")
else:
    # fallback: feature_dictionary.csv's in_universal_H2 flag (approximate —
    # may not be byte-for-byte identical to the notebook's role-based set)
    universal = fd[fd["in_universal_H2"]]["column"].tolist()
    print(f"feature_roles.json not found — falling back to feature_dictionary.csv "
          f"(approximate; for an exact match, copy feature_roles.json into "
          f"{PROC} from wherever 02_features.ipynb wrote it)")

fam_map = dict(zip(fd["column"], fd["family"]))
assert len(universal) == 35, f"expected 35 universal features, got {len(universal)}"

# --- per-league-season median imputation, natural cols only (same as 03 Cell 6) ---
for c in universal:
    med_ls = df.groupby(["league", "season"])[c].transform("median")
    med_l = df.groupby("league")[c].transform("median")
    med_g = df[c].median()
    df[c] = df[c].fillna(med_ls).fillna(med_l).fillna(med_g)
assert df[universal].isna().sum().sum() == 0, "imputation left NaN — check coverage"

# --- fit universal Isolation Forest, SAME pinned hyperparameters as 03 Cell 8 ---
X = df[universal].copy()
IF_KW = dict(
    n_estimators=200, max_samples=256, max_features=1.0,
    contamination=0.05, bootstrap=False, random_state=42, n_jobs=-1,
)
iso = IsolationForest(**IF_KW).fit(X)
df["if_u_score"] = iso.decision_function(X)

print(f"flag rate (sanity check, expect ~0.05): {(df['if_u_score'] < 0).mean():.4f}")

# --- SHAP, same as 03 Cell 13 ---
print("running TreeExplainer SHAP on 8,915 rows (may take a minute)...")
explainer = shap.TreeExplainer(iso)
sv = explainer.shap_values(X, check_additivity=False)
sv_u = pd.DataFrame(sv, columns=universal, index=df.index)

corr = np.corrcoef(sv_u.sum(axis=1), df["if_u_score"])[0, 1]
print(f"corr(sum SHAP, decision_function) = {corr:.3f}  "
      f"(sanity check against 03_modeling.ipynb's printed value)")

# --- per-row family-summed signed SHAP, same transpose-groupby as 03 Cell 15 ---
fam = pd.Series({c: fam_map.get(c, "??") for c in universal})
signed_by_fam = sv_u.T.groupby(fam).sum().T

rows = []
for code in sorted(df["league"].unique()):
    mask = (df["league"] == code).values
    means = signed_by_fam[mask].mean()
    for fam_name, val in means.items():
        rows.append({"league": code, "family": fam_name,
                     "mean_signed_shap": round(float(val), 4)})
out = pd.DataFrame(rows)

out_path = PROC / "family_shap_by_league.csv"
out.to_csv(out_path, index=False)
print(f"\nsaved {out_path}  (shape: {out.shape})")
print(out.pivot(index="family", columns="league", values="mean_signed_shap").round(4))
