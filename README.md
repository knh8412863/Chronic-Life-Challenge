# All4Health

만성질환 관리가 필요한 사용자가 건강 수치와 생활습관을 기록하고, AI 질환 예측, 맞춤형 건강 조언, 챌린지, 펫 보상 시스템을 통해 지속적으로 건강 행동을 개선할 수 있도록 설계한 웹 서비스입니다.

본 프로젝트는 고혈압, 당뇨, 만성신장질환 등 주요 만성질환을 중심으로 건강설문, 혈압/혈당, 지질 지표, 신장 지표, 운동, 식단, 생활습관 데이터를 수집하고 이를 기반으로 개인화된 건강 관리 경험을 제공합니다.

---

## 주요 기능

### 인증 및 사용자 관리

- 이메일 회원가입, 로그인, 로그아웃
- 이메일 인증 및 비밀번호 재설정
- Google OAuth 로그인 및 Google 계정 기반 신규 가입
- 로그인 실패 횟수 기반 계정 잠금 처리
- JWT 기반 인증 및 보호 API 접근 제어
- 마이페이지 비밀번호 재확인
- 내 정보 조회 및 수정
- 비밀번호 변경
- 알림 설정 관리
- 약관 동의 관리
- 회원 탈퇴

### 건강 기록 관리

- 건강설문 입력
- 혈압/혈당 기록
- 지질 지표 기록
- 신장 지표 기록
- 운동 기록
- 일일 활동 기록
- 여러 건강 기록 탭의 통합 저장
- 하루 건강 기록 입력 횟수 제한
- 당일 기록 수정/삭제 제한
- 건강 기록 목록 및 유형별 필터링
- 건강 목표 설정 및 최근 입력값 기반 목표 관리
- 홈 대시보드 건강점수 표시

### AI 질환 예측

- 당뇨, 고혈압, 만성신장질환 위험도 예측
- 건강설문과 최신 건강 수치를 조합한 예측 입력 생성
- 건강설문이 없는 경우에도 최신 건강 기록과 회원 기본정보를 기반으로 예측 가능
- 입력되지 않은 항목은 기본값 처리 및 미입력 항목 안내
- 임상 기준 기반 위험도 보정
- 예측 진행 상태 조회
- 예측 결과 상세 조회
- 예측 이력 조회
- 예측 결과 피드백 등록

### 건강 조언 및 리포트

- 오늘의 건강 조언 생성
- 조언 재생성 횟수 제한
- 조언 이력 조회
- 조언 피드백
- 주간 건강 리포트 조회
- 리포트 PDF 내보내기
- 건강 데이터 내보내기
- OpenAI API 기반 LLM 조언/리포트 생성 옵션

### 식단 관리

- 식단 직접 입력
- 식단 분석 결과 저장
- 식단 기록 목록 조회
- 식단 기록 상세 조회
- 식단 기록 수정/삭제
- 일일 식단 요약

### 챌린지 및 보상

- 챌린지 목록 조회
- 챌린지 상세 조회
- 챌린지 참여 및 취소
- 내 챌린지 관리
- 챌린지 요약 대시보드
- 리더보드
- 뱃지 목록
- 챌린지 달성 기반 보상 처리

### 마이펫

- 펫 선택
- 펫 성장 상태 조회
- 펫 이름 변경
- 보상 과제 완료 여부 조회
- 보상 수령 및 경험치 반영
- 펫 도감
- 펫 종류: 강아지, 고양이, 토끼, 카피바라, 햄스터
- 레벨별 펫 이미지 표시

### 알림

- 알림 목록 조회
- 알림 읽음 처리
- 전체 읽음 처리
- 알림 설정 저장
- 예측 결과, 챌린지, 펫 보상, 조언 업데이트 등 서비스 이벤트 알림

---

## 기술 스택

### Backend

- Python 3.13+
- FastAPI
- Tortoise ORM
- Aerich Migration
- MySQL
- Redis
- JWT 인증
- SMTP / AWS SES 메일 발송
- OpenAI API 연동
- Pytest
- Ruff

### AI Worker

- Python 기반 별도 워커 프로세스
- 질환 예측 태스크 비동기 처리
- 저장된 모델 파일 기반 추론
- 당뇨, 고혈압, 만성신장질환 모델
- 예측 결과 저장 및 알림 생성

### Frontend

- React
- TypeScript
- Vite
- CSS 기반 반응형 UI
- SPA 라우팅
- Nginx 정적 파일 서빙

