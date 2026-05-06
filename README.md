# Chronic Life Challenge

만성질환(고혈압·당뇨) 생활습관 챌린지 웹 서비스 프로젝트

## 프로젝트 목표

공개 의료/건강 데이터셋을 활용해 사용자의 만성질환 발병 가능성을 예측하고, 
건강 지표 변화 추이를 대시보드로 보여주며, 
생활습관 챌린지를 통해 사용자가 꾸준히 개선 행동을 실천하도록 돕는 웹 서비스입니다.

## 필수 구현 기능

1. 만성질환 예측 모델링
   - Kaggle, AIHub, HuggingFace 등 공개 데이터셋 활용
   - 사용자 건강 데이터 기반 고혈압/당뇨 발병 가능성 예측
   - 예측 결과와 위험도 점수 제공

2. 만성질환 추적 대시보드
   - 사용자 활동/건강 데이터 직접 입력 또는 설문 기반 수집
   - 예측 모델 기반 발병 가능성 변화 추이 제공
   - 혈압, 혈당, BMI, 운동, 수분 섭취, 예측 위험도 차트 제공

3. 생활습관 챌린지
   - 걸음 수, 물 섭취, 운동, 식단 기록 등 만성질환 개선 챌린지 제공
   - 일일 체크인, 진행률, 연속 달성일, 성공/실패 상태 관리

## 선택 구현 후보

- LLM 기반 예방 행동 추천: 사용자 건강/행동 데이터를 바탕으로 일일 맞춤 행동 가이드 생성
- 이미지 분류 기반 식단 분석: 식단 사진 업로드 후 음식 분류 및 영양 피드백
- 알림 기능: 건강 데이터 입력, 챌린지 체크, 주요 가이드 확인 알림

## 먼저 해야 할 일

1. 요구사항 확정
   - `docs/requirements.md`의 MVP 범위를 팀 기준으로 확정합니다.
   - 필수 기능은 반드시 먼저 끝까지 연결합니다.

2. 데이터셋 선정
   - 고혈압/당뇨 예측에 쓸 공개 데이터셋 1개를 정합니다.
   - 입력 컬럼을 서비스 설문/건강 기록 항목과 맞춥니다.

3. AI 베이스라인 모델 만들기
   - 노트북에서 전처리, 학습, 평가를 먼저 진행합니다.
   - 이후 `ai_worker/models`에 모델 파일을 저장하고 FastAPI에서 추론합니다.

4. 백엔드 API 구현
   - 사용자, 건강 기록, 예측 결과, 챌린지 API를 구현합니다.
   - FastAPI Swagger 문서를 API 명세서와 동기화합니다.

5. 대시보드 화면 구현
   - 먼저 목업 데이터로 차트를 만든 뒤 실제 API와 연결합니다.
   - 필수 시각화는 건강 기록 추이와 위험도 변화 추이입니다.

6. Docker 배포 골격 완성
   - FastAPI, AI Worker, DB, Redis, Nginx를 docker compose로 묶습니다.
   - EC2 배포 전 로컬 compose 실행을 검증합니다.

## 프로젝트 구조

```text
.
├── README.md                    # 프로젝트 소개, 필수 기능, 실행 방법, 폴더 구조 안내
├── docs/                        # 기획/설계/명세 문서 보관
│   ├── requirements.md          # 요구사항 정의서: 기능/비기능 요구사항과 MVP 범위
│   ├── architecture.md          # 시스템 아키텍처: 백엔드, AI Worker, Redis, DB 흐름
│   ├── api-spec.md              # API 명세서 초안: 엔드포인트, 요청/응답 기준
│   └── project-plan.md          # 주차별 개발 계획과 우선순위
├── backend/                     # FastAPI 백엔드 서버 코드
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 시작점, 라우터 등록, 헬스체크 API
│   │   ├── api/v1/              # API 라우터 모음: users, records, predictions 등
│   │   ├── core/                # 환경설정, 보안, DB 연결 같은 공통 설정
│   │   ├── models/              # DB 테이블 모델 정의
│   │   ├── repositories/        # DB 조회/저장 로직 분리
│   │   ├── schemas/             # Pydantic 요청/응답 스키마 정의
│   │   └── services/            # 비즈니스 로직: 예측 요청, 챌린지 진행률 계산 등
│   └── Dockerfile               # 백엔드 서버 Docker 이미지 빌드 설정
├── ai_worker/                   # AI 모델 학습/추론 담당 워커
│   ├── datasets/                # 공개 데이터셋 원본/전처리 데이터 보관
│   ├── models/                  # 학습된 모델 파일, 모델 메타데이터 보관
│   ├── notebooks/               # 데이터 탐색, 전처리, 베이스라인 학습 노트북
│   ├── src/                     # 학습/추론 파이프라인 Python 코드
│   └── Dockerfile               # AI Worker Docker 이미지 빌드 설정
├── frontend/                    # 사용자 화면 코드
│   └── src/                     # 대시보드, 건강 기록 입력, 챌린지 UI 구현 위치
├── docker/                      # Docker 관련 보조 설정 파일 보관
├── nginx/
│   └── default.conf             # Nginx 리버스 프록시 설정
├── envs/
│   └── .env.example             # 환경변수 예시 파일, 실제 비밀값은 .env에 작성
├── scripts/                     # 실행/배포/데이터 처리 자동화 스크립트
├── tests/                       # 테스트 코드
│   ├── backend/                 # 백엔드 API/서비스 테스트
│   └── ai_worker/               # 모델 전처리/추론 로직 테스트
├── docker-compose.yml           # 로컬/배포용 컨테이너 구성
└── pyproject.toml               # Python 프로젝트 메타정보와 의존성 정의
```

## 로컬 실행


```bash
uv sync --all-groups
uv run uvicorn backend.app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```
