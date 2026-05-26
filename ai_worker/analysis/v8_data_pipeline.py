"""
V8 데이터 파이프라인 — KNHANES 원본 SAS → 질환별 학습 데이터

의존성:
    pip install pandas pyreadstat scikit-learn
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAS_FILES = ["hn22_all.sas7bdat", "hn23_all.sas7bdat", "hn24_all.sas7bdat"]
DISEASES = ["diabetes", "hypertension", "kidney"]
RANDOM_STATE = 42
TEST_SIZE = 0.2
MIN_AGE = 19  # 성인만

# KNHANES 코딩: 8=해당없음, 9=모름/무응답 → NaN 처리
MISSING_CODES = {8, 9, 88, 99, 888, 999}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 변수 매핑 — KNHANES 원본 → 표준 영문명
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# (원본명, 표준명)
RENAME_MAP = {
    # 인구통계
    "age": "age",
    "sex": "sex",  # 1=남, 2=여
    "edu": "education",  # 1=초졸이하, 2=중졸, 3=고졸, 4=대졸이상
    # 신체계측
    "HE_ht": "height",
    "HE_wt": "weight",
    "HE_BMI": "bmi",
    "HE_wc": "waist_circumference",
    # 혈압
    "HE_sbp": "sbp",
    "HE_dbp": "dbp",
    # 혈액검사 — 기존 V7
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
    # 혈액검사 — V8 신규
    "HE_Uacid": "uric_acid",
    "HE_hsCRP": "hs_crp",
    "HE_ast": "ast",
    "HE_alt": "alt",
    "HE_HCT": "hematocrit",
    # 소변검사
    "HE_Upro": "urine_protein",
    "HE_Ualb": "urine_albumin",
    "HE_Ucrea": "urine_creatinine",  # 혈청 creatinine과 다름!
    "HE_Ubld": "urine_blood",
    "HE_Usg": "urine_sg",
    "HE_Uglu": "urine_glucose",
    # 질환 진단 (교차 피처용)
    "DI1_dg": "dx_diabetes",  # 0=없음, 1=있음
    "DI2_dg": "dx_hypertension",  # 0=없음, 1=있음
    "DI3_dg": "dx_dyslipidemia",  # 0=없음, 1=있음
    "DI1_pt": "tx_diabetes",  # 0=미치료, 1=치료중
    "DI2_pt": "tx_hypertension",
    # 가족력 — 상세 (부/모/형제)
    "HE_DMfh1": "fh_diabetes_father",
    "HE_DMfh2": "fh_diabetes_mother",
    "HE_DMfh3": "fh_diabetes_sibling",
    "HE_HPfh1": "fh_hypertension_father",
    "HE_HPfh2": "fh_hypertension_mother",
    "HE_HPfh3": "fh_hypertension_sibling",
    "DI1_pr": "fh_diabetes_parent",
    "DI2_pr": "fh_hypertension_parent",
    # 흡연
    "BS3_1": "smoking_status",  # 1=매일, 2=가끔, 3=과거, 8=비해당
    # 음주
    "BD1_11": "alcohol_frequency",  # 1=월1미만~5=주4+
    "BD2_1": "alcohol_amount",  # 1=1-2잔~5=10잔+
    # 신체활동
    "BE3_31": "walking_days",  # 주당 걷기 일수
    "BE5_1": "sedentary_hours",  # 하루 좌식시간
    # 주관적 건강/스트레스
    "BP1": "self_rated_health",  # 1=매우좋음~4=나쁨
    # 영양조사
    "N_NA": "sodium_intake",
    "N_K": "potassium_intake",
    "N_PROT": "protein_intake",
    "N_FAT": "fat_intake",
    "N_CHO": "carb_intake",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 라벨 정의 및 누수 피처 목록
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LABEL_DEFS = {
    "diabetes": {
        "description": "공복혈당 ≥ 126 mg/dL",
        "column": "glucose_fasting",
        "threshold": 126,
        "operator": ">=",
    },
    "hypertension": {
        "description": "SBP ≥ 140 OR DBP ≥ 90",
        "columns": ["sbp", "dbp"],
        "thresholds": [140, 90],
        "operator": "or",
    },
    "kidney": {
        "description": "eGFR < 60 (CKD-EPI 2021, from creatinine)",
        "column": "egfr",  # 파생 후 사용
        "threshold": 60,
        "operator": "<",
    },
}

# 질환별 누수 피처 — 라벨 원천이므로 피처에서 반드시 제거
LEAKAGE_FEATURES = {
    "diabetes": [
        "glucose_fasting",  # 라벨 원천
        "hba1c",  # 2-3개월 혈당 반영 → 누수
        "urine_glucose",  # 혈당 ≥180 초과 시 검출 → 라벨(공복혈당≥126)과 동일 생리 경로 하류 마커
    ],
    "hypertension": [
        "sbp",  # 라벨 원천
        "dbp",  # 동일 측정값
        "map_pressure",  # (sbp + 2*dbp)/3 — sbp/dbp 파생
        "pulse_pressure",  # sbp - dbp      — sbp/dbp 파생
    ],
    "kidney": [
        "egfr",  # 라벨 원천
        "creatinine",  # eGFR 계산 입력값 (혈청)
        "uacr",  # KDIGO CKD 분류의 양대 축 → eGFR 라벨과 동일 상태 반영
        "microalbuminuria",  # UACR ≥ 30 파생 플래그 → uacr에서 직접 파생
        "urine_albumin",  # UACR 분자항 → 신장 알부민 누출 직접 마커, 제거해도 성능 유지 확인됨
        "urine_creatinine",  # UACR 분모항 → 소변 크레아티닌도 신장 기능 반영
    ],
}

# 질환별 교차 진단 피처 제어
# 당뇨 모델에 dx_diabetes를 넣으면 "이미 당뇨 진단받은 사람"만 잡음 → 제거
# 하지만 고혈압 모델에 dx_diabetes는 유효한 교차 피처
CROSS_DIAGNOSIS_EXCLUDE = {
    "diabetes": ["dx_diabetes", "tx_diabetes"],
    "hypertension": ["dx_hypertension", "tx_hypertension"],
    "kidney": [],  # 신장은 DI1_dg, DI2_dg 모두 사용 가능
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. eGFR 계산 — CKD-EPI 2021 (race-free)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def calc_egfr_ckd_epi_2021(creatinine: pd.Series, age: pd.Series, sex: pd.Series) -> pd.Series:
    """
    CKD-EPI 2021 (race-free) eGFR 계산.
    sex: 1=남, 2=여 (KNHANES 코딩)
    creatinine: mg/dL
    """
    is_female = sex == 2
    kappa = np.where(is_female, 0.7, 0.9)
    alpha = np.where(is_female, -0.241, -0.302)
    factor = np.where(is_female, 1.012, 1.0)

    cr_over_k = creatinine / kappa
    min_term = np.minimum(cr_over_k, 1.0) ** alpha
    max_term = np.maximum(cr_over_k, 1.0) ** (-1.200)

    egfr = 142 * min_term * max_term * (0.9938**age) * factor
    return pd.Series(egfr, index=creatinine.index).round(2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 전처리 함수들
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def load_and_merge_sas(sas_dir: Path) -> pd.DataFrame:
    """3개년 SAS 파일 로드 + 수직 병합"""
    frames = []
    for fname in SAS_FILES:
        path = sas_dir / fname
        if not path.exists():
            print(f"  ⚠ {fname} 없음 — 건너뜀")
            continue
        year = fname[2:4]  # hn24 → 24
        df = pd.read_sas(str(path))
        df["survey_year"] = int(f"20{year}")
        frames.append(df)
        print(f"  ✓ {fname}: {len(df):,}행 × {df.shape[1]}열")
    merged = pd.concat(frames, ignore_index=True)
    print(f"  → 합산: {len(merged):,}행")
    return merged


def select_and_rename(df: pd.DataFrame) -> pd.DataFrame:
    """원본 변수 선택 + 표준명 변환"""
    available = {k: v for k, v in RENAME_MAP.items() if k in df.columns}
    missing = {k: v for k, v in RENAME_MAP.items() if k not in df.columns}
    if missing:
        print(f"  ⚠ 원본에 없는 변수 {len(missing)}개: {list(missing.keys())[:5]}...")
    result = df[list(available.keys())].rename(columns=available)
    result["survey_year"] = df["survey_year"]
    return result


def clean_missing_codes(df: pd.DataFrame) -> pd.DataFrame:
    """KNHANES 코딩(8, 9 등) → NaN 변환"""
    result = df.copy()
    # 범주형 변수에서 8, 9를 NaN으로
    categorical_cols = [
        "smoking_status",
        "alcohol_frequency",
        "alcohol_amount",
        "walking_days",
        "sedentary_hours",
        "self_rated_health",
        "dx_diabetes",
        "dx_hypertension",
        "dx_dyslipidemia",
        "tx_diabetes",
        "tx_hypertension",
        "fh_diabetes_father",
        "fh_diabetes_mother",
        "fh_diabetes_sibling",
        "fh_hypertension_father",
        "fh_hypertension_mother",
        "fh_hypertension_sibling",
        "fh_diabetes_parent",
        "fh_hypertension_parent",
        "education",
    ]
    for col in categorical_cols:
        if col in result.columns:
            result[col] = result[col].replace(MISSING_CODES, np.nan)
    return result


def filter_adults_with_bloodtest(df: pd.DataFrame) -> pd.DataFrame:
    """성인(19세+) + 혈액검사 수행자 필터"""
    mask = (df["age"] >= MIN_AGE) & (df["glucose_fasting"].notna()) & (df["creatinine"].notna())
    filtered = df[mask].copy()
    print(f"  → 성인+혈액검사: {len(filtered):,}명 (전체 {len(df):,}명 중)")
    return filtered


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 파생변수 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _safe_div(a, b, fill=0.0):
    return a.div(b.replace(0, np.nan)).fillna(fill)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """전체 파생변수 생성 — 질환 공통"""
    result = df.copy()

    # eGFR (CKD-EPI 2021) — 라벨 생성용
    if all(c in result.columns for c in ["creatinine", "age", "sex"]):
        result["egfr"] = calc_egfr_ckd_epi_2021(result["creatinine"], result["age"], result["sex"])

    # UACR (소변 알부민/크레아티닌 비율) — 신장 핵심
    # HE_Ualb: mg/L, HE_Ucrea: mg/dL → UACR = (Ualb) / (Ucrea * 0.01) = mg/g
    if all(c in result.columns for c in ["urine_albumin", "urine_creatinine"]):
        result["uacr"] = _safe_div(result["urine_albumin"], result["urine_creatinine"] * 0.01)
        # 미세알부민뇨 플래그 (UACR ≥ 30)
        result["microalbuminuria"] = (result["uacr"] >= 30).astype("int8")

    # WHtR (허리둘레/키 비율)
    if all(c in result.columns for c in ["waist_circumference", "height"]):
        result["whtr"] = _safe_div(result["waist_circumference"], result["height"])

    # BMI 범주 (KSSO 2022)
    if "bmi" in result.columns:
        result["bmi_category"] = (
            pd.cut(result["bmi"], bins=[0, 18.5, 23, 25, 30, 35, 100], labels=[0, 1, 2, 3, 4, 5], right=False)
            .astype("float32")
            .fillna(1)
        )

    # MAP / Pulse Pressure
    if all(c in result.columns for c in ["sbp", "dbp"]):
        result["map_pressure"] = (result["sbp"] + 2 * result["dbp"]) / 3
        result["pulse_pressure"] = result["sbp"] - result["dbp"]

    # TG/HDL 비율 (인슐린 저항성 프록시)
    if all(c in result.columns for c in ["triglycerides", "hdl_cholesterol"]):
        result["tg_hdl_ratio"] = _safe_div(result["triglycerides"], result["hdl_cholesterol"])

    # Non-HDL 콜레스테롤
    if all(c in result.columns for c in ["total_cholesterol", "hdl_cholesterol"]):
        result["non_hdl_cholesterol"] = result["total_cholesterol"] - result["hdl_cholesterol"]

    # AST/ALT 비율 (De Ritis ratio — 간질환 지표)
    if all(c in result.columns for c in ["ast", "alt"]):
        result["ast_alt_ratio"] = _safe_div(result["ast"], result["alt"])

    # Na/K 비율 (고혈압 식이 위험)
    if all(c in result.columns for c in ["sodium_intake", "potassium_intake"]):
        result["na_k_ratio"] = _safe_div(result["sodium_intake"], result["potassium_intake"])

    # 연령대 구간
    if "age" in result.columns:
        result["age_group"] = (result["age"] // 10).clip(upper=8).astype("float32")
        result["age_bmi"] = result["age"] * result.get("bmi", 0)

    # 흡연 정규화 (1=매일, 2=가끔, 3=과거흡연 → ordinal)
    if "smoking_status" in result.columns:
        # 원본: 1=매일, 2=가끔, 3=과거 (8/9는 이미 NaN)
        # → 0=비흡연(NaN→미해당), 1=과거, 2=현재
        smoke_map = {1: 2, 2: 2, 3: 1}  # 매일/가끔→현재(2), 과거→1
        result["smoking_ordinal"] = result["smoking_status"].map(smoke_map).fillna(0).astype("int8")

    # 가족력 복합 점수
    fh_dm = ["fh_diabetes_father", "fh_diabetes_mother", "fh_diabetes_sibling"]
    fh_hp = ["fh_hypertension_father", "fh_hypertension_mother", "fh_hypertension_sibling"]
    if all(c in result.columns for c in fh_dm):
        result["fh_diabetes_score"] = result[fh_dm].sum(axis=1).clip(upper=3)
    if all(c in result.columns for c in fh_hp):
        result["fh_hypertension_score"] = result[fh_hp].sum(axis=1).clip(upper=3)

    # 음주·흡연 복합 위험
    if all(c in result.columns for c in ["smoking_ordinal", "alcohol_frequency"]):
        smoke_risk = (result["smoking_ordinal"] >= 2).astype("float32")
        alc_risk = (result["alcohol_frequency"] >= 4).astype("float32")  # 주2-3회+
        result["substance_risk"] = smoke_risk + alc_risk

    # 빈혈 플래그 (CKD 동반 빈혈)
    if "hemoglobin" in result.columns:
        result["anemia_flag"] = (result["hemoglobin"] < 12.0).astype("int8")

    # 성별 이진화
    if "sex" in result.columns:
        result["is_female"] = (result["sex"] == 2).astype("int8")

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 라벨 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def create_labels(df: pd.DataFrame) -> dict[str, pd.Series]:
    labels = {}

    # 당뇨: 공복혈당 ≥ 126
    if "glucose_fasting" in df.columns:
        labels["diabetes"] = (df["glucose_fasting"] >= 126).astype(int)

    # 고혈압: SBP ≥ 140 OR DBP ≥ 90
    if all(c in df.columns for c in ["sbp", "dbp"]):
        labels["hypertension"] = ((df["sbp"] >= 140) | (df["dbp"] >= 90)).astype(int)

    # 신장: eGFR < 60
    if "egfr" in df.columns:
        labels["kidney"] = (df["egfr"] < 60).astype(int)

    # 고지혈증: LDL ≥ 130 mg/dL
    if "ldl_cholesterol" in df.columns:
        labels["dyslipidemia"] = (df["ldl_cholesterol"] >= 130).astype(int)

    # 비만: BMI ≥ 25 (한국비만학회 기준)
    if "bmi" in df.columns:
        labels["obesity"] = (df["bmi"] >= 25).astype(int)

    return labels


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 질환별 피처셋 구성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 제거할 메타/라벨 관련 컬럼
META_COLS = {"survey_year", "sex"}


def get_feature_set(df: pd.DataFrame, disease: str) -> pd.DataFrame:
    """질환별 누수 피처 + 교차 진단 피처 제거한 피처셋 반환"""
    exclude = set()
    exclude.update(META_COLS)
    exclude.update(LEAKAGE_FEATURES.get(disease, []))
    exclude.update(CROSS_DIAGNOSIS_EXCLUDE.get(disease, []))
    # 원본 범주형 (이미 파생변수로 대체된 것)
    exclude.update({"smoking_status", "sex"})

    feature_cols = [c for c in df.columns if c not in exclude]

    # 수치형만 남기기 (object 제거)
    features = df[feature_cols].select_dtypes(include="number")
    return features


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 결측치 처리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def handle_missing(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """결측치 처리: 중앙값 대체 (train 기준으"""
    medians = X_train.median(numeric_only=True)
    X_train_filled = X_train.fillna(medians).fillna(0)
    X_test_filled = X_test.fillna(medians).fillna(0)
    return X_train_filled, X_test_filled, medians.to_dict()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 메인 파이프라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def run_pipeline(sas_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"version": "V8", "diseases": {}}

    # 1. 로드 + 병합
    print("\n[Step 1] SAS 파일 로드")
    raw = load_and_merge_sas(sas_dir)

    # 2. 변수 선택 + 이름 변환
    print("\n[Step 2] 변수 선택 및 이름 변환")
    df = select_and_rename(raw)
    print(f"  → {df.shape[1]}개 변수 선택")

    # 3. 결측 코드 처리
    print("\n[Step 3] KNHANES 결측 코드(8/9) → NaN")
    df = clean_missing_codes(df)

    # 4. 성인 + 혈액검사 필터
    print("\n[Step 4] 성인(19+) + 혈액검사 수행자 필터")
    df = filter_adults_with_bloodtest(df)

    # 5. 파생변수 생성
    print("\n[Step 5] 파생변수 생성")
    df = add_derived_features(df)
    print(f"  → 최종 {df.shape[1]}개 변수")

    # 6. 라벨 생성
    print("\n[Step 6] 라벨 생성")
    labels = create_labels(df)
    for disease, y in labels.items():
        pos = y.sum()
        neg = len(y) - pos
        print(f"  {disease:15s}  위험={pos:,}  정상={neg:,}  비율={pos / len(y) * 100:.1f}%")

    # 7. 질환별 피처셋 구성 + 분할 + 저장
    print("\n[Step 7] 질환별 데이터셋 생성")
    for disease in DISEASES:
        if disease not in labels:
            print(f"  ⚠ {disease} 라벨 생성 실패 — 건너뜀")
            continue

        print(f"\n  === {disease.upper()} ===")
        y = labels[disease]

        # 라벨이 유효한 행만
        valid_mask = y.notna()
        y_valid = y[valid_mask]
        df_valid = df[valid_mask]

        # 피처셋 구성 (누수 제거)
        X = get_feature_set(df_valid, disease)
        print(f"  피처: {X.shape[1]}개, 샘플: {len(X):,}명")

        # 피처별 결측률 체크
        null_pct = X.isnull().mean()
        high_null = null_pct[null_pct > 0.5]
        if len(high_null) > 0:
            print(f"  ⚠ 결측률 50%+ 피처 {len(high_null)}개: {high_null.index.tolist()}")

        # Train/Test 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_valid, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_valid
        )

        # 결측치 처리
        X_train, X_test, medians = handle_missing(X_train, X_test)

        # 저장
        prefix = f"v8_{disease}"
        X_train.to_parquet(output_dir / f"{prefix}_train_X.parquet", index=False)
        pd.DataFrame({"risk_label": y_train}).to_parquet(output_dir / f"{prefix}_train_y.parquet", index=False)
        X_test.to_parquet(output_dir / f"{prefix}_test_X.parquet", index=False)
        pd.DataFrame({"risk_label": y_test}).to_parquet(output_dir / f"{prefix}_test_y.parquet", index=False)

        disease_info = {
            "n_features": X_train.shape[1],
            "n_train": len(X_train),
            "n_test": len(X_test),
            "pos_rate_train": float(y_train.mean()),
            "pos_rate_test": float(y_test.mean()),
            "features": X_train.columns.tolist(),
            "leakage_removed": LEAKAGE_FEATURES.get(disease, []),
            "cross_dx_removed": CROSS_DIAGNOSIS_EXCLUDE.get(disease, []),
        }
        report["diseases"][disease] = disease_info

        print(f"  Train: {len(X_train):,}행, Test: {len(X_test):,}행")
        print(f"  피처 목록: {X_train.columns.tolist()[:10]}...")
        print(f"  → 저장: {output_dir / prefix}_*.parquet")

    # 리포트 저장
    report_path = output_dir / "v8_pipeline_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    print(f"\n✅ 파이프라인 완료 → {report_path}")

    return report


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 엔트리포인트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V8 KNHANES → ML 데이터 파이프라인")
    parser.add_argument("--sas-dir", type=str, default="/mnt/user-data/uploads", help="SAS 파일 디렉토리")
    parser.add_argument("--output-dir", type=str, default="/home/claude/dataset/v8", help="출력 디렉토리")
    args = parser.parse_args()

    run_pipeline(Path(args.sas_dir), Path(args.output_dir))
