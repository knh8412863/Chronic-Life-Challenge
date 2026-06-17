# API 설계, 보안, 운영 안정성 근거

## 1. API 성능 검증

배포 서버 기준으로 핵심 API의 P95 Latency를 측정했습니다.

근거 문서:

- `docs/performance-result.md`

측정 요약:

- 대상 URL: `https://all4health.kro.kr/api/v1`
- 반복 횟수: endpoint당 20회
- 측정 대상: 로그인, 홈, 알림, 챌린지, 예측 이력, 주간 리포트, 건강 기록 조회 API
- 결과: 모든 측정 API가 P95 3초 이내
- 실패율: 0%

평가 기준 대응:

> P95 3초 이내 성능 테스트 결과를 제시하였다.

OCR, LLM 조언 생성, PDF 생성, SMTP 메일 발송처럼 외부 서비스 또는 파일 처리에 의존하는 API는 일반 조회 API와 분리해서 해석합니다.

## 2. HTTP Method 및 URI 설계

API는 `/api/v1` 버전 prefix 아래에서 도메인별 resource 중심으로 분리했습니다.

대표 URI:

| 도메인 | URI 예시 | 역할 |
| --- | --- | --- |
| 인증 | `/auth/login`, `/auth/signup` | 로그인, 회원가입 |
| 사용자 | `/users/me` | 내 정보 조회/수정 |
| 건강 기록 | `/health/vitals`, `/health/renal-records` | 건강 수치 CRUD |
| 식단 | `/meal-logs`, `/food-analyses` | 식단 기록 및 분석 |
| 예측 | `/prediction-tasks`, `/prediction-results` | 예측 요청 및 결과 조회 |
| 조언 | `/daily-advices` | 오늘의 조언 생성/조회 |
| 리포트 | `/weekly-reports` | 주간 리포트 조회/생성 |
| 챌린지 | `/challenges`, `/challenge-participations/me` | 챌린지 목록/참여 현황 |
| 알림 | `/notifications` | 알림 목록/읽음 처리 |

HTTP Method 사용 기준:

| Method | 사용 목적 | 예시 |
| --- | --- | --- |
| `GET` | 목록/상세 조회 | `GET /health/vitals`, `GET /prediction-results` |
| `POST` | 생성/요청/참여/피드백 등록 | `POST /prediction-tasks`, `POST /challenges/{id}/participations` |
| `PATCH` | 부분 수정/상태 변경 | `PATCH /users/me`, `PATCH /notifications/{id}/read` |
| `DELETE` | 삭제 | `DELETE /health/vitals/{id}` |

일부 URI는 서비스 액션을 명확히 표현하기 위해 `read-all`, `checkins/today`, `exports`, `generate` 같은 action-oriented path를 사용합니다. 이는 알림 일괄 읽음, 오늘 미션 체크인, PDF 내보내기처럼 resource 단순 CRUD로 표현하기 어려운 기능을 구분하기 위한 설계입니다.

평가 기준 대응:

> HTTP Method 및 URI 설계가 명확히 구분되어 있다.

## 3. 배포 및 운영 안정성

서비스는 EC2 단일 인스턴스에서 Docker Compose 기반으로 배포합니다.

운영 구성:

| 구성요소 | 역할 |
| --- | --- |
| Nginx | HTTPS termination, 프론트 정적 파일 서빙, `/api/` reverse proxy |
| FastAPI | 백엔드 API 서버 |
| AI Worker | 예측 작업 비동기 처리 |
| MySQL | 사용자, 건강 기록, 예측 결과 등 영속 데이터 저장 |
| Redis | Rate limit, 캐시성 기능, 상태성 보조 |
| Certbot | HTTPS 인증서 발급 및 갱신 |

운영 안정성 근거:

- 실제 도메인 배포: `https://all4health.kro.kr`
- HTTPS 적용
- Nginx를 통한 프론트/백엔드 경로 분리
- Docker Compose로 서비스별 컨테이너 분리
- FastAPI와 AI Worker를 별도 컨테이너로 운영
- MySQL/Redis healthcheck 기반 의존성 제어
- 성능 테스트를 실제 배포 URL 기준으로 수행

운영 확인 명령 예시:

```bash
curl -I https://all4health.kro.kr/
curl -I https://all4health.kro.kr/api/docs
docker compose ps
docker compose logs --tail=100 fastapi
docker compose logs --tail=100 nginx
```

평가 기준 대응:

> 실제 배포 환경에서 오류 없이 정상 동작한다.

