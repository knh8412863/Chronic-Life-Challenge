"""
V8 위험도 점수 데모
저장된 모델 + calibrator를 로드해 실제 점수 예측.

실행:
  uv run -p 3.11 --no-project \\
    --with "xgboost" --with lightgbm \\
    --with pandas --with pyarrow --with scikit-learn --with joblib \\
    python score_demo_v8.py
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

THRESH_DIR = Path("ai_worker/models")
DATA_DIR = Path("ai_worker/models/V8/dataset")

# ──────────────────────────────────────────────────────────────
# 모델 + calibrator + threshold 로드
# ──────────────────────────────────────────────────────────────


def load_assets():
    assets = {}

    for disease in ["diabetes", "hypertension", "kidney"]:
        pkg = joblib.load(THRESH_DIR / f"{disease}_model.pkl")
        assets[disease] = {
            "pkg": pkg,
            "calibrator": None,
        }

    calibrators = joblib.load(THRESH_DIR / "calibrators.pkl")
    for disease, cal in calibrators.items():
        assets[disease]["calibrator"] = cal

    thresholds = json.loads((THRESH_DIR / "thresholds.json").read_text())

    return assets, thresholds


# ──────────────────────────────────────────────────────────────
# 단일 샘플 예측
# ──────────────────────────────────────────────────────────────


def predict_score(disease: str, sample: pd.Series, assets: dict) -> dict:
    pkg = assets[disease]["pkg"]
    calibrator = assets[disease]["calibrator"]

    if disease == "hypertension":
        # LGBM + HistGB 블렌딩
        feat = pkg["feature_names"]
        X = sample[feat].values.reshape(1, -1)
        raw_probas = [m.predict_proba(X)[0, 1] for m in pkg["models"].values()]
        raw_proba = float(np.mean(raw_probas))
    else:
        feat = pkg["feature_names"]
        X = sample[feat].values.reshape(1, -1)
        raw_proba = float(pkg["model"].predict_proba(X)[0, 1])

    cal_proba = float(calibrator.transform(np.array([raw_proba]))[0])
    score = round(cal_proba * 100, 1)

    return {
        "raw_proba": round(raw_proba, 4),
        "cal_proba": round(cal_proba, 4),
        "score": score,
    }


# ──────────────────────────────────────────────────────────────
# 위험 등급 분류
# ──────────────────────────────────────────────────────────────


def risk_level(score: float, diagnostic_threshold: float) -> tuple[str, str]:
    t = diagnostic_threshold * 100
    if score < t * 0.5:
        return "낮음", "✅"
    elif score < t:
        return "주의", "⚠️"
    elif score < t * 1.5:
        return "높음", "🔴"
    else:
        return "매우 높음", "🚨"


# ──────────────────────────────────────────────────────────────
# 결과 출력
# ──────────────────────────────────────────────────────────────

DISEASE_KR = {
    "diabetes": "당뇨",
    "hypertension": "고혈압",
    "kidney": "신장(CKD)",
}

DISEASE_EMOJI = {
    "diabetes": "🩸",
    "hypertension": "💊",
    "kidney": "🫘",
}


def print_result(name: str, label: str, samples: list[pd.Series], assets: dict, thresholds: dict):
    print(f"\n{'─' * 60}")
    print(f"  사례: {name}  |  {label}")
    print(f"{'─' * 60}")

    for disease in ["diabetes", "hypertension", "kidney"]:
        sample = samples[disease]
        result = predict_score(disease, sample, assets)
        diag_t = thresholds[disease]["diagnostic"]["threshold"]
        level, icon = risk_level(result["score"], diag_t)

        diag_label = f"진단보조 기준 {diag_t * 100:.0f}점"
        print(
            f"  {DISEASE_EMOJI[disease]} {DISEASE_KR[disease]:<10s}  "
            f"위험도 {result['score']:>5.1f}점  {icon} {level:<8s}"
            f"  (raw→cal: {result['raw_proba']:.3f}→{result['cal_proba']:.3f}  |  {diag_label})"
        )


# ──────────────────────────────────────────────────────────────
# 메인 — 실제 테스트 데이터에서 3개 사례 선택
# ──────────────────────────────────────────────────────────────


def main():
    print("V8 위험도 점수 예측 데모")
    print("=" * 60)
    print("모델 및 calibrator 로딩 중...")

    assets, thresholds = load_assets()
    print("  로딩 완료.\n")

    # 각 질환별 테스트 데이터 로드
    test_data = {}
    test_labels = {}
    for disease in ["diabetes", "hypertension", "kidney"]:
        test_data[disease] = pd.read_parquet(DATA_DIR / f"v8_{disease}_test_X.parquet")
        test_labels[disease] = pd.read_parquet(DATA_DIR / f"v8_{disease}_test_y.parquet")["risk_label"].astype(int)

    # ── 사례 선택 ──────────────────────────────────────────────
    # 공통 인덱스에서 실제 레이블 기반으로 3명 선택
    common_idx = (
        set(test_labels["diabetes"].index) & set(test_labels["hypertension"].index) & set(test_labels["kidney"].index)
    )
    common_idx = sorted(common_idx)

    dm_pos = test_labels["diabetes"].loc[common_idx]
    hp_pos = test_labels["hypertension"].loc[common_idx]
    ckd_pos = test_labels["kidney"].loc[common_idx]

    # 사례 A: 세 질환 모두 음성 (저위험)
    neg_idx = [i for i in common_idx if dm_pos[i] == 0 and hp_pos[i] == 0 and ckd_pos[i] == 0]
    case_a_idx = neg_idx[42]

    # 사례 B: 당뇨만 양성 (부분 위험)
    dm_only = [i for i in common_idx if dm_pos[i] == 1 and hp_pos[i] == 0 and ckd_pos[i] == 0]
    case_b_idx = dm_only[0] if dm_only else neg_idx[0]

    # 사례 C: 두 개 이상 양성 (고위험)
    multi_pos = [i for i in common_idx if dm_pos[i] + hp_pos[i] + ckd_pos[i] >= 2]
    case_c_idx = multi_pos[0] if multi_pos else common_idx[-1]

    cases = [
        (case_a_idx, "사례 A", "세 질환 모두 음성 (저위험 예상)"),
        (case_b_idx, "사례 B", "당뇨 양성, 나머지 음성 (부분 위험 예상)"),
        (case_c_idx, "사례 C", "복수 질환 양성 (고위험 예상)"),
    ]

    for idx, case_name, case_label in cases:
        samples = {d: test_data[d].loc[idx] for d in ["diabetes", "hypertension", "kidney"]}

        # 해당 사람의 주요 수치 출력
        s = test_data["diabetes"].loc[idx]
        actual = {
            "당뇨": test_labels["diabetes"].loc[idx],
            "고혈압": test_labels["hypertension"].loc[idx],
            "신장": test_labels["kidney"].loc[idx],
        }
        print(
            f"\n  [{case_name}]  나이={s.get('age', '-'):.0f}세  "
            f"BMI={s.get('bmi', '-'):.1f}  "
            f"공복혈당={s.get('glucose_fasting', s.get('triglycerides', '-'))}"
            f"  → 실제 라벨 {actual}"
        )

        print_result(case_name, case_label, samples, assets, thresholds)

    # ── threshold 기준 안내 ─────────────────────────────────────
    print(f"\n\n{'=' * 60}")
    print("  위험도 점수 해석 기준 (calibrated 확률 × 100)")
    print(f"{'=' * 60}")
    for disease in ["diabetes", "hypertension", "kidney"]:
        sc = thresholds[disease]["screening"]
        di = thresholds[disease]["diagnostic"]
        print(f"\n  {DISEASE_EMOJI[disease]} {DISEASE_KR[disease]}")
        print(
            f"    · 스크리닝  {sc['threshold'] * 100:>5.1f}점 이상 → 전문의 상담 권유"
            f"  (Recall {sc['recall'] * 100:.0f}%)"
        )
        print(
            f"    · 진단보조  {di['threshold'] * 100:>5.1f}점 이상 → 고위험 판정"
            f"  (Precision {di['precision'] * 100:.0f}%, Recall {di['recall'] * 100:.0f}%)"
        )

    print()
    print("  ※ 점수 = calibrated 확률 × 100  (0~100)")
    print("  ※ calibration 덕분에 '26점 = 이 모집단에서 약 26% 확률로 해당 질환'")
    print("  ※ 의료 진단 대체 불가, 참고용 위험도 안내")


if __name__ == "__main__":
    main()
