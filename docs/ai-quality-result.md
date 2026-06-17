# AI 품질 검증 및 개선 근거

## 1. 모델 성능 검증

학습 산출물 기준으로 V8 모델은 train/test 데이터가 분리되어 있으며, 질환별 성능 지표를 별도로 관리합니다.

근거 파일:

- `ai_worker/models/V8/dataset/v8_pipeline_report.json`
- `ai_worker/models/thresholds.json`
- `ai_worker/models/medians.json`
- `ai_worker/models/calibrators.pkl`

### 데이터 분리

| 모델 | Train | Test | Train 양성 비율 | Test 양성 비율 | Feature 수 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 당뇨 | 13,342 | 3,336 | 8.65% | 8.66% | 67 |
| 고혈압 | 13,342 | 3,336 | 13.41% | 13.40% | 66 |
| 만성신장질환 | 13,342 | 3,336 | 3.01% | 3.00% | 66 |

### 성능 지표

| 모델 | 알고리즘 | Test AUC | Screening Precision | Screening Recall | Screening F1 | Diagnostic Precision | Diagnostic Recall | Diagnostic F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 당뇨 | XGBoost | 0.8500 | 0.1907 | 0.8512 | 0.3116 | 0.4538 | 0.4083 | 0.4299 |
| 고혈압 | LGBM + HistGB | 0.7754 | 0.2316 | 0.8501 | 0.3640 | 0.3396 | 0.4832 | 0.3989 |
| 만성신장질환 | XGBoost | 0.9570 | 0.2120 | 0.8500 | 0.3393 | 0.5159 | 0.6500 | 0.5752 |

### 실험 비교

| 모드 | 목적 | 특징 |
| --- | --- | --- |
| Screening | 건강관리 서비스에서 위험 신호를 놓치지 않는 것 | Recall 약 0.85 수준으로 민감도 우선 |
| Diagnostic | 더 강한 위험 신호 중심으로 분류 | Precision과 F1이 Screening 대비 높아지는 경향 |

운영 서비스는 의료 진단이 아니라 건강관리 참고 지표이므로, 위험 신호를 놓치지 않는 Screening threshold를 기본 사용합니다.

## 2. 누수 방지 및 입력 안정화

모델별로 정답에 직접 연결될 수 있는 피처를 제거했습니다.

| 모델 | 제거한 누수 피처 |
| --- | --- |
| 당뇨 | `glucose_fasting`, `hba1c`, `urine_glucose` |
| 고혈압 | `sbp`, `dbp`, `map_pressure`, `pulse_pressure` |
| 만성신장질환 | `egfr`, `creatinine`, `uacr`, `microalbuminuria`, `urine_albumin`, `urine_creatinine` |

추론 시에는 저장된 `feature_names` 순서로 입력을 재정렬하고, 결측값은 학습 데이터 기준 중앙값(`medians.json`)으로 대체합니다.

## 3. 비동기 추론 처리

예측 요청은 API 서버에서 즉시 모델을 실행하지 않고 `PredictionTask`로 저장합니다. 별도 `ai-worker` 프로세스가 대기 작업을 가져와 추론을 수행합니다.

근거 파일:

- `ai_worker/main.py`
- `app/services/predictions.py`
- `infra/docker/docker-compose.prod.yml`

구조:

1. 사용자가 예측 요청 생성
2. FastAPI가 `PredictionTask`를 생성하고 `202 Accepted` 응답
3. `ai-worker`가 `PENDING` 작업을 polling
4. 모델 추론은 `asyncio.to_thread()`로 실행
5. 결과 저장 및 알림 생성

이 구조는 일반 API 요청 흐름과 모델 추론 작업을 분리하여 응답 지연을 줄이기 위한 설계입니다.

## 4. 동일 입력 결과 편차 최소화

동일 입력에 대해 결과 편차를 줄이기 위해 아래 항목을 고정합니다.

- 저장된 모델 파일: `diabetes_model.pkl`, `hypertension_model.pkl`, `kidney_model.pkl`
- 보정기: `calibrators.pkl`
- 결측값 대체 중앙값: `medians.json`
- 위험도 threshold: `thresholds.json`
- 모델 버전: `V8`
- 피처 순서: 모델 파일의 `feature_names`

반복 검증 테스트:

- `app/tests/unit/test_prediction_determinism_rules.py`

해당 테스트는 동일한 모델 입력을 5회 반복 추론하고, 전체 예측 결과가 최초 결과와 동일한지 검증합니다.

## 5. 사용자 피드백 반영 구조

예측 결과에 대한 사용자 피드백은 DB에 저장됩니다.

근거 파일:

- `app/models/predictions.py`
- `app/services/predictions.py`
- `app/apis/v1/prediction_routers.py`

구현 범위:

- 예측 결과별 피드백 등록
- 피드백 중복 등록 방지
- 피드백 여부를 예측 이력에 표시
- 실제 진단값 및 의견 저장
- 모델 개선 검토용 export 스크립트 제공

피드백 export:

```bash
uv run python scripts/export_prediction_feedback.py --output exports/prediction-feedback.csv
```

현재 구조는 피드백을 수집하고 재학습 후보 데이터로 추출할 수 있는 단계까지 구현되어 있습니다. 자동 재학습 파이프라인은 포함하지 않습니다.

## 평가 기준 대응 요약

| 평가 항목 | 현재 근거 | 판단 |
| --- | --- | --- |
| 모델 성능 검증 및 결과 분석 | train/test 분리, AUC/Precision/Recall/F1, Screening/Diagnostic 비교 | 높은 점수 근거 확보 |
| 비동기 처리 | PredictionTask + ai-worker + `asyncio.to_thread()` | 비동기 추론 구조 반영 |
| 동일 입력 편차 최소화 | 고정 모델/보정기/threshold + 반복 테스트 | 최고 기준 근거 확보 |
| 사용자 피드백 구조 | 피드백 저장 + 중복 방지 + export 스크립트 | 수집 및 개선 후보 데이터화 구조 확보 |