### Infra

- Docker
- Docker Compose
- Nginx Reverse Proxy
- AWS EC2
- HTTPS Certbot
- Docker Hub 이미지 배포
- MySQL, Redis 컨테이너 구성

---

## 프로젝트 구조

```text
.
├── app/                         # FastAPI 백엔드
│   ├── apis/v1/                 # API 라우터
│   ├── core/                    # 설정, DB, JWT, 보안 미들웨어
│   ├── dependencies/            # 인증 의존성
│   ├── dtos/                    # Pydantic 요청/응답 DTO
│   ├── models/                  # Tortoise ORM 모델
│   ├── repositories/            # 저장소 계층
│   ├── services/                # 비즈니스 로직
│   └── tests/                   # API/단위 테스트
├── ai_worker/                   # AI 예측 워커
│   ├── analysis/                # 모델 학습/보정 스크립트
│   ├── core/                    # 워커 설정 및 로거
│   ├── models/                  # 모델 파일
│   ├── schemas/                 # 워커 스키마
│   ├── tasks/                   # 추론 전처리 및 실행 로직
│   └── main.py                  # 워커 진입점
├── frontend/                    # React 프론트엔드
│   ├── src/api/                 # API 클라이언트
│   ├── src/assets/              # 이미지, 아이콘, 펫 리소스
│   ├── src/components/          # 공통 컴포넌트
│   ├── src/layouts/             # 공통 레이아웃
│   ├── src/pages/               # 화면 페이지
│   ├── src/styles/              # 전역 스타일
│   └── src/utils/               # 유틸 함수
├── infra/                       # 인프라 설정
│   ├── docker/                  # 운영 Docker Compose 설정
│   └── nginx/                   # Nginx HTTP/HTTPS 설정
├── scripts/                     # 배포, 인증서, CI 스크립트
├── docker-compose.yml           # 로컬 Docker Compose 설정
├── pyproject.toml               # Python 의존성 및 도구 설정
└── README.md
```

---

## 환경 변수

루트의 `.env`는 로컬 실행과 Docker Compose 실행에서 사용됩니다. 실제 키와 비밀번호는 Git에 커밋하지 않습니다.

예시 파일:

```bash
envs/example.local.env
envs/example.prod.env
```

주요 환경 변수 항목:

- `ENV`: 실행 환경
- `SECRET_KEY`: JWT 및 보안 토큰 서명 키
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: MySQL 연결 정보
- `REDIS_URL`: Redis 연결 정보
- `OPENAI_API_KEY`: LLM 조언/리포트 생성용 API 키
- `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
- `GOOGLE_JWKS_URL`: Google 공개키 URL
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`: 메일 발송 설정
- `FRONTEND_BASE_URL`: 이메일 인증/비밀번호 재설정 링크 기준 URL
- `CORS_ALLOW_ORIGINS`: 허용할 프론트엔드 Origin
- `COOKIE_DOMAIN`: 쿠키 도메인

주의:

- `.env`, `envs/.local.env`, `envs/.prod.env`, `frontend/.env.local`, `frontend/.env.production` 등 실제 환경 변수 파일은 커밋하지 않습니다.
- 로컬에서 FastAPI를 직접 실행할 때는 DB/Redis Host가 로컬 기준이어야 합니다.
- Docker Compose 내부에서 실행할 때는 DB/Redis Host가 서비스명 기준이어야 합니다.

---

## 로컬 실행

### 1. 백엔드 의존성 설치

```bash
uv sync
```

### 2. DB 마이그레이션

```bash
uv run aerich upgrade
```

### 3. FastAPI 실행

```bash
uv run uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/api/docs
```

### 4. AI Worker 실행

```bash
uv run python -m ai_worker.main
```

### 5. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

Vite 개발 서버:

```text
http://localhost:5173
```

---

## Docker 실행

전체 스택 실행:

```bash
docker compose up -d --build
```

주요 서비스:

- `fastapi`: 백엔드 API 서버
- `ai-worker`: 예측 워커
- `mysql`: 데이터베이스
- `redis`: 캐시 및 Rate Limit
- `nginx`: Reverse Proxy 및 프론트 정적 파일 서빙

로그 확인:

```bash
docker compose logs --tail=100 fastapi
docker compose logs --tail=100 ai-worker
docker compose logs --tail=100 nginx
```

---

## 배포 구조

현재 배포는 EC2 단일 인스턴스 기준입니다.

