# API 성능 테스트 결과

- 측정 일시: 2026-06-17 10:38:32 KST
- 대상 Base URL: `https://all4health.kro.kr/api/v1`
- 반복 횟수: endpoint당 20회
- 측정 방식: Python 표준 라이브러리 기반 순차 요청, 클라이언트 측 왕복 시간 측정
- 인증 방식: 로그인 API로 access token 발급 후 보호 API 호출
- 평가 기준: 각 API P95 Latency 3,000ms 이내 여부
- 종합 판단: **P95 3초 이내 성능 테스트 결과를 제시하였다.**

## 측정 범위

- 로그인, 홈 요약, 알림, 챌린지, 예측 이력, 주간 리포트, 건강 기록 조회 API를 대상으로 측정합니다.
- OCR, LLM 조언 생성, PDF 생성, SMTP 메일 발송처럼 외부 서비스 또는 파일 처리에 의존하는 API는 일반 조회 API와 분리해서 해석합니다.
- 네트워크 상태, EC2 리소스 상태, DB 데이터량에 따라 결과가 달라질 수 있습니다.

## 로그인 측정

| API | Count | Success | Failure | Avg(ms) | P50(ms) | P95(ms) | Max(ms) | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `POST /auth/login` | 20 | 20 | 0 | 362.0 | 361.2 | 375.5 | 380.7 | [200] |

## API별 측정 결과

| API | Count | Success | Failure | Failure Rate | Avg(ms) | P50(ms) | P95(ms) | Max(ms) | Status | 판단 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `GET /home/summary` | 20 | 20 | 0 | 0.0% | 79.0 | 78.6 | 82.9 | 86.1 | [200] | 3초 이내 |
| `GET /notifications` | 20 | 20 | 0 | 0.0% | 58.2 | 57.1 | 62.8 | 66.4 | [200] | 3초 이내 |
| `GET /notifications/unread-count` | 20 | 20 | 0 | 0.0% | 58.4 | 56.9 | 66.2 | 73.3 | [200] | 3초 이내 |
| `GET /challenges` | 20 | 20 | 0 | 0.0% | 93.9 | 90.1 | 102.9 | 154.3 | [200] | 3초 이내 |
| `GET /challenges/summary` | 20 | 20 | 0 | 0.0% | 74.5 | 72.7 | 83.8 | 86.7 | [200] | 3초 이내 |
| `GET /challenge-participations/me` | 20 | 20 | 0 | 0.0% | 86.0 | 84.7 | 93.6 | 101.6 | [200] | 3초 이내 |
| `GET /prediction-results?limit=20` | 20 | 20 | 0 | 0.0% | 61.3 | 59.8 | 72.6 | 74.2 | [200] | 3초 이내 |
| `GET /weekly-reports?limit=20` | 20 | 20 | 0 | 0.0% | 78.5 | 76.7 | 84.4 | 92.5 | [200] | 3초 이내 |
| `GET /health/vitals?limit=20` | 20 | 20 | 0 | 0.0% | 60.4 | 59.6 | 70.1 | 71.3 | [200] | 3초 이내 |
| `GET /health/lipid-obesity-records?limit=20` | 20 | 20 | 0 | 0.0% | 58.0 | 57.6 | 63.5 | 66.4 | [200] | 3초 이내 |
| `GET /health/renal-records?limit=20` | 20 | 20 | 0 | 0.0% | 58.0 | 58.2 | 62.1 | 65.3 | [200] | 3초 이내 |
| `GET /health/exercise-logs?limit=20` | 20 | 20 | 0 | 0.0% | 60.0 | 58.8 | 70.8 | 76.7 | [200] | 3초 이내 |
| `GET /health/activity-logs?limit=20` | 20 | 20 | 0 | 0.0% | 59.1 | 57.1 | 69.0 | 80.6 | [200] | 3초 이내 |
| `GET /../docs` | 20 | 20 | 0 | 0.0% | 54.3 | 53.8 | 63.7 | 64.5 | [200] | 3초 이내 |

## 실행 방법

```bash
PERF_EMAIL='테스트계정@example.com' PERF_PASSWORD='테스트비밀번호' \
python scripts/performance_check.py --iterations 20 --output docs/performance-result.md
```

외부 의존/파일 처리 API까지 포함해서 별도로 측정하려면:

```bash
PERF_EMAIL='테스트계정@example.com' PERF_PASSWORD='테스트비밀번호' \
python scripts/performance_check.py --iterations 20 --include-external
```

## 비고

- 결과 문서에는 비밀번호, access token 등 인증 정보가 기록되지 않습니다.
- 실패율이 높은 API는 계정 데이터 부재, 권한 문제, 서버 상태를 별도로 확인해야 합니다.
- 이번 실행에는 외부 의존 API 측정 옵션이 포함되었습니다.
