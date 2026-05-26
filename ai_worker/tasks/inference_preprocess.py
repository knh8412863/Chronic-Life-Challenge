"""
추론 전처리

지원 질환: diabetes, hypertension, kidney
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. KNHANES 원본 → 표준명 매핑  (SAS 파일 직접 입력 시 사용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RENAME_MAP: dict[str, str] = {
    "age": "age",
    "sex": "sex",
    "edu": "education",
    "HE_ht": "height",
    "HE_wt": "weight",
    "HE_BMI": "bmi",
    "HE_wc": "waist_circumference",
    "HE_sbp": "sbp",
    "HE_dbp": "dbp",
    "HE_glu": "glucose_fasting",
    "HE_HbA1c": "hba1c",
    "HE_chol": "total_cholesterol",
    "HE_HDL_st2": "hdl_cholesterol",
    "HE_LDL_drct": "ldl_cholesterol",
    "HE_TG": "triglycerides",
    "HE_crea": "creatinine",
    "HE_BUN": "bun",
    "HE_HB": "hemoglobin",
    "HE_WBC": "wbc",
    "HE_RBC": "rbc",
    "HE_Uacid": "uric_acid",
    "HE_hsCRP": "hs_crp",
    "HE_ast": "ast",
    "HE_alt": "alt",
    "HE_HCT": "hematocrit",
    "HE_Upro": "urine_protein",
    "HE_Ualb": "urine_albumin",
    "HE_Ucrea": "urine_creatinine",
    "HE_Ubld": "urine_blood",
    "HE_Usg": "urine_sg",
    "HE_Uglu": "urine_glucose",
    "DI1_dg": "dx_diabetes",
    "DI2_dg": "dx_hypertension",
    "DI3_dg": "dx_dyslipidemia",
    "DI1_pt": "tx_diabetes",
    "DI2_pt": "tx_hypertension",
    "HE_DMfh1": "fh_diabetes_father",
    "HE_DMfh2": "fh_diabetes_mother",
    "HE_DMfh3": "fh_diabetes_sibling",
    "HE_HPfh1": "fh_hypertension_father",
    "HE_HPfh2": "fh_hypertension_mother",
    "HE_HPfh3": "fh_hypertension_sibling",
    "DI1_pr": "fh_diabetes_parent",
    "DI2_pr": "fh_hypertension_parent",
    "BS3_1": "smoking_status",
    "BD1_11": "alcohol_frequency",
    "BD2_1": "alcohol_amount",
    "BE3_31": "walking_days",
    "BE5_1": "sedentary_hours",
    "BP1": "self_rated_health",
    "N_NA": "sodium_intake",
    "N_K": "potassium_intake",
    "N_PROT": "protein_intake",
    "N_FAT": "fat_intake",
    "N_CHO": "carb_intake",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 누수 피처 / 메타 컬럼 제거 목록
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEAKAGE_FEATURES: dict[str, list[str]] = {
    "diabetes": ["glucose_fasting", "hba1c", "urine_glucose"],
    "hypertension": ["sbp", "dbp", "map_pressure", "pulse_pressure"],
    "kidney": ["egfr", "creatinine", "uacr", "microalbuminuria", "urine_albumin", "urine_creatinine"],
}

CROSS_DIAGNOSIS_EXCLUDE: dict[str, list[str]] = {
    "diabetes": ["dx_diabetes", "tx_diabetes"],
    "hypertension": ["dx_hypertension", "tx_hypertension"],
    "kidney": [],
}

_META_COLS = {"survey_year", "sex"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. eGFR 계산 — CKD-EPI 2021 (race-free)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def calc_egfr(creatinine: pd.Series, age: pd.Series, sex: pd.Series) -> pd.Series:
    """sex: 1=남, 2=여 (KNHANES 코딩)  /  creatinine: mg/dL"""
    is_female = sex == 2
    kappa = np.where(is_female, 0.7, 0.9)
    alpha = np.where(is_female, -0.241, -0.302)
    factor = np.where(is_female, 1.012, 1.0)
    r = creatinine / kappa
    egfr = 142 * (np.minimum(r, 1.0) ** alpha) * (np.maximum(r, 1.0) ** -1.2) * (0.9938**age) * factor
    return pd.Series(egfr, index=creatinine.index).round(2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 파생변수 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _safe_div(a: pd.Series, b: pd.Series, fill: float = 0.0) -> pd.Series:
    return a.div(b.replace(0, np.nan)).fillna(fill)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:  # noqa: C901
    r = df.copy()

    # eGFR — kidney 라벨 생성용, kidney 모델에서는 누수로 제거됨
    if all(c in r.columns for c in ["creatinine", "age", "sex"]):
        r["egfr"] = calc_egfr(r["creatinine"], r["age"], r["sex"])

    # UACR
    if all(c in r.columns for c in ["urine_albumin", "urine_creatinine"]):
        r["uacr"] = _safe_div(r["urine_albumin"], r["urine_creatinine"] * 0.01)
        r["microalbuminuria"] = (r["uacr"] >= 30).astype("int8")

    # WHtR
    if all(c in r.columns for c in ["waist_circumference", "height"]):
        r["whtr"] = _safe_div(r["waist_circumference"], r["height"])

    # BMI 범주 (KSSO 2022)
    if "bmi" in r.columns:
        r["bmi_category"] = (
            pd.cut(
                r["bmi"],
                bins=[0, 18.5, 23, 25, 30, 35, 100],
                labels=[0, 1, 2, 3, 4, 5],
                right=False,
            )
            .astype("float32")
            .fillna(1)
        )

    # MAP / Pulse Pressure
    if all(c in r.columns for c in ["sbp", "dbp"]):
        r["map_pressure"] = (r["sbp"] + 2 * r["dbp"]) / 3
        r["pulse_pressure"] = r["sbp"] - r["dbp"]

    # TG/HDL 비율
    if all(c in r.columns for c in ["triglycerides", "hdl_cholesterol"]):
        r["tg_hdl_ratio"] = _safe_div(r["triglycerides"], r["hdl_cholesterol"])

    # Non-HDL 콜레스테롤
    if all(c in r.columns for c in ["total_cholesterol", "hdl_cholesterol"]):
        r["non_hdl_cholesterol"] = r["total_cholesterol"] - r["hdl_cholesterol"]

    # AST/ALT 비율 (De Ritis)
    if all(c in r.columns for c in ["ast", "alt"]):
        r["ast_alt_ratio"] = _safe_div(r["ast"], r["alt"])

    # Na/K 비율
    if all(c in r.columns for c in ["sodium_intake", "potassium_intake"]):
        r["na_k_ratio"] = _safe_div(r["sodium_intake"], r["potassium_intake"])

    # 연령대 / Age×BMI
    if "age" in r.columns:
        r["age_group"] = (r["age"] // 10).clip(upper=8).astype("float32")
        if "bmi" in r.columns:
            r["age_bmi"] = r["age"] * r["bmi"]

    # 흡연 ordinal: 원본 코드 1(매일)/2(가끔)→현재(2), 3(과거)→1, 나머지→0
    if "smoking_status" in r.columns:
        smoke_map = {1: 2, 2: 2, 3: 1}
        r["smoking_ordinal"] = r["smoking_status"].map(smoke_map).fillna(0).astype("int8")

    # 가족력 복합 점수
    fh_dm = ["fh_diabetes_father", "fh_diabetes_mother", "fh_diabetes_sibling"]
    fh_hp = ["fh_hypertension_father", "fh_hypertension_mother", "fh_hypertension_sibling"]
    if all(c in r.columns for c in fh_dm):
        r["fh_diabetes_score"] = r[fh_dm].sum(axis=1).clip(upper=3)
    if all(c in r.columns for c in fh_hp):
        r["fh_hypertension_score"] = r[fh_hp].sum(axis=1).clip(upper=3)

    # 음주·흡연 복합 위험 (alcohol_frequency: 4=주2-3회+)
    if all(c in r.columns for c in ["smoking_ordinal", "alcohol_frequency"]):
        smoke_risk = (r["smoking_ordinal"] >= 2).astype("float32")
        alc_risk = (r["alcohol_frequency"] >= 4).astype("float32")
        r["substance_risk"] = smoke_risk + alc_risk

    # 빈혈 플래그
    if "hemoglobin" in r.columns:
        r["anemia_flag"] = (r["hemoglobin"] < 12.0).astype("int8")

    # 성별 이진화
    if "sex" in r.columns:
        r["is_female"] = (r["sex"] == 2).astype("int8")

    return r


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 추론 전처리 통합 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def preprocess_for_inference(
    df: pd.DataFrame,
    disease: str,
    feature_names: list[str],
    medians: dict[str, float],
    rename_knhanes: bool = False,
) -> pd.DataFrame:
    """
    Args:
        df: 입력 DataFrame (표준명 또는 KNHANES 원본명)
        disease: "diabetes" | "hypertension" | "kidney"
        feature_names: 모델 pkl의 feature_names 리스트
        rename_knhanes: True면 KNHANES 원본 컬럼명을 표준명으로 변환 후 처리

    Returns:
        모델 입력 준비 완료 DataFrame (feature_names 순서 보장, train 중앙값 대체)
    """
    result = df.copy()

    if rename_knhanes:
        available = {k: v for k, v in RENAME_MAP.items() if k in result.columns}
        result = result.rename(columns=available)

    result = add_derived_features(result)

    # 누수 + 교차진단 + 메타 컬럼 제거
    exclude = (
        set(LEAKAGE_FEATURES.get(disease, []))
        | set(CROSS_DIAGNOSIS_EXCLUDE.get(disease, []))
        | _META_COLS
        | {"smoking_status"}
    )
    result = result.drop(columns=[c for c in exclude if c in result.columns])

    # 수치형만 남기기
    result = result.select_dtypes(include="number")

    result = result.reindex(columns=feature_names)
    fill_values = {feature: medians.get(feature, 0.0) for feature in feature_names}
    return result.fillna(fill_values).fillna(0.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 모델 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def load_model(models_dir: str | Path, disease: str) -> dict:
    """pkl 로드. 반환 dict: {"model"|"models", "feature_names"}"""
    path = Path(models_dir) / f"{disease}_model.pkl"
    return joblib.load(path)


def load_medians(models_dir: str | Path) -> dict[str, dict[str, float]]:
    path = Path(models_dir) / "medians.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_calibrators(models_dir: str | Path) -> dict:
    path = Path(models_dir) / "calibrators.pkl"
    return joblib.load(path)


def load_thresholds(models_dir: str | Path) -> dict[str, dict]:
    path = Path(models_dir) / "thresholds.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _predict_proba_single(model_dict: dict, features: pd.DataFrame) -> np.ndarray:
    """단일 질환 predict_proba → 양성 클래스 확률 반환 (shape: n,)"""
    if "model" in model_dict:
        # diabetes, kidney: 단일 XGBoost
        return model_dict["model"].predict_proba(features)[:, 1]
    else:
        # hypertension: LGBM + HistGB 평균
        probas = [model.predict_proba(features)[:, 1] for model in model_dict["models"].values()]
        return np.mean(probas, axis=0)


def predict(
    df_raw: pd.DataFrame,
    disease: str,
    models_dir: str | Path,
    mode: str = "screening",
    rename_knhanes: bool = False,
) -> pd.DataFrame:
    """
    Args:
        df_raw: 원시 입력 DataFrame (1건 이상)
        disease: "diabetes" | "hypertension" | "kidney"
        models_dir: pkl 파일이 있는 디렉터리
        mode: "screening" (고민감도) | "diagnostic" (고특이도)
        rename_knhanes: KNHANES 원본 컬럼명 입력 시 True

    Returns:
        DataFrame with raw_probability, probability, threshold, is_at_risk.
        probability는 calibrated 확률이며 위험 판정의 기준이다.
    """
    if mode not in {"screening", "diagnostic"}:
        raise ValueError(f"Unsupported prediction mode: {mode}")

    model_dict = load_model(models_dir, disease)
    feature_names = model_dict["feature_names"]
    medians = load_medians(models_dir)
    calibrators = load_calibrators(models_dir)
    thresholds = load_thresholds(models_dir)

    if disease not in medians or disease not in calibrators or disease not in thresholds:
        raise ValueError(f"Unsupported disease: {disease}")

    features = preprocess_for_inference(df_raw, disease, feature_names, medians[disease], rename_knhanes)
    raw_probability = _predict_proba_single(model_dict, features)
    probability = calibrators[disease].transform(raw_probability)

    threshold = thresholds[disease][mode]["threshold"]
    return pd.DataFrame(
        {
            "raw_probability": raw_probability,
            "probability": probability,
            "threshold": threshold,
            "is_at_risk": (probability >= threshold).astype(bool),
        },
        index=df_raw.index,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 사용 예시 (단일 샘플)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    MODELS_DIR = Path(__file__).parent.parent / "models"

    # 표준명으로 직접 입력하는 경우
    sample = {
        "age": 55,
        "sex": 1,
        "education": 3,
        "height": 170,
        "weight": 75,
        "bmi": 26.0,
        "waist_circumference": 88,
        "sbp": 130,
        "dbp": 82,
        "total_cholesterol": 210,
        "hdl_cholesterol": 48,
        "ldl_cholesterol": 130,
        "triglycerides": 160,
        "creatinine": 1.0,
        "bun": 16,
        "hemoglobin": 14.5,
        "wbc": 6.2,
        "rbc": 4.8,
        "uric_acid": 5.5,
        "hs_crp": 0.3,
        "ast": 28,
        "alt": 22,
        "hematocrit": 43,
        "urine_protein": 0,
        "urine_albumin": 5.0,
        "urine_creatinine": 100,
        "urine_blood": 0,
        "urine_sg": 1.015,
        "urine_glucose": 0,
        "dx_hypertension": 0,
        "dx_dyslipidemia": 0,
        "tx_hypertension": 0,
        "fh_diabetes_father": 0,
        "fh_diabetes_mother": 1,
        "fh_diabetes_sibling": 0,
        "fh_hypertension_father": 0,
        "fh_hypertension_mother": 0,
        "fh_hypertension_sibling": 0,
        "fh_diabetes_parent": 1,
        "fh_hypertension_parent": 0,
        "smoking_status": 3,
        "alcohol_frequency": 3,
        "alcohol_amount": 2,
        "walking_days": 3,
        "sedentary_hours": 8,
        "self_rated_health": 2,
        "sodium_intake": 3500,
        "potassium_intake": 2800,
        "protein_intake": 65,
        "fat_intake": 50,
        "carb_intake": 280,
    }

    df_sample = pd.DataFrame([sample])

    for disease in ["diabetes", "hypertension", "kidney"]:
        result = predict(df_sample, disease, MODELS_DIR, mode="screening")
        print(
            f"[{disease}] probability={result['probability'].iloc[0]:.4f} "
            f"threshold={result['threshold'].iloc[0]:.4f} "
            f"is_at_risk={result['is_at_risk'].iloc[0]}"
        )