- Nginx가 `/` 요청에 대해 프론트엔드 정적 파일을 제공합니다.
- Nginx가 `/api/` 요청을 FastAPI 컨테이너로 프록시합니다.
- FastAPI와 AI Worker는 Docker 이미지로 빌드 후 Docker Hub에 푸시합니다.
- EC2에서 이미지를 pull 한 뒤 컨테이너를 재생성합니다.
- HTTPS는 Certbot으로 발급한 인증서를 Nginx에 연결합니다.

### 백엔드/워커 이미지 빌드 및 푸시

```bash
docker compose build fastapi ai-worker
docker compose push fastapi ai-worker
```

### EC2에서 컨테이너 반영

```bash
cd ~/ai_project
docker compose pull fastapi ai-worker
docker compose up -d --force-recreate fastapi ai-worker
```

### 프론트엔드 빌드 및 업로드

로컬 프로젝트 루트에서 실행합니다.

```bash
cd frontend
npm run build
cd ..
ssh -i ~/.ssh/all4health.pem ubuntu@15.165.80.166 "cd ~/ai_project && rm -rf frontend-dist && mkdir frontend-dist"
scp -r -i ~/.ssh/all4health.pem frontend/dist/* ubuntu@15.165.80.166:~/ai_project/frontend-dist/
ssh -i ~/.ssh/all4health.pem ubuntu@15.165.80.166 "cd ~/ai_project && docker compose up -d --force-recreate nginx"
```

배포 확인:

```bash
curl -I https://all4health.kro.kr/api/docs
```

`curl -I`는 HEAD 요청이므로 FastAPI docs에서 `405 Method Not Allowed`가 나올 수 있습니다. `allow: GET`이 보이면 서버가 응답 중인 상태입니다.

---

## 테스트 및 품질 관리

### 백엔드 테스트

```bash
uv run pytest app
```

### 백엔드 린트

```bash
uv run ruff check .
```

### 백엔드 포맷 체크

```bash
uv run ruff format . --check
```

### 프론트엔드 빌드

```bash
cd frontend
npm run build
```

### CI 스크립트

```bash
./scripts/ci/run_test.sh
./scripts/ci/code_fommatting.sh
./scripts/ci/check_mypy.sh
```

---

## API 문서

로컬:

```text
http://127.0.0.1:8000/api/docs
```

배포:

```text
https://all4health.kro.kr/api/docs
```

---

## 핵심 API 영역

- `/api/v1/auth`: 회원가입, 로그인, 이메일 인증, 비밀번호 재설정, Google 로그인
- `/api/v1/users`: 내 정보, 비밀번호 변경, 약관 동의, 회원탈퇴
- `/api/v1/health`: 건강 수치, 운동, 활동, 식단, 목표 관리
- `/api/v1/prediction-inputs`: 건강설문 입력
- `/api/v1/prediction-tasks`: 질환 예측 요청 및 진행 상태
- `/api/v1/prediction-results`: 예측 결과 및 피드백
- `/api/v1/advices`: 오늘의 조언, 조언 이력, 피드백
- `/api/v1/reports`: 주간 건강 리포트
- `/api/v1/challenges`: 챌린지, 리더보드, 뱃지
- `/api/v1/pets`: 마이펫, 보상 과제, 펫 도감
- `/api/v1/notifications`: 알림 목록 및 설정
- `/api/v1/data-exports`: 건강 데이터 내보내기

---

## 현재 운영상 주의사항

- 프로필 이미지는 현재 URL 저장 구조이며, 실제 이미지 파일 업로드를 안정적으로 운영하려면 S3 또는 서버 볼륨 기반 업로드 API가 필요합니다.
- Docker 컨테이너 재생성 시 유지되어야 하는 파일은 Docker volume으로 관리해야 합니다.
- 실제 운영 환경에서는 `.env` 값을 서버에서만 관리하고 GitHub에 커밋하지 않습니다.

---

## 팀 개발 규칙

- 기능 브랜치에서 작업 후 PR을 통해 `develop`에 머지합니다.
- `develop`에서 검증 후 `main`으로 병합합니다.
- `.env` 계열 파일은 커밋하지 않습니다.
- 백엔드 변경 시 관련 테스트를 추가하거나 기존 테스트를 갱신합니다.
- 프론트 변경 시 `npm run build`로 타입/빌드 오류를 확인합니다.
- 배포 전 `ruff check`, `pytest`, `npm run build`를 확인합니다.