단, OCR, LLM, SMTP, PDF 생성처럼 외부 서비스 또는 파일 처리에 의존하는 기능은 외부 API 상태와 입력 파일 품질에 따라 영향을 받을 수 있습니다.

## 4. 인증 및 인가 보안

서비스는 JWT 기반 인증과 Google OAuth 로그인을 함께 사용합니다.

보안 구성:

| 항목 | 구현 내용 |
| --- | --- |
| 이메일 로그인 | 이메일/비밀번호 기반 로그인 |
| JWT 인증 | access token 기반 보호 API 접근 |
| Google OAuth | Google 계정 기반 로그인/가입 |
| 이메일 인증 | 회원가입 및 이메일 변경 검증 |
| 비밀번호 재설정 | 토큰 기반 재설정 흐름 |
| 로그인 실패 제한 | Redis 기반 rate limit 및 계정 보호 |
| 보호 API | `get_request_user` 의존성으로 인증 사용자 확인 |
| 사용자별 접근 제어 | 요청 사용자 기준으로 본인 데이터만 조회/수정 |
| 보안 헤더 | CSP, HSTS, X-Frame-Options 등 적용 |
| CORS | 허용 Origin 기반 요청 제한 |

대표 근거 파일:

- `app/dependencies/security.py`
- `app/core/security.py`
- `app/core/middlewares/security_headers.py`
- `app/services/auth.py`
- `app/services/rate_limiter.py`

평가 기준 대응:

> JWT/OAuth 등 적절한 인증·인가 체계를 구현하였다.

## 5. 비동기 처리 및 리소스 효율

FastAPI와 Tortoise ORM 기반으로 API와 DB I/O를 비동기 처리하고, 무거운 AI 추론은 별도 워커로 분리했습니다.

비동기 처리 근거:

| 영역 | 적용 내용 |
| --- | --- |
| API 서버 | FastAPI `async def` endpoint 사용 |
| DB I/O | Tortoise ORM async query 사용 |
| AI 예측 | `PredictionTask` 생성 후 `ai-worker`가 비동기적으로 처리 |
| 모델 추론 | `asyncio.to_thread()`로 blocking 추론 작업 분리 |
| 메일 발송 | SMTP 발송을 thread offload 처리 |
| 알림/상태 조회 | 작업 상태를 polling 가능한 API로 분리 |

AI 예측 흐름:

```text
POST /prediction-tasks
→ PredictionTask 생성
→ 202 Accepted 응답
→ ai-worker가 PENDING 작업 처리
→ PredictionResult 저장
→ 사용자는 status API 또는 결과 API로 확인
```

이 구조는 모델 추론이 일반 API 응답을 막지 않도록 분리하기 위한 설계입니다.

성능 측정 결과:

- `docs/performance-result.md` 기준 일반 조회/목록 API는 P95 3초 이내로 측정되었습니다.

평가 기준 대응:

> 비동기 처리를 적용하였다.

동기 처리 대비 직접 비교 실험은 포함하지 않았으므로, “비동기 구조 적용 후 실제 배포 API 성능 측정 결과를 제시하였다”는 범위로 설명합니다.

## 6. 평가 기준 대응 요약

| 평가 항목 | 현재 근거 | 판단 |
| --- | --- | --- |
| 전체 API P95 3초 이내 | 실제 배포 URL 기준 성능 테스트 결과 문서 | 최고 기준 충족 |
| HTTP Method/URI 설계 | `/api/v1` 버전 prefix, resource 중심 URI, Method별 역할 분리 | 높은 점수 가능 |
| 배포 및 운영 안정성 | EC2, HTTPS, Nginx, Docker Compose, 성능 테스트 성공 | 높은 점수 가능 |
| 인증/인가 보안 | JWT, OAuth, 이메일 인증, Rate limit, 사용자별 접근 제어 | 높은 점수 가능 |
| 비동기 처리 | async endpoint, async ORM, ai-worker, `asyncio.to_thread()` | 중상~높은 점수 가능 |

## 7. 한계 및 보완 가능점

- 전체 API를 모두 측정한 것은 아니며, 핵심 사용자 플로우 API 중심으로 P95를 측정했습니다.
- OCR, LLM, SMTP, PDF 생성 API는 외부 의존성 또는 파일 처리 특성상 일반 API와 분리해 측정/해석해야 합니다.
- 비동기 처리의 성능 개선 효과를 더 강하게 입증하려면 동기 처리 대비 비교 실험이 추가로 필요합니다.
- 운영 모니터링을 강화하려면 API latency middleware, 로그 기반 P95 집계, Prometheus/Grafana 같은 관측 도구를 추가할 수 있습니다.
