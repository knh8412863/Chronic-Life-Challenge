from __future__ import annotations

import numpy as np
import pandas as pd

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 누수 피처 제거
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEAKAGE_EXTRA = {
    "diabetes": ["glucose_postprandial"],
    "hypertension": [],
    "kidney": [],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. smoking_status 인코딩 통합
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SMOKING_TEXT_COLS = [
    "smoking_status_never",
    "smoking_status_current",
    "smoking_status_former",
]
SMOKING_NUM_COLS = [
    "smoking_status_0.0",
    "smoking_status_1.0",
    "smoking_status_2.0",
]


def fix_smoking_encoding(df: pd.DataFrame) -> pd.DataFrame:  # noqa: C901
    """smoking_status 더미 5개 → smoking_ordinal(0/1/2) 단일 변수로 통합"""
    df = df.copy()

    has_text = any(c in df.columns for c in SMOKING_TEXT_COLS)
    has_num = any(c in df.columns for c in SMOKING_NUM_COLS)

    if has_text and has_num:
        # 텍스트 기준으로 통합
        smoking = pd.Series(0, index=df.index, dtype="int8")  # default: never
        if "smoking_status_current" in df.columns:
            smoking = smoking.where(df["smoking_status_current"] == 0, 2)
        if "smoking_status_former" in df.columns:
            smoking = smoking.where(df["smoking_status_former"] == 0, 1)
        # 텍스트에 없으면 숫자 쪽에서 보완
        if "smoking_status_2.0" in df.columns:
            mask_num_current = (df.get("smoking_status_2.0", 0) == 1) & (smoking == 0)
            smoking = smoking.where(~mask_num_current, 2)
        if "smoking_status_1.0" in df.columns:
            mask_num_former = (df.get("smoking_status_1.0", 0) == 1) & (smoking == 0)
            smoking = smoking.where(~mask_num_former, 1)

        df["smoking_ordinal"] = smoking
        drop_cols = [c for c in SMOKING_TEXT_COLS + SMOKING_NUM_COLS if c in df.columns]
        df = df.drop(columns=drop_cols)

    elif has_text:
        smoking = pd.Series(0, index=df.index, dtype="int8")
        if "smoking_status_current" in df.columns:
            smoking = smoking.where(df["smoking_status_current"] == 0, 2)
        if "smoking_status_former" in df.columns:
            smoking = smoking.where(df["smoking_status_former"] == 0, 1)
        df["smoking_ordinal"] = smoking
        drop_cols = [c for c in SMOKING_TEXT_COLS if c in df.columns]
        df = df.drop(columns=drop_cols)

    elif has_num:
        smoking = pd.Series(0, index=df.index, dtype="int8")
        if "smoking_status_2.0" in df.columns:
            smoking = smoking.where(df["smoking_status_2.0"] == 0, 2)
        if "smoking_status_1.0" in df.columns:
            mask = (df["smoking_status_1.0"] == 1) & (smoking == 0)
            smoking = smoking.where(~mask, 1)
        df["smoking_ordinal"] = smoking
        drop_cols = [c for c in SMOKING_NUM_COLS if c in df.columns]
        df = df.drop(columns=drop_cols)

    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 파생변수 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _safe_div(a: pd.Series, b: pd.Series, fill: float = 0.0) -> pd.Series:
    """0으로 나누기 방지"""
    return a.div(b.replace(0, np.nan)).fillna(fill)


def add_derived_common(df: pd.DataFrame) -> pd.DataFrame:
    """전 질환 공통 파생변수"""
    df = df.copy()

    # WHtR (Waist-to-Height Ratio) — 내장지방 위험 지표
    # BMI보다 대사증후군 예측력이 높다는 다수 연구
    if "waist_circumference" in df.columns and "height" in df.columns:
        df["whtr"] = _safe_div(df["waist_circumference"], df["height"])

    # BMI 범주 (KSSO 2022 한국 기준)
    if "bmi" in df.columns:
        df["bmi_category"] = (
            pd.cut(
                df["bmi"],
                bins=[0, 18.5, 23, 25, 30, 35, 100],
                labels=[0, 1, 2, 3, 4, 5],  # 저체중/정상/과체중/1단계/2단계/3단계
                right=False,
            )
            .astype("float32")
            .fillna(1)
        )

    # 연령대 (10세 단위) — 40대 이후 만성질환 급증 비선형 패턴
    if "age" in df.columns:
        df["age_group"] = (df["age"] // 10).clip(upper=8).astype("float32")  # 80+ 통합

    # Age × BMI 교호작용 — 연령대별 BMI 위험도 차이
    if "age" in df.columns and "bmi" in df.columns:
        df["age_bmi_interaction"] = df["age"] * df["bmi"]

    # 음주·흡연 복합 위험 점수
    # 현재흡연 + 주3회 이상 음주 = 고위험
    if "smoking_ordinal" in df.columns and "alcohol_frequency" in df.columns:
        smoke_risk = (df["smoking_ordinal"] >= 2).astype("float32")  # current
        alc_risk = (df["alcohol_frequency"] >= 3).astype("float32")  # 주3회+
        df["substance_risk_score"] = smoke_risk + alc_risk  # 0, 1, 2

    # 신체활동 부족 여부 — WHO 기준 주 150분 중강도
    if "physical_activity_min" in df.columns:
        df["activity_deficit"] = (df["physical_activity_min"] < 150).astype("int8")

    return df


def add_derived_diabetes(df: pd.DataFrame) -> pd.DataFrame:
    """당뇨 모델 전용 파생변수"""
    df = df.copy()

    # TG/HDL 비율 — 인슐린 저항성 대리 지표
    # 한국인 기준 TG/HDL ≥ 3.5이면 인슐린 저항 의심
    if "triglycerides" in df.columns and "hdl_cholesterol" in df.columns:
        df["tg_hdl_ratio"] = _safe_div(df["triglycerides"], df["hdl_cholesterol"])

    # Non-HDL 콜레스테롤 — LDL보다 심혈관·대사 위험 예측력 높음
    if "total_cholesterol" in df.columns and "hdl_cholesterol" in df.columns:
        df["non_hdl_cholesterol"] = df["total_cholesterol"] - df["hdl_cholesterol"]

    # MAP (Mean Arterial Pressure) — 혈관 부하 단일 지표
    if "sbp" in df.columns and "dbp" in df.columns:
        df["map_pressure"] = (df["sbp"] + 2 * df["dbp"]) / 3

    # Pulse Pressure — 동맥 경직도, 대사증후군 연관
    if "sbp" in df.columns and "dbp" in df.columns:
        df["pulse_pressure"] = df["sbp"] - df["dbp"]

    # 가족력 복합 (당뇨 + 고혈압 모두 있으면 = 2)
    fam_cols = ["family_history_diabetes", "family_history_hypertension"]
    if all(c in df.columns for c in fam_cols):
        df["family_risk_score"] = df[fam_cols].sum(axis=1).astype("float32")

    # 크레아티닌 상승 여부 (신기능 저하 → 당뇨 합병증 신호)
    if "creatinine" in df.columns:
        df["creatinine_elevated"] = (df["creatinine"] > 1.2).astype("int8")

    return df


def add_derived_hypertension(df: pd.DataFrame) -> pd.DataFrame:
    """고혈압 모델 전용 파생변수 (sbp/dbp 없이 예측해야 함)"""
    df = df.copy()

    # TG/HDL 비율 — 대사 위험 프록시
    if "triglycerides" in df.columns and "hdl_cholesterol" in df.columns:
        df["tg_hdl_ratio"] = _safe_div(df["triglycerides"], df["hdl_cholesterol"])

    # Non-HDL 콜레스테롤
    if "total_cholesterol" in df.columns and "hdl_cholesterol" in df.columns:
        df["non_hdl_cholesterol"] = df["total_cholesterol"] - df["hdl_cholesterol"]

    # HbA1c 범주화 — 당뇨 전단계(5.7-6.4)는 고혈압 동반 위험 높음
    if "hba1c" in df.columns:
        df["hba1c_prediabetic"] = ((df["hba1c"] >= 5.7) & (df["hba1c"] < 6.5)).astype("int8")
        df["hba1c_diabetic"] = (df["hba1c"] >= 6.5).astype("int8")

    # 공복혈당 범주화
    if "glucose_fasting" in df.columns:
        df["glucose_prediabetic"] = ((df["glucose_fasting"] >= 100) & (df["glucose_fasting"] < 126)).astype("int8")
        df["glucose_diabetic"] = (df["glucose_fasting"] >= 126).astype("int8")

    # 가족력 복합
    fam_cols = ["family_history_diabetes", "family_history_hypertension"]
    if all(c in df.columns for c in fam_cols):
        df["family_risk_score"] = df[fam_cols].sum(axis=1).astype("float32")

    # 크레아티닌 상승 여부
    if "creatinine" in df.columns:
        df["creatinine_elevated"] = (df["creatinine"] > 1.2).astype("int8")

    return df


def add_derived_kidney(df: pd.DataFrame) -> pd.DataFrame:
    """신장 모델 전용 파생변수"""
    df = df.copy()

    # BUN 범주화 — 정상/경계/상승
    if "bun" in df.columns:
        df["bun_elevated"] = (df["bun"] > 20).astype("int8")
        df["bun_high"] = (df["bun"] > 25).astype("int8")

    # 소변단백 × 혈압 교호작용 — CKD 진행의 강력한 복합 위험
    if "urine_protein_pos" in df.columns and "sbp" in df.columns:
        df["proteinuria_x_sbp"] = df["urine_protein_pos"] * df["sbp"]

    # 소변단백 × 연령 교호작용
    if "urine_protein_pos" in df.columns and "age" in df.columns:
        df["proteinuria_x_age"] = df["urine_protein_pos"] * df["age"]

    # 혈당 범주화 — 당뇨가 CKD 1위 원인
    if "glucose_fasting" in df.columns:
        df["glucose_dm_flag"] = (df["glucose_fasting"] >= 126).astype("int8")

    # 콜레스테롤 이상 플래그 — 이상지질혈증은 CKD 진행 위험인자
    if "total_cholesterol" in df.columns:
        df["high_cholesterol_flag"] = (df["total_cholesterol"] >= 240).astype("int8")

    # 빈혈 플래그 — CKD 동반 빈혈
    if "hemoglobin" in df.columns:
        df["anemia_flag"] = (df["hemoglobin"] < 12.0).astype("int8")

    # 혈소판 이상 플래그
    if "platelets" in df.columns:
        df["low_platelets"] = (df["platelets"] < 150).astype("int8")

    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 피처 정리 — 상관분석 기반 중복 제거
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def remove_high_correlation(
    df: pd.DataFrame,
    threshold: float = 0.85,
    protect: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    protect = set(protect or [])
    numeric = df.select_dtypes(include="number")
    corr = numeric.corr().abs()

    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = set()

    for col in upper.columns:
        high_corr = upper.index[upper[col] > threshold].tolist()
        for paired in high_corr:
            if col in to_drop or paired in to_drop:
                continue
            # protect에 있는 건 제거 안 함
            if col in protect and paired in protect:
                continue
            if col in protect:
                to_drop.add(paired)
            elif paired in protect:
                to_drop.add(col)
            else:
                # 둘 다 protect 아니면 뒤에 나온 쪽(파생변수일 확률 높음) 유지
                to_drop.add(col)

    dropped = sorted(to_drop)
    return df.drop(columns=dropped, errors="ignore"), dropped  # 제거된 컬럼 목록도 반환


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 통합 파이프라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DERIVED_FN = {
    "diabetes": add_derived_diabetes,
    "hypertension": add_derived_hypertension,
    "kidney": add_derived_kidney,
}

# 각 질환별 원본 피처 중 보호할 핵심 피처
PROTECT_FEATURES = {
    "diabetes": ["age", "bmi", "waist_circumference", "creatinine", "triglycerides", "hdl_cholesterol"],
    "hypertension": ["age", "bmi", "hba1c", "glucose_fasting", "creatinine"],
    "kidney": ["age", "bmi", "sbp", "bun", "urine_protein_pos", "hemoglobin", "glucose_fasting"],
}


def engineer_features(
    df: pd.DataFrame,
    disease: str,
    remove_leakage: bool = True,
    remove_correlated: bool = True,
    corr_threshold: float = 0.85,
) -> pd.DataFrame:
    result = df.copy()

    # 추가 누수 제거
    if remove_leakage:
        leak_cols = [c for c in LEAKAGE_EXTRA.get(disease, []) if c in result.columns]
        if leak_cols:
            result = result.drop(columns=leak_cols)
            print(f"  [누수 제거] {disease}: {leak_cols}")

    # smoking 인코딩 통합
    result = fix_smoking_encoding(result)

    # 공통 파생변수
    result = add_derived_common(result)

    # 질환별 파생변수
    if disease in DERIVED_FN:
        result = DERIVED_FN[disease](result)

    # 상관 중복 제거
    if remove_correlated:
        protect = PROTECT_FEATURES.get(disease, [])
        result, dropped = remove_high_correlation(result, corr_threshold, protect)
        if dropped:
            print(f"  [상관 제거] {disease}: {dropped}")

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 진단 유틸리티
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def feature_report(
    df: pd.DataFrame,
    disease: str,
    y: pd.Series | None = None,
) -> pd.DataFrame:
    report = pd.DataFrame(
        {
            "dtype": df.dtypes,
            "null_pct": (df.isnull().sum() / len(df) * 100).round(2),
            "nunique": df.nunique(),
            "mean": df.select_dtypes("number").mean(),
            "std": df.select_dtypes("number").std(),
        }
    )

    if y is not None:
        corr_with_target = df.select_dtypes("number").corrwith(y).abs()
        report["target_corr"] = corr_with_target

    report = report.sort_values("target_corr", ascending=False, na_position="last")
    return report


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데모 / 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    from pathlib import Path

    DATA_DIR = Path("/Users/rogan/파이널프로젝트_4조/dataset/unified")

    for disease in ["diabetes", "hypertension", "kidney"]:
        print(f"\n{'=' * 60}")
        print(f"  {disease.upper()} 피처 엔지니어링")
        print(f"{'=' * 60}")

        x_train = pd.read_parquet(DATA_DIR / f"v7_{disease}_train_X.parquet")
        y_train = pd.read_parquet(DATA_DIR / f"v7_{disease}_train_y.parquet")
        y_binary = (y_train["risk_level"] >= 1).astype(int)

        print(f"  원본: {x_train.shape[1]}개 피처, {x_train.shape[0]}행")

        # 범주형 원핫
        cat_cols = x_train.select_dtypes(exclude="number").columns.tolist()
        if cat_cols:
            x_train = pd.get_dummies(x_train, columns=cat_cols, dummy_na=False)

        # 피처 엔지니어링 적용
        x_engineered = engineer_features(x_train, disease)
        print(f"  결과: {x_engineered.shape[1]}개 피처")

        # 피처 리포트
        report = feature_report(x_engineered, disease, y_binary)
        print("\n  [Target 상관 TOP 10]")
        print(report[["target_corr", "mean", "null_pct"]].head(10).to_string())
