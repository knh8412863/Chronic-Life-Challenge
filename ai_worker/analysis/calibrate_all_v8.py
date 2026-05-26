"""
3개 질환 모델 Calibration — Isotonic Regression
OOF 확률 기반 calibration fitting → calibrated threshold 계산

  1. 5-Fold OOF 확률 생성 (train set, out-of-fold이므로 leakage 없음)
  2. IsotonicRegression으로 calibration fitting
  3. Test set 확률 calibration
  4. Calibration curve (reliability diagram) 전후 비교
  5. Calibrated 확률 기준 threshold 재계산
  6. thresholds.json 업데이트 (calibrated 섹션 추가)
  7. calibrators.pkl 저장 (서비스 연동용)

실행:
  uv run -p 3.11 --no-project \\
    --with "xgboost" --with lightgbm \\
    --with pandas --with pyarrow --with scikit-learn \\
    --with matplotlib --with joblib \\
    python calibrate_all_v8.py
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

DATA_DIR = Path("ai_worker/models/V8/dataset")
THRESH_DIR = Path("ai_worker/models")
SEED = 42
N_FOLDS = 5
SCREEN_RECALL_MIN = 0.85


# ─────────────────────────────────────────────────────────────
# 모델 정의
# ─────────────────────────────────────────────────────────────


def xgb_model(spw: float) -> XGBClassifier:
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
    """고혈압 최적 앙상블 (LGBM + HistGB)"""
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


# ─────────────────────────────────────────────────────────────
# OOF 확률 생성
# ─────────────────────────────────────────────────────────────


def get_oof_test(model, X_tr, y_tr, X_te) -> tuple[np.ndarray, np.ndarray]:
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof = np.zeros(len(X_tr))
    test_probas = []
    for tr_idx, val_idx in cv.split(X_tr, y_tr):
        model.fit(X_tr.iloc[tr_idx], y_tr.iloc[tr_idx])
        oof[val_idx] = model.predict_proba(X_tr.iloc[val_idx])[:, 1]
        test_probas.append(model.predict_proba(X_te)[:, 1])
    return oof, np.mean(test_probas, axis=0)


# ─────────────────────────────────────────────────────────────
# Threshold 계산
# ─────────────────────────────────────────────────────────────


def find_thresholds(y_true, proba) -> dict:
    precisions, recalls, thresholds = precision_recall_curve(y_true, proba)
    results = {
        "screening": {"threshold": None, "precision": None, "recall": None, "f1": None},
        "diagnostic": {"threshold": None, "precision": None, "recall": None, "f1": None},
    }
    best_screen_prec, best_f1 = -1.0, -1.0

    for t, p, r in zip(thresholds, precisions[:-1], recalls[:-1], strict=False):
        y_pred = (proba >= t).astype(int)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        if r >= SCREEN_RECALL_MIN and p > best_screen_prec:
            best_screen_prec = p
            results["screening"] = {
                "threshold": round(float(t), 3),
                "precision": round(float(p), 4),
                "recall": round(float(r), 4),
                "f1": round(float(f1), 4),
            }
        if f1 > best_f1:
            best_f1 = f1
            results["diagnostic"] = {
                "threshold": round(float(t), 3),
                "precision": round(float(p), 4),
                "recall": round(float(r), 4),
                "f1": round(float(f1), 4),
            }
    return results


# ─────────────────────────────────────────────────────────────
# Reliability diagram (calibration curve)
# ─────────────────────────────────────────────────────────────


def plot_calibration(disease: str, y_te, raw_proba, cal_proba, kr_name: str):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, proba, title, color in zip(
        axes,
        [raw_proba, cal_proba],
        ["Calibration 전 (raw)", "Calibration 후 (isotonic)"],
        ["steelblue", "crimson"],
        strict=True,
    ):
        try:
            frac_pos, mean_pred = calibration_curve(y_te, proba, n_bins=10)
        except ValueError:
            frac_pos, mean_pred = np.array([]), np.array([])

        ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="완벽한 calibration")
        ax.plot(mean_pred, frac_pos, "o-", color=color, linewidth=2, markersize=7, label=title)
        ax.set_xlabel("예측 확률 (평균)")
        ax.set_ylabel("실제 양성 비율")
        ax.set_title(f"{kr_name} — {title}", fontsize=11)
        ax.legend(fontsize=9)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.grid(alpha=0.3)

    plt.tight_layout()
    out = THRESH_DIR / f"{disease}_calibration_curve.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    calibration curve 저장: {out.name}")


# ─────────────────────────────────────────────────────────────
# ECE (Expected Calibration Error) — 수치 평가
# ─────────────────────────────────────────────────────────────


def ece(y_true, proba, n_bins=10) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
    ece_val = 0.0
    n = len(y_true)
    for lo, hi in zip(bins[:-1], bins[1:], strict=True):
        mask = (proba >= lo) & (proba < hi)
        if mask.sum() == 0:
            continue
        acc = y_true[mask].mean()
        conf = proba[mask].mean()
        ece_val += mask.sum() / n * abs(acc - conf)
    return ece_val


# ─────────────────────────────────────────────────────────────
# 단일 모델 질환 처리 (당뇨, 신장)
# ─────────────────────────────────────────────────────────────

DISEASE_KR = {"diabetes": "당뇨", "hypertension": "고혈압", "kidney": "신장(CKD)"}


def process_single(disease: str, model_label: str, data: dict) -> tuple[np.ndarray, IsotonicRegression, dict]:
    X_tr, y_tr, X_te, y_te = data["X_tr"], data["y_tr"], data["X_te"], data["y_te"]
    pos = int(y_tr.sum())
    neg = int((y_tr == 0).sum())
    spw = neg / pos

    model = xgb_model(spw)
    print(f"  OOF 확률 생성 중 ({N_FOLDS}-Fold)...")
    oof, test_proba = get_oof_test(model, X_tr, y_tr, X_te)

    # raw AUC
    raw_auc = roc_auc_score(y_te, test_proba)

    # Calibration fitting
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(oof, y_tr.values)
    cal_proba = calibrator.transform(test_proba)

    cal_auc = roc_auc_score(y_te, cal_proba)
    raw_ece = ece(y_te.values, test_proba)
    cal_ece = ece(y_te.values, cal_proba)

    print(f"  AUC: raw={raw_auc:.4f}  calibrated={cal_auc:.4f}  (AUC 불변)")
    print(
        f"  ECE: raw={raw_ece:.4f} → calibrated={cal_ece:.4f}  "
        f"({'개선' if cal_ece < raw_ece else '악화'} {abs(cal_ece - raw_ece):.4f})"
    )

    kr = DISEASE_KR[disease]
    plot_calibration(disease, y_te, test_proba, cal_proba, kr)

    thresh = find_thresholds(y_te, cal_proba)
    return (
        cal_proba,
        calibrator,
        {
            "model": model_label,
            "test_auc": round(raw_auc, 4),
            "pos_rate": round(pos / (pos + neg), 4),
            "screening": thresh["screening"],
            "diagnostic": thresh["diagnostic"],
        },
    )


# ─────────────────────────────────────────────────────────────
# 고혈압 앙상블 처리
# ─────────────────────────────────────────────────────────────


def process_hypertension(data: dict) -> tuple[np.ndarray, IsotonicRegression, dict]:
    X_tr, y_tr, X_te, y_te = data["X_tr"], data["y_tr"], data["X_te"], data["y_te"]
    pos = int(y_tr.sum())
    neg = int((y_tr == 0).sum())
    spw = neg / pos

    models = hp_models(spw)
    oof_dict, test_dict = {}, {}

    for name, model in models.items():
        print(f"    [{name}] OOF 생성 중...")
        oof, test_proba = get_oof_test(model, X_tr, y_tr, X_te)
        oof_dict[name] = oof
        test_dict[name] = test_proba

    # LGBM + HistGB 동일 가중 블렌딩
    blend_oof = np.mean(list(oof_dict.values()), axis=0)
    blend_test = np.mean(list(test_dict.values()), axis=0)

    raw_auc = roc_auc_score(y_te, blend_test)

    # Calibration
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(blend_oof, y_tr.values)
    cal_proba = calibrator.transform(blend_test)

    cal_auc = roc_auc_score(y_te, cal_proba)
    raw_ece = ece(y_te.values, blend_test)
    cal_ece = ece(y_te.values, cal_proba)

    print(f"  AUC: raw={raw_auc:.4f}  calibrated={cal_auc:.4f}")
    print(
        f"  ECE: raw={raw_ece:.4f} → calibrated={cal_ece:.4f}  "
        f"({'개선' if cal_ece < raw_ece else '악화'} {abs(cal_ece - raw_ece):.4f})"
    )

    plot_calibration("hypertension", y_te, blend_test, cal_proba, "고혈압")

    thresh = find_thresholds(y_te, cal_proba)
    return (
        cal_proba,
        calibrator,
        {
            "model": "LGBM+HistGB",
            "test_auc": round(raw_auc, 4),
            "pos_rate": round(pos / (pos + neg), 4),
            "screening": thresh["screening"],
            "diagnostic": thresh["diagnostic"],
        },
    )


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────


def main():
    print("=" * 68)
    print("  3개 질환 Calibration (Isotonic Regression)")
    print("=" * 68)

    # 데이터 로드
    diseases_data = {}
    for disease in ["diabetes", "hypertension", "kidney"]:
        diseases_data[disease] = {
            "X_tr": pd.read_parquet(DATA_DIR / f"v8_{disease}_train_X.parquet"),
            "y_tr": pd.read_parquet(DATA_DIR / f"v8_{disease}_train_y.parquet")["risk_label"].astype(int),
            "X_te": pd.read_parquet(DATA_DIR / f"v8_{disease}_test_X.parquet"),
            "y_te": pd.read_parquet(DATA_DIR / f"v8_{disease}_test_y.parquet")["risk_label"].astype(int),
        }

    calibrators = {}
    new_thresholds = {}

    # 당뇨
    print("\n[1/3] 당뇨 (XGBoost)")
    _, cal, result = process_single("diabetes", "XGBoost", diseases_data["diabetes"])
    calibrators["diabetes"] = cal
    new_thresholds["diabetes"] = result

    # 고혈압
    print("\n[2/3] 고혈압 (LGBM+HistGB 앙상블)")
    _, cal, result = process_hypertension(diseases_data["hypertension"])
    calibrators["hypertension"] = cal
    new_thresholds["hypertension"] = result

    # 신장
    print("\n[3/3] 신장 CKD (XGBoost)")
    _, cal, result = process_single("kidney", "XGBoost", diseases_data["kidney"])
    calibrators["kidney"] = cal
    new_thresholds["kidney"] = result

    # ── 결과 요약 ──────────────────────────────────────────────
    print("\n" + "=" * 68)
    print(f"  {'질환':<12s}  {'모델':<16s}  {'AUC':>6s}  {'스크리닝 T':>10s}  {'진단보조 T':>10s}")
    print("=" * 68)
    kr_map = {"diabetes": "당뇨", "hypertension": "고혈압", "kidney": "신장"}
    for disease, d in new_thresholds.items():
        sc_t = d["screening"]["threshold"] if d["screening"]["threshold"] else "N/A"
        di_t = d["diagnostic"]["threshold"] if d["diagnostic"]["threshold"] else "N/A"
        print(f"  {kr_map[disease]:<12s}  {d['model']:<16s}  {d['test_auc']:.4f}  {str(sc_t):>10s}  {str(di_t):>10s}")

    print()
    print("  스크리닝: Recall ≥ 85% 중 Precision 최대 (calibrated 확률 기준)")
    print("  진단보조: F1 최대 (calibrated 확률 기준)")
    print()

    # ── thresholds.json 업데이트 ───────────────────────────────
    json_path = THRESH_DIR / "thresholds.json"
    json_path.write_text(json.dumps(new_thresholds, ensure_ascii=False, indent=2))
    print("  thresholds.json 업데이트 완료")

    # ── calibrator pickle 저장 (서비스 연동용) ─────────────────
    pkl_path = THRESH_DIR / "calibrators.pkl"
    joblib.dump(calibrators, pkl_path)
    print(f"  calibrators.pkl 저장 완료  ({pkl_path})")
    print()
    print("  ※ 서비스에서 사용 방법:")
    print("    calibrators = joblib.load('calibrators.pkl')")
    print("    raw_proba = model.predict_proba(X)[:, 1]")
    print("    cal_proba = calibrators['diabetes'].transform(raw_proba)")
    print("    score = cal_proba * 100  # 0~100 위험도 점수")


if __name__ == "__main__":
    main()
