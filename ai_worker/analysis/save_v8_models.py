"""
V8 모델 훈련 및 저장
각 질환별 최적 모델을 pkl로 저장.
calibrators.pkl과 함께 사용하여 위험도 점수 계산.

실행:
  uv run -p 3.11 --no-project \\
    --with "xgboost" --with lightgbm \\
    --with pandas --with pyarrow --with scikit-learn --with joblib \\
    python save_v8_models.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import joblib
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

DATA_DIR = Path("ai_worker/models/V8/dataset")
THRESH_DIR = Path("ai_worker/models")
SEED = 42
N_FOLDS = 5


def load(disease: str):
    X_tr = pd.read_parquet(DATA_DIR / f"v8_{disease}_train_X.parquet")
    y_tr = pd.read_parquet(DATA_DIR / f"v8_{disease}_train_y.parquet")["risk_label"].astype(int)
    X_te = pd.read_parquet(DATA_DIR / f"v8_{disease}_test_X.parquet")
    y_te = pd.read_parquet(DATA_DIR / f"v8_{disease}_test_y.parquet")["risk_label"].astype(int)
    return X_tr, y_tr, X_te, y_te


def xgb(spw: float) -> XGBClassifier:
    return XGBClassifier(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=5,
        reg_lambda=2.0,
        scale_pos_weight=spw,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=SEED,
        n_jobs=-1,
        verbosity=0,
    )


def hp_models(spw: float) -> dict:
    return {
        "LightGBM": LGBMClassifier(
            n_estimators=795,
            max_depth=3,
            learning_rate=0.0242,
            subsample=0.505,
            colsample_bytree=0.594,
            min_child_samples=32,
            reg_lambda=19.93,
            reg_alpha=3.506,
            scale_pos_weight=spw,
            random_state=SEED,
            n_jobs=-1,
            verbose=-1,
        ),
        "HistGB": HistGradientBoostingClassifier(
            max_iter=256,
            max_depth=6,
            learning_rate=0.0570,
            min_samples_leaf=45,
            l2_regularization=8.200,
            max_features=0.474,
            random_state=SEED,
        ),
    }


def main():
    print("V8 모델 훈련 및 저장")
    print("=" * 50)

    # ── 당뇨 ───────────────────────────────────────────
    print("[1/3] 당뇨 XGBoost 훈련...")
    X_tr, y_tr, X_te, y_te = load("diabetes")
    spw = (y_tr == 0).sum() / y_tr.sum()
    model = xgb(spw)
    model.fit(X_tr, y_tr)
    joblib.dump(
        {
            "model": model,
            "feature_names": list(X_tr.columns),
        },
        THRESH_DIR / "diabetes_model.pkl",
    )
    print(f"  저장 완료: diabetes_model.pkl  (피처 {len(X_tr.columns)}개)")

    # ── 고혈압 ─────────────────────────────────────────
    print("[2/3] 고혈압 LGBM+HistGB 훈련...")
    X_tr, y_tr, X_te, y_te = load("hypertension")
    spw = (y_tr == 0).sum() / y_tr.sum()
    models = hp_models(spw)
    trained = {}
    for name, m in models.items():
        print(f"    [{name}] 훈련 중...")
        m.fit(X_tr, y_tr)
        trained[name] = m
    joblib.dump(
        {
            "models": trained,
            "feature_names": list(X_tr.columns),
        },
        THRESH_DIR / "hypertension_model.pkl",
    )
    print("  저장 완료: hypertension_model.pkl  (LGBM+HistGB 앙상블)")

    # ── 신장 ───────────────────────────────────────────
    print("[3/3] 신장 XGBoost 훈련...")
    X_tr, y_tr, X_te, y_te = load("kidney")
    spw = (y_tr == 0).sum() / y_tr.sum()
    model = xgb(spw)
    model.fit(X_tr, y_tr)
    joblib.dump(
        {
            "model": model,
            "feature_names": list(X_tr.columns),
        },
        THRESH_DIR / "kidney_model.pkl",
    )
    print(f"  저장 완료: kidney_model.pkl  (피처 {len(X_tr.columns)}개)")

    print()
    print("모든 모델 저장 완료.")
    print(f"저장 위치: {THRESH_DIR.resolve()}")


if __name__ == "__main__":
    main()
